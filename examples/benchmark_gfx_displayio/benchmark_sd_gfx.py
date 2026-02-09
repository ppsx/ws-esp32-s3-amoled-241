# SPDX-FileCopyrightText: Copyright (c) 2026 Przemyslaw Patrick Socha
#
# SPDX-License-Identifier: MIT
#
# Optimized Image Loader Example (JPG, BMP, RAW) — displayio version
# Demonstrates image loading using jpegio, OnDiskBitmap, and arrayblit.

import gc
import os
import time

import board
import sdioio
import storage
import struct
import bitmaptools
import jpegio
import displayio
from rm690b0 import RM690B0, create_qspi_bus

print("=" * 60)
print("  Optimized Image Loader Example (displayio)")
print("=" * 60)

# 1. Initialize Display
print("\nInitializing display...")
displayio.release_displays()
bus = create_qspi_bus(board)
display = RM690B0(bus)
try:
    display.brightness = 1.0
except RuntimeError:
    pass
print("Display initialized")

# Create canvas bitmap + scene
canvas = displayio.Bitmap(display.width, display.height, 65536)
cc = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565)
tg = displayio.TileGrid(canvas, pixel_shader=cc)
group = displayio.Group()
group.append(tg)
display.root_group = group

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
    print("SD card mounted at /sd")
except Exception as e:
    print(f"SD Card Error: {e}")
    print("  (Make sure SD card is inserted and formatted FAT32)")


def show_image(path, x=0, y=0, width=600, height=450):
    """Load and display an image using displayio APIs."""
    print(f"\nLoading {path}...")
    gc.collect()

    try:
        filename = path.lower()
        t0 = time.monotonic()

        if filename.endswith((".jpg", ".jpeg")):
            # JPEG via jpegio
            print("  Decoding JPEG (jpegio)...")
            decoder = jpegio.JpegDecoder()
            w, h = decoder.open(path)
            img_bitmap = displayio.Bitmap(w, h, 65536)
            decoder.decode(img_bitmap)

            t1 = time.monotonic()
            print(f"  Decode time: {t1 - t0:.3f}s")

            # jpegio outputs RGB565_SWAPPED on ESP32-S3
            # Need to byte-swap pixels before blitting to canvas
            print("  Swapping JPEG byte order...")
            import array
            pixel_count = w * h
            swapped = array.array("H", [0] * pixel_count)

            for i in range(pixel_count):
                pixel = img_bitmap[i % w, i // w]
                # Swap bytes: 0xAABB → 0xBBAA
                swapped[i] = ((pixel & 0xFF) << 8) | (pixel >> 8)

            # Blit swapped pixels to canvas
            bitmaptools.arrayblit(
                canvas, swapped,
                x1=x, y1=y,
                x2=x + w, y2=y + h
            )
            del img_bitmap, swapped

        elif filename.endswith(".bmp"):
            # BMP: Manual conversion (OnDiskBitmap doesn't support pixel access)
            print("  Loading BMP (manual read)...")
            with open(path, "rb") as f:
                # Read BMP header
                header = f.read(54)
                if header[0:2] != b'BM':
                    print("  Error: Not a valid BMP file")
                    return

                # Parse dimensions (little-endian at offset 18, 22)
                bmp_w = struct.unpack('<I', header[18:22])[0]
                bmp_h = struct.unpack('<I', header[22:26])[0]
                data_offset = struct.unpack('<I', header[10:14])[0]
                bits_per_pixel = struct.unpack('<H', header[28:30])[0]

                print(f"  BMP: {bmp_w}x{bmp_h}, {bits_per_pixel}bpp, data offset: {data_offset}")

                # Seek to pixel data
                f.seek(data_offset)

                import array
                pixel_count = bmp_w * bmp_h

                if bits_per_pixel == 24:
                    # Read 24-bit RGB and convert to RGB565
                    print("  Converting 24-bit RGB to RGB565...")
                    row_bytes = bmp_w * 3
                    # BMP rows are padded to 4-byte boundary
                    row_padding = (4 - (row_bytes % 4)) % 4

                    buffer = array.array("H", [0] * pixel_count)

                    for row in range(bmp_h):
                        row_data = f.read(row_bytes)
                        f.read(row_padding)  # Skip padding

                        # BMP is bottom-to-top, so reverse row index
                        dst_row = bmp_h - 1 - row
                        dst_start = dst_row * bmp_w

                        # Convert BGR888 to RGB565
                        for col in range(bmp_w):
                            b = row_data[col * 3]
                            g = row_data[col * 3 + 1]
                            r = row_data[col * 3 + 2]
                            # RGB565: 5 bits R, 6 bits G, 5 bits B
                            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                            buffer[dst_start + col] = rgb565

                elif bits_per_pixel == 16:
                    # Read 16-bit directly
                    buffer = array.array("H", bytearray(pixel_count * 2))
                    f.readinto(buffer)

                    # Flip rows (bottom-to-top → top-to-bottom)
                    flipped = array.array("H", bytearray(pixel_count * 2))
                    for row in range(bmp_h):
                        src_row = bmp_h - 1 - row
                        src_start = src_row * bmp_w
                        dst_start = row * bmp_w
                        flipped[dst_start:dst_start + bmp_w] = buffer[src_start:src_start + bmp_w]
                    buffer = flipped

                else:
                    print(f"  Error: Unsupported BMP format ({bits_per_pixel}bpp)")
                    return

            t1 = time.monotonic()
            print(f"  Process time: {t1 - t0:.3f}s")

            # Blit entire buffer to canvas
            bitmaptools.arrayblit(
                canvas, buffer,
                x1=x, y1=y,
                x2=x + bmp_w, y2=y + bmp_h
            )
            del buffer

        elif filename.endswith(".raw"):
            # Direct RAW RGB565 via arrayblit
            stat = os.stat(path)
            size = stat[6]
            expected_size = width * height * 2

            if size < expected_size:
                print(f"  Error: RAW file too small ({size} < {expected_size})")
                return

            print(f"  Reading RAW ({size / 1024:.1f} KB)...")
            import array
            buffer = array.array("H", bytearray(size))

            with open(path, "rb") as f:
                f.readinto(buffer)

            t1 = time.monotonic()
            print(f"  Read time: {t1 - t0:.3f}s")

            print(f"  Blitting RAW ({width}x{height})...")
            bitmaptools.arrayblit(
                canvas, buffer,
                x1=x, y1=y,
                x2=x + width, y2=y + height,
            )
            del buffer

        else:
            print("  Unsupported format")
            return

        display.refresh()
        print("  Success")

    except OSError as e:
        print(f"  File error: {e}")
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        gc.collect()


# --- Demo Loop ---
print("\nStarting slideshow...")

RAW_SIZES = {"cerber.raw": (600, 450), "cyborg.raw": (256, 256)}

for ext in ["bmp", "jpg", "raw"]:
    for file in ["cerber", "cyborg"]:
        img = file + "." + ext
        full_path = "/sd/" + img
        print(f"  Loading {img}...")

        w, h = 600, 450
        if img.lower().endswith(".raw"):
            if img in RAW_SIZES:
                w, h = RAW_SIZES[img]
            else:
                print(f"  Note: Using default 600x450 for {img}")

        show_image(full_path, 0, 0, w, h)
        time.sleep(2)

    # Clear canvas after each format group
    print(f"  Clearing screen after {ext} files...")
    canvas.fill(0)
    display.refresh()
    time.sleep(0.5)

# Clean up
canvas.fill(0)
display.refresh()
displayio.release_displays()

print("\nDone.")
