# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Simple Flappy Bird clone for the Waveshare ESP32-S3 Touch AMOLED display.

Usage:
    python flappy_bird_clone.py

Controls:
    Tap the touchscreen to flap.

The script renders a lightweight recreation of the classic Flappy Bird loop
with scrolling pipes, a bouncing bird, score keeping, and a basic HUD. It
mirrors the display setup patterns used by the other test scripts and runs
directly on the SBC that drives the display.
"""

import random
import time

import board
import busio
import rm690b0

try:
    import adafruit_focaltouch
except ImportError:  # pragma: no cover - required on the SBC
    adafruit_focaltouch = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TARGET_FPS = 60
GRAVITY = 0.65
FLAP_STRENGTH = -10.5
MAX_FALL_SPEED = 11.5
BIRD_RADIUS = 14
BIRD_X_OFFSET = 0.23  # Bird horizontal anchor as fraction of screen width
GROUND_HEIGHT = 70
PIPE_WIDTH = 72
# Base difficulty settings (these will scale with score)
BASE_PIPE_GAP = 168
BASE_PIPE_SPEED = 10
BASE_PIPE_SPAWN_GAP = 260  # Distance between consecutive pipes (pixels)

# Difficulty progression settings
DIFFICULTY_SCALE_SCORE = 10  # Score interval for difficulty increase
MIN_PIPE_GAP = 100  # Minimum gap between pipes
MAX_PIPE_SPEED = 16  # Maximum pipe speed
MIN_PIPE_SPAWN_GAP = 180  # Minimum distance between pipes

CLOUD_COUNT = 5
CLOUD_SPEED = 1.2
CLOUD_RADIUS = 26

# Font configuration for native text rendering
FONT_HUD = rm690b0.FONT_16x16  # 16×16 Liberation Sans for HUD
FONT_TITLE = rm690b0.FONT_24x24  # 24×24 for titles
CHAR_WIDTH_HUD = 16
CHAR_HEIGHT_HUD = 16
CHAR_WIDTH_TITLE = 24
CHAR_HEIGHT_TITLE = 24
HUD_MARGIN = 12

PIPE_CAP_HEIGHT = 16
PIPE_EDGE = 5

WAIT_POLL_INTERVAL = 0.02

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def rgb565(r: int, g: int, b: int) -> int:
    """Convert 0-255 RGB to 16-bit RGB565 color."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


SKY_COLOR = rgb565(120, 190, 255)
GROUND_COLOR = rgb565(210, 170, 110)
GROUND_DARK = rgb565(170, 130, 70)
PIPE_COLOR = rgb565(88, 200, 92)
PIPE_SHADE = rgb565(64, 150, 68)
HUD_COLOR = rm690b0.WHITE
HUD_SHADOW = rgb565(0, 0, 0)
BIRD_BODY = rgb565(255, 210, 0)
BIRD_WING = rgb565(255, 160, 0)
BIRD_BEAK = rgb565(255, 120, 0)
BIRD_EYE = rm690b0.WHITE
BIRD_PUPIL = rm690b0.BLACK
OVERLAY_BG = rgb565(20, 25, 35)
OVERLAY_BORDER = rm690b0.YELLOW if hasattr(rm690b0, "YELLOW") else rgb565(255, 255, 0)
SPRITE_TRANSPARENT = rgb565(255, 0, 255)  # 0xF81F magenta


# ---------------------------------------------------------------------------
# Sprite pre-rendering helpers (run once at startup, Python speed is OK)
# ---------------------------------------------------------------------------
def _sp_fill_circle(buf, bw, bh, cx, cy, r, color):
    """Fill circle into RGB565 sprite buffer using span-based writes."""
    pixel = bytes([color & 0xFF, (color >> 8) & 0xFF])
    r2 = r * r
    for y in range(max(0, cy - r), min(bh, cy + r + 1)):
        dy = y - cy
        dx = int((r2 - dy * dy) ** 0.5)
        x0 = max(0, cx - dx)
        x1 = min(bw, cx + dx + 1)
        span = x1 - x0
        if span > 0:
            off = (y * bw + x0) * 2
            buf[off:off + span * 2] = pixel * span


def _sp_fill_rect(buf, bw, bh, rx, ry, rw, rh, color):
    """Fill rect into RGB565 sprite buffer using row-based writes."""
    pixel = bytes([color & 0xFF, (color >> 8) & 0xFF])
    x0 = max(0, rx)
    x1 = min(bw, rx + rw)
    span = x1 - x0
    if span <= 0:
        return
    row_data = pixel * span
    for y in range(max(0, ry), min(bh, ry + rh)):
        off = (y * bw + x0) * 2
        buf[off:off + span * 2] = row_data


def pre_render_bird():
    """Pre-render bird sprite once. Returns (buf, w, h, offset_x, offset_y)."""
    # Bird extents from center: left=-14, right=+20, top=-14, bottom=+14
    w, h = 36, 30
    ox, oy = 15, 15  # center offsets from top-left
    magenta = bytes([SPRITE_TRANSPARENT & 0xFF, (SPRITE_TRANSPARENT >> 8) & 0xFF])
    buf = bytearray(magenta * (w * h))
    _sp_fill_circle(buf, w, h, ox, oy, BIRD_RADIUS, BIRD_BODY)
    _sp_fill_circle(buf, w, h, ox - 6, oy + 1, BIRD_RADIUS - 6, BIRD_WING)
    _sp_fill_rect(buf, w, h, ox + BIRD_RADIUS - 2, oy - 2, 8, 6, BIRD_BEAK)
    _sp_fill_circle(buf, w, h, ox + 6, oy - 4, 5, BIRD_EYE)
    _sp_fill_circle(buf, w, h, ox + 8, oy - 4, 2, BIRD_PUPIL)
    return buf, w, h, ox, oy


def pre_render_cloud():
    """Pre-render cloud sprite once. Returns (buf, w, h, offset_x, offset_y)."""
    r = CLOUD_RADIUS
    # Extents: left=-46, right=+48, top=-26, bottom=+26
    w, h = 96, 54
    ox, oy = 47, 27
    magenta = bytes([SPRITE_TRANSPARENT & 0xFF, (SPRITE_TRANSPARENT >> 8) & 0xFF])
    buf = bytearray(magenta * (w * h))
    white = rm690b0.WHITE
    _sp_fill_circle(buf, w, h, ox, oy, r, white)
    _sp_fill_circle(buf, w, h, ox + r, oy + 4, r - 4, white)
    _sp_fill_circle(buf, w, h, ox - r, oy + 6, r - 6, white)
    return buf, w, h, ox, oy


def text_pixel_width(text: str, font_id: int = FONT_HUD) -> int:
    """Return the pixel width of a text string using native font."""
    if not text:
        return 0
    # Fixed-width fonts: width = number of characters × character width
    if font_id == FONT_TITLE:
        return len(text) * CHAR_WIDTH_TITLE
    else:  # FONT_HUD
        return len(text) * CHAR_WIDTH_HUD


def draw_text(display, text, x, y, color, font_id=FONT_HUD, shadow=True):
    """Draw text using native built-in font with optional shadow effect."""
    display.set_font(font_id)
    if shadow:
        # Draw shadow (black text offset by 2 pixels)
        display.text(x + 2, y + 2, text, color=rgb565(0, 0, 0))
    # Draw main text
    display.text(x, y, text, color=color)


def draw_cloud(display, cx, cy):
    r = CLOUD_RADIUS
    display.fill_circle(cx, cy, r, rm690b0.WHITE)
    display.fill_circle(cx + r, cy + 4, r - 4, rm690b0.WHITE)
    display.fill_circle(cx - r, cy + 6, r - 6, rm690b0.WHITE)


def spawn_pipe(pipes, x, ground_y, height, pipe_gap):
    min_gap_center = 60 + pipe_gap // 2
    max_gap_center = ground_y - (60 + pipe_gap // 2)
    gap_y = random.randint(min_gap_center, max_gap_center)
    pipes.append(Pipe(x, gap_y, pipe_gap))


class TouchInput:
    """Single-touch poller using the onboard FT6336U controller."""

    def __init__(self):
        if adafruit_focaltouch is None:
            raise RuntimeError("adafruit_focaltouch library is required on the SBC.")

        self._i2c = busio.I2C(board.TP_SCL, board.TP_SDA, timeout=5)
        self._touch = adafruit_focaltouch.Adafruit_FocalTouch(self._i2c)
        self._pressed = False

    def poll(self) -> bool:
        """Return True exactly once for each new touch contact."""
        if not self._touch.touched:
            self._pressed = False
            return False
        points = self._touch.touches
        if not points:
            self._pressed = False
            return False
        if self._pressed:
            return False
        self._pressed = True
        return True

    def deinit(self):
        try:
            self._i2c.deinit()
        except AttributeError:
            pass


class Bird:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocity = 0.0

    def flap(self):
        self.velocity = FLAP_STRENGTH

    def update(self):
        self.velocity = min(self.velocity + GRAVITY, MAX_FALL_SPEED)
        self.y += self.velocity

    def draw(self, display):
        x = int(self.x)
        y = int(self.y)
        display.fill_circle(x, y, BIRD_RADIUS, BIRD_BODY)
        display.fill_circle(x - 6, y + 1, BIRD_RADIUS - 6, BIRD_WING)
        display.fill_rect(x + BIRD_RADIUS - 2, y - 2, 8, 6, BIRD_BEAK)
        display.fill_circle(x + 6, y - 4, 5, BIRD_EYE)
        display.fill_circle(x + 8, y - 4, 2, BIRD_PUPIL)

    def bounds(self):
        return (
            self.x - BIRD_RADIUS,
            self.y - BIRD_RADIUS,
            self.x + BIRD_RADIUS,
            self.y + BIRD_RADIUS,
        )


class Pipe:
    def __init__(self, x, gap_y, gap_size):
        self.x = float(x)
        self.gap_y = float(gap_y)
        self.gap_size = gap_size
        self.passed = False
        self.speed = BASE_PIPE_SPEED

    def update(self):
        self.x -= self.speed

    def draw(self, display, ground_y):
        x = int(self.x)
        width = PIPE_WIDTH
        gap_half = self.gap_size // 2
        top_end = int(self.gap_y - gap_half)
        bottom_start = int(self.gap_y + gap_half)

        if top_end > 0:
            display.fill_rect(x, 0, width, top_end, PIPE_COLOR)
            cap_y = max(0, top_end - PIPE_CAP_HEIGHT)
            display.fill_rect(
                x - PIPE_EDGE,
                cap_y,
                width + 2 * PIPE_EDGE,
                min(PIPE_CAP_HEIGHT, top_end - cap_y),
                PIPE_SHADE,
            )
        if bottom_start < ground_y:
            height = ground_y - bottom_start
            display.fill_rect(x, bottom_start, width, height, PIPE_COLOR)
            display.fill_rect(
                x - PIPE_EDGE,
                bottom_start,
                width + 2 * PIPE_EDGE,
                min(PIPE_CAP_HEIGHT, ground_y - bottom_start),
                PIPE_SHADE,
            )

    def collides(self, bird):
        bird_left, bird_top, bird_right, bird_bottom = bird.bounds()
        pipe_left = self.x
        pipe_right = self.x + PIPE_WIDTH
        if bird_right < pipe_left or bird_left > pipe_right:
            return False
        gap_half = self.gap_size / 2
        gap_top = self.gap_y - gap_half
        gap_bottom = self.gap_y + gap_half
        return bird_top < gap_top or bird_bottom > gap_bottom


def draw_hud(display, score, best, width):
    label_x = HUD_MARGIN
    label_y = HUD_MARGIN
    draw_text(display, "SCORE", label_x, label_y, HUD_COLOR, font_id=FONT_HUD)

    value = str(score)
    draw_text(display, value, label_x, label_y + 22, HUD_COLOR, font_id=FONT_HUD)

    best_label = "BEST"
    best_value = str(best)
    best_width = max(text_pixel_width(best_label), text_pixel_width(best_value))
    right_margin = width - HUD_MARGIN - best_width
    draw_text(display, best_label, right_margin, label_y, HUD_COLOR, font_id=FONT_HUD)
    draw_text(
        display, best_value, right_margin, label_y + 22, HUD_COLOR, font_id=FONT_HUD
    )


def draw_game_over(display, score, best, width, height):
    overlay_w = width - 200
    overlay_h = 160
    overlay_x = (width - overlay_w) // 2
    overlay_y = (height - overlay_h) // 2
    display.fill_rect(overlay_x, overlay_y, overlay_w, overlay_h, OVERLAY_BG)
    display.rect(overlay_x, overlay_y, overlay_w, overlay_h, OVERLAY_BORDER)
    draw_text(
        display,
        "GAME OVER",
        overlay_x + 30,
        overlay_y + 18,
        HUD_COLOR,
        font_id=FONT_TITLE,
    )
    draw_text(
        display,
        f"SCORE {score}",
        overlay_x + 30,
        overlay_y + 60,
        HUD_COLOR,
        font_id=FONT_HUD,
    )
    draw_text(
        display,
        f"BEST {best}",
        overlay_x + 30,
        overlay_y + 90,
        HUD_COLOR,
        font_id=FONT_HUD,
    )
    draw_text(
        display,
        "TAP TO PLAY",
        overlay_x + 30,
        overlay_y + 125,
        HUD_COLOR,
        font_id=FONT_HUD,
    )


def draw_start_screen(display, best):
    width = display.width
    title = "FLAPPY BIRD"
    prompt = "Tap to start"
    title_x = (width - len(title) * 24) // 2
    prompt_x = (width - len(prompt) * 16) // 2

    display.fill_color(rm690b0.BLACK)
    display.set_font(4)
    display.text(title_x, 160, title, 0x07E0)
    display.set_font(2)
    display.text(prompt_x, 220, prompt, HUD_COLOR)

    if best > 0:
        best_text = f"BEST {best}"
        best_x = (width - len(best_text) * 16) // 2
        display.text(best_x, 260, best_text, HUD_COLOR)

    display.swap_buffers(copy=True)


def draw_scene(display, clouds, pipes, bird, ground_y, score, best):
    width = display.width
    display.fill_color(SKY_COLOR)
    for cx, cy in clouds:
        draw_cloud(display, int(cx), int(cy))
    display.fill_rect(0, ground_y, width, GROUND_HEIGHT, GROUND_COLOR)
    display.fill_rect(0, ground_y, width, 6, GROUND_DARK)
    for pipe in pipes:
        pipe.draw(display, ground_y)
    bird.draw(display)
    draw_hud(display, score, best, width)


def wait_for_tap(touch):
    while True:
        if touch.poll():
            return
        time.sleep(WAIT_POLL_INTERVAL)


def play_round(display, touch, best_score, sprite_cache):
    width = display.width
    height = display.height
    ground_y = height - GROUND_HEIGHT
    bird = Bird(int(width * BIRD_X_OFFSET), height // 2)

    bird_spr, bird_sw, bird_sh, bird_ox, bird_oy = sprite_cache[0]
    cloud_spr, cloud_sw, cloud_sh, cloud_ox, cloud_oy = sprite_cache[1]

    # Difficulty
    current_pipe_gap = BASE_PIPE_GAP
    current_pipe_speed = BASE_PIPE_SPEED
    current_spawn_gap = BASE_PIPE_SPAWN_GAP

    pipes = []
    spawn_pipe(pipes, width + 40, ground_y, height, current_pipe_gap)
    spawn_pipe(pipes, width + 40 + current_spawn_gap, ground_y, height, current_pipe_gap)

    clouds = [
        [random.randint(0, width), random.randint(20, height // 2)]
        for _ in range(CLOUD_COUNT)
    ]

    score = 0
    local_best = best_score
    frame_time = 1.0 / TARGET_FPS
    game_over = False
    last_difficulty_score = 0

    # Cache methods/constants as locals (avoid attribute lookups in hot loop)
    _fill_color = display.fill_color
    _fill_rect = display.fill_rect
    _blit = display.blit_buffer
    _set_font = display.set_font
    _text = display.text
    _swap = display.swap_buffers
    _poll = touch.poll
    _mono = time.monotonic
    _sleep = time.sleep
    _randint = random.randint
    _bird_update = bird.update
    _flap = bird.flap

    _SKY = SKY_COLOR
    _TRANS = SPRITE_TRANSPARENT
    _GC = GROUND_COLOR
    _GD = GROUND_DARK
    _GH = GROUND_HEIGHT
    _PC = PIPE_COLOR
    _PS = PIPE_SHADE
    _PW = PIPE_WIDTH
    _PCH = PIPE_CAP_HEIGHT
    _PE = PIPE_EDGE
    _HC = HUD_COLOR
    _HS = rm690b0.BLACK
    _HM = HUD_MARGIN
    _BR = BIRD_RADIUS
    _CS = CLOUD_SPEED
    _CR2 = CLOUD_RADIUS * 2
    _half_h = height // 2

    elapsed_timer = _mono()
    frame_count = 0

    while not game_over:
        frame_start = _mono()

        if _poll():
            _flap()

        _bird_update()

        # Bounds
        by = bird.y
        if by - _BR <= 0:
            bird.y = _BR
            by = _BR
            game_over = True
        elif by + _BR >= ground_y:
            bird.y = ground_y - _BR
            by = ground_y - _BR
            game_over = True

        # Difficulty (only when score changes)
        if score != last_difficulty_score:
            dl = score // DIFFICULTY_SCALE_SCORE
            current_pipe_gap = max(MIN_PIPE_GAP, BASE_PIPE_GAP - dl * 8)
            current_pipe_speed = min(MAX_PIPE_SPEED, BASE_PIPE_SPEED + dl * 0.5)
            current_spawn_gap = max(MIN_PIPE_SPAWN_GAP, BASE_PIPE_SPAWN_GAP - dl * 10)
            for p in pipes:
                p.speed = current_pipe_speed
            last_difficulty_score = score

        # Update pipes (inlined)
        for p in list(pipes):
            p.x -= p.speed
            if p.x + _PW < 0:
                pipes.remove(p)

        if not pipes or pipes[-1].x < width - current_spawn_gap:
            spawn_pipe(pipes, width + _PW, ground_y, height, current_pipe_gap)

        # Scoring & collision (inlined — avoids collides() method call per pipe)
        bx = bird.x
        b_left = bx - _BR
        b_right = bx + _BR
        b_top = by - _BR
        b_bot = by + _BR
        for p in pipes:
            if not p.passed and p.x + _PW < bx:
                p.passed = True
                score += 1
                if score > local_best:
                    local_best = score
            p_left = p.x
            p_right = p.x + _PW
            if b_right >= p_left and b_left <= p_right:
                gap_half = p.gap_size / 2
                if b_top < p.gap_y - gap_half or b_bot > p.gap_y + gap_half:
                    game_over = True

        # Cloud update (inlined)
        for c in clouds:
            c[0] -= _CS
            if c[0] < -_CR2:
                c[0] = width + _randint(10, 60)
                c[1] = _randint(20, _half_h)

        # ===== RENDER (fully inlined) =====

        _fill_color(_SKY)

        # Clouds (pre-rendered sprite)
        for cx, cy in clouds:
            sx = int(cx) - cloud_ox
            sy = int(cy) - cloud_oy
            if sx + cloud_sw <= 0 or sx >= width:
                continue
            if sx >= 0 and sx + cloud_sw <= width:
                _blit(sx, sy, cloud_sw, cloud_sh, cloud_spr,
                      transparent_color=_TRANS)
            else:
                # Edge clipping
                sx1 = max(0, -sx)
                sx2 = min(cloud_sw, width - sx)
                _blit(max(0, sx), sy, cloud_sw, cloud_sh, cloud_spr,
                      transparent_color=_TRANS,
                      src_x1=sx1, src_y1=0, src_x2=sx2, src_y2=cloud_sh)

        # Ground
        _fill_rect(0, ground_y, width, _GH, _GC)
        _fill_rect(0, ground_y, width, 6, _GD)

        # Pipes (inlined draw — avoids pipe.draw() method call)
        for p in pipes:
            px = int(p.x)
            gap_half = p.gap_size // 2
            top_end = int(p.gap_y - gap_half)
            bot_start = int(p.gap_y + gap_half)
            if top_end > 0:
                _fill_rect(px, 0, _PW, top_end, _PC)
                cap_y = max(0, top_end - _PCH)
                _fill_rect(px - _PE, cap_y, _PW + _PE * 2,
                           min(_PCH, top_end - cap_y), _PS)
            if bot_start < ground_y:
                bh = ground_y - bot_start
                _fill_rect(px, bot_start, _PW, bh, _PC)
                _fill_rect(px - _PE, bot_start, _PW + _PE * 2,
                           min(_PCH, bh), _PS)

        # Bird (pre-rendered sprite — 1 blit vs 5 primitives)
        _blit(int(bx) - bird_ox, int(by) - bird_oy,
              bird_sw, bird_sh, bird_spr,
              transparent_color=_TRANS)

        # HUD labels and values with simple drop shadow
        _set_font(FONT_HUD)
        _text(_HM + 1, _HM + 1, "SCORE", color=_HS)
        _text(_HM, _HM, "SCORE", color=_HC)
        score_str = str(score)
        _text(_HM + 1, _HM + 23, score_str, color=_HS)
        _text(_HM, _HM + 22, score_str, color=_HC)
        best_str = str(local_best)
        best_w = max(4, len(best_str)) * CHAR_WIDTH_HUD
        _best_x = width - _HM - best_w
        _text(_best_x + 1, _HM + 1, "BEST", color=_HS)
        _text(_best_x, _HM, "BEST", color=_HC)
        _text(_best_x + 1, _HM + 23, best_str, color=_HS)
        _text(_best_x, _HM + 22, best_str, color=_HC)

        _swap(copy=False)

        frame_count += 1

        # FPS logging (every second)
        now = _mono()
        if now - elapsed_timer >= 1.0:
            fps = frame_count / (now - elapsed_timer)
            dl = score // DIFFICULTY_SCALE_SCORE
            print(f"FPS:{fps:.0f}  Score:{score:02d}  Pipes:{len(pipes)}  "
                  f"Diff:{dl}  Gap:{current_pipe_gap}  Spd:{current_pipe_speed:.1f}")
            elapsed_timer = now
            frame_count = 0

        # Frame pacing
        frame_elapsed = _mono() - frame_start
        if frame_elapsed < frame_time:
            _sleep(frame_time - frame_elapsed)

    return score, local_best


def main():
    seed_value = int(time.monotonic() * 1000) & 0xFFFFFFFF
    random.seed(seed_value)

    print("\n" + "=" * 70)
    print("  FLAPPY BIRD CLONE")
    print("=" * 70)
    print("Controls: tap the touchscreen to flap.\n")

    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0
    display.swap_buffers()

    touch = TouchInput()
    best_score = 0

    print("Pre-rendering sprites...")
    bird_sprite = pre_render_bird()
    cloud_sprite = pre_render_cloud()
    print(f"  Bird: {bird_sprite[1]}x{bird_sprite[2]}, Cloud: {cloud_sprite[1]}x{cloud_sprite[2]}")
    sprite_cache = (bird_sprite, cloud_sprite)

    try:
        while True:
            draw_start_screen(display, best_score)
            wait_for_tap(touch)

            score, best_score = play_round(display, touch, best_score, sprite_cache)
            print(f"\nRound finished. Score: {score}, Best: {best_score}")

            draw_game_over(display, score, best_score, display.width, display.height)
            display.swap_buffers()

            wait_for_tap(touch)

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
    except Exception as e:
        print(f"\nGame crashed: {e}")
    finally:
        display.fill_color(rm690b0.BLACK)
        display.swap_buffers()
        display.deinit()
        touch.deinit()
        print("\nBest score this session:", best_score)


if __name__ == "__main__":
    main()
