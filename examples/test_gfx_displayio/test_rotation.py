# Copyright (c) 2025 Przemyslaw Patrick Socha

import gc
import time

import board
import displayio
import jpegio
from rm690b0 import RM690B0, create_qspi_bus

print("Initializing display...")
displayio.release_displays()
bus = create_qspi_bus(board)
display = RM690B0(bus)
def set_brightness(val):
    try:
        display.brightness = val
    except RuntimeError:
        print(f">> Can't sset brightness to ${val}")
        pass

set_brightness(1.0)

# Path to image in internal flash
path = "/gfx/cyborg.jpg"
print(f"Loading {path}...")

try:
    # Decode JPEG into bitmap
    decoder = jpegio.JpegDecoder()
    w, h = decoder.open(path)
    bitmap = displayio.Bitmap(w, h, 65536)
    decoder.decode(bitmap)
    print(f"JPEG decoded: {w}x{h}")

    # Create displayio scene
    cc = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565_SWAPPED)
    tg = displayio.TileGrid(bitmap, pixel_shader=cc, x=10, y=10)
    group = displayio.Group()
    group.append(tg)

    # Rotate and display loop
    for angle in [0, 90, 180, 270]:
        print(f"Testing rotation: {angle}")
        set_brightness(1.0)
        display.rotation = angle

        display.root_group = group
        display.refresh()

        time.sleep(2)

        # Fade out
        for b in range(100, -1, -5):
            set_brightness(b / 100.0)
            time.sleep(0.1)

        # Clear screen for next rotation
        display.root_group = None
        display.refresh()

except OSError as e:
    print(f"Error reading file '{path}': {e}")
    print("Ensure the file exists in the /gfx directory on the internal flash.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    gc.collect()

displayio.release_displays()
print("Done.")
