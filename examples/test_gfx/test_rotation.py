# Copyright (c) 2025 Przemyslaw Patrick Socha

import gc
import os
import time
import rm690b0

print("Initializing display...")
display = rm690b0.RM690B0()
display.init_display()
display.brightness = 1.0

# Path to image in internal flash
path = "/gfx/cyborg.jpg"
print(f"Loading {path}...")

try:
    # Read file into memory buffer
    # Note: We rely on standard file I/O from internal flash
    with open(path, "rb") as f:
        stat = os.stat(path)
        size = stat[6]
        print(f"File size: {size} bytes")
        buffer = bytearray(size)
        f.readinto(buffer)
        
    # Rotate and display loop
    for angle in [0, 90, 180, 270]:
        print(f"Testing rotation: {angle}")
        display.brightness = 1.0
        display.rotation = angle
        
        # Display image at (10, 10)
        display.blit_jpeg(10, 10, buffer)
        display.swap_buffers()
        
        time.sleep(2)
        
        # Fade out
        for b in range(100, -1, -5):
            display.brightness = b / 100.0
            time.sleep(0.01)
            
        # Clear screen
        display.fill_color(0x0000) 
        display.swap_buffers()

except OSError as e:
    print(f"Error reading file '{path}': {e}")
    print("Ensure the file exists in the /gfx directory on the internal flash.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    buffer = None
    gc.collect()

display.deinit()
print("Done.")
