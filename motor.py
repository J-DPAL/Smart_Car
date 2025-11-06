# motor.py — Unified motor driver with PCA9685 hardware + simulation fallback
import time

try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    HARDWARE = True
except Exception as e:
    print(f"[WARN] PCA9685 not available, using simulation mode. ({e})")
    HARDWARE = False


class Ordinary_Car:
    def __init__(self, simulate=False, address=0x40):
        """
        Control class for a 4-wheel car using PCA9685.
        Each wheel has a forward/reverse channel pair.
        """
        self.simulate = simulate or (not HARDWARE)
        self.last = (0, 0, 0, 0)

        if not self.simulate:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pwm = PCA9685(i2c, address=address)
                self.pwm.frequency = 50
                print("[INFO] PCA9685 motor controller initialized.")
            except Exception as e:
                print(f"[ERROR] Failed to initialize PCA9685 motor controller: {e}")
                self.simulate = True
                self.pwm = None
                print("[FALLBACK] Switching to motor simulation mode.")
        else:
            self.pwm = None
            print("[SIM] Motor driver running in simulation mode.")

    # --- internal helpers ---
    def _clip(self, *duties):
        """Limit all duty values to the safe ±4095 range."""
        return tuple(
            4095 if d > 4095 else -4095 if d < -4095 else d for d in duties
        )

    def _apply_pwm(self, channel, duty):
        """Convert duty (0–4095) to PCA9685 duty_cycle."""
        if self.simulate:
            print(f"[SIM MOTOR] channel={channel} duty={duty}")
            return

        # Limit duty cycle between 0–4095
        duty = max(0, min(4095, abs(int(duty))))
        # PCA9685 expects 16-bit value
        self.pwm.channels[channel].duty_cycle = duty * 16

    def _set_motor_pwm(self, channel_a, channel_b, duty):
        """Drive one motor pair (forward/back/stop)."""
        if self.simulate:
            print(f"[SIM PWM] chA={channel_a} chB={channel_b} duty={duty}")
            return

        if duty > 0:  # forward
            self._apply_pwm(channel_a, 0)
            self._apply_pwm(channel_b, duty)
        elif duty < 0:  # backward
            self._apply_pwm(channel_b, 0)
            self._apply_pwm(channel_a, abs(duty))
        else:  # stop
            self._apply_pwm(channel_a, 4095)
            self._apply_pwm(channel_b, 4095)

    # --- per-wheel control ---
    def left_upper_wheel(self, duty):
        self._set_motor_pwm(0, 1, duty)

    def left_lower_wheel(self, duty):
        self._set_motor_pwm(2, 3, duty)

    def right_upper_wheel(self, duty):
        self._set_motor_pwm(6, 7, duty)

    def right_lower_wheel(self, duty):
        self._set_motor_pwm(4, 5, duty)

    # --- public interface ---
    def set_motor_model(self, duty1, duty2, duty3, duty4):
        """
        Set PWM for all four wheels.
        duty1..4 correspond to:
          left_upper, left_lower, right_upper, right_lower
        """
        duty1, duty2, duty3, duty4 = self._clip(duty1, duty2, duty3, duty4)
        self.last = (duty1, duty2, duty3, duty4)

        # Adjust signs if car moves the wrong way
        self.left_upper_wheel(-duty1)
        self.left_lower_wheel(duty2)
        self.right_upper_wheel(-duty3)
        self.right_lower_wheel(-duty4)

    def close(self):
        """Stop all motors and release resources."""
        self.set_motor_model(0, 0, 0, 0)
        if not self.simulate and self.pwm:
            self.pwm.deinit()  # proper PCA9685 cleanup
        print("[INFO] Motor driver stopped.")


# --- Self-test section ---
if __name__ == "__main__":
    car = Ordinary_Car(simulate=False)  # True = simulation mode
    try:
        print("[TEST] Forward")
        car.set_motor_model(2000, 2000, 2000, 2000)
        time.sleep(1)

        print("[TEST] Backward")
        car.set_motor_model(-2000, -2000, -2000, -2000)
        time.sleep(1)

        print("[TEST] Turn Left")
        car.set_motor_model(-2000, -2000, 2000, 2000)
        time.sleep(1)

        print("[TEST] Turn Right")
        car.set_motor_model(2000, 2000, -2000, -2000)
        time.sleep(1)

        print("[TEST] Stop")
        car.set_motor_model(0, 0, 0, 0)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    finally:
        car.close()
