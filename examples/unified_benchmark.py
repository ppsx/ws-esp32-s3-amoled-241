"""
RM690B0 Unified Image Benchmark Suite
=====================================

Comprehensive benchmark tool for testing image conversion and display performance.
Supports RAW, BMP, and JPEG formats.

Usage:
    import unified_benchmark
    unified_benchmark.run()  # Interactive menu

Or run specific tests:
    unified_benchmark.quick_test()
    unified_benchmark.full_benchmark()
    unified_benchmark.diagnostic()
    unified_benchmark.format_comparison()
"""

import time
import gc
import sys
import os
import rm690b0


# =============================================================================
# Configuration
# =============================================================================

CONFIG = {
    "files": {
        "RAW": "/cerber.raw",
        "BMP": "/cerber.bmp",
        "JPG": "/cerber.jpg",
    },
    "raw_dimensions": {"width": 600, "height": 450},
    "display_time": 3.0,  # seconds to show each image
    "separator_time": 1.5,  # black screen between images
    "iterations": {
        "quick": 3,
        "normal": 10,
        "thorough": 20,
    },
}

CHUNK_SIZE = 1024 * 1024  # read in 128 KB chunks by default

# =============================================================================
# Utility Functions
# =============================================================================


def print_line(char="=", length=70):
    """Print separator line."""
    print(char * length)


def print_header(text, char="="):
    """Print centered header with separators."""
    print_line(char)
    print(text.center(70))
    print_line(char)


def print_section(text):
    """Print section header."""
    print(f"\n{text}")
    print_line("-")


def format_size(bytes_val):
    """Format bytes as human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} bytes"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.1f} MB"


def format_time(seconds):
    """Format time in ms."""
    return f"{seconds * 1000:.2f} ms"


def calculate_stats(times):
    """Calculate min, max, avg from list of times."""
    if not times:
        return 0, 0, 0
    return min(times), max(times), sum(times) / len(times)


def get_memory_info():
    """Get current memory info."""
    try:
        import gc

        gc.collect()
        free = gc.mem_free()
        allocated = gc.mem_alloc()
        return {"free": free, "allocated": allocated, "total": free + allocated}
    except:
        return None


def show_black_screen(display, message=None):
    """Clear display and optionally show message."""
    display.fill_color(rm690b0.BLACK)
    display.swap_buffers()
    if message:
        print(f"\n>>> {message} <<<")


# =============================================================================
# File Loading
# =============================================================================


def load_file_into(filepath, buffer, size=None):
    """Stream ``filepath`` into an existing bytearray using ``readinto``."""
    expected_size = size if size is not None else len(buffer)
    mv = memoryview(buffer)
    offset = 0

    try:
        with open(filepath, "rb") as f:
            while offset < expected_size:
                chunk = min(CHUNK_SIZE, expected_size - offset)
                n_read = f.readinto(mv[offset : offset + chunk])
                if not n_read:
                    break
                offset += n_read
    except OSError:
        return -1

    return offset


def load_file(filepath):
    """Load a file into memory using a preallocated buffer and readinto()."""
    try:
        size = os.stat(filepath)[6]
    except OSError:
        return None

    try:
        buf = bytearray(size)
    except MemoryError:
        try:
            gc.collect()
            buf = bytearray(size)
        except MemoryError:
            print(f"  ⚠️  Out of memory loading {filepath}")
            return None

    read_bytes = load_file_into(filepath, buf, size)
    if read_bytes < 0:
        return None

    if read_bytes < size:
        print(f"  ⚠️  Short read from {filepath}: expected {size} bytes, got {read_bytes}")
        del buf[read_bytes:]
    return buf


def preload_files(verbose=True):
    """Pre-load all test files into RAM."""
    if verbose:
        print_header("PRE-LOADING FILES INTO RAM")
        print("\nEliminating file I/O from performance measurements.\n")

    files_data = {}
    total_size = 0

    for fmt, filepath in CONFIG["files"].items():
        if verbose:
            print(f"Loading {fmt:4s} from {filepath}...")

        t_start = time.monotonic()
        data = load_file(filepath)
        t_elapsed = time.monotonic() - t_start

        if data:
            files_data[fmt] = data
            total_size += len(data)
            if verbose:
                print(f"  ✅ Loaded {len(data):>9,} bytes in {t_elapsed * 1000:.0f}ms")
        else:
            if verbose:
                print(f"  ⚠️  File not found, skipping")

    if verbose:
        print(f"\nTotal: {len(files_data)} files, {format_size(total_size)}")

    return files_data


# =============================================================================
# Conversion Functions
# =============================================================================


def convert_image(format_name, data, width=None, height=None):
    """
    Convert image data to RGB565.

    Returns: (buffer, info) or raises exception
    """
    if format_name == "RAW":
        # RAW is already RGB565 format - ZERO CONVERSION NEEDED!
        # Data goes directly to display with no processing
        # This is instant (< 0.1ms) - just returns the data
        w = width or CONFIG["raw_dimensions"]["width"]
        h = height or CONFIG["raw_dimensions"]["height"]
        info = {
            "width": w,
            "height": h,
            "data_size": len(data),
            "bit_depth": 16,
            "channels": 3,
            "has_alpha": False,
        }
        return data, info  # Direct passthrough - no conversion!
    elif format_name == "BMP":
        return rm690b0.bmp_to_rgb565(data)
    elif format_name == "JPG":
        if not hasattr(rm690b0, "jpg_to_rgb565"):
            raise NotImplementedError("JPEG not yet implemented")
        return rm690b0.jpg_to_rgb565(data)
    else:
        raise ValueError(f"Unknown format: {format_name}")


def benchmark_conversion(format_name, data, iterations=10, debug_memory=False):
    """
    Benchmark conversion performance.

    Returns: (buffer, info, times_list)
    """
    times = []
    memory_stats = []
    buffer = None
    info = None

    # Warmup iteration to trigger JIT compilation (except for RAW)
    if format_name != "RAW":  # RAW needs no warmup - it's instant
        try:
            gc.collect()
            warmup_buffer, _ = convert_image(format_name, data)
            del warmup_buffer
            warmup_buffer = None
            gc.collect()
        except:
            pass  # If warmup fails, continue anyway

    if debug_memory:
        print(f"\n  Memory tracking enabled (iterations: {iterations})")

    for i in range(iterations):
        # Clean memory before timing
        gc.collect()

        # Track memory before conversion
        if debug_memory:
            mem_before = get_memory_info()
            if mem_before:
                memory_stats.append(mem_before["free"])

        t_start = time.monotonic()

        try:
            buffer, info = convert_image(format_name, data)
        except Exception as e:
            if i == 0:
                raise  # Re-raise on first iteration
            else:
                print(f"  Warning: iteration {i + 1} failed: {e}")
                continue

        # Stop timing immediately after conversion
        t_elapsed = time.monotonic() - t_start
        times.append(t_elapsed)

        # Show iteration stats if debugging
        if debug_memory and i < 3:  # Show first 3 iterations
            mem_after = get_memory_info()
            if mem_after:
                print(
                    f"  Iter {i + 1}: {t_elapsed * 1000:.1f}ms, mem: {format_size(mem_after['free'])}"
                )

        # Clean up buffer (except last iteration) - AFTER timing
        if i < iterations - 1:
            del buffer
            buffer = None
            # Extra gc to ensure cleanup
            gc.collect()

    if debug_memory and memory_stats:
        print(
            f"  Memory range: {format_size(min(memory_stats))} - {format_size(max(memory_stats))}"
        )

    return buffer, info, times


def benchmark_display(display, buffer, width, height, iterations=5):
    """Benchmark display performance."""
    times = []

    for i in range(iterations):
        t_start = time.monotonic()
        display.blit_buffer(0, 0, width, height, buffer)
        display.swap_buffers()
        t_elapsed = time.monotonic() - t_start
        times.append(t_elapsed)

    return times


# =============================================================================
# Test Modes
# =============================================================================


def quick_test():
    """Quick sanity test - load and display each format once."""
    print_header("QUICK TEST MODE")
    print("\nLoading and displaying each image format once.")
    print("Note: RAW format has ZERO conversion (already RGB565)\n")

    # Initialize display FIRST
    print("Initializing display...")
    try:
        display = rm690b0.RM690B0()
        display.init_display()
        print("✅ Display ready!\n")
    except Exception as e:
        print(f"❌ Failed to initialize display: {e}")
        return

    # Load files after display is initialized
    files_data = preload_files(verbose=False)
    if not files_data:
        print("❌ No files found!")
        display.deinit()
        return

    print(f"Loaded {len(files_data)} files\n")

    # Test each format
    for fmt, data in files_data.items():
        print_line("-")
        print(f"Testing {fmt} ({format_size(len(data))})")

        try:
            t_start = time.monotonic()
            buffer, info = convert_image(fmt, data)
            t_convert = time.monotonic() - t_start

            t_start = time.monotonic()
            display.blit_buffer(0, 0, info["width"], info["height"], buffer)
            display.swap_buffers()
            t_display = time.monotonic() - t_start

            print(f"  Dimensions: {info['width']}×{info['height']}")
            print(f"  Convert:    {format_time(t_convert)}")
            print(f"  Display:    {format_time(t_display)}")
            print(f"  Total:      {format_time(t_convert + t_display)}")
            print(f"  ✅ Success!")

            time.sleep(2.0)
            del buffer
            buffer = None
            gc.collect()

        except NotImplementedError as e:
            print(f"  ⚠️  {e}")
        except MemoryError:
            print(f"  ❌ Out of memory")
            gc.collect()
        except Exception as e:
            print(f"  ⚠️  {e}")

    show_black_screen(display)
    display.deinit()
    print_line()
    print("✅ Quick test complete!")


def full_benchmark(iterations=10, memory_efficient=False):
    """Full benchmark with detailed statistics."""
    mode_text = (
        "FULL BENCHMARK MODE" if not memory_efficient else "MEMORY-EFFICIENT BENCHMARK MODE"
    )
    print_header(mode_text)
    print(f"\nIterations: {iterations} (conversion), 5 (display)\n")

    if memory_efficient:
        print("🔋 Memory-efficient mode: Loading files one at a time")
        print()

    # Check memory before starting
    mem = get_memory_info()
    if mem:
        print(f"Initial memory: {format_size(mem['free'])} free\n")

    # Initialize display FIRST (before loading files)
    print_header("INITIALIZING DISPLAY", "-")
    try:
        display = rm690b0.RM690B0()
        display.init_display()
        print("✅ Display ready!")
    except Exception as e:
        print(f"❌ Failed to initialize display: {e}")
        return

    # Check memory after display init
    mem = get_memory_info()
    if mem:
        print(f"\nMemory after display: {format_size(mem['free'])} free")
        if mem["free"] < 500000:  # Less than 500KB
            print("⚠️  WARNING: Low memory! Pre-loading files may fail.")
            print("    Consider testing one format at a time.\n")

    # Pre-load files (or prepare to load individually)
    print("\n")

    if memory_efficient:
        # Memory-efficient mode: just check which files exist
        files_data = {}
        for fmt, filepath in CONFIG["files"].items():
            try:
                size = os.stat(filepath)[6]
                files_data[fmt] = {"size": size, "path": filepath}
                print(f"Found {fmt:4s}: {format_size(size)}")
            except OSError:
                pass

        if not files_data:
            print("\n❌ No files found!")
            display.deinit()
            return

        print(f"\nTotal: {len(files_data)} files (will load one at a time)\n")
    else:
        # Standard mode: pre-load all files
        files_data = preload_files()
        if not files_data:
            print("\n❌ No files found!")
            display.deinit()
            return

        # Check memory after loading files
        mem = get_memory_info()
        if mem:
            print(f"\nMemory after loading: {format_size(mem['free'])} free\n")

    results = []
    formats = ["RAW", "BMP", "JPG"]

    if memory_efficient:
        available = [f for f in formats if f in files_data]
    else:
        available = [f for f in formats if f in files_data]

    # Test each format
    for i, fmt in enumerate(available, 1):
        print(f"\n")
        print_header(f"[{i}/{len(available)}] BENCHMARKING {fmt} FORMAT")

        # Load data (either from pre-loaded dict or from file)
        if memory_efficient:
            print(f"Loading {fmt} from {files_data[fmt]['path']}...")
            data = load_file(files_data[fmt]["path"])
            if data is None:
                print(f"❌ Failed to load file!")
                continue
            print(f"✅ Loaded {format_size(len(data))}")
        else:
            data = files_data[fmt]

        try:
            show_black_screen(display)
            time.sleep(0.5)

            # Force clean memory before benchmark
            gc.collect()

            # Conversion benchmark (with memory debugging for slow cases)
            print(f"\nRunning conversion benchmark ({iterations} iterations)...")
            # Enable debug for BMP to track memory issues
            debug_mode = fmt == "BMP" and iterations > 5
            buffer, info, conv_times = benchmark_conversion(
                fmt, data, iterations, debug_memory=debug_mode
            )

            conv_min, conv_max, conv_avg = calculate_stats(conv_times)

            # Display benchmark
            print(f"Running display benchmark (5 iterations)...")
            disp_times = benchmark_display(display, buffer, info["width"], info["height"], 5)
            disp_min, disp_max, disp_avg = calculate_stats(disp_times)

            # Print results
            total = conv_avg + disp_avg
            fps = 1.0 / total if total > 0 else 0

            file_size = len(data) if not memory_efficient else files_data[fmt]["size"]

            print(f"\n{fmt} RESULTS:")
            print(f"  File size:         {file_size:>10,} bytes ({file_size / 1024:.1f} KB)")
            print(f"  Image size:        {info['width']}×{info['height']}")
            print(f"  RGB565 size:       {info['data_size']:>10,} bytes")
            if fmt == "RAW":
                print(f"  CONVERSION ({len(conv_times)} iterations):")
                print(f"    Average:         {format_time(conv_avg)}")
                print(f"    Note:            RAW is already RGB565 - no actual conversion")
                print(f"                     Time shown is Python overhead only (< 0.1ms ideal)")
            else:
                print(f"  CONVERSION ({len(conv_times)} iterations):")
                print(f"    Average:         {format_time(conv_avg)}")
                print(f"    Min:             {format_time(conv_min)}")
                print(f"    Max:             {format_time(conv_max)}")
                if conv_avg > 0:
                    throughput = len(data) / conv_avg / (1024 * 1024)
                    print(f"    Throughput:      {throughput:>10.2f} MB/s")
            print(f"\n  DISPLAY ({len(disp_times)} iterations):")
            print(f"    Average:         {format_time(disp_avg)}")
            print(f"    Min:             {format_time(disp_min)}")
            print(f"    Max:             {format_time(disp_max)}")
            print(f"\n  TOTAL:")
            print(f"    Time:            {format_time(total)}")
            print(f"    Potential FPS:   {fps:>10.1f}")

            # Store results
            file_size = len(data) if not memory_efficient else files_data[fmt]["size"]
            results.append(
                {
                    "format": fmt,
                    "file_size": file_size,
                    "convert_avg": conv_avg,
                    "display_avg": disp_avg,
                    "total": total,
                    "info": info,
                }
            )

            # Display image
            print(f"\nDisplaying {fmt} image for {CONFIG['display_time']}s...")
            display.blit_buffer(0, 0, info["width"], info["height"], buffer)
            display.swap_buffers()
            time.sleep(CONFIG["display_time"])

            # Explicitly free memory
            del buffer
            buffer = None

            # In memory-efficient mode, also free the loaded data
            if memory_efficient:
                del data
                data = None
                # Force aggressive garbage collection
                gc.collect()
                gc.collect()  # Second pass to clean circular references

            gc.collect()

            # Show memory after cleanup
            if memory_efficient:
                mem = get_memory_info()
                if mem:
                    print(f"Memory after cleanup: {format_size(mem['free'])}")

            if i < len(available):
                show_black_screen(display)
                time.sleep(CONFIG["separator_time"])

        except NotImplementedError as e:
            print(f"\n⚠️  SKIPPED: {e}")
            continue
        except MemoryError as e:
            print(f"\n❌ OUT OF MEMORY: {e}")
            print("    Try closing other programs or use smaller images.")
            gc.collect()
            continue
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            continue

    # Summary
    print("\n")
    print_header("BENCHMARK SUMMARY")

    if results:
        print("\nFormat Comparison (TRUE performance - no file I/O):")
        print_line("-")
        print(
            f"{'Format':<8} {'Size':<12} {'Convert':<12} {'Display':<12} {'Total':<12} {'FPS':<8}"
        )
        print_line("-")

        for r in results:
            size_kb = r["file_size"] / 1024
            print(
                f"{r['format']:<8} {size_kb:>8.1f} KB  {format_time(r['convert_avg']):>10}  "
                f"{format_time(r['display_avg']):>10}  {format_time(r['total']):>10}  "
                f"{1.0 / r['total']:>6.1f}"
            )

        print_line("-")

        # Find best
        fastest = min(results, key=lambda x: x["total"])
        smallest = min(results, key=lambda x: x["file_size"])

        print(f"\n🏆 Fastest:  {fastest['format']} ({format_time(fastest['total'])})")
        print(f"💾 Smallest: {smallest['format']} ({format_size(smallest['file_size'])})")

        if "RAW" in [r["format"] for r in results]:
            print(f"\nℹ️  RAW format shows true zero-conversion performance")
            print(f"   (Data goes directly to display with no processing)")
    else:
        print("\n⚠️  No results to display")

    print_line()
    show_black_screen(display)
    display.deinit()


def diagnostic():
    """Diagnostic mode - identify performance bottlenecks."""
    print_header("PERFORMANCE DIAGNOSTIC")
    print("\nIdentifying performance bottlenecks...\n")

    iterations = 5

    # System info
    print_header("SYSTEM INFORMATION", "-")
    print(f"\nPython version: {sys.version}")
    print(f"Platform: {sys.platform if hasattr(sys, 'platform') else 'Unknown'}")

    mem = get_memory_info()
    if mem:
        print(f"\nMemory:")
        print(f"  Free:       {mem['free']:>10,} bytes ({mem['free'] / 1024:.1f} KB)")
        print(f"  Allocated:  {mem['allocated']:>10,} bytes ({mem['allocated'] / 1024:.1f} KB)")

    # File I/O test
    print_header("FILE I/O PERFORMANCE", "=")

    for fmt, filepath in CONFIG["files"].items():
        print(f"\nTesting: {filepath}")

        try:
            size = os.stat(filepath)[6]
        except OSError:
            print(f"  File not found: {filepath}")
            continue

        try:
            buffer = bytearray(size)
        except MemoryError:
            gc.collect()
            try:
                buffer = bytearray(size)
            except MemoryError:
                print(f"  ⚠️  Not enough memory to allocate {size} bytes")
                continue

        times = []
        short_read = False

        for i in range(iterations):
            gc.collect()
            t_start = time.monotonic()
            read_bytes = load_file_into(filepath, buffer, size)
            if read_bytes < 0:
                short_read = True
                break
            t_elapsed = time.monotonic() - t_start
            times.append(t_elapsed)
            if read_bytes != size:
                short_read = True

        if not times:
            print(f"  ⚠️  Unable to collect timing data")
            continue

        min_t, max_t, avg_t = calculate_stats(times)

        for i, t in enumerate(times, 1):
            print(f"  Iteration {i}: {format_time(t):>10} ({size:>10,} bytes)")

        if short_read:
            print(f"  ⚠️  Detected truncated read during streaming test")

        if avg_t > 0:
            throughput = size / avg_t / (1024 * 1024)
            print(f"  Average:    {format_time(avg_t):>10} ({throughput:.2f} MB/s)")
        else:
            print(f"  Average:    {format_time(avg_t):>10} (throughput N/A)")

        del buffer

    # Memory operations
    print_header("MEMORY OPERATIONS", "=")

    test_size = 540000
    print(f"\nAllocating {test_size:,} bytes...")
    times = []
    for i in range(iterations):
        gc.collect()
        t_start = time.monotonic()
        buf = bytearray(test_size)
        t_elapsed = time.monotonic() - t_start
        times.append(t_elapsed)
        del buf

    min_t, max_t, avg_t = calculate_stats(times)
    for i, t in enumerate(times, 1):
        print(f"  Iteration {i}: {format_time(t):>10}")
    print(f"  Average:    {format_time(avg_t):>10}")
    if avg_t < 0.050:
        print(f"  ✅ Memory allocation is fast")

    # Conversion tests
    print_header("CONVERSION PERFORMANCE", "=")

    files_data = preload_files(verbose=False)

    for fmt in ["RAW", "BMP", "JPG"]:
        if fmt not in files_data:
            continue

        print(f"\nTesting {fmt} conversion...")
        data = files_data[fmt]
        times = []

        for i in range(iterations):
            gc.collect()
            t_start = time.monotonic()
            try:
                buffer, info = convert_image(fmt, data)
                t_elapsed = time.monotonic() - t_start
                times.append(t_elapsed)
                del buffer
            except Exception as e:
                print(f"  Error: {e}")
                break

        if times:
            min_t, max_t, avg_t = calculate_stats(times)
            for i, t in enumerate(times, 1):
                print(f"  Iteration {i}: {format_time(t):>10}")

            if avg_t > 0:
                throughput = len(data) / avg_t / (1024 * 1024)
                print(f"  Average:      {format_time(avg_t):>10} ({throughput:.2f} MB/s)")
            else:
                print(f"  Average:      {format_time(avg_t):>10} (throughput N/A)")

            if fmt == "RAW":
                print(f"  ✅ RAW format: ZERO conversion (already RGB565)")
                print(f"      Data goes directly to display - instant!")
                print(f"      Measured time is just Python function call overhead")

    # Display test
    print_header("DISPLAY PERFORMANCE", "=")

    print("\nInitializing display...")
    display = rm690b0.RM690B0()
    display.init_display()
    print("✅ Display initialized")

    if "RAW" in files_data:
        print("\nLoading test image...")
        buffer, info = convert_image("RAW", files_data["RAW"])
        print(f"✅ Image ready: {info['width']}×{info['height']}")

        print("\nDrawing to display...")
        times = benchmark_display(display, buffer, info["width"], info["height"], iterations)

        min_t, max_t, avg_t = calculate_stats(times)
        for i, t in enumerate(times, 1):
            print(f"  Iteration {i}: {format_time(t):>10}")

        fps = 1.0 / avg_t if avg_t > 0 else 0
        print(f"  Average:    {format_time(avg_t):>10} ({fps:.1f} FPS)")

        if avg_t > 0.070:
            print(f"  ⚠️  Display is slow (check SPI speed?)")

        del buffer

    show_black_screen(display)
    display.deinit()

    print_header("DIAGNOSTIC COMPLETE", "=")


def format_comparison():
    """Side-by-side format comparison."""
    print_header("FORMAT COMPARISON")
    print("\nComparing all available image formats.\n")

    # Initialize display FIRST
    print("Initializing display...")
    try:
        display = rm690b0.RM690B0()
        display.init_display()
        print("✅ Display ready!\n")
    except Exception as e:
        print(f"❌ Failed to initialize display: {e}")
        return

    # Pre-load files after display is initialized
    files_data = preload_files(verbose=False)
    if not files_data:
        print("❌ No files found!")
        display.deinit()
        return

    print(f"Found {len(files_data)} formats\n")

    results = []

    for i, (fmt, data) in enumerate(files_data.items(), 1):
        print_line("-")
        print(f"[{i}/{len(files_data)}] {fmt} FORMAT")
        print_line("-")
        filepath = CONFIG["files"][fmt]

        try:
            print(f"\nLoading: {filepath}")

            buffer_size = len(data)
            try:
                load_buffer = bytearray(buffer_size)
            except MemoryError:
                gc.collect()
                try:
                    load_buffer = bytearray(buffer_size)
                except MemoryError:
                    raise MemoryError(f"Not enough memory to allocate {buffer_size} bytes for load buffer")

            t_start = time.monotonic()
            read_bytes = load_file_into(filepath, load_buffer, buffer_size)
            t_load = time.monotonic() - t_start

            if read_bytes != buffer_size:
                raise OSError(f"Short read: expected {buffer_size} bytes, got {read_bytes}")

            del load_buffer
            gc.collect()

            print("Converting to RGB565...")
            t_start = time.monotonic()
            buffer, info = convert_image(fmt, data)
            t_convert = time.monotonic() - t_start

            print("Displaying image...")
            t_start = time.monotonic()
            display.blit_buffer(0, 0, info["width"], info["height"], buffer)
            display.swap_buffers()
            t_display = time.monotonic() - t_start

            total = t_load + t_convert + t_display

            print(f"\nResults:")
            print(f"  File size:     {len(data):>10,} bytes ({len(data) / 1024:.1f} KB)")
            print(f"  Dimensions:    {info['width']}×{info['height']}")
            print(f"  Load time:     {format_time(t_load)}")
            print(f"  Convert time:  {format_time(t_convert)}")
            print(f"  Display time:  {format_time(t_display)}")
            print(f"  TOTAL:         {format_time(total)}")
            fps = 1.0 / total if total > 0 else float("inf")
            print(f"  Potential FPS: {fps:.1f}")

            results.append(
                {
                    "format": fmt,
                    "size": len(data),
                    "load": t_load,
                    "convert": t_convert,
                    "total": total,
                }
            )

            print(f"\nShowing {fmt} image for {CONFIG['display_time']}s...")
            time.sleep(CONFIG["display_time"])

            del buffer
            gc.collect()

            if i < len(files_data):
                show_black_screen(display)
                time.sleep(CONFIG["separator_time"])

        except Exception as e:
            print(f"\n⚠️  SKIPPED: {e}")

    # Summary
    print_header("COMPARISON SUMMARY")

    if results:
        print(
            f"\n{'Format':<8} {'Size (KB)':<12} {'Load':<12} {'Convert':<12} {'Total':<12} {'FPS':<8}"
        )
        print_line("-")

        for r in results:
            size_kb = r["size"] / 1024
            fps = (1.0 / r["total"]) if r["total"] > 0 else float("inf")
            print(
                f"{r['format']:<8} {size_kb:>8.1f} KB  {format_time(r['load']):>10}  "
                f"{format_time(r['convert']):>10}  {format_time(r['total']):>10}  {fps:>6.1f}"
            )

        print_line("-")

        fastest = min(results, key=lambda x: x["total"])
        smallest = min(results, key=lambda x: x["size"])

        print(f"\nFastest: {fastest['format']} ({format_time(fastest['total'])})")
        print(f"Smallest: {smallest['format']} ({format_size(smallest['size'])})")

    print_line()
    show_black_screen(display)
    display.deinit()
    print("\n✅ Comparison complete!")


# =============================================================================
# Interactive Menu
# =============================================================================


def show_menu():
    """Display interactive menu."""
    print_header("RM690B0 UNIFIED BENCHMARK SUITE")
    print("\nSelect a test mode:\n")
    print("  1. Quick Test        - Fast sanity check (3 iterations)")
    print("  2. Full Benchmark    - Detailed performance analysis (10 iterations)")
    print("  3. Diagnostic        - Identify bottlenecks")
    print("  4. Format Comparison - Side-by-side comparison")
    print("  5. Exit")
    print()


def run():
    """Main entry point with interactive menu."""
    while True:
        show_menu()

        try:
            choice = input("Enter choice (1-5): ").strip()
            print()

            if choice == "1":
                quick_test()
            elif choice == "2":
                full_benchmark()
            elif choice == "3":
                diagnostic()
            elif choice == "4":
                format_comparison()
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1-5.")

            print("\n")
            input("Press Enter to continue...")
            print("\n" * 2)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            if hasattr(sys, "print_exception"):
                sys.print_exception(e)
            input("\nPress Enter to continue...")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
