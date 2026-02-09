"""
Pac-Man Clone for Waveshare ESP32-S3 Touch AMOLED 2.41
Includes Classic Map, Ghost AI, and Touch/Joystick Controls.
"""

import gc
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
TARGET_FPS = 45
TILE_SIZE = 14  # Reduced tile size to fit 31 rows in 450px height (31*14 = 434)
# Map width = 28 * 14 = 392. Display width = 600.
# Place Map on left to minimize dirty region gap between Map and UI (on right)
MAP_OFFSET_X = 10
MAP_OFFSET_Y = 8  # (450 - 434)/2 = 8


# Colors (RGB565)
def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


COLOR_BLACK = 0x0000
COLOR_WALL = rgb565(20, 20, 180)
COLOR_PELLET = rgb565(255, 180, 180)
COLOR_POWER = rgb565(255, 210, 210)
COLOR_PACMAN = rgb565(255, 255, 0)
COLOR_GHOST_RED = rgb565(255, 0, 0)
COLOR_GHOST_PINK = rgb565(255, 180, 255)
COLOR_GHOST_CYAN = rgb565(0, 255, 255)
COLOR_GHOST_ORANGE = rgb565(255, 180, 50)
COLOR_GHOST_SCARED = rgb565(0, 0, 255)
COLOR_GHOST_EYES = rgb565(220, 220, 255)  # For "dead" ghost
COLOR_WHITE = 0xFFFF
COLOR_UI_TEXT = 0xFFFF

# Directions
DIR_NONE = 0
DIR_UP = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4

# Map Chars
CHAR_WALL = "#"
CHAR_PELLET = "."
CHAR_POWER = "o"
CHAR_EMPTY = " "
CHAR_DOOR = "-"
CHAR_PACMAN = "P"

# Ghost ID constants
GHOST_BLINKY = 0
GHOST_PINKY = 1
GHOST_INKY = 2
GHOST_CLYDE = 3

# Ghost States
STATE_SCATTER = 0
STATE_CHASE = 1
STATE_FRIGHTENED = 2
STATE_DEAD = 3  # Eaten, returning to house
STATE_LEAVING_HOUSE = 4  # Exiting from ghost house

# ---------------------------------------------------------------------------
# Hardware Abstraction (Joystick & Touch)
# ---------------------------------------------------------------------------
PCA9554_ADDR = 0x21
PIN_UP = 0
PIN_DOWN = 1
PIN_RIGHT = 2
PIN_LEFT = 3
PIN_CENTER = 4


class PCA9554:
    def __init__(self, i2c, address=PCA9554_ADDR):
        self._i2c = i2c
        self._address = address
        self._buffer = bytearray(2)

    def _write_register(self, register, value):
        self._buffer[0] = register
        self._buffer[1] = value
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(self._address, self._buffer)
        finally:
            self._i2c.unlock()

    def _read_register(self, register):
        self._buffer[0] = register
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto_then_readfrom(
                self._address, self._buffer, self._buffer, out_end=1, in_end=1
            )
            return self._buffer[0]
        finally:
            self._i2c.unlock()

    def configure_pins(self, direction_mask):
        self._write_register(3, direction_mask)

    def read_inputs(self):
        return self._read_register(0)

    def write_outputs(self, value):
        self._write_register(1, value)


class JoystickInput:
    def __init__(self, i2c):
        self.i2c = i2c
        self.pca = PCA9554(self.i2c)
        self.pca.configure_pins(0b00011111)
        self.pca.write_outputs(0b11100000)

    def get_input(self):
        try:
            val = self.pca.read_inputs()
        except OSError:
            return DIR_NONE

        # Ignore invalid state (all 0 usually means read error or detached)
        if val == 0:
            return DIR_NONE

        if not (val & (1 << PIN_UP)):
            return DIR_UP
        if not (val & (1 << PIN_DOWN)):
            return DIR_DOWN
        if not (val & (1 << PIN_LEFT)):
            return DIR_LEFT
        if not (val & (1 << PIN_RIGHT)):
            return DIR_RIGHT
        return DIR_NONE

    def check_center(self):
        try:
            val = self.pca.read_inputs()
            # Ignore invalid state
            if val == 0:
                return False
            return not (val & (1 << PIN_CENTER))
        except OSError:
            return False

    def deinit(self):
        pass


class TouchInput:
    def __init__(self, i2c):
        if adafruit_focaltouch is None:
            raise RuntimeError("adafruit_focaltouch library is required.")
        self.i2c = i2c
        self.touch = adafruit_focaltouch.Adafruit_FocalTouch(self.i2c)
        self.start_x = 0
        self.start_y = 0
        self.is_swiping = False
        self.last_tap_time = 0

    def get_input(self):
        if not self.touch.touched:
            self.is_swiping = False
            return DIR_NONE
        try:
            points = self.touch.touches
        except:
            return DIR_NONE
        if not points:
            self.is_swiping = False
            return DIR_NONE

        # Map coordinates (Landscape)
        raw_x = points[0]["x"]
        raw_y = points[0]["y"]
        x = 600 - raw_y
        y = raw_x

        if not self.is_swiping:
            self.start_x = x
            self.start_y = y
            self.is_swiping = True
            return DIR_NONE

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
        return DIR_NONE

    def check_center(self):
        # Interpret a tap anywhere as "center/select" if not swiping
        if self.touch.touched and not self.is_swiping:
            # Very simple debounced tap
            now = time.monotonic()
            if now - self.last_tap_time > 0.5:
                self.last_tap_time = now
                return True
        return False

    def deinit(self):
        pass


# ---------------------------------------------------------------------------
# Game Logic & Map
# ---------------------------------------------------------------------------

# Classic Layout approximation (28x31)
# Classic Pac-Man Map
MAP_PACMAN = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "     #.##### ## #####.#     ",
    "     #.##          ##.#     ",
    "     #.## ###--### ##.#     ",
    "######.## #      # ##.######",
    "      .   #      #   .      ",
    "######.## #      # ##.######",
    "     #.## ######## ##.#     ",
    "     #.##          ##.#     ",
    "     #.## ######## ##.#     ",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#o..##.......P........##..o#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
]

# Ms. Pac-Man Map 1 (Pink/Cyan maze)
MAP_MS_PACMAN_1 = [
    "############################",
    "#......##..........##......#",
    "#o####.##.########.##.####o#",
    "#.####.##.########.##.####.#",
    "#..........................#",
    "###.##.#####.##.#####.##.###",
    "  #.##.#####.##.#####.##.#  ",
    "###.##.#####.##.#####.##.###",
    "   .##.......##.......##.   ",
    "###.##### ######## #####.###",
    "  #.##### ######## #####.#  ",
    "  #.                    .#  ",
    "  #.##### ###--### #####.#  ",
    "  #.##### #      # #####.#  ",
    "  #.##    #      #    ##.#  ",
    "  #.## ## #      # ## ##.#  ",
    "###.## ## ######## ## ##.###",
    "   .   ##          ##   .   ",
    "###.######## ## ########.###",
    "  #.######## ## ########.#  ",
    "  #.......   ##   .......#  ",
    "  #.#####.########.#####.#  ",
    "###.#####.########.#####.###",
    "#............P.............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#.####.##....##....##.####.#",
    "#o####.##.########.##.####o#",
    "#.####.##.########.##.####.#",
    "#..........................#",
    "############################",
]

# Ms. Pac-Man Map 2 (Cyan maze)
MAP_MS_PACMAN_2 = [
    "############################",
    "       ##..........##       ",
    "###### ##.########.## ######",
    "###### ##.########.## ######",
    "#o...........##...........o#",
    "#.#######.##.##.##.#######.#",
    "#.#######.##.##.##.#######.#",
    "#.##......##.##.##......##.#",
    "#.##.#### ##....## ####.##.#",
    "#.##.#### ######## ####.##.#",
    "#......## ######## ##......#",
    "######.##          ##.######",
    "######.## ###--### ##.######",
    "#......## #      # ##......#",
    "#.####.## #      # ##.####.#",
    "#.####.   #      #   .####.#",
    "#...##.## ######## ##.##...#",
    "###.##.##          ##.##.###",
    "  #.##.#### #### ####.##.#  ",
    "  #.##.#### #### ####.##.#  ",
    "  #.........####.........#  ",
    "  #.#######.####.#######.#  ",
    "###.#######.####.#######.###",
    ".......##....P.....##.......",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#o..##.......##.......##..o#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "############################",
]

# Ms. Pac-Man Map 3 (Orange/Brown maze)
MAP_MS_PACMAN_3 = [
    "############################",
    "#.........##....##.........#",
    "#.#######.##.##.##.#######.#",
    "#o#######.##.##.##.#######o#",
    "#.##.........##.........##.#",
    "#.##.##.####.##.####.##.##.#",
    "#....##.####.##.####.##....#",
    "####.##.####.##.####.##.####",
    "####.##..............##.####",
    " ....#### ######## ####.... ",
    "#.##.#### ######## ####.##.#",
    "#.##...              ...##.#",
    "#.####.## ###--### ##.####.#",
    "#.####.## #      # ##.####.#",
    "#......## #      # ##......#",
    "#.##.#### #      # ####.##.#",
    "#.##.#### ######## ####.##.#",
    "#.##...              ...##.#",
    "#.####.##### ## #####.####.#",
    "#.####.##### ## #####.####.#",
    "#......##....##....##......#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#o..##.......P........##..o#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#......##....##....##......#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##..........##......#",
    "############################",
]

# Ms. Pac-Man Map 4 (Purple/Blue maze)
MAP_MS_PACMAN_4 = [
    "############################",
    "#..........................#",
    "#.##.####.########.####.##.#",
    "#o##.####.########.####.##o#",
    "#.##.####.##....##.####.##.#",
    "#.##......##.##.##......##.#",
    "#.####.##.##.##.##.##.####.#",
    "#.####.##.##.##.##.##.####.#",
    "#......##....##....##......#",
    "###.######## ## ########.###",
    "  #.######## ## ########.#  ",
    "  #....##          ##....#  ",
    "### ##.## ###--### ##.## ###",
    "    ##.## #      # ##.##    ",
    "######.   #      #   .######",
    "######.## #      # ##.######",
    "    ##.## ######## ##.##    ",
    "###....##          ##....###",
    "  #.##.##### ## #####.##.#  ",
    "  #.##.##### ## #####.##.#  ",
    "  #.##....   ##   ....##.#  ",
    "  #.#####.## ## ##.#####.#  ",
    "###.#####.## ## ##.#####.###",
    "#.........## P  ##.........#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#.##...##..........##...##.#",
    "#o##.#######.##.#######.##o#",
    "#.##.#######.##.#######.##.#",
    "#............##............#",
    "############################",
]

# All maps in order
ALL_MAPS = [
    MAP_PACMAN,
    MAP_MS_PACMAN_1,
    MAP_MS_PACMAN_2,
    MAP_MS_PACMAN_3,
    MAP_MS_PACMAN_4,
]

# For backward compatibility
CLASSIC_MAP = MAP_PACMAN

# Helper for font drawing (using built-in font)
FONT_HUD = rm690b0.FONT_16x16
CHAR_WIDTH = 16
CHAR_HEIGHT = 16


def draw_text(display, text, x, y, color, scale=1):
    display.set_font(FONT_HUD)
    display.text(x, y, text, color=color)


def text_width(text):
    return len(text) * CHAR_WIDTH


class Entity:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.prev_x = float(x)
        self.prev_y = float(y)
        self.start_x = x
        self.start_y = y
        self.color = color
        self.dir = DIR_NONE
        self.next_dir = DIR_NONE
        self.speed = 0.25  # Tiles per frame (approx)
        self.radius = TILE_SIZE // 2

    def snap_to_grid(self):
        # Return nearest grid integer coordinates
        return int(round(self.x)), int(round(self.y))

    def get_pixel_pos(self):
        return (
            int(self.x * TILE_SIZE + MAP_OFFSET_X + TILE_SIZE / 2),
            int(self.y * TILE_SIZE + MAP_OFFSET_Y + TILE_SIZE / 2),
        )


class Pacman(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, COLOR_PACMAN)
        self.score = 0
        self.lives = 3
        self.mouth_open = 0
        self.mouth_anim_dir = 1
        self.angle = 0  # For rotation


class Ghost(Entity):
    def __init__(self, x, y, color, type_id):
        super().__init__(x, y, color)
        self.type_id = type_id
        self.state = STATE_LEAVING_HOUSE if type_id != GHOST_BLINKY else STATE_SCATTER
        self.speed *= 0.9  # ghosts should move a bit slower than Pac-man
        self.scared_speed_modifier = 0.5  # Slower when scared
        self.dead_speed_modifier = 2.0  # 2x faster when returning home
        self.target_x = 0
        self.target_y = 0
        self.original_color = color
        self.in_house = type_id != GHOST_BLINKY  # All except Blinky start in house
        self.house_timer = 0  # Time to stay in house before leaving
        self.respawn_timer = 0  # Time to stay in house after being eaten
        self.reverse_on_next_intersection = (
            False  # Flag to reverse direction at next intersection
        )
        self.last_decision_tile = (-1, -1)  # Track last tile where AI made a decision
        self.state_before_frightened = None  # Remember state before becoming frightened


class Game:
    def __init__(self, display, joystick):
        self.display = display
        self.joystick = joystick
        self.width = 28
        self.height = 31
        self.grid = []
        self.pacman = None
        self.ghosts = []
        self.game_over = False
        self.high_score = 0
        self.previous_high_score = 0  # Track high score at start of game
        self.scared_timer = 0
        self.scatter_chase_timer = 0
        self.global_mode_scatter = True
        self.scatter_chase_phase = 0  # Track which phase we're in (0-6)
        self.ghosts_eaten_combo = 0  # Track consecutive ghost eats for bonus
        self.walls_drawn = False  # Track if static walls are drawn

        # Map progression system
        self.current_map_index = 0
        self.current_map = ALL_MAPS[self.current_map_index]
        self.ghost_house_center = (14, 14)  # Will be set dynamically per map
        self.ghost_house_exit = (14, 11)  # Exit point above door

        # Classic Pac-Man scatter/chase pattern (in seconds, converted to frames)
        # Pattern: Scatter, Chase, Scatter, Chase, Scatter, Chase, Scatter, Chase forever
        self.scatter_chase_pattern = [
            (True, 7 * TARGET_FPS),  # Scatter 7s
            (False, 20 * TARGET_FPS),  # Chase 20s
            (True, 7 * TARGET_FPS),  # Scatter 7s
            (False, 20 * TARGET_FPS),  # Chase 20s
            (True, 5 * TARGET_FPS),  # Scatter 5s
            (False, 20 * TARGET_FPS),  # Chase 20s
            (True, 5 * TARGET_FPS),  # Scatter 5s
            (False, -1),  # Chase forever (-1 = infinite)
        ]

        # Parse map
        self.reset_level()

    def reset_level(self, next_map=False):
        """Reset level. If next_map=True, advance to next map."""
        if next_map:
            self.current_map_index = (self.current_map_index + 1) % len(ALL_MAPS)
            self.current_map = ALL_MAPS[self.current_map_index]

        self.grid = []
        self.ghosts = []

        # Find ghost house center by looking for the door marker (---)
        ghost_house_y = None
        ghost_house_x = None
        door_y = None
        for y_idx, row_str in enumerate(self.current_map):
            if "--" in row_str:
                door_y = y_idx  # Door position
                ghost_house_y = y_idx + 1  # One row below the door
                # Find the center X position (middle of the door)
                door_start = row_str.find("--")
                door_end = row_str.rfind("--") + 2
                ghost_house_x = (door_start + door_end) // 2
                break

        # If found, use it; otherwise fallback to default
        if (
            ghost_house_y is not None
            and ghost_house_x is not None
            and door_y is not None
        ):
            self.ghost_house_center = (ghost_house_x, ghost_house_y)
            self.ghost_house_exit = (ghost_house_x, door_y - 1)  # One row above door
        else:
            self.ghost_house_center = (14, 14)  # Fallback
            self.ghost_house_exit = (14, 11)  # Fallback

        row_idx = 0
        for row_str in self.current_map:
            # Pad or trim row
            if len(row_str) < self.width:
                row_str = row_str.ljust(self.width, CHAR_WALL)
            if len(row_str) > self.width:
                row_str = row_str[: self.width]

            grid_row = []
            for col_idx, char in enumerate(row_str):
                if char == "P":
                    self.pacman_start = (col_idx, row_idx)
                    grid_row.append(CHAR_EMPTY)
                else:
                    grid_row.append(char)
            self.grid.append(grid_row)
            row_idx += 1

        # Init Entities
        if self.pacman is None:
            # First time init
            self.pacman = Pacman(self.pacman_start[0], self.pacman_start[1])
        else:
            # Respawn
            self.pacman.x = self.pacman_start[0]
            self.pacman.y = self.pacman_start[1]
            self.pacman.dir = DIR_NONE
            self.pacman.next_dir = DIR_NONE

        # Spawn Ghosts (dynamic positions based on ghost house)
        # Use integer coordinates to ensure they are centered and AI runs immediately
        house_x, house_y = self.ghost_house_center
        exit_x, exit_y = self.ghost_house_exit

        # Blinky (Red) starts outside (at exit point)
        blinky = Ghost(exit_x, exit_y, COLOR_GHOST_RED, GHOST_BLINKY)
        blinky.in_house = False
        blinky.house_timer = 0
        self.ghosts.append(blinky)

        # Pinky (Pink) inside center - exits after 5 seconds
        pinky = Ghost(house_x, house_y, COLOR_GHOST_PINK, GHOST_PINKY)
        pinky.in_house = True
        pinky.house_timer = 5 * TARGET_FPS
        self.ghosts.append(pinky)

        # Inky (Cyan) inside left - exits after 10 seconds
        inky = Ghost(house_x - 2, house_y, COLOR_GHOST_CYAN, GHOST_INKY)
        inky.in_house = True
        inky.house_timer = 10 * TARGET_FPS
        self.ghosts.append(inky)

        # Clyde (Orange) inside right - exits after 15 seconds
        clyde = Ghost(house_x + 2, house_y, COLOR_GHOST_ORANGE, GHOST_CLYDE)
        clyde.in_house = True
        clyde.house_timer = 15 * TARGET_FPS
        self.ghosts.append(clyde)

        self.scared_timer = 0
        self.game_over = False
        self.pellets_remaining = self.count_pellets()
        self.walls_drawn = False  # Reset for new level

        # Initialize scatter/chase system
        self.scatter_chase_phase = 0
        self.global_mode_scatter = self.scatter_chase_pattern[0][0]
        self.scatter_chase_timer = self.scatter_chase_pattern[0][1]
        gc.collect()

    def count_pellets(self):
        """Count total pellets and power pellets in the level"""
        count = 0
        for row in self.grid:
            for char in row:
                if char == CHAR_PELLET or char == CHAR_POWER:
                    count += 1
        return count

    def is_wall(self, x, y):
        # Tunnel handling
        if x < 0 or x >= self.width:
            return False  # Walkable tunnel
        if y < 0 or y >= self.height:
            return True
        # Treat door as wall for Pacman, walkable for ghosts (handled separately)
        return self.grid[y][x] == CHAR_WALL

    def is_door(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return self.grid[y][x] == CHAR_DOOR

    def get_valid_moves(self, x, y, include_reverse_of=DIR_NONE, ghost=None):
        moves = []
        # Check UP, DOWN, LEFT, RIGHT
        # x, y are integers here
        dirs = [(DIR_UP, 0, -1), (DIR_DOWN, 0, 1), (DIR_LEFT, -1, 0), (DIR_RIGHT, 1, 0)]
        for d, dx, dy in dirs:
            nx, ny = x + dx, y + dy

            # Tunnel logic
            if nx < 0:
                nx = self.width - 1
            if nx >= self.width:
                nx = 0

            if not self.is_wall(nx, ny):
                # Ghost door logic
                if self.is_door(nx, ny):
                    if ghost is None:
                        continue  # Pacman can't pass door
                    elif ghost.state not in (STATE_DEAD, STATE_LEAVING_HOUSE):
                        continue  # Normal ghosts can't pass door

                # Reverse check
                is_reverse = False
                if include_reverse_of == DIR_UP and d == DIR_DOWN:
                    is_reverse = True
                if include_reverse_of == DIR_DOWN and d == DIR_UP:
                    is_reverse = True
                if include_reverse_of == DIR_LEFT and d == DIR_RIGHT:
                    is_reverse = True
                if include_reverse_of == DIR_RIGHT and d == DIR_LEFT:
                    is_reverse = True

                if not is_reverse:
                    moves.append(d)
        return moves

    def move_entity(self, entity):
        # Basic movement logic with grid snapping

        # Determine center of current tile
        # Entity x,y are float grid coords. 13.5, 14.0 means center of tile (13,14)?
        # No, let's say 13.0, 14.0 is top-left of tile. 13.5, 14.5 is center.
        # But to simplify, let's say 13.0, 14.0 is the grid intersection (top-left).
        # We render offset by half tile.

        # Check if entity is "centered" on a tile to allow turning
        current_tile_x = int(round(entity.x))
        current_tile_y = int(round(entity.y))

        diff_x = entity.x - current_tile_x
        diff_y = entity.y - current_tile_y
        dist_sq = diff_x * diff_x + diff_y * diff_y

        is_centered = dist_sq < 0.01

        # Calculate Move Vector
        dx, dy = 0, 0
        if entity.dir == DIR_UP:
            dy = -1
        elif entity.dir == DIR_DOWN:
            dy = 1
        elif entity.dir == DIR_LEFT:
            dx = -1
        elif entity.dir == DIR_RIGHT:
            dx = 1

        # Check wall ahead
        next_tile_x = current_tile_x + dx
        next_tile_y = current_tile_y + dy

        # Tunnel wrapping for lookahead
        if next_tile_x < 0:
            next_tile_x = self.width - 1
        if next_tile_x >= self.width:
            next_tile_x = 0

        wall_ahead = self.is_wall(next_tile_x, next_tile_y)
        if isinstance(entity, Pacman) and self.is_door(next_tile_x, next_tile_y):
            wall_ahead = True
        # Ghosts can only pass through doors when DEAD or LEAVING_HOUSE
        if isinstance(entity, Ghost):
            if self.is_door(next_tile_x, next_tile_y):
                if entity.state not in (STATE_DEAD, STATE_LEAVING_HOUSE):
                    wall_ahead = True

        # Turn Logic (Pacman)
        if isinstance(entity, Pacman):
            if entity.next_dir != DIR_NONE and entity.next_dir != entity.dir:
                # Try to turn
                # Check if next_dir is valid from current tile
                nx, ny = 0, 0
                if entity.next_dir == DIR_UP:
                    ny = -1
                elif entity.next_dir == DIR_DOWN:
                    ny = 1
                elif entity.next_dir == DIR_LEFT:
                    nx = -1
                elif entity.next_dir == DIR_RIGHT:
                    nx = 1

                check_x = current_tile_x + nx
                check_y = current_tile_y + ny

                # Tunnel wrap
                if check_x < 0:
                    check_x = self.width - 1
                if check_x >= self.width:
                    check_x = 0

                can_turn = not self.is_wall(check_x, check_y) and not self.is_door(
                    check_x, check_y
                )

                # If turning 180 degrees, do it immediately
                is_180 = (
                    (entity.dir == DIR_UP and entity.next_dir == DIR_DOWN)
                    or (entity.dir == DIR_DOWN and entity.next_dir == DIR_UP)
                    or (entity.dir == DIR_LEFT and entity.next_dir == DIR_RIGHT)
                    or (entity.dir == DIR_RIGHT and entity.next_dir == DIR_LEFT)
                )

                if is_180:
                    entity.dir = entity.next_dir
                    entity.next_dir = DIR_NONE
                    dx, dy = nx, ny  # Update vector immediately
                    wall_ahead = False  # Assume clear if we just came from there
                elif is_centered and can_turn:
                    entity.x = current_tile_x  # Snap to center
                    entity.y = current_tile_y
                    entity.dir = entity.next_dir
                    entity.next_dir = DIR_NONE
                    dx, dy = nx, ny
                    wall_ahead = False

        if wall_ahead and is_centered:
            # Stop
            entity.x = current_tile_x
            entity.y = current_tile_y
        else:
            # Move
            speed = entity.speed
            if isinstance(entity, Ghost):
                if entity.state == STATE_DEAD:
                    speed *= entity.dead_speed_modifier
                elif entity.state == STATE_FRIGHTENED:
                    speed *= entity.scared_speed_modifier

            entity.x += dx * speed
            entity.y += dy * speed

            # Tunnel Teleport
            if entity.x < -0.5:
                entity.x = self.width - 0.5
            elif entity.x >= self.width - 0.5:
                entity.x = -0.5

    def update_ghost_ai(self, g):
        # Handle house timer
        if g.in_house:
            if g.house_timer > 0:
                g.house_timer -= 1
                return  # Don't move while in house
            else:
                # Time to leave house - start moving towards exit
                g.in_house = False
                g.state = STATE_LEAVING_HOUSE

        # Handle respawn timer (after being eaten)
        if g.respawn_timer > 0:
            g.respawn_timer -= 1
            if g.respawn_timer == 0:
                # Exit house
                g.in_house = False
                g.state = STATE_LEAVING_HOUSE
                g.color = g.original_color
            return  # Don't move while respawning

        # Simple AI update at intersections
        current_tile_x = int(round(g.x))
        current_tile_y = int(round(g.y))

        diff_x = g.x - current_tile_x
        diff_y = g.y - current_tile_y
        dist_sq = diff_x * diff_x + diff_y * diff_y

        # Check if we're close enough to center to make decisions
        is_close_to_center = dist_sq < 0.04

        # Check if we already made a decision on this tile
        current_tile_pos = (current_tile_x, current_tile_y)
        already_decided_here = g.last_decision_tile == current_tile_pos

        # Handle reverse flag - reverse when reasonably close to center
        if (
            is_close_to_center
            and g.reverse_on_next_intersection
            and not already_decided_here
        ):
            # Snap to center
            g.x = current_tile_x
            g.y = current_tile_y

            # Reverse direction
            reverse_map = {
                DIR_UP: DIR_DOWN,
                DIR_DOWN: DIR_UP,
                DIR_LEFT: DIR_RIGHT,
                DIR_RIGHT: DIR_LEFT,
                DIR_NONE: DIR_NONE,
            }
            g.dir = reverse_map.get(g.dir, g.dir)
            g.reverse_on_next_intersection = False
            g.last_decision_tile = current_tile_pos  # Mark this tile as processed
            # Return here so ghost doesn't change direction again this frame
            return

        # Only run AI when close to center AND haven't decided on this tile yet
        if is_close_to_center and not already_decided_here:
            # Snap
            g.x = current_tile_x
            g.y = current_tile_y

            # Determine target based on state and ghost personality
            tx, ty = self.pacman.x, self.pacman.y  # Default target

            if g.state == STATE_CHASE:
                # Each ghost has unique chase behavior (classic Pac-Man AI)
                if g.type_id == GHOST_BLINKY:
                    # Blinky (Red): "Shadow" - targets Pacman directly (aggressive)
                    tx, ty = self.pacman.x, self.pacman.y

                elif g.type_id == GHOST_PINKY:
                    # Pinky (Pink): "Speedy" - targets 4 tiles ahead of Pacman
                    tx, ty = self.pacman.x, self.pacman.y
                    if self.pacman.dir == DIR_UP:
                        ty -= 4
                    elif self.pacman.dir == DIR_DOWN:
                        ty += 4
                    elif self.pacman.dir == DIR_LEFT:
                        tx -= 4
                    elif self.pacman.dir == DIR_RIGHT:
                        tx += 4

                elif g.type_id == GHOST_INKY:
                    # Inky (Cyan): "Bashful" - uses Blinky's position + Pacman
                    # Vector from Blinky to 2 tiles ahead of Pacman, then double it
                    ahead_x, ahead_y = self.pacman.x, self.pacman.y
                    if self.pacman.dir == DIR_UP:
                        ahead_y -= 2
                    elif self.pacman.dir == DIR_DOWN:
                        ahead_y += 2
                    elif self.pacman.dir == DIR_LEFT:
                        ahead_x -= 2
                    elif self.pacman.dir == DIR_RIGHT:
                        ahead_x += 2

                    # Find Blinky
                    blinky_x, blinky_y = 14, 11  # Default if not found
                    for ghost in self.ghosts:
                        if ghost.type_id == GHOST_BLINKY:
                            blinky_x, blinky_y = ghost.x, ghost.y
                            break

                    # Vector from Blinky to ahead point, doubled
                    vec_x = ahead_x - blinky_x
                    vec_y = ahead_y - blinky_y
                    tx = int(blinky_x + vec_x * 2)
                    ty = int(blinky_y + vec_y * 2)

                elif g.type_id == GHOST_CLYDE:
                    # Clyde (Orange): "Pokey" - targets Pacman when far, his corner when close
                    dist_to_pacman = (
                        (g.x - self.pacman.x) ** 2 + (g.y - self.pacman.y) ** 2
                    ) ** 0.5
                    if dist_to_pacman > 8:  # More than 8 tiles away
                        tx, ty = self.pacman.x, self.pacman.y  # Chase
                    else:
                        tx, ty = 0, 32  # Retreat to his scatter corner

            elif g.state == STATE_LEAVING_HOUSE:
                # Target: Exit position (above the door - dynamic per map)
                tx, ty = self.ghost_house_exit
                if (
                    current_tile_x == self.ghost_house_exit[0]
                    and current_tile_y == self.ghost_house_exit[1]
                ):
                    # Exited house - switch to normal mode
                    g.state = (
                        STATE_CHASE if not self.global_mode_scatter else STATE_SCATTER
                    )
                    # Continue with normal AI this frame, don't return
            elif g.state == STATE_DEAD:
                # Target: Ghost House Center (dynamic per map)
                tx, ty = self.ghost_house_center
                if (
                    current_tile_x == self.ghost_house_center[0]
                    and current_tile_y == self.ghost_house_center[1]
                ):
                    # Arrived at house - start respawn timer
                    g.in_house = True
                    g.respawn_timer = (
                        self.scared_timer if self.scared_timer > 0 else (3 * TARGET_FPS)
                    )
                    return
            elif g.state == STATE_FRIGHTENED:
                # Run away from Pacman - target opposite direction
                dx = current_tile_x - self.pacman.x
                dy = current_tile_y - self.pacman.y
                # Amplify direction to create target far from Pacman
                tx = int(current_tile_x + dx * 2)
                ty = int(current_tile_y + dy * 2)
            elif g.state == STATE_SCATTER:
                # Corners
                if g.type_id == GHOST_BLINKY:
                    tx, ty = 25, -2
                elif g.type_id == GHOST_PINKY:
                    tx, ty = 2, -2
                elif g.type_id == GHOST_INKY:
                    tx, ty = 27, 32
                elif g.type_id == GHOST_CLYDE:
                    tx, ty = 0, 32

            # Get valid moves (excluding reversing direction)
            moves = self.get_valid_moves(current_tile_x, current_tile_y, g.dir, ghost=g)

            if not moves:
                # Dead end (shouldn't happen in standard map except start), reverse
                reverse_map = {
                    DIR_UP: DIR_DOWN,
                    DIR_DOWN: DIR_UP,
                    DIR_LEFT: DIR_RIGHT,
                    DIR_RIGHT: DIR_LEFT,
                }
                g.dir = reverse_map.get(g.dir, DIR_NONE)
                return

            # Choose move minimizing distance to target
            best_dist = 999999
            best_dir = moves[0]

            # Randomness for frightened
            if g.state == STATE_FRIGHTENED:
                best_dir = random.choice(moves)
            else:
                # Calculate best direction
                for d in moves:
                    nx, ny = current_tile_x, current_tile_y
                    if d == DIR_UP:
                        ny -= 1
                    elif d == DIR_DOWN:
                        ny += 1
                    elif d == DIR_LEFT:
                        nx -= 1
                    elif d == DIR_RIGHT:
                        nx += 1

                    dist = (nx - tx) ** 2 + (ny - ty) ** 2
                    if dist < best_dist:
                        best_dist = dist
                        best_dir = d

                # 10% chance to pick random direction instead (make ghosts less perfect)
                if g.state != STATE_DEAD and random.random() < 0.1:
                    best_dir = random.choice(moves)

            g.dir = best_dir
            g.last_decision_tile = current_tile_pos  # Mark this tile as processed

    def update(self):
        # Save previous positions
        self.pacman.prev_x = self.pacman.x
        self.pacman.prev_y = self.pacman.y
        for g in self.ghosts:
            g.prev_x = g.x
            g.prev_y = g.y

        # Update Pacman
        self.move_entity(self.pacman)

        # Check interactions
        px = int(round(self.pacman.x))
        py = int(round(self.pacman.y))

        if 0 <= px < self.width and 0 <= py < self.height:
            char = self.grid[py][px]
            if char == CHAR_PELLET:
                self.grid[py][px] = CHAR_EMPTY
                self.pacman.score += 10
                self.pellets_remaining -= 1
            elif char == CHAR_POWER:
                self.grid[py][px] = CHAR_EMPTY
                self.pacman.score += 50
                self.pellets_remaining -= 1
                self.scared_timer = 7 * TARGET_FPS  # 7 seconds
                self.ghosts_eaten_combo = 0  # Reset combo counter

                # Make ghosts frightened and mark them to reverse at next intersection
                for g in self.ghosts:
                    if (
                        g.state != STATE_DEAD
                        and not g.in_house
                        and g.respawn_timer == 0
                    ):
                        # Remember previous state before becoming frightened
                        g.state_before_frightened = g.state
                        g.state = STATE_FRIGHTENED
                        # Set flag to reverse direction at next intersection
                        g.reverse_on_next_intersection = True

        # Update Scatter/Chase Timer (only when not in frightened mode)
        if self.scared_timer == 0:
            if self.scatter_chase_timer > 0:
                self.scatter_chase_timer -= 1
                if self.scatter_chase_timer == 0:
                    # Move to next phase
                    self.scatter_chase_phase += 1
                    if self.scatter_chase_phase < len(self.scatter_chase_pattern):
                        self.global_mode_scatter, timer_duration = (
                            self.scatter_chase_pattern[self.scatter_chase_phase]
                        )
                        self.scatter_chase_timer = timer_duration

                        # Switch all active ghosts to new mode and reverse direction
                        for g in self.ghosts:
                            if g.state == STATE_SCATTER or g.state == STATE_CHASE:
                                g.state = (
                                    STATE_SCATTER
                                    if self.global_mode_scatter
                                    else STATE_CHASE
                                )
                                # Reverse direction when switching modes (classic behavior)
                                g.reverse_on_next_intersection = True
                    else:
                        # Stay in final phase (Chase forever)
                        self.global_mode_scatter = False
                        self.scatter_chase_timer = -1  # Infinite
            elif self.scatter_chase_timer == -1:
                # Infinite chase mode - do nothing
                pass

        # Update Timers
        if self.scared_timer > 0:
            self.scared_timer -= 1
            if self.scared_timer == 0:
                for g in self.ghosts:
                    if g.state == STATE_FRIGHTENED:
                        # Restore previous state or default to current global mode
                        if g.state_before_frightened is not None:
                            g.state = g.state_before_frightened
                            g.state_before_frightened = None
                        else:
                            g.state = (
                                STATE_SCATTER
                                if self.global_mode_scatter
                                else STATE_CHASE
                            )

        # Update Ghosts
        for g in self.ghosts:
            self.update_ghost_ai(g)
            self.move_entity(g)

            # Collision
            dist_sq = (g.x - self.pacman.x) ** 2 + (g.y - self.pacman.y) ** 2
            if dist_sq < 0.5:  # Collision radius
                if g.state == STATE_FRIGHTENED:
                    g.state = STATE_DEAD
                    g.color = COLOR_GHOST_EYES  # Show as "eyes" when dead
                    # Progressive points: 200, 400, 800, 1600
                    ghost_points = 200 * (2**self.ghosts_eaten_combo)
                    self.pacman.score += ghost_points
                    self.ghosts_eaten_combo += 1

                elif g.state == STATE_DEAD:
                    pass
                else:
                    # Pacman dies
                    self.pacman.lives -= 1
                    if self.pacman.lives <= 0:
                        self.game_over = True
                    else:
                        self.soft_reset()

            # Check level complete
            if self.pellets_remaining <= 0:
                # Bonus points for completing level
                self.pacman.score += 1000
                # Advance to next map
                self.reset_level(next_map=True)

    def soft_reset(self):
        # Clear old entity positions before reset
        entities = [self.pacman] + self.ghosts
        for e in entities:
            self.clear_entity_area(e)

        # Force full redraw after reset to clean up any remaining artifacts
        self.walls_drawn = False

        # Reset positions
        self.pacman.x, self.pacman.y = self.pacman_start
        self.pacman.dir = DIR_NONE

        # Reset ghosts with dynamic positions based on current map
        self.ghosts = []
        house_x, house_y = self.ghost_house_center
        exit_x, exit_y = self.ghost_house_exit

        # Blinky (Red) starts outside (at exit point)
        blinky = Ghost(exit_x, exit_y, COLOR_GHOST_RED, GHOST_BLINKY)
        blinky.in_house = False
        blinky.house_timer = 0
        self.ghosts.append(blinky)

        # Pinky (Pink) inside center - exits after 5 seconds
        pinky = Ghost(house_x, house_y, COLOR_GHOST_PINK, GHOST_PINKY)
        pinky.in_house = True
        pinky.house_timer = 5 * TARGET_FPS
        self.ghosts.append(pinky)

        # Inky (Cyan) inside left - exits after 10 seconds
        inky = Ghost(house_x - 2, house_y, COLOR_GHOST_CYAN, GHOST_INKY)
        inky.in_house = True
        inky.house_timer = 10 * TARGET_FPS
        self.ghosts.append(inky)

        # Clyde (Orange) inside right - exits after 15 seconds
        clyde = Ghost(house_x + 2, house_y, COLOR_GHOST_ORANGE, GHOST_CLYDE)
        clyde.in_house = True
        clyde.house_timer = 15 * TARGET_FPS
        self.ghosts.append(clyde)

        self.scared_timer = 0

    def draw_ui(self):
        """Draw UI elements (score, lives, etc.)"""
        ui_x = 420  # Place UI to the right of the map
        ui_y = 20

        # Clear entire UI area first to prevent text overlap
        ui_width = 180  # Width of UI area
        ui_height = 210  # Height of UI area (increased for LEVEL display)
        self.display.fill_rect(ui_x - 5, ui_y - 5, ui_width, ui_height, COLOR_BLACK)

        # Always draw all UI elements (full redraw approach)
        draw_text(self.display, "SCORE", ui_x, ui_y, COLOR_UI_TEXT)
        draw_text(self.display, str(self.pacman.score), ui_x, ui_y + 20, COLOR_WHITE)

        draw_text(self.display, "HIGH SCORE", ui_x, ui_y + 50, COLOR_UI_TEXT)
        current_high = max(self.high_score, self.pacman.score)
        draw_text(self.display, str(current_high), ui_x, ui_y + 70, COLOR_WHITE)

        draw_text(self.display, "LIVES", ui_x, ui_y + 110, COLOR_UI_TEXT)

        # Draw lives as pacman icons
        for i in range(self.pacman.lives):
            self.display.fill_circle(ui_x + 8 + i * 20, ui_y + 135, 7, COLOR_PACMAN)

        # Draw current map/level
        draw_text(self.display, "LEVEL", ui_x, ui_y + 160, COLOR_UI_TEXT)
        map_names = ["PAC-MAN", "MS.PAC 1", "MS.PAC 2", "MS.PAC 3", "MS.PAC 4"]
        level_name = map_names[self.current_map_index]
        draw_text(self.display, level_name, ui_x, ui_y + 180, COLOR_PACMAN)

    def clear_entity_area(self, entity):
        """Clear area where entity was in pixels, then restore background tiles"""
        # Entity radius is 7 pixels, add margin for safety
        radius = 9

        # Calculate pixel coordinates
        prev_px = int(entity.prev_x * TILE_SIZE + MAP_OFFSET_X + TILE_SIZE / 2)
        prev_py = int(entity.prev_y * TILE_SIZE + MAP_OFFSET_Y + TILE_SIZE / 2)

        # Clear circular area in pixels
        clear_x = prev_px - radius
        clear_y = prev_py - radius
        clear_size = radius * 2

        # Clear the rectangular area containing the circle
        self.display.fill_rect(clear_x, clear_y, clear_size, clear_size, COLOR_BLACK)

        # Now restore any tiles that overlap with this area
        min_gx = max(0, int(entity.prev_x - 1.0))
        max_gx = min(self.width - 1, int(entity.prev_x + 1.0))
        min_gy = max(0, int(entity.prev_y - 1.0))
        max_gy = min(self.height - 1, int(entity.prev_y + 1.0))

        for gy in range(min_gy, max_gy + 1):
            for gx in range(min_gx, max_gx + 1):
                char = self.grid[gy][gx]
                px = int(gx * TILE_SIZE + MAP_OFFSET_X)
                py = int(gy * TILE_SIZE + MAP_OFFSET_Y)

                # Restore walls/doors (static elements)
                if char == CHAR_WALL:
                    self.display.fill_rect(px, py, TILE_SIZE, TILE_SIZE, COLOR_WALL)
                    self.display.fill_rect(
                        px + 3, py + 3, TILE_SIZE - 6, TILE_SIZE - 6, COLOR_BLACK
                    )
                elif char == CHAR_DOOR:
                    self.display.fill_rect(px, py + 6, TILE_SIZE, 2, COLOR_GHOST_PINK)
                # Restore pellets
                elif char == CHAR_PELLET:
                    self.display.fill_rect(px + 6, py + 6, 2, 2, COLOR_PELLET)
                elif char == CHAR_POWER:
                    self.display.fill_circle(px + 7, py + 7, 5, COLOR_POWER)

    def draw(self):
        """Dirty regions optimization - walls once, entities every frame"""
        gc.collect()

        entities = [self.pacman] + self.ghosts

        # First frame - draw everything
        if not self.walls_drawn:
            self.display.fill_color(COLOR_BLACK)

            # Draw all tiles
            for y in range(self.height):
                for x in range(self.width):
                    char = self.grid[y][x]
                    px = int(x * TILE_SIZE + MAP_OFFSET_X)
                    py = int(y * TILE_SIZE + MAP_OFFSET_Y)

                    if char == CHAR_WALL:
                        self.display.fill_rect(px, py, TILE_SIZE, TILE_SIZE, COLOR_WALL)
                        self.display.fill_rect(
                            px + 3, py + 3, TILE_SIZE - 6, TILE_SIZE - 6, COLOR_BLACK
                        )
                    elif char == CHAR_DOOR:
                        self.display.fill_rect(
                            px, py + 6, TILE_SIZE, 2, COLOR_GHOST_PINK
                        )
                    elif char == CHAR_PELLET:
                        self.display.fill_rect(px + 6, py + 6, 2, 2, COLOR_PELLET)
                    elif char == CHAR_POWER:
                        self.display.fill_circle(px + 7, py + 7, 5, COLOR_POWER)

            self.draw_ui()

            for e in entities:
                px, py = e.get_pixel_pos()
                if isinstance(e, Pacman):
                    self.display.fill_circle(px, py, 7, e.color)
                elif isinstance(e, Ghost):
                    if e.state == STATE_DEAD:
                        self.display.circle(px, py, 6, COLOR_GHOST_EYES)
                        self.display.fill_circle(px - 2, py - 1, 1, COLOR_WHITE)
                        self.display.fill_circle(px + 2, py - 1, 1, COLOR_WHITE)
                    elif e.state == STATE_FRIGHTENED:
                        if (self.scared_timer < 60) and (
                            (self.scared_timer // 5) % 2 == 0
                        ):
                            self.display.fill_circle(px, py, 7, COLOR_WHITE)
                        else:
                            self.display.fill_circle(px, py, 7, COLOR_GHOST_SCARED)
                    else:
                        self.display.fill_circle(px, py, 7, e.color)

            self.display.swap_buffers()
            self.walls_drawn = True
            return

        # Subsequent frames - only clear/redraw entity areas (dirty regions!)
        for e in entities:
            self.clear_entity_area(e)

        # Redraw UI
        self.draw_ui()

        # Draw entities at new positions
        for e in entities:
            px, py = e.get_pixel_pos()

            if isinstance(e, Pacman):
                self.display.fill_circle(px, py, 7, e.color)
            elif isinstance(e, Ghost):
                if e.state == STATE_DEAD:
                    self.display.circle(px, py, 6, COLOR_GHOST_EYES)
                    self.display.fill_circle(px - 2, py - 1, 1, COLOR_WHITE)
                    self.display.fill_circle(px + 2, py - 1, 1, COLOR_WHITE)
                elif e.state == STATE_FRIGHTENED:
                    if (self.scared_timer < 60) and ((self.scared_timer // 5) % 2 == 0):
                        self.display.fill_circle(px, py, 7, COLOR_WHITE)
                    else:
                        self.display.fill_circle(px, py, 7, COLOR_GHOST_SCARED)
                else:
                    self.display.fill_circle(px, py, 7, e.color)

        # Swap buffers - driver auto-tracks dirty regions with fixed chunk size!
        self.display.swap_buffers()

    def draw_welcome(self):
        self.display.fill_color(COLOR_BLACK)
        w = self.display.width
        h = self.display.height

        title = "PAC-MAN"
        t_w = text_width(title)
        draw_text(self.display, title, (w - t_w) // 2, h // 2 - 40, COLOR_PACMAN)

        sub = "CLICK OR SWIPE TO PLAY"
        s_w = text_width(sub)
        draw_text(self.display, sub, (w - s_w) // 2, h // 2 + 20, COLOR_WHITE)

        self.display.swap_buffers()

    def draw_game_over(self):
        # Clear entire screen to remove all previous content
        self.display.fill_color(COLOR_BLACK)

        w = self.display.width
        h = self.display.height

        # Center box (larger to fit score info)
        bx, by = w // 2 - 140, h // 2 - 80
        box_w, box_h = 280, 160
        self.display.rect(bx, by, box_w, box_h, COLOR_GHOST_RED)

        # "GAME OVER" text
        txt = "GAME OVER"
        tw = text_width(txt)
        draw_text(self.display, txt, (w - tw) // 2, by + 20, COLOR_GHOST_RED)

        # Display score
        score_txt = f"SCORE: {self.pacman.score}"
        score_tw = text_width(score_txt)
        score_x = (w - score_tw) // 2
        score_y = by + 50
        draw_text(self.display, score_txt, score_x, score_y, COLOR_PELLET)

        # Display high score if beaten
        high_y = by + 70
        if self.pacman.score > self.previous_high_score:
            new_high_txt = "NEW HIGH SCORE!"
            new_high_tw = text_width(new_high_txt)
            new_high_x = (w - new_high_tw) // 2
            draw_text(self.display, new_high_txt, new_high_x, high_y, COLOR_POWER)
        else:
            high_txt = f"HIGH: {self.high_score}"
            high_tw = text_width(high_txt)
            high_x = (w - high_tw) // 2
            draw_text(self.display, high_txt, high_x, high_y, COLOR_WHITE)

        # Instruction text (two lines)
        instr_txt1 = "TAP OR PRESS"
        instr_tw1 = text_width(instr_txt1)
        draw_text(
            self.display,
            instr_txt1,
            (w - instr_tw1) // 2,
            by + 105,
            COLOR_GHOST_CYAN,
        )

        instr_txt2 = "TO CONTINUE"
        instr_tw2 = text_width(instr_txt2)
        draw_text(
            self.display,
            instr_txt2,
            (w - instr_tw2) // 2,
            by + 125,
            COLOR_GHOST_CYAN,
        )

        self.display.swap_buffers()


def main():
    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0

    # Input Init
    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)

    joystick = None
    touch = None

    try:
        joystick = JoystickInput(i2c)
        print("Joystick initialized")
    except Exception as e:
        print("Joystick init failed:", e)

    try:
        touch = TouchInput(i2c)
        print("Touch initialized")
    except Exception as e:
        print("Touch init failed:", e)

    if not joystick and not touch:
        print("No input devices found!")
        return

    # Helper to check all inputs
    def get_combined_input():
        d = DIR_NONE
        if joystick:
            d = joystick.get_input()
        if d == DIR_NONE and touch:
            d = touch.get_input()
        return d

    def check_start():
        if joystick and joystick.check_center():
            return True
        if touch and touch.check_center():
            return True
        return False

    game = Game(display, None)

    try:
        while True:
        # Welcome Screen
        game.draw_welcome()

        # Wait for inputs to be released (debounce)
        # We loop until no inputs are detected
        while check_start() or get_combined_input() != DIR_NONE:
            time.sleep(0.1)

        # Wait for input to start
        start = False
        while not start:
            if check_start():
                start = True
            elif get_combined_input() != DIR_NONE:
                start = True
            time.sleep(0.05)

        # Play Game
        game.previous_high_score = (
            game.high_score
        )  # Remember high score before this game
        game.reset_level()
        game.pacman.score = 0
        game.pacman.lives = 3

        last_time = time.monotonic()

        while not game.game_over:
            now = time.monotonic()
            dt = now - last_time
            if dt > 0.033:  # 30 FPS cap
                last_time = now

                # Input
                inp = get_combined_input()
                if inp != DIR_NONE:
                    game.pacman.next_dir = inp

                game.update()
                game.draw()

        # Game Over
        if game.pacman.score > game.high_score:
            game.high_score = game.pacman.score

        game.draw_game_over()

        # Wait for inputs to be released (debounce)
        while check_start() or get_combined_input() != DIR_NONE:
            time.sleep(0.1)

        # Wait for any input to continue
        waiting = True
        while waiting:
            if check_start():
                waiting = False
            elif get_combined_input() != DIR_NONE:
                waiting = False
            time.sleep(0.05)

            # Loop back to welcome

    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"\nGame crashed: {e}")
    finally:
        print("Cleaning up display...")
        display.fill_color(0x0000)
        display.swap_buffers()
        display.deinit()
        try:
            i2c.deinit()
        except:
            pass
        print("Pac-Man exited")


if __name__ == "__main__":
    main()
