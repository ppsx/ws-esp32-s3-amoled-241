# SPDX-FileCopyrightText: Copyright (c) 2025 Przemyslaw Patrick Socha
#
# SPDX-License-Identifier: MIT
#
# Optimized Image Loader Example (JPG, BMP, RAW)
# Demonstrates high-performance image loading using PSRAM and native drivers.

import gc
import os
import time

import board
import espsdcard
import rm690b0
import storage

print("=" * 60)
print("  Optimized Image Loader Example")
print("=" * 60)

# 1. Initialize Display
print("\nInitializing display...")
display = rm690b0.RM690B0()
display.init_display()
display.brightness = 1.0
print("✓ Display initialized")

# 2. Initialize SD Card (Native SDMMC Interface)
# Using espsdcard provides ~645 KB/s read speeds vs ~200 KB/s for SPI
print("\nInitializing SD card...")
try:
    sd = espsdcard.SDCard(
        cs=board.SD_CS, miso=board.SD_MISO, mosi=board.SD_MOSI, clk=board.SD_CLK
    )
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")
    print("✓ SD card mounted at /sd")
except Exception as e:
    print(f"✗ SD Card Error: {e}")
    print("  (Make sure SD card is inserted and formatted FAT32)")


def show_image(path, x=0, y=0, width=600, height=450):
    """
    Load and display an image with maximum performance.

    Strategies used:
    1. Pre-allocate buffer in PSRAM (avoids fragmentation)
    2. Use f.readinto() for direct DMA transfer from SD
    3. Use hardware-accelerated rendering methods

    Args:
        path (str): Path to image file on SD card
        x, y (int): Coordinates for top-left corner
        width, height (int): Dimensions (required ONLY for .raw files)
    """
    print(f"\nLoading {path}...")

    # Force GC before allocation to maximize continuous memory
    gc.collect()

    try:
        # Check if file exists and get size
        stat = os.stat(path)
        size = stat[6]

        # Strategy: Allocate buffer in PSRAM
        # On ESP32-S3, large allocations automatically go to PSRAM
        print(f"  Allocating {size / 1024:.1f} KB buffer...")
        try:
            buffer = bytearray(size)
        except MemoryError:
            print("  ✗ Failed to allocate buffer (Out of Memory)")
            return

        # Strategy: Fast read using native driver
        t0 = time.monotonic()
        with open(path, "rb") as f:
            f.readinto(buffer)
        t1 = time.monotonic()
        read_speed = (size / 1024) / (t1 - t0)
        print(f"  Read finished in {t1 - t0:.3f}s ({read_speed:.1f} KB/s)")

        # Strategy: Select optimal rendering method
        t2 = time.monotonic()
        filename = path.lower()

        if filename.endswith((".jpg", ".jpeg")):
            # Hardware JPEG Decoder (ESP32-S3)
            # - Handles decompression in hardware
            # - Handles colorspace conversion
            print("  Rendering JPEG...")
            display.blit_jpeg(x, y, buffer)

        elif filename.endswith(".bmp"):
            # Native BMP Renderer
            # - Optimized for 16/24-bit uncompressed BMP
            # - Uses fast clipping and direct framebuffer access
            print("  Rendering BMP...")
            display.blit_bmp(x, y, buffer)

        elif filename.endswith(".raw"):
            # Direct Framebuffer Blit
            # - Fastest possible method (memory copy)
            # - Requires known dimensions
            # - Format must be RGB565 (2 bytes per pixel)
            expected_size = width * height * 2
            if size < expected_size:
                print(f"  ✗ Error: RAW file too small ({size} < {expected_size})")
                return

            print(f"  Blitting RAW ({width}x{height})...")
            display.blit_buffer(x, y, width, height, buffer)

        else:
            print("  ✗ Unsupported format")
            return

        # Hardware buffer swap (vsync)
        display.swap_buffers()

        t3 = time.monotonic()
        print(f"  Render time: {t3 - t2:.3f}s")
        print("  ✓ Success")

    except OSError as e:
        print(f"  ✗ File error: {e}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    finally:
        # Cleanup: Help GC reclaim the large buffer immediately
        buffer = None
        gc.collect()


# --- Demo Loop ---
# Looks for images on SD card and displays them

print("\nStarting slideshow...")

# Define some known raw image sizes if you have them
# filename -> (width, height)
RAW_SIZES = {"cerber.raw": (600, 450), "cyborg.raw": (256, 256)}

# On the uSD card there are 6 files present:
# cerber.[bmp|jpg|raw] (600x450) and cyborg.[bmp|jpg|raw] (256x256)

for ext in ['bmp', 'jpg', 'raw']:
    for file in ['cerber', 'cyborg']:
        img = file + "." + ext
        full_path = "/sd/" + img
        print(f"  Loading {img}...")

        # Determine dimensions for RAW files
        w, h = 600, 450  # Default full screen
        if img.lower().endswith(".raw"):
            if img in RAW_SIZES:
                w, h = RAW_SIZES[img]
            else:
                # Try to guess or default to full screen
                print(f"  Note: Using default 600x450 for {img}")

        show_image(full_path, 0, 0, w, h)
        time.sleep(2)

# Clean up
display.fill_color(rm690b0.BLACK)
display.swap_buffers()
display.deinit()

print("\nDone.")
