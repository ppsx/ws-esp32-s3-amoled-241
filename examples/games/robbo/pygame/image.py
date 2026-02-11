# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Image Shim
from .display import Surface
import os

# Transparent color #ff00df in byte-swapped RGB565 for RM690B0
_TRANSPARENT = 0x1BF8

class BitmapSurface(Surface):
    def __init__(self, filename):
        super().__init__((32,32))
        self.filename = filename
        self.bmp_data = None
        self.buffer = None
        self.swapped = False
        self.width = 32
        self.height = 32
        
        try:
            with open(filename, "rb") as f:
                self.bmp_data = f.read()
                
            # Parse header
            import struct
            if self.bmp_data[:2] == b'BM':
                # Offset 18: Width (i32), Offset 22: Height (i32)
                self.width, self.height = struct.unpack_from("<ii", self.bmp_data, 18)
                self.height = abs(self.height)
        except Exception as e:
            print(f"Failed to load {filename}: {e}")

    
    def draw_to_display(self, display, x, y, src_offset=None):
        if not self.bmp_data and not self.buffer: return
        
        if self.buffer is None:
            # Lazy conversion
            import displayio
            import gc
            
            # print(f"DEBUG: Lazy loading BMP {self.filename} ({self.width}x{self.height})...")
            try:
                self.buffer = displayio.Bitmap(self.width, self.height, 65535)
                
                # FORCE Fallback to bitmaptools for safety with standard BMPs
                import bitmaptools
                import io
                import struct
                
                # Find start of pixel data (offset at 0x0A)
                offset = struct.unpack_from("<I", self.bmp_data, 10)[0]
                
                stream = io.BytesIO(self.bmp_data)
                stream.seek(offset)
                
                try:
                    bitmaptools.readinto(self.buffer, stream, bits_per_pixel=16)
                    self.swapped = False # bitmaptools usually reads as native/LE?
                    # Note: If colors are wrong (swapped R/B), toggle this.
                    # Standard BMP is BGR. 565 is usually LE. 
                    # If we use bits_per_pixel=16, it expects 16-bit data?
                    # NO! bitmaptools.readinto expects the INPUT stream to match bits_per_pixel?
                    # "Read the file into the bitmap... bits_per_pixel: The number of bits per pixel in the file"
                    # But our file is 24-bit RBG! 
                    # bitmaptools.readinto in CircuitPython 9.x usually implies converting?
                    # Documentation says: "Reads data from the file into the bitmap... If bits_per_pixel is 0, it is inferred from the bitmap."
                    # If we pass 24-bit data to a 16-bit bitmap, does it convert?
                    # NO! bitmaptools usually expects the data in the stream to MATCH the bitmap or be specific format.
                    # THERE IS NO AUTO-CONVERT from 24-bit to 16-bit in simple readinto?
                    # Wait, convert_bmp DOES do that.
                    # let's try convert_bmp again but WRAPPED safer?
                    pass 
                except Exception as b_err:
                     print(f"bitmaptools error: {b_err}")
                
                # RETRY convert_bmp as primary since readinto might not handle 24->16 conversion
                if hasattr(display, "convert_bmp"):
                     # print("DEBUG: Trying convert_bmp...")
                     try:
                         display.convert_bmp(self.bmp_data, self.buffer)
                         self.swapped = True
                         # print("DEBUG: convert_bmp success")
                     except Exception as c_err:
                         print(f"convert_bmp failed: {c_err}")
                         # If both fail, we have a problem.
                
                # Free raw data to save RAM
                self.bmp_data = None
                gc.collect()
            except Exception as e:
                print(f"Conversion failed for {self.filename}: {e}")
                self.buffer = None
                return

        if self.buffer:
             if hasattr(display, "blit_buffer"):
                  display.blit_buffer(int(x), int(y), self.width, self.height, self.buffer, dest_is_swapped=self.swapped, transparent_color=_TRANSPARENT)
             elif hasattr(display, "blit_bmp"): 
                  pass

def load(filename):
    return BitmapSurface(filename)
