# # servo.py
# # Freenove-compatible PCA9685 driver

# import time
# from adafruit_pca9685 import PCA9685      # <-- FIXED (use local driver, NOT Adafruit)
# from parameter import ParameterManager


# class Servo:
    # def __init__(self, simulate=False):
        # self.simulate = simulate
        # self.param = ParameterManager()

        # # Default angles
        # self.angles = {0: 90, 1: 90}
        # self.min_angle = 0
        # self.max_angle = 180

        # if not simulate:
            # pi_ver = self.param.get_raspberry_pi_version()

            # # Freenove uses I2C bus 1 on both Pi 4 and Pi 5
            # i2c_bus = 1

            # print(f"[SERVO] Initializing PCA9685 on I2C bus {i2c_bus} (Pi version = {pi_ver})")

            # # Local Freenove driver → correct constructor
            # self.pwm = PCA9685(i2c_bus)
            # self.pwm.set_pwm_freq(50)

        # print(f"[SERVO] Initialized (simulate={simulate})")

    # def clamp(self, angle):
        # return max(self.min_angle, min(self.max_angle, angle))

    # def set_servo_angle(self, channel: int, angle: float):
        # angle = self.clamp(angle)
        # self.angles[channel] = angle

        # if self.simulate:
            # print(f"[SIM SERVO] Ch{channel}: {angle}°")
            # return

        # pulse = self.angle_to_pulse(angle)
        # self.pwm.set_pwm(channel, 0, pulse)

        # print(f"[SERVO] Ch{channel}: {angle}° (pulse={pulse})")

    # def move_servo_relative(self, channel: int, delta: float):
        # new_angle = self.angles[channel] + delta
        # self.set_servo_angle(channel, new_angle)
        # return new_angle

    # def get_servo_angle(self, channel: int):
        # return self.angles[channel]

    # def angle_to_pulse(self, angle):
        # min_pulse = 150
        # max_pulse = 600
        # pulse = int(min_pulse + (angle / 180.0) * (max_pulse - min_pulse))
        # return pulse
