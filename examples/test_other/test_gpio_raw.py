# Raw GPIO pin monitor - bypasses joystick module entirely.
# Shows real-time state of all pins used by joystick settings.

import time
import digitalio
import microcontroller


def main():
    try:
        import settings
        pins_cfg = settings.gpio_pins
    except ImportError:
        print("No settings.py with gpio_pins found.")
        return

    # Init all configured pins with pull-up
    pins = {}
    for key in ("up", "down", "left", "right", "center"):
        num = pins_cfg.get(key)
        if num is not None:
            try:
                dio = digitalio.DigitalInOut(getattr(microcontroller.pin, "GPIO" + str(num)))
                dio.direction = digitalio.Direction.INPUT
                dio.pull = digitalio.Pull.UP
                pins[key] = (num, dio)
                print(f"  {key:>6s} -> GPIO {num:2d}  OK")
            except Exception as e:
                print(f"  {key:>6s} -> GPIO {num:2d}  FAILED: {e}")

    print("\nMonitoring raw .value for each pin. Ctrl+C to stop.\n")
    print("  " + "  ".join(f"{k.upper():>6s}" for k in pins) + "   (0=LOW/pressed, 1=HIGH/idle)")
    print("  " + "-" * (8 * len(pins)))

    prev = {}
    try:
        while True:
            cur = {}
            for key, (num, dio) in pins.items():
                cur[key] = dio.value  # raw: True=HIGH, False=LOW

            if cur != prev:
                line = "  "
                for key in pins:
                    val = cur[key]
                    mark = " *" if not val else "  "  # * = pressed
                    line += f"  {int(val)}{mark}   "
                print(line)
            prev = cur
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        for _, dio in pins.values():
            dio.deinit()
        print("Pins released.")


if __name__ == "__main__":
    main()
