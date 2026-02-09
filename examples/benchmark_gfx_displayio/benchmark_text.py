"""
Text Rendering Benchmark — displayio version
=============================================

Measures the performance of text rendering using adafruit_display_text Labels
with terminalio.FONT at different scales (simulating different font sizes).

Tested scenarios:
1. Scale 1 (~6x12) - short string
2. Scale 1 (~6x12) - long string
3. Scale 2 (~12x24) - short string
4. Scale 4 (~24x48) - short string
5. Menu simulation (5 labels per frame)

Usage:
    import benchmark_text
"""

import gc
import time
import sys

import board
import displayio
import terminalio
from adafruit_display_text import label as label_mod
from rm690b0 import RM690B0, create_qspi_bus

try:
    from display_compat import DisplayCompat
except ImportError:
    sys.path.insert(0, ".")
    from display_compat import DisplayCompat

# ============================================================================
# Configuration
# ============================================================================

ITERATIONS = 200
FONT = terminalio.FONT

TEST_STRINGS = {
    "short": "Hello",
    "long": "The quick brown fox jumps over the lazy dog",
    "nums": "0123456789",
}

# ============================================================================
# Benchmarking Engine
# ============================================================================


def format_cps(chars_count, total_ms):
    if total_ms <= 0:
        return 0.0
    return chars_count / (total_ms / 1000.0)


def run_benchmark(iterations, func):
    gc.collect()
    start_ns = time.monotonic_ns()
    count = 0
    for i in range(iterations):
        count += func(i)
    elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000.0
    avg_ms = elapsed_ms / iterations
    return avg_ms, elapsed_ms, count


def run_suite():
    displayio.release_displays()
    bus = create_qspi_bus(board)
    display = RM690B0(bus)
    dc = DisplayCompat(display)
    dc.brightness = 1.0

    # Use dc.group for labels (already set as display.root_group)
    group = dc.group

    results = []

    def record(test_name, func):
        # Clear group (keep background bitmap)
        while len(group) > 0:
            group.pop()
        # Clear background to black
        dc.fill_color(0x0000)
        dc.refresh()
        # Reset dirty tracking
        dc._bitmap.dirty()
        gc.collect()

        avg_ms, total_ms, total_chars = run_benchmark(ITERATIONS, func)
        chars_per_sec = format_cps(total_chars, total_ms)

        results.append({
            "test": test_name,
            "avg_ms": avg_ms,
            "cps": chars_per_sec,
        })

    # --- Test Cases ---

    # 1. Scale 1 - Short
    def test_s1_short(i):
        lbl = label_mod.Label(FONT, text=TEST_STRINGS["short"], color=0xFFFFFF,
                              x=10, y=10, scale=1)
        group.append(lbl)
        display.refresh()
        group.pop()
        # Mark LARGE region as dirty (workaround for displayio bug with small elements)
        dc._bitmap.dirty(0, 0, 300, 100)
        return len(TEST_STRINGS["short"])

    record("Scale 1 Short", test_s1_short)

    # 2. Scale 1 - Long
    def test_s1_long(i):
        lbl = label_mod.Label(FONT, text=TEST_STRINGS["long"], color=0x00FF00,
                              x=10, y=50, scale=1)  # x=10 (even alignment)
        group.append(lbl)
        display.refresh()
        group.pop()
        # Mark FULL SCREEN as dirty (long text requires maximum dirty region)
        dc._bitmap.dirty(0, 0, dc.width, dc.height)
        return len(TEST_STRINGS["long"])

    record("Scale 1 Long", test_s1_long)

    # 3. Scale 2 - Short (simulates ~12x24 font)
    def test_s2_short(i):
        lbl = label_mod.Label(FONT, text=TEST_STRINGS["short"], color=0x00FFFF,
                              x=20, y=100, scale=2)
        group.append(lbl)
        display.refresh()
        group.pop()
        dc._bitmap.dirty()  # Reset dirty tracking after each iteration
        return len(TEST_STRINGS["short"])

    record("Scale 2 Short", test_s2_short)

    # 4. Scale 4 - Short (simulates ~24x48 font)
    def test_s4_short(i):
        lbl = label_mod.Label(FONT, text=TEST_STRINGS["nums"], color=0xFFFF00,
                              x=10, y=200, scale=4)
        group.append(lbl)
        display.refresh()
        group.pop()
        dc._bitmap.dirty()  # Reset dirty tracking after each iteration
        return len(TEST_STRINGS["nums"])

    record("Scale 4 Short", test_s4_short)

    # 5. Menu Simulation (5 labels per frame)
    menu_items = ["Item 1", "Settings", "Network", "About", "Exit"]

    def test_menu(i):
        chars = 0
        labels = []
        y = 10
        for item in menu_items:
            lbl = label_mod.Label(FONT, text=item, color=0xFFFFFF,
                                  x=10, y=y, scale=2)
            group.append(lbl)
            labels.append(lbl)
            y += 30
            chars += len(item)
        display.refresh()
        for _ in labels:
            group.pop()
        dc._bitmap.dirty()  # Reset dirty tracking after each iteration
        return chars

    record("Menu (5 lines)", test_menu)

    dc.deinit()
    return results


def main():
    print("Text Rendering Benchmark (adafruit_display_text)")
    print(f"Iterations: {ITERATIONS}")

    all_results = run_suite()

    if not all_results:
        print("No results.")
        return

    op_width = max(20, max(len(r["test"]) for r in all_results))
    header = f"{{:<{op_width}}}  {{:>8}}  {{:>8}}"
    row_fmt = f"{{:<{op_width}}}  {{:8.2f}}  {{:8.1f}}"

    print()
    print(header.format("Test Case", "Avg (ms)", "Chars/s"))
    print(header.format("-" * op_width, "--------", "-------"))
    for r in all_results:
        print(row_fmt.format(r["test"], r["avg_ms"], r["cps"]))
    print()


if __name__ == "__main__":
    main()
