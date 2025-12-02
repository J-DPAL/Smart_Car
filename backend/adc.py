# ADC driver with simulated fallback
import time, random
try:
    import smbus
    HARDWARE = True
except Exception:
    HARDWARE = False

class ADC:
    def __init__(self, simulate=False):
        self.simulate = simulate or (not HARDWARE)
        self.pcb_version = 2
        if not self.simulate:
            self.I2C_ADDRESS = 0x48
            self.ADS7830_COMMAND = 0x84
            self.i2c_bus = smbus.SMBus(1)
            self.adc_voltage_coefficient = 5.2
        else:
            self.adc_voltage_coefficient = 5.0

    def _read_stable_byte(self):
        if self.simulate:
            return int(random.random()*255)
        else:
            while True:
                value1 = self.i2c_bus.read_byte(self.I2C_ADDRESS)
                value2 = self.i2c_bus.read_byte(self.I2C_ADDRESS)
                if value1 == value2:
                    return value1

    def read_adc(self, channel: int) -> float:
        if self.simulate:
            # simulate light sensors and battery voltage slightly varying
            if channel in (0,1):
                return round(2.0 + random.random()*1.5, 2)
            elif channel == 2:
                return round(3.5 + random.random()*0.5, 2)
            else:
                return 0.0
        else:
            command_set = self.ADS7830_COMMAND | ((((channel << 2) | (channel >> 1)) & 0x07) << 4)
            self.i2c_bus.write_byte(self.I2C_ADDRESS, command_set)
            value = self._read_stable_byte()
            voltage = value / 255.0 * self.adc_voltage_coefficient
            return round(voltage, 2)

    def close_i2c(self):
        if not self.simulate:
            self.i2c_bus.close()
