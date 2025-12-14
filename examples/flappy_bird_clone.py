#!/usr/bin/env python3
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
FONT_HUD = 1  # 16×16 Liberation Sans for HUD
FONT_TITLE = 3  # 24×24 for titles
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
    height = display.height
    ground_y = height - GROUND_HEIGHT

    display.fill_color(SKY_COLOR)

    for offset in range(CLOUD_COUNT):
        cx = int((width / CLOUD_COUNT) * offset + width * 0.1)
        cy = int(40 + (offset % 3) * 30)
        draw_cloud(display, cx % width, cy)

    display.fill_rect(0, ground_y, width, GROUND_HEIGHT, GROUND_COLOR)
    display.fill_rect(0, ground_y, width, 6, GROUND_DARK)

    title = "FLAPPY BIRD"
    subtitle = "TAP TO PLAY"
    title_x = (width - text_pixel_width(title, FONT_TITLE)) // 2
    subtitle_x = (width - text_pixel_width(subtitle, FONT_HUD)) // 2
    draw_text(
        display, title, title_x, ground_y // 2 - 12, HUD_COLOR, font_id=FONT_TITLE
    )
    draw_text(
        display, subtitle, subtitle_x, ground_y // 2 + 18, HUD_COLOR, font_id=FONT_HUD
    )

    if best > 0:
        best_text = f"BEST {best}"
        best_x = (width - text_pixel_width(best_text, FONT_HUD)) // 2
        draw_text(
            display, best_text, best_x, ground_y // 2 + 46, HUD_COLOR, font_id=FONT_HUD
        )

    display.swap_buffers()


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


def play_round(display, touch, best_score):
    width = display.width
    height = display.height
    ground_y = height - GROUND_HEIGHT
    bird = Bird(int(width * BIRD_X_OFFSET), height // 2)

    # Initialize difficulty parameters
    current_pipe_gap = BASE_PIPE_GAP
    current_pipe_speed = BASE_PIPE_SPEED
    current_spawn_gap = BASE_PIPE_SPAWN_GAP

    pipes = []
    spawn_pipe(pipes, width + 40, ground_y, height, current_pipe_gap)
    spawn_pipe(
        pipes, width + 40 + current_spawn_gap, ground_y, height, current_pipe_gap
    )

    clouds = [
        [random.randint(0, width), random.randint(20, height // 2)]
        for _ in range(CLOUD_COUNT)
    ]

    def update_clouds():
        for cloud in clouds:
            cloud[0] -= CLOUD_SPEED
            if cloud[0] < -CLOUD_RADIUS * 2:
                cloud[0] = width + random.randint(10, 60)
                cloud[1] = random.randint(20, height // 2)

    def calculate_difficulty(score):
        """Calculate difficulty parameters based on score."""
        difficulty_level = score // DIFFICULTY_SCALE_SCORE

        # Gradually decrease pipe gap
        pipe_gap = max(MIN_PIPE_GAP, BASE_PIPE_GAP - (difficulty_level * 8))

        # Gradually increase pipe speed
        pipe_speed = min(MAX_PIPE_SPEED, BASE_PIPE_SPEED + (difficulty_level * 0.5))

        # Gradually decrease spawn gap (pipes closer together)
        spawn_gap = max(
            MIN_PIPE_SPAWN_GAP, BASE_PIPE_SPAWN_GAP - (difficulty_level * 10)
        )

        return pipe_gap, pipe_speed, spawn_gap

    score = 0
    local_best = best_score
    elapsed_timer = time.monotonic()
    frame_time = 1.0 / TARGET_FPS
    game_over = False
    last_difficulty_score = 0

    while not game_over:
        frame_start = time.monotonic()

        if touch.poll():
            bird.flap()

        bird.update()

        if bird.y - BIRD_RADIUS <= 0:
            bird.y = BIRD_RADIUS
            game_over = True
        elif bird.y + BIRD_RADIUS >= ground_y:
            bird.y = ground_y - BIRD_RADIUS
            game_over = True

        # Update difficulty when score changes
        if score != last_difficulty_score:
            current_pipe_gap, current_pipe_speed, current_spawn_gap = (
                calculate_difficulty(score)
            )
            # Update speed of existing pipes
            for pipe in pipes:
                pipe.speed = current_pipe_speed
            last_difficulty_score = score

        for pipe in list(pipes):
            pipe.update()
            if pipe.x + PIPE_WIDTH < 0:
                pipes.remove(pipe)

        if not pipes or pipes[-1].x < width - current_spawn_gap:
            spawn_pipe(pipes, width + PIPE_WIDTH, ground_y, height, current_pipe_gap)

        for pipe in pipes:
            if not pipe.passed and pipe.x + PIPE_WIDTH < bird.x:
                pipe.passed = True
                score += 1
                if score > local_best:
                    local_best = score
            if pipe.collides(bird):
                game_over = True

        update_clouds()
        draw_scene(display, clouds, pipes, bird, ground_y, score, local_best)
        display.swap_buffers(copy=False)

        if time.monotonic() - elapsed_timer >= 1.0:
            elapsed_timer = time.monotonic()
            difficulty_level = score // DIFFICULTY_SCALE_SCORE
            print(
                f"Score: {score:02d}  Pipes: {len(pipes)}  Bird Y: {bird.y:6.1f}  "
                f"Difficulty: {difficulty_level}  Gap: {current_pipe_gap}  "
                f"Speed: {current_pipe_speed:.1f}"
            )

        frame_elapsed = time.monotonic() - frame_start
        if frame_elapsed < frame_time:
            time.sleep(frame_time - frame_elapsed)

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

    try:
        while True:
            draw_start_screen(display, best_score)
            wait_for_tap(touch)

            score, best_score = play_round(display, touch, best_score)
            print(f"\nRound finished. Score: {score}, Best: {best_score}")

            draw_game_over(display, score, best_score, display.width, display.height)
            display.swap_buffers()

            wait_for_tap(touch)

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
    finally:
        display.fill_color(rm690b0.BLACK)
        display.swap_buffers()
        display.deinit()
        touch.deinit()
        print("\nBest score this session:", best_score)


if __name__ == "__main__":
    main()
