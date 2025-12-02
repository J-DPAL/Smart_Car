# car.py
import time, math
from adc import ADC
from infrared import Infrared
from ultrasonic import Ultrasonic
from motor import Ordinary_Car
#from servo import Servo
from buzzer import Buzzer

# import new LED controller
try:
    from leds import Led
except Exception:
    # if leds.py fails, continue but set leds to None
    Led = None

class Car:
    def __init__(self, simulate=False):
        self.simulate = simulate
        #self.servo = None
        self.sonic = None
        self.motor = None
        self.infrared = None
        self.adc = None
        self.buzzer = None
        self.leds = None
        self.car_record_time = time.time()
        self.car_sonic_servo_angle = 90   # Center by default
        self.car_sonic_servo_dir = 1
        self.car_sonic_distance = [30, 30, 30]
        self.time_compensate = 3
        self.start()

    def start(self):
        # initialize components
        #self.servo = Servo(simulate=self.simulate)
        self.sonic = Ultrasonic(simulate=self.simulate)
        self.motor = Ordinary_Car(simulate=self.simulate)
        self.infrared = Infrared(simulate=self.simulate)
        self.adc = ADC(simulate=self.simulate)
        self.buzzer = Buzzer(simulate=self.simulate)

        # Init LED controller if available
        try:
            if Led is not None:
                # Led() accepts simulate flag in our wrapper
                self.leds = Led(simulate=self.simulate)
            else:
                self.leds = None
        except Exception as e:
            print("[CAR] LED controller init failed:", e)
            self.leds = None

        # # center servos to safe default
        # try:
            # # default pan (channel '0') and tilt (channel '1') centered
            # self.servo.set_servo_angle('0', 90)
            # self.servo.set_servo_angle('1', 90)
        # except Exception:
            # pass

        print("[INFO] Car initialized (simulate=%s)" % self.simulate)

    def close(self):
        try:
            self.motor.set_motor_model(0,0,0,0)
        except Exception:
            pass
        for comp in (self.sonic, self.motor, self.infrared, self.adc, self.servo, self.buzzer):
            try:
                comp.close()
            except Exception:
                pass

        # close leds if present
        try:
            if self.leds:
                self.leds.close()
        except Exception:
            pass

        print("[INFO] Car shut down cleanly.")

    # ---------- Combined Infrared + Ultrasonic ----------
    def mode_infrared_ultrasonic(self):
        if (time.time() - self.car_record_time) > 0.2:
            self.car_record_time = time.time()
            ir_value = self.infrared.read_all_infrared()
            left = (ir_value >> 2) & 1
            mid = (ir_value >> 1) & 1
            right = ir_value & 1
            distance = self.sonic.get_distance()
            try:
                print(f"[SENSORS] IR={ir_value:03b} (L:{left} M:{mid} R:{right}) | Distance={distance:.1f}cm")
            except Exception:
                print(f"[SENSORS] IR={ir_value:03b} | Distance={distance}")

            if mid:
                if distance > 30:
                    print("[ACTION] Line detected & path clear — moving forward")
                    self.motor.set_motor_model(800, 800, 800, 800)
                else:
                    print("[ACTION] Line detected & obstacle ahead — reversing")
                    self.motor.set_motor_model(-600, -600, -600, -600)
                    time.sleep(0.3)
                    self.motor.set_motor_model(-400, -400, 400, 400)
                    time.sleep(0.3)
            else:
                print("[ACTION] No line detected — stop")
                self.motor.set_motor_model(0, 0, 0, 0)

            if distance < 30:
                try:
                    self.buzzer.run('1')
                except Exception:
                    pass
            else:
                try:
                    self.buzzer.run('0')
                except Exception:
                    pass

    # ---------- Rotation (unchanged) ----------
    def mode_rotate(self, n):
        angle = n
        bat_compensate = 7.5 / (self.adc.read_adc(2) * (3 if self.adc.pcb_version == 1 else 2))
        while True:
            W = 2000
            VY = int(2000 * math.cos(math.radians(angle)))
            VX = -int(2000 * math.sin(math.radians(angle)))
            FR = VY - VX + W
            FL = VY + VX - W
            BL = VY - VX - W
            BR = VY + VX + W
            self.motor.set_motor_model(FL, BL, FR, BR)
            time.sleep(5 * self.time_compensate * bat_compensate / 1000)
            angle -= 5

    # ---------- NEW: servo & LED helpers ----------
    # def move_servo_direction(self, direction: str, step: int = 10):
        # """
        # Move pan/tilt servos by a step in degrees.
        # direction: one of 'up','down','left','right','center'
        # Returns tuple (pan_angle, tilt_angle) after move.
        # """
        # # pan -> channel '0', tilt -> channel '1'
        # try:
            # if direction == "left":
                # new_pan = self.servo.move_servo_relative('0', -step)
                # return (new_pan, self.servo.get_servo_angle('1'))
            # elif direction == "right":
                # new_pan = self.servo.move_servo_relative('0', step)
                # return (new_pan, self.servo.get_servo_angle('1'))
            # elif direction == "up":
                # new_tilt = self.servo.move_servo_relative('1', -step)
                # return (self.servo.get_servo_angle('0'), new_tilt)
            # elif direction == "down":
                # new_tilt = self.servo.move_servo_relative('1', step)
                # return (self.servo.get_servo_angle('0'), new_tilt)
            # elif direction == "center":
                # self.servo.set_servo_angle('0', 90)
                # self.servo.set_servo_angle('1', 90)
                # return (90, 90)
            # else:
                # raise ValueError("Unknown direction")
        # except Exception as e:
            # print("[CAR] move_servo_direction error:", e)
            # # return current angles as fallback
            # return (self.servo.get_servo_angle('0'), self.servo.get_servo_angle('1'))

    def set_led(self, which: str, on: bool):
        """
        which: 'all', 'led1', 'led2'
        on: True/False
        """
        if not self.leds:
            print("[CAR] No LED controller available.")
            return
        try:
            if which == "all":
                # map to two logical leds 1 and 2
                self.leds.set_led(1, on)
                self.leds.set_led(2, on)
            elif which == "led1":
                self.leds.set_led(1, on)
            elif which == "led2":
                self.leds.set_led(2, on)
            else:
                print("[CAR] Unknown LED target:", which)
        except Exception as e:
            print("[CAR] set_led error:", e)
