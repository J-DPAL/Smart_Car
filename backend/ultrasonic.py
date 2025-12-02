# Ultrasonic distance sensor with simulation fallback
import time, random
try:
    from gpiozero import DistanceSensor, DistanceSensorNoEcho, PWMSoftwareFallback
    import warnings
    HARDWARE = True
except Exception:
    HARDWARE = False

class Ultrasonic:
    def __init__(self, trigger_pin=5, echo_pin=6, max_distance=3.0, simulate=False):
        self.simulate = simulate or (not HARDWARE)
        if not self.simulate:
            import warnings
            warnings.filterwarnings('ignore')
            self.sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin, max_distance=max_distance)
        else:
            self.sensor = None

    def get_distance(self):
        if self.simulate:
            return round(10 + random.random()*90, 1)
        else:
            try:
                return round(self.sensor.distance * 100, 1)
            except Exception:
                return None

    def close(self):
        if self.sensor:
            try:
                self.sensor.close()
            except Exception:
                pass
