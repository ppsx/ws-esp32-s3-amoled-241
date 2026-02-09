# Copyright (c) 2025 Przemyslaw Patrick Socha

import sys
import board
import displayio
import terminalio
from adafruit_display_text import label as label_mod
from rm690b0 import RM690B0, create_qspi_bus

# Ensure display_compat is importable from the same directory as this script
try:
    from display_compat import (
        DisplayCompat, BLACK, WHITE, RED, GREEN, BLUE, CYAN, YELLOW,
        MAGENTA, DARK_GRAY, SKY_BLUE, VIOLET, BROWN, DARK_BROWN,
    )
except ImportError:
    sys.path.insert(0, ".")
    from display_compat import (
        DisplayCompat, BLACK, WHITE, RED, GREEN, BLUE, CYAN, YELLOW,
        MAGENTA, DARK_GRAY, SKY_BLUE, VIOLET, BROWN, DARK_BROWN,
    )

# -- Init display --
displayio.release_displays()
bus = create_qspi_bus(board)
display = RM690B0(bus)
dc = DisplayCompat(display)
FONT = terminalio.FONT


def clear_labels():
    """Remove all label overlays from the group, keep only the canvas TileGrid."""
    while len(dc.group) > 1:
        dc.group.pop()


def add_label(x, y, text, color=0xFFFFFF, bg_color=None, scale=1):
    """Add a text label overlay at (x, y)."""
    lbl = label_mod.Label(
        FONT, text=text, color=color, background_color=bg_color,
        x=x, y=y + (scale * 6) // 2, scale=scale,
    )
    dc.group.append(lbl)


# -----
input("Press Enter to display small font (scale=1)...")
dc.fill_color(BLACK)
clear_labels()
add_label(10, 10, "Font Test: scale=1", WHITE)
add_label(10, 30, "displayio text rendering", CYAN)
add_label(10, 40, "WHITE on RED", WHITE, bg_color=RED)
add_label(10, 50, "GREEN on BLACK", GREEN)
add_label(10, 60, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", YELLOW)
add_label(10, 70, "0123456789!@#$%^&*()", MAGENTA)
dc.refresh()
# -----
input("Press Enter to display larger font (scale=2)...")
dc.fill_color(BLACK)
clear_labels()
add_label(10, 10, "Font Test: scale=2", WHITE, scale=2)
add_label(10, 30, "Scaled text!", CYAN, scale=2)
add_label(10, 60, "ABCDEFGHIJKLM", YELLOW, scale=2)
add_label(10, 85, "0123456789", GREEN, scale=2)
add_label(10, 110, "Bigger & Better!", MAGENTA, scale=2)
dc.refresh()
# -----
input("Press Enter to display graphics...")
clear_labels()
dc.rect(0, 0, 600, 450, WHITE)
dc.line(0, 0, 599, 449, RED)
dc.line(599, 0, 0, 449, GREEN)
dc.line(0, 225, 599, 225, YELLOW)
dc.line(150, 0, 150, 449, MAGENTA)
dc.vline(300, 0, 450, CYAN)
dc.hline(0, 300, 600, DARK_GRAY)
dc.line(150, 0, 599, 449, SKY_BLUE)
dc.circle(150, 225, 150, VIOLET)
dc.fill_circle(500, 100, 50, BROWN)
dc.fill_rect(400, 350, 100, 50, DARK_BROWN)
dc.fill_rect(350, 50, 50, 100, BLUE)
dc.refresh()
# -----
input("Press Enter to check filling the screen...")
dc.fill_color(WHITE)
dc.refresh()
input("Press Enter...")
dc.fill_color(BLACK)
dc.refresh()
input("Press Enter...")
dc.fill_rect(0, 0, 600, 450, WHITE)
dc.refresh()
# -----
input("Press Enter to check rotation...")
dc.fill_color(BLACK)
dc.fill_rect(10, 10, 10, 10, WHITE)
dc.rotation = 90
dc.fill_rect(10, 10, 10, 10, GREEN)
dc.rotation = 180
dc.fill_rect(10, 10, 10, 10, RED)
dc.rotation = 270
dc.fill_rect(10, 10, 10, 10, YELLOW)
dc.rotation = 0
dc.refresh()
# -----
input("Press Enter to check circle...")
dc.fill_color(WHITE)
dc.fill_circle(300, 225, 200, BLACK)
dc.circle(300, 225, 220, BLACK)
dc.refresh()
# -----
input("Press Enter to check patterns...")


def fill_white():
    dc.fill_color(WHITE)


def fill_black():
    dc.fill_color(BLACK)


def draw_vlines(spacing, color):
    w, h = dc.width, dc.height
    x = 0
    while x < w:
        dc.vline(x, 0, h, color)
        x += spacing
    dc.refresh()


def draw_hlines(spacing, color):
    w, h = dc.width, dc.height
    for y in range(0, h, spacing):
        dc.hline(0, y, w, color)
    dc.refresh()


input("Press Enter to check vertical lines...")
for a in range(1, 11):
    fill_black()
    draw_vlines(a, GREEN)
    input("Press Enter...")
input("Press Enter to check horizontal lines...")
for a in range(1, 11):
    fill_white()
    draw_hlines(a, RED)
    input("Press Enter...")
# -----
input("Press Enter to close...")
dc.deinit()
