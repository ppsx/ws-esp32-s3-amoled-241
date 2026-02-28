# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Unified Image Benchmark Suite - displayio version
===================================================

Comprehensive benchmark for testing image conversion and display performance.
Supports RAW, BMP, and JPEG formats using displayio, jpegio, bitmaptools.
"""

import gc
import os
import sys
import time
import struct
import io
import array

import board
import bitmaptools
import jpegio
import displayio
from rm690b0 import RM690B0, create_qspi_bus

# =============================================================================
# Configuration
# =============================================================================

CONFIG = {
    "files": {
        "RAW": "/gfx/cerber.raw",
        "BMP": "/gfx/cerber.bmp",
        "JPG": "/gfx/cerber.jpg",
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

canvas = None
display = None

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


def show_black_screen(display, canvas):
    """Clear display"""
    canvas.fill(0)


def get_bmp_parameters(data):
    """Extract width, height, and data offset from BMP data."""
    if isinstance(data, (bytes, bytearray, memoryview)):
        # Data Offset at 0x0A (4 bytes)
        offset = struct.unpack_from("<I", data, 10)[0]
        # Width/Height at 0x12 (18)
        width, height = struct.unpack_from("<ii", data, 18)
    else:
        # Assuming BytesIO or file-like
        pos = data.tell()
        data.seek(10)
        offset = struct.unpack("<I", data.read(4))[0]
        data.seek(18)
        width, height = struct.unpack("<ii", data.read(8))
        data.seek(pos)
    return width, abs(height), offset


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
            print(f"   Out of memory loading {filepath}")
            return None

    read_bytes = load_file_into(filepath, buf, size)
    if read_bytes < 0:
        return None
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
                print(f"  Loaded {len(data):>9,} bytes in {t_elapsed * 1000:.0f}ms")
        else:
            if verbose:
                print(f"  File not found, skipping")

    if verbose:
        print(f"\nTotal: {len(files_data)} files, {format_size(total_size)}")

    return files_data


# =============================================================================
# Conversion Functions
# =============================================================================


def convert_image(format_name, data, width=None, height=None):
    """Convert image data to displayio Bitmap."""
    if format_name == "RAW":
        w = width or CONFIG["raw_dimensions"]["width"]
        h = height or CONFIG["raw_dimensions"]["height"]
        bitmap = displayio.Bitmap(w, h, 65536)
        raw_array = array.array("H", data)
        bitmaptools.arrayblit(bitmap, raw_array, x1=0, y1=0, x2=w, y2=h)
        info = {
            "width": w,
            "height": h,
            "data_size": len(data),
            "bit_depth": 16,
            "swapped": False,
        }
        return bitmap, info

    elif format_name == "BMP":
        # Parse dimensions
        w, h, offset = get_bmp_parameters(data)
        # Parse BMP header for bits_per_pixel
        bits_per_pixel = struct.unpack_from('<H', data, 28)[0]

        pixel_count = w * h

        if bits_per_pixel == 24:
            # Manual 24-bit BGR → RGB565 conversion
            row_bytes = w * 3
            row_padding = (4 - (row_bytes % 4)) % 4
            buffer = array.array("H", [0] * pixel_count)

            for row in range(h):
                src_offset = offset + row * (row_bytes + row_padding)
                dst_row = h - 1 - row  # BMP is bottom-to-top
                dst_start = dst_row * w

                for col in range(w):
                    b = data[src_offset + col * 3]
                    g = data[src_offset + col * 3 + 1]
                    r = data[src_offset + col * 3 + 2]
                    rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                    buffer[dst_start + col] = rgb565

            bitmap = displayio.Bitmap(w, h, 65536)
            bitmaptools.arrayblit(bitmap, buffer, x1=0, y1=0, x2=w, y2=h)

        elif bits_per_pixel == 16:
            # 16-bit BMP: read and flip rows
            buffer = array.array("H", data[offset:offset + pixel_count * 2])
            flipped = array.array("H", [0] * pixel_count)
            for row in range(h):
                src_row = h - 1 - row
                src_start = src_row * w
                dst_start = row * w
                flipped[dst_start:dst_start + w] = buffer[src_start:src_start + w]

            bitmap = displayio.Bitmap(w, h, 65536)
            bitmaptools.arrayblit(bitmap, flipped, x1=0, y1=0, x2=w, y2=h)
        else:
            raise ValueError(f"Unsupported BMP format: {bits_per_pixel}bpp")

        info = {
            "width": w,
            "height": h,
            "data_size": w * h * 2,
            "bit_depth": 16,
            "swapped": False,
        }
        return bitmap, info

    elif format_name == "JPG":
        # Use jpegio
        decoder = jpegio.JpegDecoder()
        stream = io.BytesIO(data)
        w, h = decoder.open(stream)
        img_bitmap = displayio.Bitmap(w, h, 65536)
        decoder.decode(img_bitmap)

        # jpegio outputs RGB565_SWAPPED on ESP32-S3, need to byte-swap
        pixel_count = w * h
        swapped = array.array("H", [0] * pixel_count)

        for i in range(pixel_count):
            pixel = img_bitmap[i % w, i // w]
            # Swap bytes: 0xAABB → 0xBBAA
            swapped[i] = ((pixel & 0xFF) << 8) | (pixel >> 8)

        # Reuse img_bitmap and overwrite with swapped data
        bitmaptools.arrayblit(img_bitmap, swapped, x1=0, y1=0, x2=w, y2=h)
        del swapped

        info = {
            "width": w,
            "height": h,
            "data_size": w * h * 2,
            "bit_depth": 16,
            "swapped": False,
        }
        return img_bitmap, info

    else:
        raise ValueError(f"Unknown format: {format_name}")


def benchmark_conversion(format_name, data, iterations=10):
    times = []
    bitmap = None
    info = None

    # Warmup
    if format_name != "RAW":  # RAW needs no warmup - it's instant
        try:
            gc.collect()
            warmup_buffer, _ = convert_image(format_name, data)
            del warmup_buffer
            warmup_buffer = None
            gc.collect()
        except:
            pass  # If warmup fails, continue anyway

    for i in range(iterations):
        # Clean memory before timing
        gc.collect()
        t_start = time.monotonic()

        try:
            bitmap, info = convert_image(format_name, data)
        except Exception as e:
            if i == 0:
                raise  # Re-raise on first iteration
            else:
                print(f"  Warning: iteration {i + 1} failed: {e}")
                continue

        # Stop timing immediately after conversion
        t_elapsed = time.monotonic() - t_start
        times.append(t_elapsed)
        # Clean up buffer (except last iteration) - AFTER timing
        if i < iterations - 1:
            del bitmap
            bitmap = None
            # Extra gc to ensure cleanup
            gc.collect()

    return bitmap, info, times


def benchmark_display(display, canvas, bitmap, info, iterations=5):
    """Benchmark blit + refresh performance."""
    times = []
    w = info["width"]
    h = info["height"]
    for _ in range(iterations):
        t_start = time.monotonic()
        bitmaptools.blit(canvas, bitmap, 0, 0)
        display.refresh()
        t_elapsed = time.monotonic() - t_start
        times.append(t_elapsed)

    return times


# =============================================================================
# Test Modes
# =============================================================================


def _init_display():
    """Common display initialization."""
    global display, canvas
    print("Initializing display...")
    displayio.release_displays()
    bus = create_qspi_bus(board)
    display = RM690B0(bus)
    print(f"Display created: {display.width}x{display.height}")

    try:
        display.brightness = 1.0
        print("Brightness set to 1.0")
    except RuntimeError as e:
        print(f"Brightness not adjustable: {e}")

    # Use fixed dimensions like test_animation.py
    WIDTH = 600
    HEIGHT = 450

    canvas = displayio.Bitmap(WIDTH, HEIGHT, 65536)
    print(f"Canvas created: {canvas.width}x{canvas.height}")

    cc = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565)
    tg = displayio.TileGrid(canvas, pixel_shader=cc)
    group = displayio.Group()
    group.append(tg)
    display.root_group = group
    print("Display group set")

    # Initial clear and refresh (important!)
    canvas.fill(0x0000)
    print("Canvas cleared")

    # Test pattern to verify display works
    # Draw red diagonal line
    for i in range(min(WIDTH, HEIGHT)):
        canvas[i, i] = 0xF800  # Red
    print("Test pattern drawn")

    display.refresh()
    print("Display refreshed")

    return display, canvas


def quick_test():
    """Quick sanity test - load and display each format once."""
    print_header("QUICK TEST MODE")
    print("\nLoading and displaying each image format once.")

    display, canvas = _init_display()
    # Load files after display is initialized
    files_data = preload_files(verbose=False)
    if not files_data:
        print("No files found!")
        displayio.release_displays()
        return

    print(f"Loaded {len(files_data)} files\n")

    # Test each format
    for fmt, data in files_data.items():
        print_line("-")
        print(f"Testing {fmt} ({format_size(len(data))})")

        try:
            t_start = time.monotonic()
            bitmap, info = convert_image(fmt, data)
            t_convert = time.monotonic() - t_start

            t_start = time.monotonic()
            bitmaptools.blit(canvas, bitmap, 0, 0)
            display.refresh()
            t_display = time.monotonic() - t_start

            print(f"  Dimensions: {info['width']}x{info['height']}")
            print(f"  Convert:    {format_time(t_convert)}")
            print(f"  Display:    {format_time(t_display)}")
            print(f"  Total:      {format_time(t_convert + t_display)}")
            print(f"  Success!")

            time.sleep(2.0)
            del bitmap
            bitmap = None
            gc.collect()

        except NotImplementedError as e:
            print(f"  {e}")
        except MemoryError:
            print(f"  Out of memory")
            gc.collect()
        except Exception as e:
            print(f"  Error: {e}")

    show_black_screen(display, canvas)
    displayio.release_displays()
    print_line()
    print("Quick test complete!")


def full_benchmark(iterations=10):
    """Full benchmark with detailed statistics."""
    print_header("FULL BENCHMARK MODE")
    print(f"\nIterations: {iterations} (conversion), 5 (display)\n")

    # Check memory before starting
    mem = get_memory_info()
    if mem:
        print(f"Initial memory: {format_size(mem['free'])} free\n")

    # Initialize display FIRST (before loading files)
    display, canvas = _init_display()

    files_data = preload_files()
    if not files_data:
        print("No files found!")
        displayio.release_displays()
        return

    results = []
    formats = ["RAW", "BMP", "JPG"]
    available = [f for f in formats if f in files_data]

    # Test each format
    for i, fmt in enumerate(available, 1):
        print(f"\n")
        print_header(f"[{i}/{len(available)}] BENCHMARKING {fmt} FORMAT")
        data = files_data[fmt]

        try:
            show_black_screen(display, canvas)
            time.sleep(0.5)

            # Force clean memory before benchmark
            gc.collect()

            # Conversion benchmark (with memory debugging for slow cases)
            print(f"\nRunning conversion benchmark ({iterations} iterations)...")
            bitmap, info, conv_times = benchmark_conversion(fmt, data, iterations)
            conv_min, conv_max, conv_avg = calculate_stats(conv_times)

            # Display benchmark
            print(f"Running display benchmark (5 iterations)...")
            disp_times = benchmark_display(display, canvas, bitmap, info, 5)
            disp_min, disp_max, disp_avg = calculate_stats(disp_times)

            # Print results
            total = conv_avg + disp_avg
            fps = 1.0 / total if total > 0 else 0

            print(f"\n{fmt} RESULTS:")
            print(f"  File size:         {len(data):>10,} bytes ({len(data) / 1024:.1f} KB)")
            print(f"  Image size:        {info['width']}x{info['height']}")
            print(f"  CONVERSION ({len(conv_times)} iterations):")
            print(f"    Average:         {format_time(conv_avg)}")
            if fmt != "RAW":
                print(f"    Min:             {format_time(conv_min)}")
                print(f"    Max:             {format_time(conv_max)}")
                if conv_avg > 0:
                    throughput = len(data) / conv_avg / (1024 * 1024)
                    print(f"    Throughput:      {throughput:>10.2f} MB/s")
            else:
                print(f"    Note:            RAW is already RGB565 - arrayblit only")
            print(f"\n  DISPLAY ({len(disp_times)} iterations):")
            print(f"    Average:         {format_time(disp_avg)}")
            print(f"    Min:             {format_time(disp_min)}")
            print(f"    Max:             {format_time(disp_max)}")
            print(f"\n  TOTAL:")
            print(f"    Time:            {format_time(total)}")
            print(f"    Potential FPS:   {fps:>10.1f}")

            results.append({
                "format": fmt,
                "file_size": len(data),
                "convert_avg": conv_avg,
                "display_avg": disp_avg,
                "total": total,
                "info": info,
            })

            # Display image
            print(f"\nDisplaying {fmt} image for {CONFIG['display_time']}s...")
            bitmaptools.blit(canvas, bitmap, 0, 0)
            display.refresh()
            time.sleep(CONFIG["display_time"])

            # Explicitly free memory
            del bitmap
            bitmap = None
            gc.collect()

            if i < len(available):
                show_black_screen(display, canvas)
                time.sleep(CONFIG["separator_time"])

        except NotImplementedError as e:
            print(f"\nSKIPPED: {e}")
            continue
        except MemoryError as e:
            print(f"\nOUT OF MEMORY: {e}")
            gc.collect()
            continue
        except Exception as e:
            print(f"\nERROR: {e}")
            continue

    # Summary
    print("\n")
    print_header("BENCHMARK SUMMARY")

    if results:
        print(f"\n{'Format':<8} {'Size':<12} {'Convert':<12} {'Display':<12} {'Total':<12} {'FPS':<8}")
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

        print(f"\nFastest:  {fastest['format']} ({format_time(fastest['total'])})")
        print(f"Smallest: {smallest['format']} ({format_size(smallest['file_size'])})")

    print_line()
    show_black_screen(display, canvas)
    displayio.release_displays()


def format_comparison():
    """Side-by-side format comparison."""
    print_header("FORMAT COMPARISON")
    print("\nComparing all available image formats.\n")

    # Initialize display FIRST
    print("Initializing display...")
    display, canvas = _init_display()

    # Pre-load files after display is initialized
    files_data = preload_files(verbose=False)
    if not files_data:
        print("No files found!")
        displayio.release_displays()
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
            load_buffer = bytearray(buffer_size)
            t_start = time.monotonic()
            load_file_into(filepath, load_buffer, buffer_size)
            t_load = time.monotonic() - t_start
            del load_buffer
            gc.collect()

            # Conversion
            print("Converting to RGB565...")
            t_start = time.monotonic()
            bitmap, info = convert_image(fmt, data)
            t_convert = time.monotonic() - t_start

            # Display
            print("Displaying image...")
            t_start = time.monotonic()
            bitmaptools.blit(canvas, bitmap, 0, 0)
            display.refresh()
            t_display = time.monotonic() - t_start

            total = t_load + t_convert + t_display

            print(f"\n  File size:     {len(data):>10,} bytes ({len(data) / 1024:.1f} KB)")
            print(f"  Dimensions:    {info['width']}x{info['height']}")
            print(f"  Load time:     {format_time(t_load)}")
            print(f"  Convert time:  {format_time(t_convert)}")
            print(f"  Display time:  {format_time(t_display)}")
            print(f"  TOTAL:         {format_time(total)}")
            fps = 1.0 / total if total > 0 else float("inf")
            print(f"  Potential FPS: {fps:.1f}")

            results.append({
                "format": fmt,
                "size": len(data),
                "load": t_load,
                "convert": t_convert,
                "total": total,
            })

            print(f"\nShowing {fmt} image for {CONFIG['display_time']}s...")
            time.sleep(CONFIG["display_time"])

            del bitmap
            gc.collect()

            if i < len(files_data):
                show_black_screen(display, canvas)
                time.sleep(CONFIG["separator_time"])

        except Exception as e:
            print(f"\n  SKIPPED: {e}")

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

    show_black_screen(display, canvas)
    displayio.release_displays()
    print("\nComparison complete!")


# =============================================================================
# Interactive Menu
# =============================================================================


def show_menu():
    """Display interactive menu."""
    print_header("IMAGE BENCHMARK SUITE (displayio)")
    print("\nSelect a test mode:\n")
    print("  1. Quick Test        - Fast sanity check")
    print("  2. Full Benchmark    - Detailed performance analysis")
    print("  3. Format Comparison - Side-by-side comparison")
    print("  x. Exit")
    print()


def run():
    """Main entry point with interactive menu."""
    while True:
        show_menu()

        try:
            choice = input("Enter choice (1-3, x): ").strip()
            print()

            if choice == "1":
                quick_test()
            elif choice == "2":
                full_benchmark()
            elif choice == "3":
                format_comparison()
            elif choice == "x":
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")

            print("\n")
            input("Press Enter to continue...")
            print("\n" * 2)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nERROR: {e}")
            input("\nPress Enter to continue...")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        # Clean up
        canvas.fill(0)
        display.refresh()
        displayio.release_displays()
