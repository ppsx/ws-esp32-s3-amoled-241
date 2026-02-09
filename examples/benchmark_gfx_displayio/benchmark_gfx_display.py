# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Comprehensive Display Driver Benchmark - displayio version
Tests all drawing primitives with various sizes and outputs results in markdown table format.
"""

import board
import displayio
import time
import gc
import sys
from rm690b0 import RM690B0, create_qspi_bus
from display_compat import DisplayCompat


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

    def __init__(self, dc):
        self.dc = dc
        self.results = []

    def run_test(self, name, category, test_func, iterations=100, setup_func=None):
        """Run a benchmark test and store results"""
        if setup_func:
            setup_func()

        gc.collect()
        start_ns = time.monotonic_ns()

        for _ in range(iterations):
            test_func()
        elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000

        result = BenchmarkResult(name, category, iterations, elapsed_ms)
        self.results.append(result)

        # Refresh display to show the result AFTER recording time
        self.dc.refresh()

        # WORKAROUND: Reset dirty tracking to full screen after each test
        # Without this, displayio dirty tracking gets corrupted and subsequent
        # tests fail to render correctly (lines/circles deformed or invisible).
        # This forces full screen refresh between tests, which is slower but stable.
        self.dc._bitmap.dirty()

        return result

    def print_results_table(self):
        """Print results in markdown table format"""
        print("=" * 100)
        print("  BENCHMARK RESULTS (displayio + bitmaptools)")
        print("=" * 100)

        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Print table header with proper alignment
        print(
            "| Category   | Operation                          | Iterations | Avg Time (ms) | Ops/sec | Rating  |"
        )
        print(
            "|------------|------------------------------------|------------|---------------|---------|---------|"
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
        print("=" * 100)
        print()

    def _get_rating(self, result):
        """Rate performance based on operation type and timing"""
        avg = result.avg_ms

        # Define thresholds based on operation type
        if "fill_color" in result.name.lower() or "full screen" in result.name.lower():
            if avg < 20:
                return "***"
            elif avg < 30:
                return "** "
            elif avg < 40:
                return "*  "
            else:
                return "   "

        elif "large" in result.name.lower() or "big" in result.name.lower():
            if avg < 15:
                return "***"
            elif avg < 25:
                return "** "
            elif avg < 40:
                return "*  "
            else:
                return "   "
        else:
            if avg < 1:
                return "***"
            elif avg < 5:
                return "** "
            elif avg < 10:
                return "*  "
            else:
                return "   "


def main():
    """Main benchmark routine"""
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE BENCHMARK (displayio + bitmaptools)")
    print("  Testing all drawing primitives with various sizes")
    print("=" * 80)

    # Initialize display
    print("\nInitializing display...")
    displayio.release_displays()
    bus = create_qspi_bus(board)
    display = RM690B0(bus)
    dc = DisplayCompat(display)
    dc.brightness = 1.0
    print(f"Display ready: {dc.width}x{dc.height} pixels\n")

    runner = BenchmarkRunner(dc)

    # TEST 1: FILL_COLOR (Full Screen)

    runner.run_test(
        "fill_color (full screen)",
        "Fill",
        lambda: dc.fill_color(0xF800),
        iterations=50,
    )

    # TEST 2: HORIZONTAL LINES

    runner.run_test(
        "hline - short (50px)",
        "Lines",
        lambda: dc.hline(100, 100, 50, 0xFFFF),
        iterations=1000,
    )

    runner.run_test(
        "hline - medium (200px)",
        "Lines",
        lambda: dc.hline(100, 100, 200, 0xFFFF),
        iterations=500,
    )

    runner.run_test(
        "hline - long (500px)",
        "Lines",
        lambda: dc.hline(50, 100, 500, 0xFFFF),
        iterations=200,
    )

    # TEST 3: VERTICAL LINES

    runner.run_test(
        "vline - short (50px)",
        "Lines",
        lambda: dc.vline(100, 100, 50, 0xFFFF),
        iterations=1000,
    )

    runner.run_test(
        "vline - medium (200px)",
        "Lines",
        lambda: dc.vline(100, 100, 200, 0xFFFF),
        iterations=500,
    )

    runner.run_test(
        "vline - long (400px)",
        "Lines",
        lambda: dc.vline(100, 25, 400, 0xFFFF),
        iterations=200,
    )

    # TEST 4: DIAGONAL LINES

    runner.run_test(
        "line - short diagonal (50px)",
        "Lines",
        lambda: dc.line(100, 100, 150, 150, 0xFFFF),
        iterations=500,
    )

    runner.run_test(
        "line - medium diagonal (200px)",
        "Lines",
        lambda: dc.line(100, 100, 300, 300, 0xFFFF),
        iterations=200,
    )

    runner.run_test(
        "line - long diagonal (400px)",
        "Lines",
        lambda: dc.line(50, 50, 450, 450, 0xFFFF),
        iterations=100,
    )

    # TEST 5: FILLED RECTANGLES

    runner.run_test(
        "fill_rect - tiny (10x10)",
        "Rectangles",
        lambda: dc.fill_rect(100, 100, 10, 10, 0x07E0),
        iterations=1000,
    )

    runner.run_test(
        "fill_rect - small (50x50)",
        "Rectangles",
        lambda: dc.fill_rect(100, 100, 50, 50, 0x07E0),
        iterations=500,
    )

    runner.run_test(
        "fill_rect - medium (100x100)",
        "Rectangles",
        lambda: dc.fill_rect(100, 100, 100, 100, 0x07E0),
        iterations=200,
    )

    runner.run_test(
        "fill_rect - large (200x200)",
        "Rectangles",
        lambda: dc.fill_rect(100, 100, 200, 200, 0x07E0),
        iterations=100,
    )

    runner.run_test(
        "fill_rect - huge (400x300)",
        "Rectangles",
        lambda: dc.fill_rect(100, 75, 400, 300, 0x07E0),
        iterations=50,
    )

    runner.run_test(
        "fill_rect - full screen (600x450)",
        "Rectangles",
        lambda: dc.fill_rect(0, 0, 600, 450, 0x07E0),
        iterations=50,
    )

    # TEST 6: RECTANGLE OUTLINES

    runner.run_test(
        "rect - small (50x50)",
        "Outlines",
        lambda: dc.rect(100, 100, 50, 50, 0x001F),
        iterations=500,
    )

    runner.run_test(
        "rect - medium (100x100)",
        "Outlines",
        lambda: dc.rect(100, 100, 100, 100, 0x001F),
        iterations=300,
    )

    runner.run_test(
        "rect - large (200x200)",
        "Outlines",
        lambda: dc.rect(100, 100, 200, 200, 0x001F),
        iterations=200,
    )

    runner.run_test(
        "rect - huge (400x300)",
        "Outlines",
        lambda: dc.rect(100, 75, 400, 300, 0x001F),
        iterations=100,
    )

    runner.run_test(
        "rect - full screen (600x450)",
        "Outlines",
        lambda: dc.rect(0, 0, 600, 450, 0x001F),
        iterations=50,
    )

    # TEST 7: CIRCLE OUTLINES

    runner.run_test(
        "circle - small (r=10)",
        "Circles",
        lambda: dc.circle(300, 225, 10, 0xFFE0),
        iterations=500,
    )

    runner.run_test(
        "circle - medium (r=50)",
        "Circles",
        lambda: dc.circle(300, 225, 50, 0xFFE0),
        iterations=200,
    )

    runner.run_test(
        "circle - large (r=100)",
        "Circles",
        lambda: dc.circle(300, 225, 100, 0xFFE0),
        iterations=100,
    )

    runner.run_test(
        "circle - huge (r=200)",
        "Circles",
        lambda: dc.circle(300, 225, 200, 0xFFE0),
        iterations=50,
    )

    # Multiple circles test
    def draw_10_circles():
        for r in range(10, 110, 10):
            dc.circle(300, 225, r, 0xF800)

    runner.run_test(
        "circle - 10 circles (r=10-100)",
        "Circles",
        draw_10_circles,
        iterations=10,
        setup_func=lambda: dc.fill_color(0x0000),
    )

    # TEST 8: FILLED CIRCLES

    runner.run_test(
        "fill_circle - small (r=10)",
        "Circles",
        lambda: dc.fill_circle(300, 225, 10, 0xF81F),
        iterations=200,
    )

    runner.run_test(
        "fill_circle - medium (r=50)",
        "Circles",
        lambda: dc.fill_circle(300, 225, 50, 0xF81F),
        iterations=50,
    )

    runner.run_test(
        "fill_circle - large (r=100)",
        "Circles",
        lambda: dc.fill_circle(300, 225, 100, 0xF81F),
        iterations=20,
    )

    runner.run_test(
        "fill_circle - huge (r=200)",
        "Circles",
        lambda: dc.fill_circle(300, 225, 200, 0xF81F),
        iterations=10,
    )

    # TEST 9: SINGLE PIXELS

    runner.run_test(
        "pixel - single draw",
        "Pixels",
        lambda: dc.pixel(100, 100, 0xFFFF),
        iterations=1000,
    )

    # PRINT RESULTS TABLE
    runner.print_results_table()

    # Cleanup
    dc.fill_color(0x0000)
    dc.refresh()
    print("Benchmark complete. Display cleared.")
    dc.deinit()
    print()


if __name__ == "__main__":
    main()
