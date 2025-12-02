import time
from gpiozero import OutputDevice
from gpiozero.exc import GPIOPinInUse, GPIODeviceError

class Buzzer:
    def __init__(self, pin=17, simulate=False, retries=3):
        """
        Initialize the Buzzer.
        If simulate=True, skip GPIO setup.
        Retries initialization if the pin is busy.
        """
        self.PIN = pin
        self.simulate = simulate
        self.buzzer_pin = None

        if self.simulate:
            print("[BUZZER] Simulated mode - GPIO not initialized.")
            return

        for attempt in range(retries):
            try:
                self.buzzer_pin = OutputDevice(self.PIN)
                print(f"[BUZZER] Initialized on GPIO{self.PIN}")
                return
            except GPIOPinInUse:
                print(f"[BUZZER] GPIO{self.PIN} is busy, retrying ({attempt+1}/{retries})...")
                self._cleanup_pin()
                time.sleep(0.2)
            except Exception as e:
                print(f"[BUZZER] Initialization failed: {e}")
                time.sleep(0.2)

        print(f"[BUZZER] Failed to initialize after {retries} retries.")

    def _cleanup_pin(self):
        """Force cleanup of the GPIO pin (use only when safe)."""
        try:
            import RPi.GPIO as GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup(self.PIN)
            print(f"[BUZZER] Forced cleanup on GPIO{self.PIN}.")
        except Exception as e:
            print(f"[BUZZER] GPIO cleanup failed: {e}")

    def set_state(self, state: bool) -> None:
        """Turn the buzzer ON or OFF."""
        if self.simulate:
            print(f"[BUZZER] (Simulated) {'ON' if state else 'OFF'}")
            return

        if not self.buzzer_pin:
            print("[BUZZER] Warning: buzzer_pin not initialized.")
            return

        try:
            if state:
                self.buzzer_pin.on()
                print("[BUZZER] ON")
            else:
                self.buzzer_pin.off()
                print("[BUZZER] OFF")
        except GPIODeviceError as e:
            print(f"[BUZZER] GPIO error: {e}")
        except Exception as e:
            print(f"[BUZZER] Error setting state: {e}")

    def close(self) -> None:
        """Release the GPIO resource."""
        if self.simulate:
            print("[BUZZER] Simulated buzzer closed.")
            return

        if self.buzzer_pin:
            try:
                self.buzzer_pin.off()
                self.buzzer_pin.close()
                print(f"[BUZZER] GPIO{self.PIN} released.")
            except Exception as e:
                print(f"[BUZZER] Error during close: {e}")
        else:
            print("[BUZZER] Warning: buzzer_pin not initialized.")

if __name__ == '__main__':
    print("Starting buzzer test...")
    buzzer = Buzzer(simulate=False)
    try:
        for _ in range(3):
            buzzer.set_state(True)
            time.sleep(0.3)
            buzzer.set_state(False)
            time.sleep(0.3)
    finally:
        buzzer.close()
        print("Buzzer test complete.")
