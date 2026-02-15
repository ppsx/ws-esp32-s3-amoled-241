# Copyright (c) 2025 Przemyslaw Patrick Socha
# Galaxian Clone - Sprite Definitions & Builder

"""
Procedural bitmask sprites for Galaxian clone.
Each sprite is an 8x8 bitmask rendered to RGB565 bytearray at 2x (aliens) or 3x (player).
Two animation frames per alien type (wings open/closed).
"""


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


# --- Bitmask definitions (8x8, 2 frames per alien) ---

DRONE_F1 = (
    0b00111100, 0b01111110, 0b11011011, 0b11111111,
    0b01011010, 0b01100110, 0b10000001, 0b01000010,
)
DRONE_F2 = (
    0b00111100, 0b01111110, 0b11111111, 0b11011011,
    0b01111110, 0b10100101, 0b10100101, 0b01000010,
)

EMISSARY_F1 = (
    0b00011000, 0b00111100, 0b01111110, 0b11011011,
    0b11111111, 0b00100100, 0b01011010, 0b10000001,
)
EMISSARY_F2 = (
    0b00011000, 0b00111100, 0b01111110, 0b11111111,
    0b11011011, 0b01100110, 0b10000001, 0b01000010,
)

GUARD_F1 = (
    0b00011000, 0b00111100, 0b01111110, 0b11111111,
    0b11011011, 0b00111100, 0b01100110, 0b11000011,
)
GUARD_F2 = (
    0b00011000, 0b00111100, 0b01111110, 0b11011011,
    0b11111111, 0b01011010, 0b10000001, 0b11000011,
)

FLAGSHIP_F1 = (
    0b00011000, 0b00111100, 0b01111110, 0b11111111,
    0b11111111, 0b01111110, 0b00111100, 0b01100110,
)
FLAGSHIP_F2 = (
    0b00011000, 0b00111100, 0b01111110, 0b11111111,
    0b11111111, 0b01111110, 0b00111100, 0b10011001,
)

PLAYER = (
    0b00011000, 0b00011000, 0b00111100, 0b00111100,
    0b01111110, 0b11111111, 0b10111101, 0b10011001,
)

EXPLOSION = (
    0b10000001, 0b01001010, 0b00100100, 0b01000010,
    0b01000010, 0b00100100, 0b01001010, 0b10000001,
)

# --- Colors ---
COLOR_DRONE = rgb565(60, 120, 255)
COLOR_EMISSARY = rgb565(180, 60, 255)
COLOR_GUARD = rgb565(255, 60, 60)
COLOR_FLAGSHIP_1 = rgb565(255, 220, 40)
COLOR_FLAGSHIP_2 = rgb565(40, 220, 100)
COLOR_PLAYER = rgb565(220, 220, 255)
COLOR_PLAYER_ACCENT = rgb565(100, 160, 255)
COLOR_EXPLOSION = rgb565(255, 200, 60)


def _render_bitmask(bitmask, color, scale):
    """Render 8x8 bitmask to RGB565 bytearray at given scale. Black (0x0000) = transparent."""
    w = 8 * scale
    h = 8 * scale
    buf = bytearray(w * h * 2)
    lo = color & 0xFF
    hi = (color >> 8) & 0xFF
    for row in range(8):
        bits = bitmask[row]
        for col in range(8):
            if bits & (0x80 >> col):
                for sy in range(scale):
                    for sx in range(scale):
                        px = col * scale + sx
                        py = row * scale + sy
                        off = (py * w + px) * 2
                        buf[off] = lo
                        buf[off + 1] = hi
    return buf


def _render_bitmask_2color(bitmask, color1, color2, scale):
    """Render with color1 on top half, color2 on bottom half (flagship gradient)."""
    w = 8 * scale
    h = 8 * scale
    buf = bytearray(w * h * 2)
    for row in range(8):
        bits = bitmask[row]
        c = color1 if row < 4 else color2
        lo = c & 0xFF
        hi = (c >> 8) & 0xFF
        for col in range(8):
            if bits & (0x80 >> col):
                for sy in range(scale):
                    for sx in range(scale):
                        px = col * scale + sx
                        py = row * scale + sy
                        off = (py * w + px) * 2
                        buf[off] = lo
                        buf[off + 1] = hi
    return buf


def _render_player(bitmask, color_main, color_accent, scale):
    """Render player with accent on top rows (nose/cockpit)."""
    w = 8 * scale
    h = 8 * scale
    buf = bytearray(w * h * 2)
    for row in range(8):
        bits = bitmask[row]
        c = color_accent if row < 3 else color_main
        lo = c & 0xFF
        hi = (c >> 8) & 0xFF
        for col in range(8):
            if bits & (0x80 >> col):
                for sy in range(scale):
                    for sx in range(scale):
                        px = col * scale + sx
                        py = row * scale + sy
                        off = (py * w + px) * 2
                        buf[off] = lo
                        buf[off + 1] = hi
    return buf


def build_sprites():
    """Build all sprites. Returns dict of name → (buf, w, h).
    Aliens: 16×16 (scale 2), Player: 24×24 (scale 3).
    """
    sprites = {}

    sprites['drone_f1'] = (_render_bitmask(DRONE_F1, COLOR_DRONE, 2), 16, 16)
    sprites['drone_f2'] = (_render_bitmask(DRONE_F2, COLOR_DRONE, 2), 16, 16)

    sprites['emissary_f1'] = (_render_bitmask(EMISSARY_F1, COLOR_EMISSARY, 2), 16, 16)
    sprites['emissary_f2'] = (_render_bitmask(EMISSARY_F2, COLOR_EMISSARY, 2), 16, 16)

    sprites['guard_f1'] = (_render_bitmask(GUARD_F1, COLOR_GUARD, 2), 16, 16)
    sprites['guard_f2'] = (_render_bitmask(GUARD_F2, COLOR_GUARD, 2), 16, 16)

    sprites['flagship_f1'] = (_render_bitmask_2color(
        FLAGSHIP_F1, COLOR_FLAGSHIP_1, COLOR_FLAGSHIP_2, 2), 16, 16)
    sprites['flagship_f2'] = (_render_bitmask_2color(
        FLAGSHIP_F2, COLOR_FLAGSHIP_2, COLOR_FLAGSHIP_1, 2), 16, 16)

    sprites['player'] = (_render_player(
        PLAYER, COLOR_PLAYER, COLOR_PLAYER_ACCENT, 3), 24, 24)

    sprites['explosion'] = (_render_bitmask(EXPLOSION, COLOR_EXPLOSION, 2), 16, 16)

    return sprites
