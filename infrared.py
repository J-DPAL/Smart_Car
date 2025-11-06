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
