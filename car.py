import time, math
from adc import ADC
from infrared import Infrared
from ultrasonic import Ultrasonic
from motor import Ordinary_Car
from servo import Servo
from buzzer import Buzzer


class Car:
    def __init__(self, simulate=False):
        self.simulate = simulate
        self.servo = None
        self.sonic = None
        self.motor = None
        self.infrared = None
        self.adc = None
        self.buzzer = None
        self.car_record_time = time.time()
        self.car_sonic_servo_angle = 90   # Center by default
        self.car_sonic_servo_dir = 1
        self.car_sonic_distance = [30, 30, 30]
        self.time_compensate = 3
        self.start()

    def start(self):
        self.servo = Servo(simulate=self.simulate)
        self.sonic = Ultrasonic(simulate=self.simulate)
        self.motor = Ordinary_Car(simulate=self.simulate)
        self.infrared = Infrared(simulate=self.simulate)
        self.adc = ADC(simulate=self.simulate)
        self.buzzer = Buzzer(simulate=self.simulate)
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
        print("[INFO] Car shut down cleanly.")


    # ---------- Combined Infrared + Ultrasonic ----------
    def mode_infrared_ultrasonic(self):
        """
        Move forward only if:
            - The infrared detects a line (mid sensor = 1)
            - No obstacle ahead (ultrasonic distance > 30 cm)

        Move backward only if:
            - The infrared detects a line (mid sensor = 1)
            - There IS an obstacle (ultrasonic distance < 30 cm)

        Stop otherwise.
        """

        if (time.time() - self.car_record_time) > 0.2:
            self.car_record_time = time.time()

            # Read infrared
            ir_value = self.infrared.read_all_infrared()
            left = (ir_value >> 2) & 1
            mid = (ir_value >> 1) & 1
            right = ir_value & 1

            # Read ultrasonic (forward distance only)
            distance = self.sonic.get_distance()
            print(f"[SENSORS] IR={ir_value:03b} (L:{left} M:{mid} R:{right}) | Distance={distance:.1f}cm")

            # Logic
            if mid:  # Line detected in the middle
                if distance > 30:
                    print("[ACTION] Line detected & path clear — moving forward")
                    self.motor.set_motor_model(800, 800, 800, 800)
                else:
                    print("[ACTION] Line detected & obstacle ahead — reversing")
                    self.motor.set_motor_model(-600, -600, -600, -600)
                    time.sleep(0.3)
                    # Optional: turn a bit to avoid object
                    self.motor.set_motor_model(-400, -400, 400, 400)
                    time.sleep(0.3)
            else:
                print("[ACTION] No line detected — stop")
                self.motor.set_motor_model(0, 0, 0, 0)

            # Optional: beep when obstacle detected
            if distance < 30:
                self.buzzer.run('1')
            else:
                self.buzzer.run('0')

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
