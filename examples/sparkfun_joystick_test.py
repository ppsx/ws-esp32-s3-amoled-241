#!/usr/bin/env python3
"""
SparkFun Joystick (QWIIC) Test Script for Waveshare ESP32-S3 Touch AMOLED 2.41

This script scans for I2C devices, initializes a SparkFun QWIIC Joystick,
and continuously reads its state (X, Y axes and button).

Hardware:
- Waveshare ESP32-S3 Touch AMOLED 2.41
- I2C pins: SDA=GPIO47, SCL=GPIO48
- SparkFun QWIIC Joystick connected via QWIIC port

NOTE: The Waveshare board has an IO Expander (PCA9554) at 0x20.
      SparkFun Joystick default is also 0x20, so you may need to change
      the joystick address via solder jumpers to 0x21 or scan for it.

Known I2C devices on Waveshare board:
- 0x20: IO Expander (PCA9554) - CONFLICT with joystick default!
- 0x38: Touch controller (FT6336U)
- 0x51: RTC (PCF85063)
- 0x6B: IMU (QMI8658C)

References:
- https://www.sparkfun.com/products/15168
- Default I2C address: 0x20 (but conflicts with IO expander)
- Alternative addresses: 0x21 (via jumper)
"""

import time

import board
import busio

# SparkFun Joystick I2C addresses
JOYSTICK_POSSIBLE_ADDRS = [0x20, 0x21]  # 0x20 conflicts with IO expander!
JOYSTICK_DEVICE_ID = 0x13  # Expected device ID

# Register addresses
REG_ID = 0x00  # Device ID (should be 0x13)
REG_VERSION = 0x01  # Firmware version
REG_X_MSB = 0x03  # X position MSB
REG_X_LSB = 0x04  # X position LSB
REG_Y_MSB = 0x05  # Y position MSB
REG_Y_LSB = 0x06  # Y position LSB
REG_BUTTON = 0x07  # Button state (0 = pressed, 1 = released)
REG_STATUS = 0x08  # Status register

# Joystick center values (approximately)
CENTER_X = 512
CENTER_Y = 512
DEADZONE = 50  # Deadzone around center


def scan_i2c(i2c):
    """Scan I2C bus and return list of found device addresses."""
    print("\nScanning I2C bus (SDA=GPIO47, SCL=GPIO48)...")
    print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")

    devices = []
    for addr in range(0x08, 0x78):  # Valid I2C address range
        try:
            while not i2c.try_lock():
                pass
            try:
                i2c.writeto(addr, b"")
                devices.append(addr)
                if (addr % 16) == 0:
                    print(f"{(addr // 16):x}0:", end=" ")
                print(f"{addr:02x}", end=" ")
            except OSError:
                if (addr % 16) == 0:
                    print(f"{(addr // 16):x}0:", end=" ")
                print("--", end=" ")
            finally:
                i2c.unlock()
        except Exception:
            if (addr % 16) == 0:
                print(f"{(addr // 16):x}0:", end=" ")
            print("??", end=" ")

        # New line every 16 addresses
        if (addr + 1) % 16 == 0:
            print()

    print(f"\nFound {len(devices)} device(s):")
    known_devices = {
        0x20: "IO Expander (PCA9554) or Joystick?",
        0x21: "Joystick (alternative address)?",
        0x38: "Touch (FT6336U)",
        0x51: "RTC (PCF85063)",
        0x6B: "IMU (QMI8658C)",
    }
    for addr in devices:
        device_name = known_devices.get(addr, "Unknown")
        print(f"  0x{addr:02X} ({addr:3d}) - {device_name}")

    return devices


class SparkFunJoystick:
    """Driver for SparkFun QWIIC Joystick."""

    def __init__(self, i2c, address):
        """Initialize joystick on I2C bus."""
        self.i2c = i2c
        self.address = address

        # Verify device is present
        try:
            device_id = self._read_register(REG_ID)
            print(f"\nJoystick found at 0x{address:02X}")
            print(f"  Device ID: 0x{device_id:02X}")

            if device_id != JOYSTICK_DEVICE_ID:
                raise RuntimeError(
                    f"Wrong device ID: expected 0x{JOYSTICK_DEVICE_ID:02X}, got 0x{device_id:02X}"
                )

            version = self._read_register(REG_VERSION)
            print(f"  Firmware version: {version}")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize joystick at 0x{address:02X}: {e}")

    def _read_register(self, register):
        """Read a single byte from a register."""
        while not self.i2c.try_lock():
            pass
        try:
            result = bytearray(1)
            self.i2c.writeto_then_readfrom(self.address, bytes([register]), result)
            return result[0]
        finally:
            self.i2c.unlock()

    def _read_register_16bit(self, reg_msb):
        """Read a 16-bit value from two consecutive registers (MSB first)."""
        msb = self._read_register(reg_msb)
        lsb = self._read_register(reg_msb + 1)
        return (msb << 8) | lsb

    def read_position(self):
        """
        Read joystick X and Y position.

        Returns:
            tuple: (x, y) where x and y are 0-1023 (10-bit values)
                   Center is approximately (512, 512)
        """
        x = self._read_register_16bit(REG_X_MSB)
        y = self._read_register_16bit(REG_Y_MSB)
        return x, y

    def read_button(self):
        """
        Read button state.

        Returns:
            bool: True if button is pressed, False if released
        """
        button_state = self._read_register(REG_BUTTON)
        # Button register: 0 = pressed, 1 = released
        return button_state == 0

    def read_all(self):
        """
        Read all joystick data at once.

        Returns:
            dict: {'x': int, 'y': int, 'button': bool}
        """
        x, y = self.read_position()
        button = self.read_button()
        return {"x": x, "y": y, "button": button}

    def get_direction(self, x=None, y=None, deadzone=DEADZONE):
        """
        Get directional state from X/Y position.

        Args:
            x: X position (0-1023), or None to read current
            y: Y position (0-1023), or None to read current
            deadzone: Deadzone threshold around center

        Returns:
            tuple: (up, down, left, right) as booleans
        """
        if x is None or y is None:
            x, y = self.read_position()

        up = y < (CENTER_Y - deadzone)
        down = y > (CENTER_Y + deadzone)
        left = x < (CENTER_X - deadzone)
        right = x > (CENTER_X + deadzone)

        return up, down, left, right

    def get_direction_string(self, x=None, y=None):
        """
        Get human-readable direction string.

        Returns:
            str: Direction like "UP", "DOWN-LEFT", "CENTER", etc.
        """
        if x is None or y is None:
            x, y = self.read_position()

        up, down, left, right = self.get_direction(x, y)

        # Build direction string
        direction = []
        if up:
            direction.append("UP")
        if down:
            direction.append("DOWN")
        if left:
            direction.append("LEFT")
        if right:
            direction.append("RIGHT")

        if not direction:
            return "CENTER"

        return "-".join(direction)


def find_joystick(i2c, devices):
    """
    Try to find SparkFun Joystick among I2C devices.

    Returns:
        int or None: Joystick address if found, None otherwise
    """
    print("\nLooking for SparkFun Joystick...")

    for addr in devices:
        if addr not in JOYSTICK_POSSIBLE_ADDRS:
            continue

        try:
            # Try to read device ID
            while not i2c.try_lock():
                pass
            try:
                result = bytearray(1)
                i2c.writeto_then_readfrom(addr, bytes([REG_ID]), result)
                if result[0] == JOYSTICK_DEVICE_ID:
                    print(f"✓ Found SparkFun Joystick at 0x{addr:02X}")
                    return addr
                else:
                    print(
                        f"✗ Device at 0x{addr:02X} has ID 0x{result[0]:02X} (not a joystick)"
                    )
            finally:
                i2c.unlock()
        except Exception as e:
            print(f"✗ Error reading device at 0x{addr:02X}: {e}")

    return None


def main():
    """Main test loop."""
    print("=" * 70)
    print("SparkFun QWIIC Joystick Test")
    print("Waveshare ESP32-S3 Touch AMOLED 2.41")
    print("=" * 70)

    # Initialize I2C bus with correct Waveshare pins
    print("\nInitializing I2C bus...")
    print("  SDA: GPIO47 (board.SDA)")
    print("  SCL: GPIO48 (board.SCL)")
    i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

    # Scan for devices
    devices = scan_i2c(i2c)

    if not devices:
        print("\n❌ ERROR: No I2C devices found!")
        print("\nCheck your connections:")
        print("  - QWIIC cable properly connected")
        print("  - Joystick powered on")
        print("  - Correct I2C pins (SDA=GPIO47, SCL=GPIO48)")
        return

    # Find joystick
    joystick_addr = find_joystick(i2c, devices)

    if joystick_addr is None:
        print("\n❌ ERROR: SparkFun Joystick not found!")
        print("\nPossible issues:")
        print("  1. Address conflict: Default 0x20 conflicts with IO Expander")
        print("  2. Solution: Change joystick address to 0x21 via solder jumper")
        print("  3. Or joystick is not connected properly")
        print("\nWaveshare board uses these addresses:")
        print("  - 0x20: IO Expander (PCA9554) ⚠️  CONFLICTS with joystick!")
        print("  - 0x38: Touch controller (FT6336U)")
        print("  - 0x51: RTC (PCF85063)")
        print("  - 0x6B: IMU (QMI8658C)")
        return

    # Initialize joystick
    try:
        joystick = SparkFunJoystick(i2c, joystick_addr)
    except Exception as e:
        print(f"\n❌ ERROR: Failed to initialize joystick: {e}")
        return

    print("\n" + "=" * 70)
    print("✓ Joystick initialized successfully!")
    print("=" * 70)
    print("\nReading joystick state (Ctrl+C to exit)...")
    print("\nFormat: X, Y, Button | Direction")
    print("-" * 70)

    last_button = False
    update_count = 0

    try:
        while True:
            # Read joystick state
            data = joystick.read_all()
            x = data["x"]
            y = data["y"]
            button = data["button"]

            # Get direction
            direction = joystick.get_direction_string(x, y)

            # Print state (update line in place)
            button_str = "PRESSED " if button else "Released"
            print(
                f"\rX: {x:4d}, Y: {y:4d}, Button: {button_str} | {direction:12s}",
                end="",
                flush=True,
            )

            # Detect button press/release with newline
            if button and not last_button:
                print(f"\n>>> BUTTON PRESSED at ({x}, {y}) - {direction}")
            elif not button and last_button:
                print(f"\n>>> BUTTON RELEASED")

            last_button = button
            update_count += 1

            # Print periodic update every 100 reads
            if update_count % 100 == 0:
                print(f"\n[{update_count} updates] Still running...", end="")

            time.sleep(0.05)  # 20 Hz update rate

    except KeyboardInterrupt:
        print("\n\n✓ Test stopped by user.")

    finally:
        i2c.deinit()
        print("✓ I2C bus closed.")


if __name__ == "__main__":
    main()
