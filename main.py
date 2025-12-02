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
    CLOUD_DB_URL,
    LOCAL_DB_FILE,
    CAPTURE_DIR
)

from logger import log_jsonl
from mqtt_client import MQTTClient
from car import Car
from camera import Camera
from buzzer import Buzzer
from localdb import LocalDB
from sync_to_cloud import CloudSync

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


def _capture_image_thread(camera: Camera, path: str, mqtt: MQTTClient = None):
    """
    Non-blocking capture worker.
    """
    global _is_capturing
    with _capture_lock:
        if _is_capturing:
            return
        _is_capturing = True

    started_here = False
    try:
        # Try starting camera if necessary
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

            # Publish image URL to MQTT for frontend
            if mqtt is not None:
                image_url = f"http://<RPI_IP>:5000/images/{os.path.basename(path)}"
                mqtt.publish("JDover9000/feeds/smartcar-images", json.dumps({"url": image_url}))
                print(f"[MQTT] Published image URL: {image_url}")

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


def _execute_manual_command(car: Car, buzzer: Buzzer, cmd: str):
    """
    Execute immediate manual command. Defensive: captures exceptions so handler won't crash.
    """
    try:
        if cmd == "forward":
            print("[MANUAL] Forward")
            car.motor.set_motor_model(800, 800, 800, 800)
        elif cmd == "backward":
            print("[MANUAL] Backward")
            car.motor.set_motor_model(-800, -800, -800, -800)
        elif cmd == "left":
            print("[MANUAL] Turn Left")
            car.motor.set_motor_model(-600, -600, 1000, 1000)
        elif cmd == "right":
            print("[MANUAL] Turn Right")
            car.motor.set_motor_model(1000, 1000, -600, -600)
        elif cmd == "stop" or cmd == "manual_stop":
            print("[MANUAL] Stop")
            car.motor.set_motor_model(0, 0, 0, 0)
        elif cmd == "buzzer_on":
            print("[MANUAL] Buzzer ON")
            buzzer.set_state(True)
        elif cmd == "buzzer_off":
            print("[MANUAL] Buzzer OFF")
            buzzer.set_state(False)
        else:
            print(f"[MANUAL] Unknown manual command: {cmd}")
    except Exception as e:
        print(f"[MANUAL] Error executing '{cmd}':", e)


def on_command_factory(car, buzzer, camera, mqtt):
    """
    Command handler that accepts:
    - start / stop
    - mode switches
    - manual movement commands
    - buzzer toggles
    - led controls
    - take_photo / capture
    """
    def _on_cmd(topic, payload):
        global car_active, _is_capturing
        print("[MQTT CMD]", topic, payload)

        cmd = None
        mode_value = None

        try:
            if isinstance(payload, dict):
                cmd = payload.get("command") or payload.get("value")
                mode_value = payload.get("mode") or payload.get("mode_value")
            else:
                cmd = payload
        except Exception:
            cmd = payload

        # Decode bytes if needed
        if isinstance(cmd, (bytes, bytearray)):
            cmd = cmd.decode("utf-8")

        if cmd is None:
            print("[MQTT CMD] No command found in payload.")
            return

        cmd_norm = str(cmd).strip().lower()

        try:
            # Global stop/start
            if cmd_norm == "stop":
                print("[CMD] Stop command received.")
                car_active = False
                try:
                    car.motor.set_motor_model(0, 0, 0, 0)
                    buzzer.set_state(False)
                except Exception:
                    pass
                with _capture_lock:
                    _is_capturing = False
                return

            if cmd_norm == "start":
                print("[CMD] Start command received.")
                car_active = True
                return

            # Mode switching
            if mode_value:
                m = mode_value
                if m in ("ultrasonic", "infrared", "infrared_ultrasonic", "light", "manual"):
                    car.current_mode = m
                    car_active = True
                return

            if cmd_norm.startswith("mode_"):
                m = cmd_norm[len("mode_"):]
                if m in ("ultrasonic", "infrared", "infrared_ultrasonic", "light", "manual"):
                    car.current_mode = m
                    car_active = True
                    return

            # Manual commands
            manual_cmds = ("forward", "backward", "left", "right", "stop", "manual_stop", "buzzer_on", "buzzer_off")
            if cmd_norm in manual_cmds:
                if cmd_norm in ("forward", "backward", "left", "right"):
                    car.current_mode = "manual"
                    car_active = True
                _execute_manual_command(car, buzzer, cmd_norm)
                return

            # LED commands
            if cmd_norm in ("led_on", "led_off", "led1_on", "led1_off", "led2_on", "led2_off"):
                try:
                    if cmd_norm == "led_on":
                        car.set_led("all", True)
                    elif cmd_norm == "led_off":
                        car.set_led("all", False)
                    elif cmd_norm == "led1_on":
                        car.set_led("led1", True)
                    elif cmd_norm == "led1_off":
                        car.set_led("led1", False)
                    elif cmd_norm == "led2_on":
                        car.set_led("led2", True)
                    elif cmd_norm == "led2_off":
                        car.set_led("led2", False)
                    print(f"[LED CMD] {cmd_norm} executed")
                except Exception as e:
                    print("[LED CMD] Error:", e)
                return

            # Take photo / capture
            if cmd_norm in ("take_photo", "capture"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img_path = os.path.join(CAPTURE_DIR, f"manual_{timestamp}.jpg")
                with _capture_lock:
                    already = _is_capturing
                if not already:
                    t = threading.Thread(target=_capture_image_thread, args=(camera, img_path, mqtt), daemon=True)
                    t.start()
                    print("[CMD] capture started:", img_path)
                else:
                    print("[CMD] capture already in progress")
                return

            print(f"[CMD] Unhandled command: {cmd_norm}")

        except Exception as e:
            print("[CMD] Error handling command:", e)

    return _on_cmd


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
        data["battery"] = car.adc.read_adc(2) * (3 if getattr(car.adc, "pcb_version", 2) == 1 else 2)
    except Exception:
        data["battery"] = None
    data["ts"] = datetime.utcnow().isoformat() + "Z"
    return data


def main(simulate=False):
    global running, car_active, _is_capturing

    car = create_car(simulate=simulate)
    camera = Camera()
    initial_mode = "infrared_ultrasonic" if not simulate else "simulate"
    car.current_mode = initial_mode

    # Use car's buzzer
    buzzer = car.buzzer
    os.makedirs(CAPTURE_DIR, exist_ok=True)

    # Local DB + Cloud Sync
    os.makedirs(os.path.dirname(LOCAL_DB_FILE), exist_ok=True)
    local_db = LocalDB(LOCAL_DB_FILE)
    cloud_sync = CloudSync(CLOUD_DB_URL, local_db, interval=30)
    cloud_sync.start()

    mqtt = MQTTClient(on_command=on_command_factory(car, buzzer, camera, None))  # temp None
    mqtt.connect()
    mqtt.on_command = on_command_factory(car, buzzer, camera, mqtt)

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

                # --- Autonomous modes ---
                if mode == "infrared_ultrasonic":
                    distance = car.sonic.get_distance()
                    ir_bits = car.infrared.read_all_infrared()
                    left = (ir_bits >> 2) & 1
                    mid = (ir_bits >> 1) & 1
                    right = ir_bits & 1

                    print(f"[SENSORS] IR={ir_bits:03b} (L:{left} M:{mid} R:{right}) | Distance={distance}")

                    # --- Obstacle avoidance ---
                    if distance is not None and distance < 20:
                        print("[AVOID] Obstacle detected — stopping.")
                        car.motor.set_motor_model(0, 0, 0, 0)

                        if not buzzer_on:
                            buzzer.set_state(True)
                            buzzer_on = True

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_path = os.path.join(CAPTURE_DIR, f"obstacle_{timestamp}.jpg")
                        with _capture_lock:
                            already = _is_capturing
                        if not already:
                            t = threading.Thread(target=_capture_image_thread, args=(camera, img_path, mqtt), daemon=True)
                            t.start()

                        print("[AVOID] Reversing...")
                        car.motor.set_motor_model(-500, -500, -500, -500)
                        time.sleep(0.8)
                        car.motor.set_motor_model(0, 0, 0, 0)

                        if buzzer_on:
                            buzzer.set_state(False)
                            buzzer_on = False

                        time.sleep(0.05)
                        continue

                    # --- Line tracking ---
                    if mid == 1 and left == 0 and right == 0:
                        car.motor.set_motor_model(700, 700, 700, 700)
                    elif left == 1 and mid == 0:
                        car.motor.set_motor_model(400, 400, 700, 700)
                    elif right == 1 and mid == 0:
                        car.motor.set_motor_model(700, 700, 400, 400)
                    elif left == 1 and mid == 1:
                        car.motor.set_motor_model(600, 600, 700, 700)
                    elif right == 1 and mid == 1:
                        car.motor.set_motor_model(700, 700, 600, 600)
                    elif left == 1 and mid == 1 and right == 1:
                        car.motor.set_motor_model(700, 700, 700, 700)
                    else:
                        car.motor.set_motor_model(300, 300, 300, 300)

                    time.sleep(0.05)

                # Telemetry interval
                now = time.time()
                if now - last_telemetry > 10.0:
                    last_telemetry = now
                    telem = collect_telemetry(car, mode)
                    log_jsonl(telem)
                    local_db.insert_telemetry(telem)
                    try:
                        mqtt.publish(MQTT_TELEMETRY_FEED, json.dumps(telem))
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
        try:
            cloud_sync.stop()
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["simulate", "hardware"], default="hardware")
    args = parser.parse_args()
    simulate = args.mode == "simulate"
    main(simulate=simulate)


# Infrared (line) sensors with simulation fallback
import time, random
try:
    from gpiozero import LineSensor
    HARDWARE = True
except Exception:
    HARDWARE = False

class Infrared:
    def __init__(self, simulate=False):
        self.simulate = simulate or (not HARDWARE)
        self.IR_PINS = {1:14, 2:15, 3:23}
        if not self.simulate:
            self.sensors = {ch: LineSensor(pin) for ch,pin in self.IR_PINS.items()}
        else:
            self.sensors = None

    def read_one_infrared(self, channel: int) -> int:
        if self.simulate:
            return 1 if random.random() > 0.5 else 0
        else:
            return 1 if self.sensors[channel].value else 0

    def read_all_infrared(self) -> int:
        return (self.read_one_infrared(1) << 2) | (self.read_one_infrared(2) << 1) | self.read_one_infrared(3)

    def close(self):
        if not self.simulate and self.sensors:
            for s in self.sensors.values():
                s.close()
