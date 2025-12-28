"""
Comprehensive RM690B0 Display Driver Benchmark

Tests all drawing primitives with various sizes and outputs results in markdown table format.

Hardware: Waveshare ESP32-S3 AMOLED 2.41" (600×450)
"""

import rm690b0
import time
import gc

# ============================================================================
# CONFIGURATION
# ============================================================================

DOUBLE_BUFF = False  # Set to True to test with double-buffering enabled


class BenchmarkResult:
    """Store results for a single benchmark test"""

    def __init__(self, name, category, iterations, total_ms):
        self.name = name
        self.category = category
        self.iterations = iterations
        self.total_ms = total_ms
        self.avg_ms = total_ms / iterations if iterations > 0 else 0
        self.ops_per_sec = 1000 / self.avg_ms if self.avg_ms > 0 else 0

    def __repr__(self):
        return f"{self.name}: {self.avg_ms:.2f}ms avg ({self.iterations}x)"


class BenchmarkRunner:
    """Benchmark execution and result collection"""

    def __init__(self, display, double_buff=False):
        self.display = display
        self.double_buff = double_buff
        self.results = []

    def run_test(self, name, category, test_func, iterations=100, setup_func=None):
        """Run a benchmark test and store results"""
        if setup_func:
            setup_func()

        gc.collect()
        start_ns = time.monotonic_ns()

        for _ in range(iterations):
            test_func()
        if self.double_buff:
            self.display.swap_buffers()
    
        elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000

        result = BenchmarkResult(name, category, iterations, elapsed_ms)
        self.results.append(result)

        print(f"  {name}: {result.avg_ms:.2f}ms avg ({iterations}x)")

        return result

    def print_results_table(self):
        """Print results in markdown table format"""
        print("\n" + "=" * 100)
        print("  BENCHMARK RESULTS")
        print("=" * 100 + "\n")

        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Print table header with proper alignment
        print(
            "| Category   | Operation                         | Iterations | Avg Time (ms) | Ops/sec | Rating  |"
        )
        print(
            "|------------|-----------------------------------|------------|---------------|---------|---------|"
        )

        for category in sorted(categories.keys()):
            results = categories[category]
            for i, result in enumerate(results):
                category_name = category if i == 0 else ""
                rating = self._get_rating(result)
                # Format rating with spaces for centering
                rating_str = f"  {rating}  "
                print(
                    f"| {category_name:10} | {result.name:34} | {result.iterations:10} | "
                    f"{result.avg_ms:13.2f} | {result.ops_per_sec:7.0f} | {rating_str:7} |"
                )

        print()

    def _get_rating(self, result):
        """Rate performance based on operation type and timing"""
        avg = result.avg_ms

        # Define thresholds based on operation type
        if "fill_color" in result.name.lower() or "full screen" in result.name.lower():
            if avg < 20:
                return "★★★"
            elif avg < 30:
                return "★★☆"
            elif avg < 40:
                return "★☆☆"
            else:
                return "☆☆☆"

        elif "circle" in result.name.lower() and "10" in result.name:
            if avg < 20:
                return "★★★"
            elif avg < 30:
                return "★★☆"
            elif avg < 50:
                return "★☆☆"
            else:
                return "☆☆☆"

        elif "large" in result.name.lower() or "big" in result.name.lower():
            if avg < 15:
                return "★★★"
            elif avg < 25:
                return "★★☆"
            elif avg < 40:
                return "★☆☆"
            else:
                return "☆☆☆"

        else:  # Small operations
            if avg < 1:
                return "★★★"
            elif avg < 5:
                return "★★☆"
            elif avg < 10:
                return "★☆☆"
            else:
                return "☆☆☆"


def print_header(title):
    """Print section header"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)


def main():
    """Main benchmark routine"""
    print("\n" + "=" * 80)
    print("  RM690B0 COMPREHENSIVE BENCHMARK")
    print("  Testing all drawing primitives with various sizes")
    if DOUBLE_BUFF:
        print("  Mode: DOUBLE-BUFFERING ENABLED (tear-free rendering)")
    else:
        print("  Mode: SINGLE-BUFFER (direct rendering)")
    print("=" * 80)

    # Initialize display
    print("\nInitializing display...")
    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0

    # Initialize double-buffering if enabled
    if DOUBLE_BUFF:
        print("Enabling double-buffering...")
        display.swap_buffers()  # Allocate front buffer
        print("✓ Double-buffering enabled")

    print(f"✓ Display ready: {display.width}×{display.height} pixels\n")

    runner = BenchmarkRunner(display, double_buff=DOUBLE_BUFF)

    # ========================================================================
    # TEST 1: FILL_COLOR (Full Screen)
    # ========================================================================
    print_header("TEST 1: Full Screen Fill (fill_color)")

    runner.run_test(
        "fill_color (full screen)",
        "Fill",
        lambda: display.fill_color(0xF800),
        iterations=50,
    )

    # ========================================================================
    # TEST 2: HORIZONTAL LINES
    # ========================================================================
    print_header("TEST 2: Horizontal Lines (hline)")

    runner.run_test(
        "hline - short (50px)",
        "Lines",
        lambda: display.hline(100, 100, 50, 0xFFFF),
        iterations=1000,
    )

    runner.run_test(
        "hline - medium (200px)",
        "Lines",
        lambda: display.hline(100, 100, 200, 0xFFFF),
        iterations=500,
    )

    runner.run_test(
        "hline - long (500px)",
        "Lines",
        lambda: display.hline(50, 100, 500, 0xFFFF),
        iterations=200,
    )

    # ========================================================================
    # TEST 3: VERTICAL LINES
    # ========================================================================
    print_header("TEST 3: Vertical Lines (vline)")

    runner.run_test(
        "vline - short (50px)",
        "Lines",
        lambda: display.vline(100, 100, 50, 0xFFFF),
        iterations=1000,
    )

    runner.run_test(
        "vline - medium (200px)",
        "Lines",
        lambda: display.vline(100, 100, 200, 0xFFFF),
        iterations=500,
    )

    runner.run_test(
        "vline - long (400px)",
        "Lines",
        lambda: display.vline(100, 25, 400, 0xFFFF),
        iterations=200,
    )

    # ========================================================================
    # TEST 4: DIAGONAL LINES
    # ========================================================================
    print_header("TEST 4: Diagonal Lines (line)")

    runner.run_test(
        "line - short diagonal (50px)",
        "Lines",
        lambda: display.line(100, 100, 150, 150, 0xFFFF),
        iterations=500,
    )

    runner.run_test(
        "line - medium diagonal (200px)",
        "Lines",
        lambda: display.line(100, 100, 300, 300, 0xFFFF),
        iterations=200,
    )

    runner.run_test(
        "line - long diagonal (400px)",
        "Lines",
        lambda: display.line(50, 50, 450, 450, 0xFFFF),
        iterations=100,
    )

    # ========================================================================
    # TEST 5: FILLED RECTANGLES
    # ========================================================================
    print_header("TEST 5: Filled Rectangles (fill_rect)")

    runner.run_test(
        "fill_rect - tiny (10×10)",
        "Rectangles",
        lambda: display.fill_rect(100, 100, 10, 10, 0x07E0),
        iterations=1000,
    )

    runner.run_test(
        "fill_rect - small (50×50)",
        "Rectangles",
        lambda: display.fill_rect(100, 100, 50, 50, 0x07E0),
        iterations=500,
    )

    runner.run_test(
        "fill_rect - medium (100×100)",
        "Rectangles",
        lambda: display.fill_rect(100, 100, 100, 100, 0x07E0),
        iterations=200,
    )

    runner.run_test(
        "fill_rect - large (200×200)",
        "Rectangles",
        lambda: display.fill_rect(100, 100, 200, 200, 0x07E0),
        iterations=100,
    )

    runner.run_test(
        "fill_rect - huge (400×300)",
        "Rectangles",
        lambda: display.fill_rect(100, 75, 400, 300, 0x07E0),
        iterations=50,
    )

    runner.run_test(
        "fill_rect - full screen (600×450)",
        "Rectangles",
        lambda: display.fill_rect(0, 0, 600, 450, 0x07E0),
        iterations=50,
    )

    # ========================================================================
    # TEST 6: RECTANGLE OUTLINES
    # ========================================================================
    print_header("TEST 6: Rectangle Outlines (rect)")

    runner.run_test(
        "rect - small (50×50)",
        "Outlines",
        lambda: display.rect(100, 100, 50, 50, 0x001F),
        iterations=500,
    )

    runner.run_test(
        "rect - medium (100×100)",
        "Outlines",
        lambda: display.rect(100, 100, 100, 100, 0x001F),
        iterations=300,
    )

    runner.run_test(
        "rect - large (200×200)",
        "Outlines",
        lambda: display.rect(100, 100, 200, 200, 0x001F),
        iterations=200,
    )

    runner.run_test(
        "rect - huge (400×300)",
        "Outlines",
        lambda: display.rect(100, 75, 400, 300, 0x001F),
        iterations=100,
    )

    runner.run_test(
        "rect - full screen (600×450)",
        "Outlines",
        lambda: display.rect(0, 0, 600, 450, 0x001F),
        iterations=50,
    )

    # ========================================================================
    # TEST 7: CIRCLE OUTLINES
    # ========================================================================
    print_header("TEST 7: Circle Outlines (circle)")

    runner.run_test(
        "circle - small (r=10)",
        "Circles",
        lambda: display.circle(300, 225, 10, 0xFFE0),
        iterations=500,
    )

    runner.run_test(
        "circle - medium (r=50)",
        "Circles",
        lambda: display.circle(300, 225, 50, 0xFFE0),
        iterations=200,
    )

    runner.run_test(
        "circle - large (r=100)",
        "Circles",
        lambda: display.circle(300, 225, 100, 0xFFE0),
        iterations=100,
    )

    runner.run_test(
        "circle - huge (r=200)",
        "Circles",
        lambda: display.circle(300, 225, 200, 0xFFE0),
        iterations=50,
    )

    # Multiple circles test
    def draw_10_circles():
        for r in range(10, 110, 10):
            display.circle(300, 225, r, 0xF800)

    runner.run_test(
        "circle - 10 circles (r=10-100)",
        "Circles",
        draw_10_circles,
        iterations=10,
        setup_func=lambda: display.fill_color(0x0000),
    )

    # ========================================================================
    # TEST 8: FILLED CIRCLES
    # ========================================================================
    print_header("TEST 8: Filled Circles (fill_circle)")

    runner.run_test(
        "fill_circle - small (r=10)",
        "Circles",
        lambda: display.fill_circle(300, 225, 10, 0xF81F),
        iterations=200,
    )

    runner.run_test(
        "fill_circle - medium (r=50)",
        "Circles",
        lambda: display.fill_circle(300, 225, 50, 0xF81F),
        iterations=50,
    )

    runner.run_test(
        "fill_circle - large (r=100)",
        "Circles",
        lambda: display.fill_circle(300, 225, 100, 0xF81F),
        iterations=20,
    )

    runner.run_test(
        "fill_circle - huge (r=200)",
        "Circles",
        lambda: display.fill_circle(300, 225, 200, 0xF81F),
        iterations=10,
    )

    # ========================================================================
    # TEST 9: SINGLE PIXELS
    # ========================================================================
    print_header("TEST 9: Single Pixels (pixel)")

    runner.run_test(
        "pixel - single draw",
        "Pixels",
        lambda: display.pixel(100, 100, 0xFFFF),
        iterations=1000,
    )

    # ========================================================================
    # TEST 10: MEMORY & CLEANUP
    # ========================================================================
    print_header("TEST 10: Memory Usage")

    gc.collect()
    free_mem = gc.mem_free()
    print(f"  Free memory: {free_mem / 1024:.1f} KB")
    print(f"  Used memory: ~{(8192 - free_mem / 1024):.1f} KB / 8192 KB")
    print(f"  Usage: ~{((8192 - free_mem / 1024) / 8192 * 100):.1f}%")

    # ========================================================================
    # PRINT RESULTS TABLE
    # ========================================================================
    runner.print_results_table()

    # ========================================================================
    # SUMMARY STATISTICS
    # ========================================================================
    print("=" * 100)
    print("  SUMMARY STATISTICS")
    print("=" * 100 + "\n")

    # Mode information
    mode_str = "Double-buffer" if DOUBLE_BUFF else "Single-buffer"
    print(f"Test Mode: {mode_str}")
    print()

    # Find key metrics
    fill_color_result = None
    circles_10_result = None
    large_rect_result = None

    for r in runner.results:
        if "fill_color" in r.name and not fill_color_result:
            fill_color_result = r
        if "10 circles" in r.name and not circles_10_result:
            circles_10_result = r
        if "fill_rect - large" in r.name and not large_rect_result:
            large_rect_result = r

    print("Key Performance Metrics:")
    print(
        f"  • Full screen fill:     {fill_color_result.avg_ms:.2f}ms"
        if fill_color_result
        else "  • Full screen fill: N/A"
    )
    print(
        f"  • 10 circles:           {circles_10_result.avg_ms:.2f}ms (avg)"
        if circles_10_result
        else "  • 10 circles: N/A"
    )
    print(
        f"  • Large rect (200×200): {large_rect_result.avg_ms:.2f}ms"
        if large_rect_result
        else "  • Large rect: N/A"
    )
    print(f"  • Total tests:          {len(runner.results)}")
    print(f"  • Memory usage:         {((8192 - free_mem / 1024) / 8192 * 100):.1f}%")

    print("\nBaseline Comparison:")
    if fill_color_result:
        # Adjust baseline for double-buffering overhead
        baseline_fill = 54.0 if DOUBLE_BUFF else 27.0
        diff_fill = (baseline_fill - fill_color_result.avg_ms) / baseline_fill * 100
        mode_note = " (with swap)" if DOUBLE_BUFF else " (direct)"
        print(
            f"  • Full screen: {fill_color_result.avg_ms:.2f}ms vs {baseline_fill:.2f}ms baseline ({diff_fill:+.1f}%){mode_note}"
        )

    if circles_10_result:
        # Adjust baseline for double-buffering overhead (~27ms per swap)
        baseline_circles = 41.0 if DOUBLE_BUFF else 14.0
        diff_circles = (
            (baseline_circles - circles_10_result.avg_ms) / baseline_circles * 100
        )
        threshold = 50 if DOUBLE_BUFF else 20
        status = "✓" if circles_10_result.avg_ms < threshold else "⚠"
        mode_note = " (with swap)" if DOUBLE_BUFF else " (direct)"
        print(
            f"  • 10 circles: {circles_10_result.avg_ms:.2f}ms vs {baseline_circles:.2f}ms baseline ({diff_circles:+.1f}%) {status}{mode_note}"
        )

    print()

    # Overall rating
    issues = sum(1 for r in runner.results if runner._get_rating(r) == "☆☆☆")
    excellent = sum(1 for r in runner.results if runner._get_rating(r) == "★★★")

    print("Overall Assessment:")
    if issues == 0 and excellent > len(runner.results) * 0.7:
        print("  ★★★ EXCELLENT - All tests performing well!")
    elif issues == 0:
        print("  ★★☆ GOOD - Performance within acceptable range")
    elif issues < 3:
        print(f"  ★☆☆ ACCEPTABLE - {issues} test(s) need attention")
    else:
        print(f"  ⚠️  REVIEW NEEDED - {issues} test(s) performing poorly")

    print()

    # Cleanup
    display.fill_color(0x0000)
    print("✓ Benchmark complete. Display cleared.")
    display.deinit()
    print()


if __name__ == "__main__":
    main()
