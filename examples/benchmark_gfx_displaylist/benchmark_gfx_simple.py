# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Benchmark: rm690b0 performance
- Full screen fill (600x450)
- Partial update (100x100 rectangles)
- Multi-element scene (4 rectangles + moving sprite)
"""

import time
import rm690b0

# Colors (RGB565)
BLACK = 0x0000
RED = 0xFF0000
BLUE = 0x0010FF
GREEN = 0x00FF00
YELLOW = 0xFFFF00
WHITE = 0xFFFFFF


def _average_ms(samples):
    return (sum(samples) / len(samples)) * 1000.0


def _bench_full_screen(display, iterations=8):
    """Benchmark full screen fill operations."""
    samples = []
    for i in range(iterations):
        color = RED if (i & 1) == 0 else BLUE
        start = time.monotonic()
        display.fill_color(color)
        display.swap_buffers(copy=True)
        samples.append(time.monotonic() - start)
    return _average_ms(samples)


def _bench_partial_update(display, iterations=12):
    """Benchmark partial updates - moving 100x100 sprite."""
    # Clear to black
    display.fill_color(BLACK)
    display.swap_buffers(copy=True)

    positions = (
        (20, 20),
        (120, 20),
        (220, 20),
        (320, 20),
        (420, 20),
        (420, 160),
        (320, 260),
        (220, 260),
        (120, 260),
        (20, 260),
        (20, 140),
        (220, 140),
    )

    samples = []
    for i in range(iterations):
        x, y = positions[i % len(positions)]

        # Clear screen (simulate background)
        display.fill_color(BLACK)

        # Draw green 100x100 sprite
        display.fill_rect(x, y, 100, 100, GREEN)

        start = time.monotonic()
        display.swap_buffers(copy=True)
        samples.append(time.monotonic() - start)

    return _average_ms(samples)


def _bench_multi_element(display, iterations=10):
    """Benchmark multi-element scene with moving sprite."""
    samples = []

    for i in range(iterations):
        # Background
        display.fill_color(0x050505)

        # Static rectangles
        display.fill_rect(24, 24, 140, 80, RED)
        display.fill_rect(220, 90, 160, 120, GREEN)
        display.fill_rect(420, 260, 140, 120, BLUE)
        display.fill_rect(100, 280, 120, 100, YELLOW)

        # Moving white sprite (80x80)
        moving_x = 120 + ((i * 37) % 320)
        moving_y = 90 + ((i * 29) % 220)
        display.fill_rect(moving_x, moving_y, 80, 80, WHITE)

        start = time.monotonic()
        display.swap_buffers(copy=True)
        samples.append(time.monotonic() - start)

    return _average_ms(samples)


def _cleanup(display):
    """Clear screen to black."""
    try:
        display.fill_color(BLACK)
        display.swap_buffers(copy=True)
        print("Cleanup: screen cleared")
    except Exception as exc:
        print(f"[WARN] Screen clear failed: {exc}")

    try:
        display.deinit()
        print("Cleanup: display deinitialized")
    except Exception as exc:
        print(f"[WARN] deinit failed: {exc}")


print("=" * 60)
print("Display Benchmark")
print("RM690B0 Imperative API (fill_color, fill_rect, swap_buffers)")
print("=" * 60)

display = None

try:
    print("\nInitializing display...")
    display = rm690b0.RM690B0(render_mode=rm690b0.RENDER_DISPLAY_LIST)
    display.init_display()
    try:
        import settings
        display.rotation = settings.rotation
    except ImportError:
        pass
    display.brightness = 1.0
    print("  OK: display initialized")

    # Warm-up
    display.fill_color(BLACK)
    display.swap_buffers(copy=True)
    time.sleep(0.1)

    print("\nRunning benchmarks...")
    full_ms = _bench_full_screen(display)
    partial_ms = _bench_partial_update(display)
    scene_ms = _bench_multi_element(display)

    print("\n" + "=" * 60)
    print("Baseline Performance (v2.0)")
    print("=" * 60)
    print(f"Full screen fill (600x450): {full_ms:.3f} ms")
    print(f"Partial update (100x100):   {partial_ms:.3f} ms")
    print(f"Multi-element scene:        {scene_ms:.3f} ms")
    print("=" * 60)

except Exception as exc:
    print("\n" + "=" * 60)
    print(f"[FAIL] BENCHMARK FAILED: {exc}")
    print("=" * 60)
    import traceback
    traceback.print_exception(type(exc), exc, exc.__traceback__)

finally:
    if display is not None:
        _cleanup(display)
