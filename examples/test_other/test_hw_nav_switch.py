#!/usr/bin/env python3
"""
SparkFun Qwiic Navigation Switch Test for Waveshare ESP32-S3 Touch AMOLED 2.41

The Navigation Switch uses PCA9554 (8-bit I2C I/O expander) at address 0x21 (modified).
This is the SAME PCA9554 that's already on the Waveshare board!

Hardware:
- Waveshare ESP32-S3 Touch AMOLED 2.41
- SparkFun Qwiic Navigation Switch (PRT-27576)
- Connected via QWIIC port
- I2C pins: SDA=GPIO47, SCL=GPIO48

PCA9554 Pin Mapping for Navigation Switch:
- GPIO0: UP switch
- GPIO1: DOWN switch
- GPIO2: RIGHT switch
- GPIO3: LEFT switch
- GPIO4: CENTER switch
- GPIO5: Blue LED (output)
- GPIO6: Green LED (output)
- GPIO7: Red LED (output)

References:
- https://www.sparkfun.com/products/27576
- PCA9554 Datasheet: https://www.nxp.com/docs/en/data-sheet/PCA9554_9554A.pdf
- Default I2C address: 0x20, modified: 0x21
"""

import time

import board
import busio

# PCA9554 I2C address (same as IO expander on Waveshare board)
PCA9554_ADDR = 0x21

# PCA9554 Register addresses
REG_INPUT_PORT = 0x00  # Read input pins
REG_OUTPUT_PORT = 0x01  # Write output pins
REG_POLARITY_INV = 0x02  # Polarity inversion
REG_CONFIG = 0x03  # Configuration (1=input, 0=output)

# Navigation Switch pin mapping on PCA9554 (CORRECTED based on testing)
PIN_UP = 0  # GPIO0 - NOT WORKING
PIN_DOWN = 1  # GPIO1
PIN_RIGHT = 2  # GPIO2 (was LEFT)
PIN_LEFT = 3  # GPIO3 (was RIGHT)
PIN_CENTER = 4  # GPIO4
PIN_LED_BLUE = 5  # GPIO5
PIN_LED_GREEN = 6  # GPIO6
PIN_LED_RED = 7  # GPIO7

# LED colors (RGB combinations)
LED_OFF = 0b000
LED_RED = 0b100
LED_GREEN = 0b010
LED_BLUE = 0b001
LED_YELLOW = 0b110
LED_CYAN = 0b011
LED_MAGENTA = 0b101
LED_WHITE = 0b111


class PCA9554:
    """Driver for PCA9554 8-bit I2C I/O expander."""

    def __init__(self, i2c, address=PCA9554_ADDR):
        """Initialize PCA9554."""
        self.i2c = i2c
        self.address = address

        # Verify device is present
        try:
            self._read_register(REG_INPUT_PORT)
        except Exception as e:
            raise RuntimeError(f"PCA9554 not found at 0x{address:02X}: {e}")

    def _read_register(self, register):
        """Read a single byte from a register."""
        timeout = 1.0  # 1 second timeout
        start = time.monotonic()
        while not self.i2c.try_lock():
            if time.monotonic() - start > timeout:
                raise RuntimeError("I2C bus lock timeout")
            time.sleep(0.001)
        try:
            result = bytearray(1)
            self.i2c.writeto_then_readfrom(self.address, bytes([register]), result)
            return result[0]
        except OSError as e:
            raise RuntimeError(
                f"I2C read error at 0x{self.address:02X} reg 0x{register:02X}: {e}"
            )
        finally:
            self.i2c.unlock()

    def _write_register(self, register, value):
        """Write a single byte to a register."""
        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(self.address, bytes([register, value]))
        finally:
            self.i2c.unlock()

    def configure_pins(self, config_mask):
        """
        Configure pin directions (1=input, 0=output).

        Args:
            config_mask: 8-bit mask where 1=input, 0=output
        """
        self._write_register(REG_CONFIG, config_mask)

    def read_inputs(self):
        """
        Read all input pins.

        Returns:
            8-bit value representing pin states (0=pressed/low, 1=released/high)
        """
        return self._read_register(REG_INPUT_PORT)

    def write_outputs(self, value):
        """
        Write to all output pins.

        Args:
            value: 8-bit value to write (only bits 5-7 will be written)
        """
        # Read current state first to preserve input pin bits
        current = self._read_register(REG_OUTPUT_PORT)
        # Only modify output pins (bits 5-7), preserve input pins (bits 0-4)
        new_value = (current & 0b00011111) | (value & 0b11100000)
        self._write_register(REG_OUTPUT_PORT, new_value)

    def read_pin(self, pin):
        """
        Read a single pin state.

        Args:
            pin: Pin number (0-7)

        Returns:
            bool: True if high, False if low
        """
        value = self.read_inputs()
        return bool(value & (1 << pin))

    def write_pin(self, pin, state):
        """
        Write to a single output pin.

        Args:
            pin: Pin number (0-7)
            state: True for high, False for low
        """
        current = self._read_register(REG_OUTPUT_PORT)
        if state:
            new_value = current | (1 << pin)
        else:
            new_value = current & ~(1 << pin)
        self.write_outputs(new_value)


class NavigationSwitch:
    """Driver for SparkFun Qwiic Navigation Switch."""

    def __init__(self, i2c, address=PCA9554_ADDR):
        """
        Initialize Navigation Switch.

        Args:
            i2c: I2C bus object
            address: I2C address of PCA9554 (default: 0x20, modified: 0x21)
        """
        self.pca = PCA9554(i2c, address)

        # Configure pins: 0-4 as inputs (switches), 5-7 as outputs (LEDs)
        # Config register: 1=input, 0=output
        # 0b00011111 = pins 0-4 input, pins 5-7 output
        self.pca.configure_pins(0b00011111)

        config = self.pca._read_register(REG_CONFIG)
        print(f"Navigation Switch initialized at 0x{address:02X}")
        print(f"  Current config: 0b{config:08b} (pins 0-4=input, 5-7=output)")

        # Turn off LED initially
        self.set_led(LED_OFF)

    def read_switches(self):
        """
        Read all switch states.

        Returns:
            dict: {'up': bool, 'down': bool, 'left': bool, 'right': bool, 'center': bool}
                  True = pressed, False = released
        """
        value = self.pca.read_inputs()

        # Switches are active LOW (0 = pressed, 1 = released)
        # Invert the logic for easier understanding
        return {
            "up": not bool(value & (1 << PIN_UP)),
            "down": not bool(value & (1 << PIN_DOWN)),
            "left": not bool(value & (1 << PIN_LEFT)),
            "right": not bool(value & (1 << PIN_RIGHT)),
            "center": not bool(value & (1 << PIN_CENTER)),
        }

    def read_switch(self, direction):
        """
        Read a single switch state.

        Args:
            direction: 'up', 'down', 'left', 'right', or 'center'

        Returns:
            bool: True if pressed, False if released
        """
        switches = self.read_switches()
        return switches.get(direction, False)

    def set_led(self, color):
        """
        Set RGB LED color.

        Args:
            color: LED color constant (LED_OFF, LED_RED, LED_GREEN, LED_BLUE,
                   LED_YELLOW, LED_CYAN, LED_MAGENTA, LED_WHITE)
        """
        # LED pins are active LOW (0 = on, 1 = off)
        # So we need to invert the color bits
        inverted_color = (~color) & 0b111

        # Shift to correct bit positions (pins 5-7)
        # Pin 7 = Red, Pin 6 = Green, Pin 5 = Blue
        led_value = inverted_color << 5

        self.pca.write_outputs(led_value)

    def set_led_rgb(self, red, green, blue):
        """
        Set RGB LED color using individual RGB values.

        Args:
            red: True/False for red LED
            green: True/False for green LED
            blue: True/False for blue LED
        """
        color = 0
        if red:
            color |= LED_RED
        if green:
            color |= LED_GREEN
        if blue:
            color |= LED_BLUE
        self.set_led(color)

    def get_direction_string(self):
        """
        Get human-readable direction string.

        Returns:
            str: Direction like "UP", "DOWN-LEFT", "CENTER", etc.
        """
        switches = self.read_switches()

        directions = []
        if switches["up"]:
            directions.append("UP")
        if switches["down"]:
            directions.append("DOWN")
        if switches["left"]:
            directions.append("LEFT")
        if switches["right"]:
            directions.append("RIGHT")
        if switches["center"]:
            directions.append("CENTER")

        if not directions:
            return "NONE"

        return "-".join(directions)

    def wait_for_press(self, timeout=None):
        """
        Wait for any switch to be pressed.

        Args:
            timeout: Timeout in seconds (None = wait forever)

        Returns:
            str or None: Direction pressed, or None if timeout
        """
        start_time = time.monotonic()

        while True:
            switches = self.read_switches()

            # Check each switch
            for direction, pressed in switches.items():
                if pressed:
                    return direction

            # Check timeout
            if timeout and (time.monotonic() - start_time) > timeout:
                return None

            time.sleep(0.01)


def test_leds(nav):
    """Test RGB LED colors."""
    print("\n" + "=" * 70)
    print("RGB LED Test")
    print("=" * 70)
    print("\nCycling through colors (3 seconds each)...")
    print("-" * 70)

    colors = [
        (LED_RED, "RED"),
        (LED_GREEN, "GREEN"),
        (LED_BLUE, "BLUE"),
        (LED_YELLOW, "YELLOW (Red + Green)"),
        (LED_CYAN, "CYAN (Green + Blue)"),
        (LED_MAGENTA, "MAGENTA (Red + Blue)"),
        (LED_WHITE, "WHITE (Red + Green + Blue)"),
        (LED_OFF, "OFF"),
    ]

    for color, name in colors:
        print(f"Setting LED to: {name}")
        nav.set_led(color)
        time.sleep(3)

    print("\nLED test complete!")


def main():
    """Main test loop."""
    print("=" * 70)
    print("SparkFun Qwiic Navigation Switch Test")
    print("Waveshare ESP32-S3 Touch AMOLED 2.41")
    print("=" * 70)

    # Initialize I2C bus
    print("\nInitializing I2C bus...")
    print("  SDA: GPIO47 (board.TP_SDA)")
    print("  SCL: GPIO48 (board.TP_SCL)")
    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=100000)

    # Initialize Navigation Switch
    try:
        nav = NavigationSwitch(i2c)
    except Exception as e:
        print(f"\n❌ ERROR: Failed to initialize Navigation Switch: {e}")
        print("\nPossible issues:")
        print("  1. Navigation Switch not connected via QWIIC")
        print("  2. Wrong I2C address (should be 0x21)")
        print("  3. I2C bus conflict")
        return

    print("\n" + "=" * 70)
    print("Navigation Switch initialized successfully!")
    print("=" * 70)

    # Run LED test first
    test_leds(nav)

    print("\n" + "=" * 70)
    print("Interactive Switch + LED Test")
    print("=" * 70)
    print("\nPress switches to control LED colors:")
    print("  UP    = RED")
    print("  DOWN  = GREEN")
    print("  LEFT  = BLUE")
    print("  RIGHT = YELLOW")
    print("  CENTER = WHITE")
    print("  (No press = OFF)")
    print("\nPress Ctrl+C to exit")
    print("-" * 70)

    last_direction = "NONE"
    last_switches = nav.read_switches()

    # Color mapping for each direction
    direction_colors = {
        "UP": LED_RED,
        "DOWN": LED_GREEN,
        "LEFT": LED_BLUE,
        "RIGHT": LED_YELLOW,
        "CENTER": LED_WHITE,
        "UP-LEFT": LED_MAGENTA,
        "UP-RIGHT": LED_YELLOW,
        "DOWN-LEFT": LED_CYAN,
        "DOWN-RIGHT": LED_GREEN,
        "NONE": LED_OFF,
    }

    try:
        while True:
            try:
                switches = nav.read_switches()
                direction = nav.get_direction_string()
            except RuntimeError as e:
                print(f"\n⚠️  I2C Error: {e}")
                print("Retrying in 1 second...")
                time.sleep(1)
                continue

            # Update LED based on direction
            led_color = direction_colors.get(direction, LED_OFF)
            nav.set_led(led_color)

            # Print state (update line in place)
            status = " | ".join(
                [
                    f"UP: {'X' if switches['up'] else ' '}",
                    f"DOWN: {'X' if switches['down'] else ' '}",
                    f"LEFT: {'X' if switches['left'] else ' '}",
                    f"RIGHT: {'X' if switches['right'] else ' '}",
                    f"CENTER: {'X' if switches['center'] else ' '}",
                ]
            )
            print(f"\r{status} | {direction:15s}", end="")

            last_direction = direction
            last_switches = switches.copy()

            time.sleep(0.05)  # 20 Hz update rate for responsive LED feedback

    except KeyboardInterrupt:
        print("\n\nTest stopped by user.")

    finally:
        # Cleanup - turn off LED
        try:
            nav.set_led(LED_OFF)
        except:
            pass
        i2c.deinit()
        print("\nI2C bus closed.")


if __name__ == "__main__":
    main()
