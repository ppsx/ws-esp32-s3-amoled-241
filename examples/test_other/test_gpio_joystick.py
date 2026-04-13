# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Joystick test - prints direction and button presses using current settings.
Works with both I2C and GPIO joystick backends.
Deploy to CIRCUITPY and run, or execute via Thonny.
"""

import time
from joystick import Joystick


def main():
    # Show current config
    try:
        import settings
        jtype = settings.joystick_type
        pins = settings.gpio_pins
        print(f"Joystick type: {jtype}")
        if jtype == "gpio":
            for k, v in pins.items():
                print(f"  {k}: GPIO {v}")
    except ImportError:
        print("No settings.py found, defaulting to I2C")

    joystick = Joystick()
    print("\nReading joystick. Press Ctrl+C to stop.\n")

    prev = {}
    try:
        while True:
            state = joystick.read()
            # Print full state on any change
            if state != prev:
                active = [k.upper() for k in ("up", "down", "left", "right", "center") if state[k]]
                if active:
                    print("  pressed: " + " + ".join(active))
                else:
                    released = [k.upper() for k in ("up", "down", "left", "right", "center") if prev.get(k)]
                    if released:
                        print("  released: " + " + ".join(released))
            prev = dict(state)
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        joystick.deinit()
        print("Joystick released.")


if __name__ == "__main__":
    main()
