#!/usr/bin/env python3
import argparse
import time
import json
import os
import signal
import threading
from datetime import datetime
from config import (
    LOG_DIR,
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_KEY,
    MQTT_TELEMETRY_FEED,
    MQTT_COMMAND_FEED,
)
from logger import log_jsonl
from mqtt_client import MQTTClient
from car import Car
from camera import Camera
from buzzer import Buzzer

# Global flags
running = True
car_active = False
_capture_lock = threading.Lock()
_is_capturing = False


def handle_sigint(signum, frame):
    global running
    print("[INFO] SIGINT received, shutting down...")
    running = False


signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGTERM, handle_sigint)


def create_car(simulate=False):
    return Car(simulate=simulate)


def _capture_image_thread(camera: Camera, path: str):
    global _is_capturing
    with _capture_lock:
        if _is_capturing:
            return
        _is_capturing = True

    try:
        started_here = False
        try:
            if hasattr(camera, "camera"):
                started_attr = getattr(camera.camera, "started", None)
                if not started_attr and hasattr(camera.camera, "start"):
                    try:
                        camera.camera.start()
                        started_here = True
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            camera.save_image(path)
            print(f"[CAM] Saved image: {path}")
        except Exception as e:
            print("[CAM] Error saving image:", e)

    finally:
        if started_here:
            try:
                camera.camera.stop()
            except Exception:
                pass
        with _capture_lock:
            _is_capturing = False


def main(simulate=False):
    global running, car_active, _is_capturing

    car = create_car(simulate=simulate)
    initial_mode = "infrared_ultrasonic" if not simulate else "simulate"
    car.current_mode = initial_mode

    buzzer = car.buzzer
    mqtt = MQTTClient(on_command=on_command_factory(car, buzzer))
    camera = Camera()

    capture_dir = os.path.join(os.getcwd(), "captures")
    os.makedirs(capture_dir, exist_ok=True)

    try:
        mqtt.connect()
    except Exception as e:
        print("[ERROR] MQTT connect failed:", e)

    print(f"[INFO] Starting main loop (simulate={simulate}) mode={car.current_mode}")

    last_telemetry = 0
    buzzer_on = False

    try:
        while running:
            try:
                mode = getattr(car, "current_mode", initial_mode)

                if not car_active:
                    try:
                        car.motor.set_motor_model(0, 0, 0, 0)
                    except Exception:
                        pass
                    if buzzer_on:
                        try:
                            buzzer.set_state(False)
                        except Exception:
                            pass
                        buzzer_on = False
                    time.sleep(0.1)
                    continue

                if mode == "infrared_ultrasonic":
                    distance = car.sonic.get_distance()
                    ir_bits = car.infrared.read_all_infrared()
                    left = (ir_bits >> 2) & 1
                    mid = (ir_bits >> 1) & 1
                    right = ir_bits & 1

                    print(f"[SENSORS] IR={ir_bits:03b} (L:{left} M:{mid} R:{right}) | Distance={distance}")

                    # --- Obstacle detected ---
                    if distance is not None and distance < 20:
                        print("[AVOID] Obstacle detected — stopping.")
                        car.motor.set_motor_model(0, 0, 0, 0)

                        if not buzzer_on:
                            buzzer.set_state(True)
                            buzzer_on = True

                        time.sleep(0.5)

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_path = os.path.join(capture_dir, f"obstacle_{timestamp}.jpg")
                        with _capture_lock:
                            already = _is_capturing
                        if not already:
                            t = threading.Thread(target=_capture_image_thread, args=(camera, img_path), daemon=True)
                            t.start()

                        print("[AVOID] Reversing...")
                        car.motor.set_motor_model(-500, -500, -500, -500)
                        time.sleep(0.8)
                        car.motor.set_motor_model(0, 0, 0, 0)

                        if buzzer_on:
                            buzzer.set_state(False)
                            buzzer_on = False

                    elif mid == 1 and (distance is None or distance >= 20):
                        print("[MOVE] Moving forward.")
                        car.motor.set_motor_model(450, 450, 450, 450)
                        if buzzer_on:
                            buzzer.set_state(False)
                            buzzer_on = False

                    elif left == 1:
                        print("[ADJUST] Turning left.")
                        car.motor.set_motor_model(-600, -600, 1000, 1000)
                        if not buzzer_on:
                            buzzer.set_state(True)
                            buzzer_on = True

                    elif right == 1:
                        print("[ADJUST] Turning right.")
                        car.motor.set_motor_model(1000, 1000, -600, -600)
                        if not buzzer_on:
                            buzzer.set_state(True)
                            buzzer_on = True

                    else:
                        print("[STOP] No valid IR input.")
                        car.motor.set_motor_model(0, 0, 0, 0)
                        if buzzer_on:
                            buzzer.set_state(False)
                            buzzer_on = False

                    time.sleep(0.05)

                elif mode == "infrared":
                    car.mode_infrared()
                elif mode == "ultrasonic":
                    car.mode_ultrasonic()
                elif mode == "light":
                    car.mode_light()

                # Telemetry every 10s
                now = time.time()
                if now - last_telemetry > 10.0:
                    last_telemetry = now
                    telem = collect_telemetry(car, mode)
                    log_jsonl(telem)
                    try:
                        mqtt.publish(
                            os.environ.get(
                                "MQTT_TELEMETRY_FEED",
                                f"{MQTT_USERNAME}/feeds/smartcar-telemetry",
                            ),
                            json.dumps(telem),
                        )
                    except Exception as e:
                        print("[MQTT] Telemetry publish failed:", e)

            except Exception as e:
                print("[MAIN] Loop error:", e)
                time.sleep(0.2)

    finally:
        print("[INFO] Shutting down...")
        try:
            buzzer.set_state(False)
            buzzer.close()
        except Exception:
            pass
        try:
            camera.close()
        except Exception:
            pass
        try:
            car.close()
        except Exception:
            pass
        try:
            mqtt.disconnect()
        except Exception:
            pass


def collect_telemetry(car, mode):
    data = {
        "mode": mode,
        "simulate": car.simulate,
        "ir": None,
        "distance": None,
        "battery": None,
        "motor": getattr(car.motor, "last", None),
        "car_active": car_active,
    }
    try:
        data["ir"] = car.infrared.read_all_infrared()
    except Exception:
        data["ir"] = None
    try:
        data["distance"] = car.sonic.get_distance()
    except Exception:
        data["distance"] = None
    try:
        data["battery"] = car.adc.read_adc(2) * (
            3 if getattr(car.adc, "pcb_version", 2) == 1 else 2
        )
    except Exception:
        data["battery"] = None

    data["ts"] = datetime.utcnow().isoformat() + "Z"
    return data


def on_command_factory(car, buzzer):
    def _on_cmd(topic, payload):
        global car_active, _is_capturing
        print("[MQTT CMD]", topic, payload)

        if isinstance(payload, dict):
            cmd = payload.get("command")
            mode = payload.get("mode")

            if cmd == "stop":
                print("[CMD] Stop command received.")
                car_active = False
                try:
                    car.motor.set_motor_model(0, 0, 0, 0)
                except Exception:
                    pass
                try:
                    buzzer.set_state(False)
                except Exception as e:
                    print(f"[BUZZER] Stop failed: {e}")
                with _capture_lock:
                    _is_capturing = False

            elif cmd == "start":
                print("[CMD] Start command received.")
                car_active = True

            elif cmd == "mode" and mode:
                if mode in ("ultrasonic", "infrared", "infrared_ultrasonic", "light"):
                    print(f"[CMD] Switching mode to {mode}")
                    car.current_mode = mode
                else:
                    print(f"[WARN] Unknown mode {mode}")

        else:
            print("[WARN] Unknown command format:", payload)

    return _on_cmd


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["simulate", "hardware"], default="hardware")
    args = parser.parse_args()
    simulate = args.mode == "simulate"
    main(simulate=simulate)
