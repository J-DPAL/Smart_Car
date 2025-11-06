# servo.py — Unified servo controller with PCA9685 hardware + simulation fallback
from time import sleep

try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    HARDWARE = True
except Exception as e:
    print(f"[WARN] PCA9685 not available, using simulation mode. ({e})")
    HARDWARE = False


class Servo:
    def __init__(self, simulate=False, address=0x40, debug=False):
        """
        Servo driver wrapper. Controls up to 8 servos via PCA9685.
        Falls back to simulation when hardware is not available.
        """
        self.simulate = simulate or (not HARDWARE)
        self.pwm_frequency = 50
        self.initial_pulse = 1500
        self.pos = {}

        # Map logical servo channels (as strings) to PCA9685 channels
        self.pwm_channel_map = {
            '0': 8,
            '1': 9,
            '2': 10,
            '3': 11,
            '4': 12,
            '5': 13,
            '6': 14,
            '7': 15
        }

        if not self.simulate:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pwm_servo = PCA9685(i2c, address=0x40)
                self.pwm_servo.frequency = self.pwm_frequency
                print("[INFO] PCA9685 hardware controller initialized.")
            except Exception as e:
                print(f"[ERROR] Failed to initialize PCA9685: {e}")
                self.simulate = True
                self.pwm_servo = None
                print("[FALLBACK] Switching to simulation mode.")
        else:
            self.pwm_servo = None
            print("[SIM] Servo controller running in simulation mode.")

    def set_servo_pwm(self, channel: str, angle: int, error: int = 10):
        if channel not in self.pwm_channel_map:
            raise ValueError(f"Invalid channel '{channel}'. Valid channels: {list(self.pwm_channel_map.keys())}")

        angle = int(angle)
        self.pos[channel] = angle

        # Convert angle to PWM pulse width (500–2500 µs typical)
        if channel == '0':
            pulse = 2500 - int((angle + error) / 0.09)
        else:
            pulse = 500 + int((angle + error) / 0.09)

        if self.simulate:
            print(f"[SIM SERVO] channel={channel} angle={angle}° pulse={pulse}")
        else:
            # ✅ FIXED LINE HERE
            self.set_servo_pulse(self.pwm_channel_map[channel], pulse)


    def close(self):
        """Reset all servos to neutral and clean up."""
        if not self.simulate:
            for ch in self.pwm_channel_map:
                self.set_servo_pwm(ch, 90)
        print("[INFO] Servo controller stopped.")
        
    def set_servo_pulse(self, channel, pulse_us):
        pulse_length = 1000000    # 1,000,000 us per second
        pulse_length //= 60       # 60 Hz
        pulse_length //= 4096     # 12 bits of resolution
        duty_cycle = int(pulse_us / pulse_length)
        self.pwm_servo.channels[channel].duty_cycle = duty_cycle



# --- Self-test section ---
if __name__ == "__main__":
    print("Now servos will rotate to 90°.")
    print("If they’re already at 90°, nothing will move.")
    print("Press Ctrl+C to stop the test.")

    servo = Servo(simulate=False)  # set simulate=True for testing without hardware
    try:
        while True:
            servo.set_servo_pwm('0', 90)
            servo.set_servo_pwm('1', 90)
            sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] End of program.")
    finally:
        servo.close()
