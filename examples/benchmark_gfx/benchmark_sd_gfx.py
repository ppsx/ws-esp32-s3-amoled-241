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
import sdioio
import rm690b0
import storage
import struct
import bitmaptools
import jpegio
import displayio

print("=" * 60)
print("  Optimized Image Loader Example")
print("=" * 60)

# 1. Initialize Display
print("\nInitializing display...")
display = rm690b0.RM690B0()
display.init_display()
display.brightness = 1.0
print("✓ Display initialized")

# 2. Initialize SD Card (sdioio 1-bit mode)
print("\nInitializing SD card...")
try:
    sd = sdioio.SDCard(
        clock=board.SDIO_CLK,
        command=board.SDIO_CMD,
        data=[board.SDIO_D0],
        frequency=40_000_000,
    )
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")
    print("✓ SD card mounted at /sd")
except Exception as e:
    print(f"✗ SD Card Error: {e}")
    print("  (Make sure SD card is inserted and formatted FAT32)")



def get_bmp_parameters(path):
    with open(path, "rb") as f:
        # Offset at 10, Width/Height at 18
        f.seek(10)
        offset = struct.unpack("<I", f.read(4))[0]
        f.seek(18)
        width, height = struct.unpack("<ii", f.read(8))
    return width, abs(height), offset


def show_image(path, x=0, y=0, width=600, height=450):
    """
    Load and display an image with maximum performance.

    Strategies used:
    1. Pre-allocate buffer in PSRAM (avoids fragmentation)
    2. Use bitmaptools/jpegio for optimized decoding
    3. Use direct framebuffer access via blit_buffer
    """
    print(f"\nLoading {path}...")
    gc.collect()

    try:
        filename = path.lower()
        t0 = time.monotonic()

        if filename.endswith((".jpg", ".jpeg")):
            # Hardware-accelerated JPEG Decoder (via jpegio)
            print("  Decoding JPEG (jpegio)...")
            decoder = jpegio.JpegDecoder()
            w, h = decoder.open(path)

            # Create bitmap in PSRAM (implicitly via displayio)
            bitmap = displayio.Bitmap(w, h, 65535)
            decoder.decode(bitmap)

            t1 = time.monotonic()
            print(f"  Decor time: {t1 - t0:.3f}s")

            # JPEG decoder on ESP32-S3 outputs swapped bytes (Big Endian) for LCD direct drive.
            # We must tell blit_buffer that the data is already swapped.
            display.blit_buffer(x, y, w, h, bitmap, dest_is_swapped=True)

        elif filename.endswith(".bmp"):
            # Native BMP Renderer (via RM690B0 converter)
            print("  Decoding BMP (rm690b0.convert_bmp)...")
            w, h, offset = get_bmp_parameters(path)
            bitmap = displayio.Bitmap(w, h, 65535)

            # Read whole file for convert_bmp
            with open(path, "rb") as f:
                data = f.read()

            # Convert in-place from RGB888/RGB565 to Swapped RGB565
            display.convert_bmp(data, bitmap)

            t1 = time.monotonic()
            print(f"  Decor time: {t1 - t0:.3f}s")

            display.blit_buffer(x, y, w, h, bitmap, dest_is_swapped=True)

        elif filename.endswith(".raw"):
            # Direct Framebuffer Blit
            # Requires known dimensions
            stat = os.stat(path)
            size = stat[6]
            expected_size = width * height * 2

            if size < expected_size:
                print(f"  ✗ Error: RAW file too small ({size} < {expected_size})")
                return

            print(f"  Allocating {size / 1024:.1f} KB buffer...")
            buffer = bytearray(size)

            with open(path, "rb") as f:
                f.readinto(buffer)

            t1 = time.monotonic()
            print(f"  Read time: {t1 - t0:.3f}s")

            print(f"  Blitting RAW ({width}x{height})...")
            display.blit_buffer(x, y, width, height, buffer)
            del buffer

        else:
            print("  ✗ Unsupported format")
            return

        # Hardware buffer swap (vsync)
        display.swap_buffers()
        print("  ✓ Success")

    except OSError as e:
        print(f"  ✗ File error: {e}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    finally:
        gc.collect()


# --- Demo Loop ---
# Looks for images on SD card and displays them

print("\nStarting slideshow...")

# Define some known raw image sizes if you have them
# filename -> (width, height)
RAW_SIZES = {"cerber.raw": (600, 450), "cyborg.raw": (256, 256)}

# On the uSD card there are 6 files present:
# cerber.[bmp|jpg|raw] (600x450) and cyborg.[bmp|jpg|raw] (256x256)

for ext in ["bmp", "jpg", "raw"]:
    for file in ["cerber", "cyborg"]:
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
