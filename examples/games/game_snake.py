# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Snake Game for Waveshare ESP32-S3 Touch AMOLED 2.41

A classic Snake game implementation using the SparkFun Qwiic Navigation Switch
for directional control. Features:
- Joystick-based controls (UP/DOWN/LEFT/RIGHT)
- Score tracking with best score
- Progressive difficulty (speed increases with score)
- Classic snake gameplay mechanics

Hardware:
- Waveshare ESP32-S3 Touch AMOLED 2.41
- SparkFun Qwiic Navigation Switch (PRT-27576)
- Connected via QWIIC port
- I2C pins: SDA=GPIO47, SCL=GPIO48

Controls:
    Use the navigation switch to change snake direction.
    Press CENTER to start/restart the game.
"""

import random
import time

import board
import busio
import rm690b0

try:
    import adafruit_focaltouch
except ImportError:
    adafruit_focaltouch = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GRID_SIZE = 15  # Size of each grid cell in pixels
GRID_COLS = 40  # Number of columns
GRID_ROWS = 28  # Number of rows (reduced from 30 to make room for HUD bar)
INITIAL_SPEED = 8  # Initial moves per second
SPEED_INCREMENT = 0.5  # Speed increase per food eaten
MAX_SPEED = 20  # Maximum speed
SCORE_PER_FOOD = 1

# Font configuration
FONT_HUD = rm690b0.FONT_16x16  # 16×16 Liberation Sans
FONT_TITLE = rm690b0.FONT_24x24  # 24×24
CHAR_WIDTH_HUD = 16
CHAR_HEIGHT_HUD = 16
CHAR_WIDTH_TITLE = 24
CHAR_HEIGHT_TITLE = 24
HUD_MARGIN = 8
HUD_BAR_HEIGHT = 22

WAIT_POLL_INTERVAL = 0.02

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------


def rgb565(r: int, g: int, b: int) -> int:
    """Convert 0-255 RGB to 16-bit RGB565 color."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


BG_COLOR = rgb565(20, 30, 20)  # Dark green background
GRID_COLOR = rgb565(30, 45, 30)  # Slightly lighter green for grid
SNAKE_HEAD_COLOR = rgb565(100, 220, 100)  # Bright green head
SNAKE_BODY_COLOR = rgb565(60, 180, 60)  # Green body
FOOD_COLOR = rgb565(255, 80, 80)  # Red food
WALL_COLOR = rgb565(100, 100, 100)  # Gray walls
HUD_COLOR = rm690b0.WHITE
OVERLAY_BG = rgb565(20, 25, 35)
OVERLAY_BORDER = rgb565(255, 255, 0)
HUD_BAR_BG = rgb565(10, 10, 15)

# Direction constants
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

# Joystick debounce state for center-press detection
_js_last_center = False


def joystick_direction(js):
    """Convert joystick.read() to direction tuple."""
    state = js.read()
    if state["up"]: return DIR_UP
    if state["down"]: return DIR_DOWN
    if state["left"]: return DIR_LEFT
    if state["right"]: return DIR_RIGHT
    return None


def joystick_center_pressed(js):
    """Rising-edge center button detection (returns True once per press)."""
    global _js_last_center
    pressed = js.read()["center"]
    was = _js_last_center
    _js_last_center = pressed
    return pressed and not was

# ---------------------------------------------------------------------------
# Text Rendering
# ---------------------------------------------------------------------------


def text_pixel_width(text: str, font_id: int = FONT_HUD) -> int:
    """Return the pixel width of a text string using native font."""
    if not text:
        return 0
    if font_id == FONT_TITLE:
        return len(text) * CHAR_WIDTH_TITLE
    else:
        return len(text) * CHAR_WIDTH_HUD


def draw_text(display, text, x, y, color, font_id=FONT_HUD, shadow=True):
    """Draw text using native built-in font with optional shadow effect."""
    display.set_font(font_id)
    if shadow:
        display.text(x + 2, y + 2, text, color=rgb565(0, 0, 0))
    display.text(x, y, text, color=color)


class TouchInput:
    """Touch screen input handler using FocalTouch."""

    def __init__(self, i2c):
        if adafruit_focaltouch is None:
            raise RuntimeError("adafruit_focaltouch library is required.")
        self.i2c = i2c
        self.touch = adafruit_focaltouch.Adafruit_FocalTouch(self.i2c)
        self.start_x = 0
        self.start_y = 0
        self.is_swiping = False
        self.last_tap_time = 0
        try:
            import settings
            self._rotation = settings.rotation
        except ImportError:
            self._rotation = 0

    def _map(self, raw_x, raw_y):
        if self._rotation == 180:
            return raw_y, 450 - raw_x
        return 600 - raw_y, raw_x

    def get_direction(self):
        """Get swipe direction from touch input (returns direction tuple or None)."""
        if not self.touch.touched:
            self.is_swiping = False
            return None

        try:
            points = self.touch.touches
        except:
            return None

        if not points:
            self.is_swiping = False
            return None

        x, y = self._map(points[0]["x"], points[0]["y"])

        if not self.is_swiping:
            self.start_x = x
            self.start_y = y
            self.is_swiping = True
            return None

        dx = x - self.start_x
        dy = y - self.start_y
        threshold = 30

        if abs(dx) > abs(dy):
            if abs(dx) > threshold:
                self.start_x = x
                self.start_y = y
                return DIR_RIGHT if dx > 0 else DIR_LEFT
        else:
            if abs(dy) > threshold:
                self.start_x = x
                self.start_y = y
                return DIR_DOWN if dy > 0 else DIR_UP
        return None

    def is_center_pressed(self):
        """Check if center is pressed (tap anywhere)."""
        if self.touch.touched and not self.is_swiping:
            now = time.monotonic()
            if now - self.last_tap_time > 0.5:
                self.last_tap_time = now
                return True
        return False

    def wait_for_center(self, timeout=None):
        """Wait for center press with optional timeout."""
        start = time.monotonic()
        while True:
            if self.is_center_pressed():
                return True
            if timeout and (time.monotonic() - start) > timeout:
                return False
            time.sleep(WAIT_POLL_INTERVAL)

    def deinit(self):
        """Cleanup resources."""
        pass


# ---------------------------------------------------------------------------
# Game Classes
# ---------------------------------------------------------------------------


class Snake:
    """Snake entity."""

    def __init__(self, start_x, start_y):
        self.segments = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y),
        ]
        self.direction = DIR_RIGHT
        self.next_direction = DIR_RIGHT
        self.grow_pending = 0

    def set_direction(self, new_direction):
        """Set new direction (prevents 180-degree turns)."""
        # Can't turn directly opposite
        if (
            new_direction[0] + self.direction[0],
            new_direction[1] + self.direction[1],
        ) == (0, 0):
            return
        self.next_direction = new_direction

    def move(self):
        """Move snake one step forward."""
        self.direction = self.next_direction
        head_x, head_y = self.segments[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        self.segments.insert(0, new_head)

        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.segments.pop()

    def grow(self):
        """Schedule snake to grow by one segment."""
        self.grow_pending += 1

    def collides_with_self(self):
        """Check if head collides with body."""
        return self.segments[0] in self.segments[1:]

    def collides_with_walls(self, cols, rows):
        """Check if head is outside boundaries."""
        head_x, head_y = self.segments[0]
        return head_x < 0 or head_x >= cols or head_y < 0 or head_y >= rows

    def get_head(self):
        """Get head position."""
        return self.segments[0]


class Food:
    """Food entity."""

    def __init__(self, cols, rows, snake_segments):
        self.position = self._spawn(cols, rows, snake_segments)

    def _spawn(self, cols, rows, snake_segments):
        """Spawn food at random empty position."""
        while True:
            x = random.randint(0, cols - 1)
            y = random.randint(0, rows - 1)
            if (x, y) not in snake_segments:
                return (x, y)

    def respawn(self, cols, rows, snake_segments):
        """Respawn food at new location."""
        self.position = self._spawn(cols, rows, snake_segments)


# ---------------------------------------------------------------------------
# Drawing Functions
# ---------------------------------------------------------------------------


def draw_grid(display, offset_x, offset_y):
    """Draw subtle grid lines."""
    for col in range(GRID_COLS + 1):
        x = offset_x + col * GRID_SIZE
        display.fill_rect(x, offset_y, 1, GRID_ROWS * GRID_SIZE, GRID_COLOR)
    for row in range(GRID_ROWS + 1):
        y = offset_y + row * GRID_SIZE
        display.fill_rect(offset_x, y, GRID_COLS * GRID_SIZE, 1, GRID_COLOR)


def draw_snake(display, snake, offset_x, offset_y):
    """Draw the snake."""
    for i, (x, y) in enumerate(snake.segments):
        px = offset_x + x * GRID_SIZE
        py = offset_y + y * GRID_SIZE
        color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_BODY_COLOR
        display.fill_rect(px + 1, py + 1, GRID_SIZE - 2, GRID_SIZE - 2, color)


def draw_food(display, food, offset_x, offset_y):
    """Draw the food."""
    x, y = food.position
    px = offset_x + x * GRID_SIZE
    py = offset_y + y * GRID_SIZE
    display.fill_rect(px + 2, py + 2, GRID_SIZE - 4, GRID_SIZE - 4, FOOD_COLOR)


def draw_hud(display, score, best, width):
    """Draw score HUD in dedicated bar above the grid."""
    display.fill_rect(0, 0, width, HUD_BAR_HEIGHT, HUD_BAR_BG)
    display.set_font(FONT_HUD)
    text_y = (HUD_BAR_HEIGHT - CHAR_HEIGHT_HUD) // 2
    display.text(HUD_MARGIN, text_y, f"SCORE: {score}", color=HUD_COLOR)
    best_text = f"BEST: {best}"
    best_w = len(best_text) * CHAR_WIDTH_HUD
    display.text(width - HUD_MARGIN - best_w, text_y, best_text, color=HUD_COLOR)


def draw_start_screen(display, best):
    """Draw start screen."""
    width = display.width
    title = "SNAKE"
    prompt = "Press any key"
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


def draw_game_over(display, score, best, width, height):
    """Draw game over overlay."""
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
        "CENTER TO PLAY",
        overlay_x + 30,
        overlay_y + 125,
        HUD_COLOR,
        font_id=FONT_HUD,
    )


def draw_scene(display, snake, food, score, best):
    """Draw the complete game scene."""
    width = display.width
    height = display.height

    # Calculate offsets — grid centered below HUD bar
    grid_width = GRID_COLS * GRID_SIZE
    grid_height = GRID_ROWS * GRID_SIZE
    offset_x = (width - grid_width) // 2
    offset_y = HUD_BAR_HEIGHT + (height - HUD_BAR_HEIGHT - grid_height) // 2

    display.fill_color(BG_COLOR)
    draw_hud(display, score, best, width)
    draw_grid(display, offset_x, offset_y)
    draw_food(display, food, offset_x, offset_y)
    draw_snake(display, snake, offset_x, offset_y)


# ---------------------------------------------------------------------------
# Game Logic
# ---------------------------------------------------------------------------


def play_round(display, joystick, touch, best_score):
    """Play one round of Snake."""
    width = display.width
    height = display.height

    # Pre-calculate grid offsets — grid centered below HUD bar
    grid_width = GRID_COLS * GRID_SIZE
    grid_height = GRID_ROWS * GRID_SIZE
    offset_x = (width - grid_width) // 2
    offset_y = HUD_BAR_HEIGHT + (height - HUD_BAR_HEIGHT - grid_height) // 2

    # Initialize game state
    start_x = GRID_COLS // 2
    start_y = GRID_ROWS // 2
    snake = Snake(start_x, start_y)
    food = Food(GRID_COLS, GRID_ROWS, snake.segments)

    score = 0
    local_best = best_score
    speed = INITIAL_SPEED
    game_over = False
    elapsed_timer = time.monotonic()
    last_move_time = time.monotonic()
    input_poll_rate = 60  # Hz - check input 60 times per second

    # --- Initial full draw (once) ---
    display.fill_color(BG_COLOR)
    draw_grid(display, offset_x, offset_y)
    draw_food(display, food, offset_x, offset_y)
    draw_snake(display, snake, offset_x, offset_y)
    draw_hud(display, score, local_best, width)
    display.swap_buffers(copy=True)

    # Cache locals for hot path
    _fill_rect = display.fill_rect
    _GS = GRID_SIZE
    _ox = offset_x
    _oy = offset_y
    _BG = BG_COLOR
    _HEAD = SNAKE_HEAD_COLOR
    _BODY = SNAKE_BODY_COLOR
    last_drawn_score = score

    while not game_over:
        frame_start = time.monotonic()

        # Handle input from joystick or touch (polled at high rate)
        new_direction = None
        if joystick:
            new_direction = joystick_direction(joystick)
        if new_direction is None and touch:
            new_direction = touch.get_direction()
        if new_direction:
            snake.set_direction(new_direction)

        # Move snake only at game speed
        move_interval = 1.0 / speed
        if time.monotonic() - last_move_time >= move_interval:
            last_move_time = time.monotonic()

            # Remember state before move
            old_tail = snake.segments[-1]
            old_head = snake.segments[0]
            was_growing = snake.grow_pending > 0

            snake.move()

            # Check collisions
            if (
                snake.collides_with_walls(GRID_COLS, GRID_ROWS)
                or snake.collides_with_self()
            ):
                game_over = True

            # Check food collision
            ate_food = snake.get_head() == food.position
            if ate_food:
                snake.grow()
                score += SCORE_PER_FOOD
                if score > local_best:
                    local_best = score
                speed = min(speed + SPEED_INCREMENT, MAX_SPEED)
                food.respawn(GRID_COLS, GRID_ROWS, snake.segments)

            # --- Delta drawing (only changed cells) ---
            # 1. Clear old tail (if snake didn't grow)
            if not was_growing:
                tx, ty = old_tail
                _fill_rect(_ox + tx * _GS + 1, _oy + ty * _GS + 1,
                           _GS - 2, _GS - 2, _BG)

            # 2. Old head → body color
            ohx, ohy = old_head
            _fill_rect(_ox + ohx * _GS + 1, _oy + ohy * _GS + 1,
                       _GS - 2, _GS - 2, _BODY)

            # 3. New head → head color
            nhx, nhy = snake.segments[0]
            _fill_rect(_ox + nhx * _GS + 1, _oy + nhy * _GS + 1,
                       _GS - 2, _GS - 2, _HEAD)

            # 4. Draw new food if eaten
            if ate_food:
                draw_food(display, food, offset_x, offset_y)

            # 5. Update HUD only when score changed
            if score != last_drawn_score:
                draw_hud(display, score, local_best, width)
                last_drawn_score = score

            display.swap_buffers(copy=True)

            # Status update
            if time.monotonic() - elapsed_timer >= 1.0:
                elapsed_timer = time.monotonic()
                print(
                    f"Score: {score:03d}  Length: {len(snake.segments):02d}  Speed: {speed:.1f}"
                )

        # Frame timing for input polling (60 Hz)
        frame_time = 1.0 / input_poll_rate
        frame_elapsed = time.monotonic() - frame_start
        if frame_elapsed < frame_time:
            time.sleep(frame_time - frame_elapsed)

    return score, local_best


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(display=None):
    """Main game loop."""
    seed_value = int(time.monotonic() * 1000) & 0xFFFFFFFF
    random.seed(seed_value)

    print("\n" + "=" * 70)
    print("  SNAKE GAME")
    print("=" * 70)
    print("Controls: Use joystick for direction, CENTER button to start.\n")

    # Initialize display
    display_owned = display is None
    if display_owned:
        display = rm690b0.RM690B0()
        display.init_display()
        try:
            import settings
            display.rotation = settings.rotation
        except ImportError:
            pass
        display.brightness = 1.0
    display.fill_color(rm690b0.BLACK)
    display.swap_buffers(copy=True)

    # Initialize input devices
    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)

    joystick = None
    touch = None

    try:
        from joystick import Joystick
        joystick = Joystick(i2c=i2c)
        print("Joystick initialized")
    except Exception as e:
        print(f"Joystick init failed: {e}")

    try:
        touch = TouchInput(i2c)
        print("Touch initialized")
    except Exception as e:
        print(f"Touch init failed: {e}")

    if not joystick and not touch:
        print("No input devices found!")
        return

    best_score = 0

    # Helper functions for combined input (like Pacman)
    def get_combined_input():
        """Get input from joystick or touch."""
        direction = None
        if joystick:
            direction = joystick_direction(joystick)
        if direction is None and touch:
            direction = touch.get_direction()
        return direction

    def check_start():
        """Check if start/center is pressed."""
        if joystick and joystick_center_pressed(joystick):
            return True
        if touch and touch.is_center_pressed():
            return True
        return False

    try:
        while True:
            # Show start screen
            draw_start_screen(display, best_score)

            # Wait for inputs to be released (debounce)
            while check_start() or get_combined_input() is not None:
                display.swap_buffers()
                time.sleep(0.1)

            # Wait for input to start
            start = False
            while not start:
                if check_start():
                    start = True
                elif get_combined_input() is not None:
                    start = True
                display.swap_buffers()
                time.sleep(0.05)

            # Play round
            score, best_score = play_round(display, joystick, touch, best_score)
            print(f"\nRound finished. Score: {score}, Best: {best_score}")

            # Show game over screen
            draw_game_over(display, score, best_score, display.width, display.height)
            display.swap_buffers()

            # Wait for inputs to be released (debounce)
            while check_start() or get_combined_input() is not None:
                display.swap_buffers()
                time.sleep(0.1)

            # Wait for any input to continue
            waiting = True
            while waiting:
                if check_start():
                    waiting = False
                elif get_combined_input() is not None:
                    waiting = False
                display.swap_buffers()
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
    except Exception as e:
        print(f"\nGame crashed: {e}")
    finally:
        if joystick:
            joystick.deinit()
        if touch:
            touch.deinit()
        i2c.deinit()
        display.fill_color(rm690b0.BLACK)
        display.swap_buffers()
        if display_owned:
            display.deinit()
        print("\nBest score this session:", best_score)


if __name__ == "__main__":
    main()
