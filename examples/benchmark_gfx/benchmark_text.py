# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Text Rendering Benchmark - rm690b0 version
=============================================

Measures the performance of text rendering operations in both Single Buffer
and Double Buffer modes. This benchmark is used to evaluate optimizations
in the `rm690b0_text` function (e.g. batching, rotation).

Tested scenarios:
1. Small Font (8x8) - short string
2. Small Font (8x8) - long string
3. Medium Font (24x24) - short string
4. Large Font (32x48) - short string
5. Vertical List (simulating a menu)
"""

import gc
import time
import rm690b0

# ============================================================================
# Configuration
# ============================================================================

ITERATIONS = 200
RUN_MODES = [False, True]  # Single Buffer, then Double Buffer

TEST_STRINGS = {
    "short": "Hello",
    "long": "The quick brown fox jumps over the lazy dog",
    "nums": "0123456789",
}

# ============================================================================
# Benchmarking Engine
# ============================================================================

def format_cps(chars_count, total_ms):
    """Return characters/second."""
    if total_ms <= 0:
        return 0.0
    return chars_count / (total_ms / 1000.0)


def run_benchmark(iterations, func):
    """Run a benchmark case and return avg time and total time."""
    gc.collect()
    start_ns = time.monotonic_ns()
    count = 0
    for i in range(iterations):
        count += func(i)
    elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000.0
    avg_ms = elapsed_ms / iterations
    return avg_ms, elapsed_ms, count

def run_suite(double_buffer_requested):
    display = rm690b0.RM690B0()
    display.init_display()
    try:
        import settings
        display.rotation = settings.rotation
    except ImportError:
        pass

    active_double_buffer = False
    if double_buffer_requested:
        try:
            display.swap_buffers(copy=True)
            display.swap_buffers(copy=False)
            active_double_buffer = True
        except Exception:
            active_double_buffer = False

    mode_label = "DBL" if active_double_buffer else "SGL"
    if double_buffer_requested and not active_double_buffer:
        mode_label = "SGL*"

    results = []

    def record(test_name, font_id, func):
        display.fill_color(rm690b0.BLACK)
        if active_double_buffer:
             display.swap_buffers(copy=False)
             
        display.set_font(font_id)
        
        avg_ms, total_ms, total_chars = run_benchmark(ITERATIONS, func)
        chars_per_sec = format_cps(total_chars, total_ms)

        results.append({
            "mode": mode_label,
            "test": test_name,
            "avg_ms": avg_ms,
            "cps": chars_per_sec,
        })

    # --- Test Cases ---

    # 1. Small Font - Short
    def test_small_short(i):
        display.text(10, 10 + (i % 20), TEST_STRINGS["short"], rm690b0.WHITE)
        if active_double_buffer: display.swap_buffers(copy=False)
        return len(TEST_STRINGS["short"])
    record("8x8 Short", rm690b0.FONT_8x8, test_small_short)

    # 2. Small Font - Long
    def test_small_long(i):
        display.text(5, 50, TEST_STRINGS["long"], rm690b0.GREEN)
        if active_double_buffer: display.swap_buffers(copy=False)
        return len(TEST_STRINGS["long"])
    record("8x8 Long", rm690b0.FONT_8x8, test_small_long)

    # 3. Medium Font - Short
    def test_med_short(i):
        display.text(20, 100, TEST_STRINGS["short"], rm690b0.CYAN)
        if active_double_buffer: display.swap_buffers(copy=False)
        return len(TEST_STRINGS["short"])
    record("24x24 Short", rm690b0.FONT_24x24, test_med_short)

    # 4. Large Font - Short
    def test_large_short(i):
        display.text(10, 200, TEST_STRINGS["nums"], rm690b0.YELLOW)
        if active_double_buffer: display.swap_buffers(copy=False)
        return len(TEST_STRINGS["nums"])
    record("32x48 Short", rm690b0.FONT_32x48, test_large_short)

    # 5. Menu Simulation (Multiple lines per frame)
    menu_items = ["Item 1", "Settings", "Network", "About", "Exit"]
    def test_menu(i):
        y = 10
        chars = 0
        for item in menu_items:
            display.text(10, y, item, rm690b0.WHITE)
            y += 30
            chars += len(item)
        if active_double_buffer: display.swap_buffers(copy=False)
        return chars
    record("Menu (5 lines)", rm690b0.FONT_24x24, test_menu)

    # 6. Centered text using text_width / font_width / font_height
    def test_centered(i):
        txt = TEST_STRINGS["long"]
        tw = display.text_width(txt)
        x = (display.width - tw) // 2
        y = (display.height - display.font_height) // 2
        display.text(x, y, txt, rm690b0.WHITE)
        if active_double_buffer: display.swap_buffers(copy=False)
        return len(txt)
    record("Centered text", rm690b0.FONT_16x16, test_centered)

    display.deinit()
    return results


def main():
    print("Text Rendering Benchmark (rm690b0)")
    print(f"Iterations: {ITERATIONS}")

    all_results = []
    for mode in RUN_MODES:
        all_results.extend(run_suite(mode))

    if not all_results:
        print("No results.")
        return

    # Print Table
    op_width = max(20, max(len(r["test"]) for r in all_results))
    header = f"{{:>4}}  {{:<{op_width}}}  {{:>8}}  {{:>8}}"
    row_fmt = f"{{:>4}}  {{:<{op_width}}}  {{:8.2f}}  {{:8.1f}}"

    print()
    print(header.format("Mode", "Test Case", "Avg (ms)", "Chars/s"))
    print(header.format("----", "-" * op_width, "--------", "-------"))
    for r in all_results:
        print(row_fmt.format(r["mode"], r["test"], r["avg_ms"], r["cps"]))
    print()


if __name__ == "__main__":
    main()
