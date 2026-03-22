# Common joystick driver - supports I2C (PCA9554) and GPIO backends

_PCA9554_ADDR = 0x21


class Joystick:
    """Unified joystick interface. Reads settings to select I2C or GPIO backend."""

    def __init__(self, i2c=None):
        """Initialize joystick.

        Args:
            i2c: Optional shared I2C bus. If None and backend is I2C, creates one.
        """
        try:
            import settings
            self._type = settings.joystick_type
            self._gpio_pins_cfg = settings.gpio_pins
        except ImportError:
            self._type = "i2c"
            self._gpio_pins_cfg = {}

        self._i2c = None
        self._i2c_owned = False
        self._gpio_pins = {}

        if self._type == "gpio":
            self._init_gpio()
        else:
            self._init_i2c(i2c)

    def _init_i2c(self, i2c):
        if i2c is not None:
            self._i2c = i2c
            self._i2c_owned = False
        else:
            import busio
            import board
            self._i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)
            self._i2c_owned = True

        # Configure PCA9554: pins 0-4 input, 5-7 output
        self._i2c_write(3, 0b00011111)
        # LEDs off
        self._i2c_write(1, 0b11100000)

    def _i2c_write(self, reg, val):
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(_PCA9554_ADDR, bytes([reg, val]))
        finally:
            self._i2c.unlock()

    def _i2c_read_inputs(self):
        while not self._i2c.try_lock():
            pass
        try:
            buf = bytearray(1)
            self._i2c.writeto_then_readfrom(_PCA9554_ADDR, bytes([0]), buf)
            return buf[0]
        finally:
            self._i2c.unlock()

    def _init_gpio(self):
        import digitalio
        import microcontroller

        for key in ("up", "down", "left", "right", "center"):
            pin_num = self._gpio_pins_cfg.get(key)
            if pin_num is not None:
                pin = digitalio.DigitalInOut(microcontroller.pin.GPIO(pin_num))
                pin.direction = digitalio.Direction.INPUT
                pin.pull = digitalio.Pull.UP
                self._gpio_pins[key] = pin
            else:
                self._gpio_pins[key] = None

    def read(self):
        """Read joystick state. Returns dict with 5 boolean keys."""
        if self._type == "gpio":
            return self._read_gpio()
        return self._read_i2c()

    def _read_i2c(self):
        try:
            val = self._i2c_read_inputs()
        except OSError:
            return {"up": False, "down": False, "left": False, "right": False, "center": False}

        if val == 0:
            return {"up": False, "down": False, "left": False, "right": False, "center": False}

        return {
            "up": not bool(val & (1 << 0)),
            "down": not bool(val & (1 << 1)),
            "left": not bool(val & (1 << 3)),
            "right": not bool(val & (1 << 2)),
            "center": not bool(val & (1 << 4)),
        }

    def _read_gpio(self):
        result = {}
        for key in ("up", "down", "left", "right", "center"):
            pin = self._gpio_pins.get(key)
            if pin is not None:
                result[key] = not pin.value  # active-LOW
            else:
                result[key] = False
        return result

    def deinit(self):
        """Release hardware resources."""
        if self._type == "gpio":
            for pin in self._gpio_pins.values():
                if pin is not None:
                    pin.deinit()
            self._gpio_pins.clear()
        elif self._i2c_owned and self._i2c is not None:
            try:
                self._i2c.deinit()
            except Exception:
                pass
            self._i2c = None
