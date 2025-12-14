#!/usr/bin/env python3
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

# Import the Navigation Switch driver
# We'll use a simplified version inline to avoid external dependencies
PCA9554_ADDR = 0x21
REG_INPUT_PORT = 0x00
REG_OUTPUT_PORT = 0x01
REG_CONFIG = 0x03

PIN_UP = 0
PIN_DOWN = 1
PIN_RIGHT = 2
PIN_LEFT = 3
PIN_CENTER = 4

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GRID_SIZE = 15  # Size of each grid cell in pixels
GRID_COLS = 40  # Number of columns
GRID_ROWS = 30  # Number of rows
INITIAL_SPEED = 8  # Initial moves per second
SPEED_INCREMENT = 0.5  # Speed increase per food eaten
MAX_SPEED = 20  # Maximum speed
SCORE_PER_FOOD = 10

# Font configuration
FONT_HUD = 1  # 16×16 Liberation Sans
FONT_TITLE = 3  # 24×24
CHAR_WIDTH_HUD = 16
CHAR_HEIGHT_HUD = 16
CHAR_WIDTH_TITLE = 24
CHAR_HEIGHT_TITLE = 24
HUD_MARGIN = 12

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

# Direction constants
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

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


# ---------------------------------------------------------------------------
# Navigation Switch Input
# ---------------------------------------------------------------------------


class PCA9554:
    """Minimal PCA9554 driver for Navigation Switch."""

    def __init__(self, i2c, address=PCA9554_ADDR):
        self.i2c = i2c
        self.address = address
        try:
            self._read_register(REG_INPUT_PORT)
        except Exception as e:
            raise RuntimeError(f"PCA9554 not found at 0x{address:02X}: {e}")

    def _read_register(self, register):
        timeout = 1.0
        start = time.monotonic()
        while not self.i2c.try_lock():
            if time.monotonic() - start > timeout:
                raise RuntimeError("I2C bus lock timeout")
            time.sleep(0.001)
        try:
            result = bytearray(1)
            self.i2c.writeto_then_readfrom(self.address, bytes([register]), result)
            return result[0]
        finally:
            self.i2c.unlock()

    def _write_register(self, register, value):
        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(self.address, bytes([register, value]))
        finally:
            self.i2c.unlock()

    def configure_pins(self, config_mask):
        self._write_register(REG_CONFIG, config_mask)

    def read_inputs(self):
        return self._read_register(REG_INPUT_PORT)

    def write_outputs(self, value):
        current = self._read_register(REG_OUTPUT_PORT)
        new_value = (current & 0b00011111) | (value & 0b11100000)
        self._write_register(REG_OUTPUT_PORT, new_value)


class JoystickInput:
    """Joystick input handler using Navigation Switch."""

    def __init__(self, i2c):
        self.pca = PCA9554(i2c, PCA9554_ADDR)
        self.pca.configure_pins(0b00011111)
        # Turn off LED
        self.pca.write_outputs(0b11100000)
        self._last_state = {}

    def read_switches(self):
        """Read all switch states."""
        value = self.pca.read_inputs()
        return {
            "up": not bool(value & (1 << PIN_UP)),
            "down": not bool(value & (1 << PIN_DOWN)),
            "left": not bool(value & (1 << PIN_LEFT)),
            "right": not bool(value & (1 << PIN_RIGHT)),
            "center": not bool(value & (1 << PIN_CENTER)),
        }

    def get_direction(self):
        """Get current direction pressed (returns DIR_* constant or None)."""
        switches = self.read_switches()
        if switches["up"]:
            return DIR_UP
        elif switches["down"]:
            return DIR_DOWN
        elif switches["left"]:
            return DIR_LEFT
        elif switches["right"]:
            return DIR_RIGHT
        return None

    def is_center_pressed(self):
        """Check if center button is pressed (with debounce)."""
        switches = self.read_switches()
        pressed = switches["center"]
        was_pressed = self._last_state.get("center", False)
        self._last_state["center"] = pressed
        return pressed and not was_pressed

    def wait_for_center(self):
        """Wait for center button press."""
        while True:
            if self.is_center_pressed():
                return
            time.sleep(WAIT_POLL_INTERVAL)

    def deinit(self):
        try:
            self.pca.write_outputs(0b11100000)  # Turn off LED
        except:
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
    """Draw score HUD."""
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


def draw_start_screen(display, best):
    """Draw start screen."""
    width = display.width
    height = display.height

    display.fill_color(BG_COLOR)

    title = "SNAKE GAME"
    subtitle = "CENTER TO PLAY"
    title_x = (width - text_pixel_width(title, FONT_TITLE)) // 2
    subtitle_x = (width - text_pixel_width(subtitle, FONT_HUD)) // 2
    draw_text(display, title, title_x, height // 2 - 30, HUD_COLOR, font_id=FONT_TITLE)
    draw_text(
        display, subtitle, subtitle_x, height // 2 + 6, HUD_COLOR, font_id=FONT_HUD
    )

    if best > 0:
        best_text = f"BEST {best}"
        best_x = (width - text_pixel_width(best_text, FONT_HUD)) // 2
        draw_text(
            display, best_text, best_x, height // 2 + 34, HUD_COLOR, font_id=FONT_HUD
        )

    controls = "USE JOYSTICK TO MOVE"
    controls_x = (width - text_pixel_width(controls, FONT_HUD)) // 2
    draw_text(display, controls, controls_x, height - 60, HUD_COLOR, font_id=FONT_HUD)

    display.swap_buffers()


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

    # Calculate offsets to center the grid
    grid_width = GRID_COLS * GRID_SIZE
    grid_height = GRID_ROWS * GRID_SIZE
    offset_x = (width - grid_width) // 2
    offset_y = (height - grid_height) // 2

    display.fill_color(BG_COLOR)
    draw_grid(display, offset_x, offset_y)
    draw_food(display, food, offset_x, offset_y)
    draw_snake(display, snake, offset_x, offset_y)
    draw_hud(display, score, best, width)


# ---------------------------------------------------------------------------
# Game Logic
# ---------------------------------------------------------------------------


def play_round(display, joystick, best_score):
    """Play one round of Snake."""
    width = display.width
    height = display.height

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

    while not game_over:
        frame_start = time.monotonic()

        # Handle input
        new_direction = joystick.get_direction()
        if new_direction:
            snake.set_direction(new_direction)

        # Move snake
        snake.move()

        # Check collisions
        if (
            snake.collides_with_walls(GRID_COLS, GRID_ROWS)
            or snake.collides_with_self()
        ):
            game_over = True

        # Check food collision
        if snake.get_head() == food.position:
            snake.grow()
            score += SCORE_PER_FOOD
            if score > local_best:
                local_best = score
            speed = min(speed + SPEED_INCREMENT, MAX_SPEED)
            food.respawn(GRID_COLS, GRID_ROWS, snake.segments)

        # Draw scene
        draw_scene(display, snake, food, score, local_best)
        display.swap_buffers(copy=False)

        # Status update
        if time.monotonic() - elapsed_timer >= 1.0:
            elapsed_timer = time.monotonic()
            print(
                f"Score: {score:03d}  Length: {len(snake.segments):02d}  Speed: {speed:.1f}"
            )

        # Frame timing
        frame_time = 1.0 / speed
        frame_elapsed = time.monotonic() - frame_start
        if frame_elapsed < frame_time:
            time.sleep(frame_time - frame_elapsed)

    return score, local_best


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    """Main game loop."""
    seed_value = int(time.monotonic() * 1000) & 0xFFFFFFFF
    random.seed(seed_value)

    print("\n" + "=" * 70)
    print("  SNAKE GAME")
    print("=" * 70)
    print("Controls: Use joystick for direction, CENTER button to start.\n")

    # Initialize display
    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0
    display.swap_buffers()

    # Initialize joystick
    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=100000)
    joystick = JoystickInput(i2c)

    best_score = 0

    try:
        while True:
            # Show start screen
            draw_start_screen(display, best_score)
            joystick.wait_for_center()

            # Play round
            score, best_score = play_round(display, joystick, best_score)
            print(f"\nRound finished. Score: {score}, Best: {best_score}")

            # Show game over screen
            draw_game_over(display, score, best_score, display.width, display.height)
            display.swap_buffers()

            # Wait for restart
            joystick.wait_for_center()

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
    finally:
        display.fill_color(rm690b0.BLACK)
        display.swap_buffers()
        display.deinit()
        joystick.deinit()
        i2c.deinit()
        print("\nBest score this session:", best_score)


if __name__ == "__main__":
    main()
