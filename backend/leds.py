
import time
import traceback

# Try to import the project's hardware driver modules (they exist in your repo)
try:
    from parameter import ParameterManager
    from rpi_ledpixel import Freenove_RPI_WS281X
    from spi_ledpixel import Freenove_SPI_LedPixel
    HAS_HW = True
except Exception as e:
    # If parameter or driver imports fail, still provide a simulated API
    # but we'll mark hardware as unavailable.
    HAS_HW = False
    # print small debug if needed
    # print("leds.py: hardware drivers not available:", e)


class Led:
    """
    LED controller compatible with your project's expectations.

    The original Freenove drivers support a full strip; this wrapper offers
    a minimal control API used by car.set_led(...).
    """

    def __init__(self, simulate=False):
        # simulate param can be used to force software-only mode
        self.simulate = simulate or (not HAS_HW)
        self.strip = None
        self.is_support_led_function = False
        self._last_color = (0, 0, 0)

        if self.simulate:
            print("[LED] Simulation mode enabled (no hardware).")
            self.is_support_led_function = False
            return

        # Try to initialize hardware using ParameterManager settings
        try:
            self.param = ParameterManager()
            self.connect_version = self.param.get_connect_version()  # 1 = WS281x; 2 = SPI
            self.pi_version = self.param.get_raspberry_pi_version()  # 1 = Pi 4/earlier, 2 = Pi 5

            print("[LED] Initializing LED system... connect_version=%s pi_version=%s" %
                  (self.connect_version, self.pi_version))

            if self.connect_version == 1 and self.pi_version == 1:
                # WS281x (GPIO PWM) typical Freenove driver
                self.strip = Freenove_RPI_WS281X(60, 255, 'RGB')
                self.is_support_led_function = True
                print("[LED] Using WS281x-based LED driver (GPIO18).")
            elif self.connect_version == 2 and (self.pi_version in (1, 2)):
                # SPI-based Freenove LED driver
                self.strip = Freenove_SPI_LedPixel(60, 255, 'GRB')
                self.is_support_led_function = True
                print("[LED] Using SPI-based LED driver.")
            else:
                print("[LED] Unsupported LED configuration. LED functions disabled.")
                self.is_support_led_function = False

        except Exception as e:
            print("[LED] Initialization error:", e)
            traceback.print_exc()
            self.is_support_led_function = False
            self.strip = None

    # low-level helper to set all LEDs to a color
    def set_all_led_color(self, r: int, g: int, b: int):
        if not getattr(self, "is_support_led_function", False) or not self.strip:
            # simulate: just remember the color
            self._last_color = (r, g, b)
            print(f"[LED SIM] set_all_led_color -> ({r},{g},{b})")
            return

        try:
            count = self.strip.get_led_count()
            for i in range(count):
                self.strip.set_led_rgb_data(i, (r, g, b))
            self.strip.show()
            self._last_color = (r, g, b)
        except Exception as e:
            print("[LED] Error setting LED color:", e)

    def clear(self):
        self.set_all_led_color(0, 0, 0)

    # High-level API
    def set_color(self, r: int, g: int, b: int):
        """Set entire strip to a color."""
        print(f"[LED] set_color ({r},{g},{b})")
        self.set_all_led_color(r, g, b)

    def off(self):
        """Turn off all LEDs."""
        print("[LED] off()")
        self.clear()

    def blink(self, r: int, g: int, b: int, interval: float = 0.3, times: int = 3):
        """Blink LEDs as feedback."""
        if not getattr(self, "is_support_led_function", False):
            print("[LED SIM] blink -> ({},{},{}) x{}".format(r, g, b, times))
            return
        for _ in range(times):
            self.set_all_led_color(r, g, b)
            time.sleep(interval)
            self.clear()
            time.sleep(interval)

    # Compatibility method used by car.set_led(which, on)
    # we implement a small mapping: led index '1' and '2' map to two simple colors/zones
    def set_led(self, index: int, on: bool):
        """
        index: 1 or 2 (small logical mapping)
        on: True to turn on, False to turn off
        Behaviour:
            - led 1 -> set strip to warm white (200,180,140)
            - led 2 -> set strip to cool blue (0,0,200)
            - If index is other, treat as 'all'
        """
        if not self.strip and self.simulate:
            print(f"[LED SIM] set_led({index}, {on})")
            return

        try:
            if not on:
                # if turning off a specific led we simply clear entire strip (simple)
                self.clear()
                return

            if index == 1:
                # warm white
                self.set_all_led_color(200, 180, 140)
            elif index == 2:
                # blue
                self.set_all_led_color(0, 0, 200)
            else:
                # default => white
                self.set_all_led_color(255, 255, 255)
        except Exception as e:
            print("[LED] set_led error:", e)

    # Close/cleanup
    def close(self):
        try:
            self.clear()
        except Exception:
            pass
        print("[LED] closed")
