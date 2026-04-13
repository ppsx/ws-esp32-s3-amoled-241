# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Display Shim wrapping RM690B0
import rm690b0
from .rect import Rect

_display = None
_display_owned = True

class Surface:
    def __init__(self, size_or_raw=None, flags=0):
        if isinstance(size_or_raw, (tuple, list)):
            self.width, self.height = size_or_raw
            self._bitmap = None # We will load bitmaps lazily or manage raw data
            self.is_display = False
        else:
            # Assume it's an internal object or display
            self.width = 0
            self.height = 0
            self.is_display = False
        self.fill_color = None

    def subsurface(self, rect):
        return SubSurface(self, rect)

    def blit(self, source, dest, area=None, special_flags=0):
        if self.is_display:
            if not _display: return
            
            # Determine dest coords
            dx, dy = 0, 0
            if isinstance(dest, Rect):
                dx, dy = dest.x, dest.y
            elif isinstance(dest, (tuple, list)):
                dx, dy = dest[0], dest[1]
                
            # Handle SubSurface source
            src_x, src_y = 0, 0
            real_source = source
            
            if isinstance(source, SubSurface):
                src_x, src_y = source.get_offset()
                real_source = source.parent
                
            # Check clip
            if hasattr(self, '_clip') and self._clip:
                # Simple rejection test
                if isinstance(dest, Rect):
                   draw_rect = Rect(dest.x, dest.y, 0, 0)
                else: 
                   draw_rect = Rect(dest[0], dest[1], 0, 0)
                
                # We need source size to know full rect
                if hasattr(real_source, 'width') and hasattr(real_source, 'height'):
                    draw_rect.w = real_source.width
                    draw_rect.h = real_source.height
                    
                    if not self._clip.colliderect(draw_rect):
                        return # Clipped out
            
            # Draw source to display
            # We assume real_source (likely BitmapSurface) has a way to draw itself
            if hasattr(real_source, 'draw_to_display'):
                # Pass the offset from subsurface + any area offset
                if area:
                    src_x += area[0]
                    src_y += area[1]
                
                real_source.draw_to_display(_display, dx, dy, src_offset=(src_x, src_y))
                
            elif source.fill_color is not None:
                 # Solid color surface
                 w = source.width
                 h = source.height
                 if area: w, h = area[2], area[3]
                 _display.fill_rect(int(dx), int(dy), int(w), int(h), source.fill_color)
                 
    def fill(self, color, rect=None):
        # Convert any color format to BGR565 (RM690B0 framebuffer byte order)
        if isinstance(color, (tuple, list)):
            r, g, b = color[0], color[1], color[2]
            c565 = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)
        elif isinstance(color, (bytes, bytearray)):
            r, g, b = color[0], color[1], color[2]
            c565 = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)
        elif isinstance(color, int):
            c565 = color
        else:
            c565 = 0

        if self.is_display:
            if _display:
                if rect:
                    _display.fill_rect(int(rect.x), int(rect.y),
                                       int(rect.w), int(rect.h), c565)
                else:
                    _display.fill_color(c565)
        else:
            self.fill_color = c565
             
    def convert(self): return self
    def convert_alpha(self): return self
    def set_colorkey(self, color): pass
    def get_rect(self): return Rect(0,0,self.width, self.height)
    def get_size(self): return (self.width, self.height)
    
    def set_clip(self, rect):
        # We store it but current blit shim might ignore it for now
        # Ideally we should respect it in blit
        self._clip = rect
        
    def get_clip(self):
        if hasattr(self, '_clip') and self._clip:
            return self._clip
        return self.get_rect()
    
    def copy(self):
        s = Surface((self.width, self.height))
        s.fill_color = self.fill_color
        return s

    def get_flags(self):
        return 0

    def draw_to_display(self, display, x, y, src_offset=None):
        pass

class SubSurface(Surface):
    def __init__(self, parent, rect):
        self.parent = parent
        self.rect = rect
        self.width = rect.w
        self.height = rect.h
        self.is_display = False

    def get_offset(self):
        # Recursive offset if needed
        return self.rect.x, self.rect.y

def inject_display(hw_display):
    """Accept an externally-owned display (from code.py menu)."""
    global _display, _display_owned
    _display = hw_display
    _display_owned = False

def set_mode(size=(600, 450), flags=0):
    global _display, _display_owned
    if _display is None:
         _display = rm690b0.RM690B0()
         _display.init_display()
         try:
             import settings
             _display.rotation = settings.rotation
         except ImportError:
             pass
         _display.brightness = 1.0
         _display_owned = True

    # Return a Surface representing the display
    s = Surface(size)
    s.is_display = True
    return s

def is_display_owned():
    return _display_owned

def flip():
    if _display:
        _display.swap_buffers()

def update():
    flip()

def get_surface():
    # Return main display surface if needed
    return None 

# Stub
def set_caption(caption): pass
def get_driver(): return "rm690b0"
def toggle_fullscreen(): return True

# Internal access to driver
def get_hw_driver():
    return _display
