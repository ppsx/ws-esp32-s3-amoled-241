# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Startup menu for ESP32-S3 CircuitPython
"""

import time

import board
import busio
import rm690b0

try:
    import adafruit_focaltouch
except ImportError:
    adafruit_focaltouch = None


def rgb565(r: int, g: int, b: int) -> int:
    """Convert 0-255 RGB to 16-bit RGB565 color."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


# Colors
BG_COLOR = rgb565(20, 25, 35)
BUTTON_COLOR = rgb565(70, 130, 180)
BUTTON_PRESSED_COLOR = rgb565(100, 160, 210)
TEXT_COLOR = rgb565(255, 255, 255)
BORDER_COLOR = rgb565(200, 200, 200)

# Font configuration for native text rendering
FONT_16x16 = rm690b0.FONT_16x16  # Built-in 16×16 Liberation Sans font
CHAR_WIDTH_16x16 = 16
CHAR_HEIGHT_16x16 = 16


def text_pixel_width(text: str, font_id: int = FONT_16x16) -> int:
    """Return the pixel width of a text string using native font."""
    if not text:
        return 0
    # For fixed-width fonts, width = number of characters × character width
    return len(text) * CHAR_WIDTH_16x16


def draw_text(display, text, x, y, color, font_id=FONT_16x16, shadow=True):
    """Draw text using native built-in font with optional shadow effect."""
    display.set_font(font_id)
    if shadow:
        # Draw shadow (black text offset by 2 pixels)
        display.text(x + 2, y + 2, text, color=rgb565(0, 0, 0))
    # Draw main text
    display.text(x, y, text, color=color)


class TouchInput:
    """Touch input handler using FT6336U controller."""

    def __init__(self):
        if adafruit_focaltouch is None:
            raise RuntimeError("adafruit_focaltouch library is required.")

        self._i2c = busio.I2C(board.TP_SCL, board.TP_SDA, timeout=5)
        self._touch = adafruit_focaltouch.Adafruit_FocalTouch(self._i2c)
        self._last_touch = None

    def map_touch_to_display(self, touch_x, touch_y):
        """
        Transform touch coordinates from portrait to landscape.

        Touch controller reports portrait (450×600), display is landscape (600×450).
        Apply 270° clockwise rotation.

        Note: This is needed when using adafruit_focaltouch directly (not LVGL).
        LVGL integration has automatic transformation, but direct touch reading does not.

        Args:
            touch_x: 0-450 (portrait width)
            touch_y: 0-600 (portrait height)

        Returns:
            (display_x, display_y): 0-600, 0-450 (landscape)
        """
        display_x = 600 - touch_y
        display_y = touch_x
        return display_x, display_y

    def get_touch(self):
        """Return (x, y) if touched, None otherwise. Coordinates are transformed to display space."""
        if not self._touch.touched:
            self._last_touch = None
            return None

        points = self._touch.touches
        if not points:
            self._last_touch = None
            return None

        # Get raw touch coordinates
        touch_x = points[0]["x"]
        touch_y = points[0]["y"]

        # Transform to display coordinates
        display_x, display_y = self.map_touch_to_display(touch_x, touch_y)

        current = (display_x, display_y)
        # Debounce - only register new touches
        if self._last_touch == current:
            return None

        self._last_touch = current
        return current

    def deinit(self):
        try:
            self._i2c.deinit()
        except (AttributeError, Exception):
            pass


class Button:
    """Simple rectangular button."""

    def __init__(self, x, y, width, height, text):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def contains(self, px, py):
        """Check if point (px, py) is inside button."""
        return (
            self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height
        )

    def draw(self, display, color=BUTTON_COLOR):
        """Draw button on display."""
        # Fill button background
        display.fill_rect(self.x, self.y, self.width, self.height, color)

        # Draw border
        # Top
        display.fill_rect(self.x, self.y, self.width, 2, BORDER_COLOR)
        # Bottom
        display.fill_rect(self.x, self.y + self.height - 2, self.width, 2, BORDER_COLOR)
        # Left
        display.fill_rect(self.x, self.y, 2, self.height, BORDER_COLOR)
        # Right
        display.fill_rect(self.x + self.width - 2, self.y, 2, self.height, BORDER_COLOR)

        # Draw text (centered)
        text_width = text_pixel_width(self.text)
        text_height = CHAR_HEIGHT_16x16
        text_x = self.x + (self.width - text_width) // 2
        text_y = self.y + (self.height - text_height) // 2

        draw_text(display, self.text, text_x, text_y, TEXT_COLOR)


def draw_menu(display, buttons):
    """Draw the main menu."""
    display.fill_color(BG_COLOR)

    # Draw title
    title = "SELECT AN OPTION"
    title_width = text_pixel_width(title)
    title_x = (display.width - title_width) // 2
    draw_text(display, title, title_x, 40, TEXT_COLOR)

    # Draw buttons
    for button in buttons:
        button.draw(display)

    display.swap_buffers()


def main():
    """Main menu loop."""
    print("\n" + "=" * 50)
    print("  STARTUP MENU")
    print("=" * 50)
    print("Touch a button to select an option.\n")

    # Initialize display
    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0

    # Enable double buffering
    display.swap_buffers()

    # Initialize touch
    touch = TouchInput()

    # Create buttons (2-column layout)
    # Screen 600 wide, 450 high.
    col1_x = 25
    col2_x = 315
    btn_w = 260
    btn_h = 58
    gap_y = 14

    # 4 Rows + Exit
    start_y = 76
    y1 = start_y
    y2 = start_y + btn_h + gap_y
    y3 = start_y + (btn_h + gap_y) * 2
    y4 = start_y + (btn_h + gap_y) * 3
    y_exit = y4 + btn_h + gap_y + 4

    # Column 1
    flappy_button = Button(col1_x, y1, btn_w, btn_h, "FLAPPY BIRD")
    snake_button = Button(col1_x, y2, btn_w, btn_h, "SNAKE")
    minesweeper_button = Button(col1_x, y3, btn_w, btn_h, "MINESWEEPER")
    frogger_button = Button(col1_x, y4, btn_w, btn_h, "FROGGER")

    # Column 2
    pacman_button = Button(col2_x, y1, btn_w, btn_h, "PAC-MAN")
    sokoban_button = Button(col2_x, y2, btn_w, btn_h, "SOKOBAN")
    robbo_button = Button(col2_x, y3, btn_w, btn_h, "ROBBO")

    # Exit (Centered)
    exit_button = Button((display.width - 300) // 2, y_exit, 300, btn_h, "EXIT")

    buttons = [
        flappy_button,
        snake_button,
        pacman_button,
        sokoban_button,
        minesweeper_button,
        robbo_button,
        frogger_button,
        exit_button,
    ]

    # Draw initial menu
    draw_menu(display, buttons)

    selected = None
    try:
        # Main loop
        while selected is None:
            touch_point = touch.get_touch()

            if touch_point:
                x, y = touch_point
                print(f"Touch detected at: ({x}, {y})")

                for btn in buttons:
                    if btn.contains(x, y):
                        print(f"{btn.text} button pressed!")
                        btn.draw(display, BUTTON_PRESSED_COLOR)
                        display.swap_buffers()
                        time.sleep(0.2)

                        if btn == flappy_button:
                            selected = "flappy"
                        elif btn == snake_button:
                            selected = "snake"
                        elif btn == pacman_button:
                            selected = "pacman"
                        elif btn == sokoban_button:
                            selected = "sokoban"
                        elif btn == minesweeper_button:
                            selected = "minesweeper"
                        elif btn == robbo_button:
                            selected = "robbo"
                        elif btn == frogger_button:
                            selected = "frogger"
                        elif btn == exit_button:
                            selected = "exit"
                        elif btn == flight_button:
                            selected = "flight"
                        break

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        selected = "exit"

    finally:
        # Cleanup
        print("Cleaning up display and touch...")
        display.fill_color(rgb565(0, 0, 0))
        display.swap_buffers()
        display.deinit()
        touch.deinit()
        print("Cleanup complete.")

    # Execute selected option
    if selected == "flappy":
        print("\nStarting Flappy Bird...\n")
        try:
            from games import game_flappy_bird
            game_flappy_bird.main()
        except Exception as e:
            print(f"Error: {e}")
    elif selected == "snake":
        print("\nStarting Snake Game...\n")
        try:
            from games import game_snake
            game_snake.main()
        except Exception as e:
            print(f"Error: {e}")
    elif selected == "pacman":
        print("\nStarting Pac-Man...\n")
        try:
            from games import game_pacman
            game_pacman.main()
        except Exception as e:
            print(f"Error: {e}")
    elif selected == "sokoban":
        print("\nStarting Sokoban...\n")
        try:
            from games import game_sokoban
            game_sokoban.main()
        except Exception as e:
            print(f"Error: {e}")
    elif selected == "minesweeper":
        print("\nStarting Minesweeper...\n")
        try:
            from games import game_minesweeper
            game_minesweeper.main()
        except Exception as e:
            print(f"Error: {e}")
    elif selected == "robbo":
        print("\nStarting Robbo...\n")
        try:
            from games import game_robbo
            game_robbo.main()
        except Exception as e:
            print(f"Error: {e}")
    elif selected == "frogger":
        print("\nStarting Frogger...\n")
        try:
            from games import game_frogger
            game_frogger.main()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\nExiting to REPL.")


if __name__ == "__main__":
    main()
