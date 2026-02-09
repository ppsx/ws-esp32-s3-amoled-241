# SPDX-FileCopyrightText: Copyright (c) 2026 Przemyslaw Patrick Socha
#
# SPDX-License-Identifier: MIT

"""
DisplayCompat - rm690b0-style imperative drawing API on top of displayio.
Should be used only on the firmware without native rm690b0 module.

Provides a compatibility layer so old test scripts can run on the new
displayio-based firmware with minimal changes.

Usage:
    import board
    import displayio
    from rm690b0 import RM690B0, create_qspi_bus
    from display_compat import DisplayCompat, BLACK, WHITE, RED

    displayio.release_displays()
    bus = create_qspi_bus(board)
    display = RM690B0(bus)
    dc = DisplayCompat(display)

    dc.fill_color(BLACK)
    dc.fill_rect(10, 10, 100, 50, RED)
    dc.circle(300, 225, 100, WHITE)
    dc.refresh()
"""

import math
import displayio
import bitmaptools

# ============================================================================
# RGB565 Color Constants (exact values from old rm690b0 C module)
# ============================================================================

WHITE = 0xFFFF
BLACK = 0x0000
DARK_GRAY = 0x2104
GRAY = 0x8410
LIGHT_GRAY = 0xC618
BROWN = 0x59E4
DARK_BROWN = 0x30A0
YELLOW = 0xFFE0
BLUE = 0x001F
ROYAL_BLUE = 0x435C
SKY_BLUE = 0x867D
DARK_BLUE = 0x0010
LIGHT_BLUE = 0x261F
LIGHT_VIOLET = 0x8BFD
VIOLET = 0x49F1
PURPLE = 0x8010
PINK = 0xF81F
MAGENTA = 0xBABA
OLIVE = 0x8400
GREEN = 0x0400
DARK_GREEN = 0x0200
LIME = 0xAFE5
CYAN = 0x07FF
RED = 0xF800
ORANGE = 0xFC60


class DisplayCompat:
    """Imperative drawing API backed by displayio Bitmap + bitmaptools."""

    def __init__(self, display):
        self._display = display
        w = display.width
        h = display.height

        # Create 16-bit RGB565 canvas
        self._bitmap = displayio.Bitmap(w, h, 65536)
        self._cc = displayio.ColorConverter(
            input_colorspace=displayio.Colorspace.RGB565
        )
        self._tg = displayio.TileGrid(self._bitmap, pixel_shader=self._cc)
        self._group = displayio.Group()
        self._group.append(self._tg)
        display.root_group = self._group

    # -- Properties --

    @property
    def width(self):
        return self._display.width

    @property
    def height(self):
        return self._display.height

    @property
    def rotation(self):
        return self._display.rotation

    @rotation.setter
    def rotation(self, value):
        self._display.rotation = value

    @property
    def brightness(self):
        try:
            return self._display.brightness
        except RuntimeError:
            return 1.0

    @brightness.setter
    def brightness(self, value):
        try:
            self._display.brightness = value
        except RuntimeError:
            pass

    @property
    def bitmap(self):
        """Direct access to the underlying Bitmap for advanced use."""
        return self._bitmap

    @property
    def group(self):
        """Direct access to the displayio Group for adding overlays."""
        return self._group

    # -- Drawing primitives --

    def fill_color(self, color):
        """Fill entire screen with a solid color."""
        self._bitmap.fill(color)
        self._bitmap.dirty()  # Mark entire screen as dirty for refresh

    def fill_rect(self, x, y, w, h, color):
        """Draw a filled rectangle with 2-pixel X alignment."""
        x1 = x & ~1  # Round down to even
        x2 = (x + w + 1) & ~1  # Round up to even
        bitmaptools.fill_region(
            self._bitmap, x1, y, x2, y + h, color
        )

    def rect(self, x, y, w, h, color):
        """Draw a rectangle outline."""
        bm = self._bitmap
        x2 = x + w - 1
        y2 = y + h - 1
        bitmaptools.draw_line(bm, x, y, x2, y, color)      # top
        bitmaptools.draw_line(bm, x, y2, x2, y2, color)    # bottom
        bitmaptools.draw_line(bm, x, y, x, y2, color)      # left
        bitmaptools.draw_line(bm, x2, y, x2, y2, color)    # right

    def line(self, x1, y1, x2, y2, color):
        """Draw a line between two points."""
        bitmaptools.draw_line(self._bitmap, x1, y1, x2, y2, color)

    def hline(self, x, y, length, color):
        """Draw a horizontal line."""
        bitmaptools.draw_line(self._bitmap, x, y, x + length - 1, y, color)

    def vline(self, x, y, length, color):
        """Draw a vertical line."""
        bitmaptools.draw_line(self._bitmap, x, y, x, y + length - 1, color)

    def circle(self, cx, cy, r, color):
        """Draw a circle outline."""
        # Use Bresenham's circle algorithm via pixel setting
        # (bitmaptools doesn't have draw_circle in all CP versions)
        bm = self._bitmap
        x = 0
        y = r
        d = 3 - 2 * r
        while x <= y:
            # Draw all 8 octant points
            for px, py in (
                (cx + x, cy + y), (cx - x, cy + y),
                (cx + x, cy - y), (cx - x, cy - y),
                (cx + y, cy + x), (cx - y, cy + x),
                (cx + y, cy - x), (cx - y, cy - x),
            ):
                if 0 <= px < bm.width and 0 <= py < bm.height:
                    bm[px, py] = color
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def fill_circle(self, cx, cy, r, color):
        """Draw a filled circle using horizontal scan lines with 2-pixel X alignment."""
        bm = self._bitmap
        w = bm.width
        h = bm.height
        for dy in range(-r, r + 1):
            py = cy + dy
            if py < 0 or py >= h:
                continue
            # Half-width at this row
            dx = int(math.sqrt(r * r - dy * dy))
            # 2-pixel alignment for RM690B0 hardware
            x1 = max(0, cx - dx) & ~1  # Round down to even
            x2 = min(w, (cx + dx + 2) & ~1)  # Round up to even
            if x2 <= x1:
                x2 = min(w, x1 + 2)
            if x1 < x2:
                bitmaptools.fill_region(bm, x1, py, x2, py + 1, color)

    def pixel(self, x, y, color):
        """Set a single pixel."""
        if 0 <= x < self._bitmap.width and 0 <= y < self._bitmap.height:
            self._bitmap[x, y] = color

    # -- Display control --

    def refresh(self):
        """Push bitmap to display (equivalent to old swap_buffers)."""
        self._display.refresh()

    def swap_buffers(self, copy=True):
        """Alias for refresh() — backward compatibility."""
        self._display.refresh()

    def deinit(self):
        """Release display resources."""
        displayio.release_displays()
