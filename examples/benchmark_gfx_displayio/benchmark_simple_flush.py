# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Simple Flush Benchmark - displayio version
"""

import array
import gc
import time

import board
import displayio
import bitmaptools
import sys
from rm690b0 import RM690B0, create_qspi_bus
from display_compat import DisplayCompat

# ============================================================================
# Configuration
# ============================================================================

FILL_ITERATIONS = 25  # Iterations for fill_color/fill_rect
BLIT_ITERATIONS = 10  # Iterations for blit_buffer test
CIRCLE_ITERATIONS = 20  # Iterations for circle/fill_circle tests

# Additional rectangles to probe recent driver optimizations.
# Each tuple: (label, width_pixels or ratio, height_pixels, align)
# - width_entry: if <= 1.0 treat as ratio of display width, otherwise absolute pixels.
# - height_pixels: positive integer rows or None for full height.
# - align: placement hint ("top" or "middle").
RECT_TEST_CASES = (
    ("fill_rect (FS)", 1.0, None, "top"),
    ("fill_rect (full width, 64 rows)", 1.0, 64, "top"),
    ("fill_rect (narrow column 64px)", 64, None, "middle"),
)


def resolve_rect_case(dc, case):
    """Return (label, x, y, width, height) for a configured rect test."""
    label, width_entry, height_rows, align = case
    screen_w = dc.width
    screen_h = dc.height

    if isinstance(width_entry, float) and width_entry <= 1.0:
        rect_w = max(1, int(screen_w * width_entry))
    else:
        rect_w = int(width_entry)
    rect_w = max(1, min(rect_w, screen_w))

    if height_rows is None:
        rect_h = screen_h
    else:
        rect_h = max(1, min(int(height_rows), screen_h))

    if rect_w >= screen_w:
        x = 0
    elif align == "middle":
        x = (screen_w - rect_w) // 2
    else:
        x = 0

    if rect_h >= screen_h:
        y = 0
    elif align == "middle":
        y = (screen_h - rect_h) // 2
    else:
        y = 0

    return label, x, y, rect_w, rect_h


def format_mp_per_sec(total_pixels, total_ms):
    """Return megapixels/second based on processed pixels and time."""
    if total_ms <= 0:
        return 0.0
    seconds = total_ms / 1000.0
    return (total_pixels / 1_000_000.0) / seconds


def run_benchmark(iterations, area_pixels, op, dc):
    """Run a benchmark case and return timing/throughput."""
    gc.collect()
    start_ns = time.monotonic_ns()
    for i in range(iterations):
        op(i)
        # WORKAROUND: Reset dirty tracking after each iteration
        # Without this, displayio dirty tracking corrupts and subsequent operations fail
        dc._bitmap.dirty()
    elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000.0
    avg_ms = elapsed_ms / iterations
    mp_per_s = format_mp_per_sec(area_pixels * iterations, elapsed_ms)
    return avg_ms, mp_per_s


def build_blit_buffer(width, height):
    """Create a gradient RGB565 buffer of the requested size."""
    pixels = width * height
    data = array.array("H", (0,) * pixels)
    for row in range(height):
        # Create a simple gradient that changes every row to avoid RLE effects
        base = row * width
        # Cycle through red/green/blue bands
        red = ((row * 3) & 0x1F) << 11
        green = ((row * 5) & 0x3F) << 5
        blue = (row * 7) & 0x1F
        color = red | green | blue
        for col in range(width):
            data[base + col] = color
            color ^= 0x1F  # Flip a few bits to avoid identical cache lines
    return data


def run_suite():
    displayio.release_displays()
    bus = create_qspi_bus(board)
    display = RM690B0(bus)
    dc = DisplayCompat(display)
    dc.brightness = 1.0

    area_pixels = dc.width * dc.height
    colors = (0xF800, 0x07E0, 0x001F, 0xFFFF)

    results = []

    def record(test_name, iterations, area, func):
        avg_ms, mp_per_s = run_benchmark(iterations, area, func, dc)
        results.append({
            "test": test_name,
            "avg_ms": avg_ms,
            "mp_per_s": mp_per_s,
        })

    # Test 1: fill_color (bitmap.fill)
    def fill_color_op(i):
        dc.fill_color(colors[i % len(colors)])
        dc.refresh()

    record("fill_color", FILL_ITERATIONS, area_pixels, fill_color_op)

    # Test 2: fill_rect (bitmaptools.fill_region)
    for case in RECT_TEST_CASES:
        label, rx, ry, rw, rh = resolve_rect_case(dc, case)
        rect_area = rw * rh
        if rect_area <= 0:
            continue

        def fill_rect_case_op(i, bounds=(rx, ry, rw, rh)):
            bx, by, bw, bh = bounds
            dc.fill_rect(bx, by, bw, bh, colors[i % len(colors)])
            dc.refresh()

        record(label, FILL_ITERATIONS, rect_area, fill_rect_case_op)

    # Test 3: blit_buffer (bitmaptools.arrayblit)
    blit_height = dc.height
    blit_buffer = None
    while blit_height > 0:
        try:
            blit_buffer = build_blit_buffer(dc.width, blit_height)
            break
        except MemoryError:
            blit_height //= 2
            gc.collect()

    if blit_buffer is not None:

        def blit_op(_):
            bitmaptools.arrayblit(
                dc.bitmap, blit_buffer,
                x1=0, y1=0,
                x2=dc.width, y2=blit_height,
            )
            dc.refresh()

        record(
            f"arrayblit ({blit_height}px)",
            BLIT_ITERATIONS,
            dc.width * blit_height,
            blit_op,
        )
        del blit_buffer

    # Test 4: circle / fill_circle
    circle_radius = min(dc.width, dc.height) // 3
    if circle_radius > 0:
        circle_area = (circle_radius * 2 + 1) ** 2
        cx = dc.width // 2
        cy = dc.height // 2

        def circle_op(i):
            dc.circle(cx, cy, circle_radius, colors[i % len(colors)])
            dc.refresh()

        record("circle (r=1/3)", CIRCLE_ITERATIONS, circle_area, circle_op)

        def fill_circle_op(i):
            dc.fill_circle(cx, cy, circle_radius, colors[i % len(colors)])
            dc.refresh()

        record("fill_circle (r=1/3)", CIRCLE_ITERATIONS, circle_area, fill_circle_op)

    dc.deinit()
    return results


def main():
    print("Simple Flush Benchmark (displayio + bitmaptools)")
    print(f"fill iterations={FILL_ITERATIONS}, blit iterations={BLIT_ITERATIONS}")

    all_results = run_suite()

    if not all_results:
        print("No results collected.")
        return

    op_width = max(23, max(len(entry["test"]) for entry in all_results))
    header_fmt = f"{{:<{op_width}}}  {{:>8}}  {{:>6}}"
    row_fmt = f"{{:<{op_width}}}  {{:8.2f}}  {{:6.2f}}"

    print()
    print(header_fmt.format("Operation", "Avg (ms)", "MP/s"))
    print(header_fmt.format("-" * op_width, "--------", "------"))
    for row in all_results:
        print(row_fmt.format(row["test"], row["avg_ms"], row["mp_per_s"]))


if __name__ == "__main__":
    main()
