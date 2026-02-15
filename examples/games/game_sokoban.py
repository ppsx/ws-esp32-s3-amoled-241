# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Sokoban Game for Waveshare ESP32-S3 Touch AMOLED 2.41
Based on Bansoko levels.
"""

BASE_DIR = "/games"

import sys
import time
import board
import busio
import rm690b0
import math

try:
    import adafruit_focaltouch
except ImportError:
    adafruit_focaltouch = None

try:
    from sokoban.levels import LEVELS
except ImportError:
    if __file__ == "<stdin>":
        path = BASE_DIR
    else:
        path = "/" + __file__.rsplit("/", 1)[0] if "/" in __file__ else ""
    sys.path.insert(0, path)
    from sokoban.levels import LEVELS

# ---------------------------------------------------------------------------
# Hardware & Configuration
# ---------------------------------------------------------------------------
PCA9554_ADDR = 0x21
REG_INPUT_PORT = 0x00
REG_OUTPUT_PORT = 0x01
REG_CONFIG = 0x03

PIN_UP = 0
PIN_DOWN = 1
PIN_RIGHT = 2
PIN_LEFT = 3
PIN_CENTER = 4

# Colors (RGB565)
def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

FONT_SMALL = rm690b0.FONT_16x16
FONT_LARGE = rm690b0.FONT_24x24

# Modern/Arcade Palette
BG_COLOR = rgb565(20, 20, 28)       # Deep Dark Blue
FLOOR_COLOR = rgb565(45, 45, 55)    # Slate floor

# Wall: Brick Red/Brown style
WALL_FACE = rgb565(160, 80, 60)
WALL_LIGHT = rgb565(200, 120, 100)
WALL_DARK = rgb565(100, 40, 30)

# Crate: Wood style
CRATE_FACE = rgb565(210, 180, 130)
CRATE_LIGHT = rgb565(240, 220, 160)
CRATE_DARK = rgb565(140, 100, 50)

# Crate on Goal: Greenish Wood
CRATE_GOAL_FACE = rgb565(100, 200, 100)
CRATE_GOAL_LIGHT = rgb565(150, 250, 150)
CRATE_GOAL_DARK = rgb565(50, 150, 50)

# Player: Cute Blue Character
PLAYER_BODY = rgb565(0, 150, 255)
GOAL_COLOR = rgb565(255, 60, 60)
TEXT_COLOR = rm690b0.WHITE
FLOOR_DOT = rgb565(60, 60, 70)
MENU_SHADOW = rgb565(10, 10, 10)
MENU_BG = rgb565(30, 30, 40)
MENU_SEL = rgb565(60, 60, 80)

# Directions
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

# ---------------------------------------------------------------------------
# Input Classes (Reused from Snake/Pacman)
# ---------------------------------------------------------------------------

class PCA9554:
    def __init__(self, i2c, address=PCA9554_ADDR):
        self.i2c = i2c
        self.address = address
        try:
            self._read_register(REG_INPUT_PORT)
        except Exception as e:
            raise RuntimeError(f"PCA9554 not found at 0x{address:02X}: {e}")

    def _read_register(self, register):
        while not self.i2c.try_lock():
            pass
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
    def __init__(self, i2c):
        self.pca = PCA9554(i2c, PCA9554_ADDR)
        self.pca.configure_pins(0b00011111)
        self.pca.write_outputs(0b11100000) # LED off
        self._last_state = {}
        self._last_press_time = 0
        self._repeat_delay = 0.2

    def read_switches(self):
        val = self.pca.read_inputs()
        return {
            "up": not bool(val & (1 << PIN_UP)),
            "down": not bool(val & (1 << PIN_DOWN)),
            "left": not bool(val & (1 << PIN_LEFT)),
            "right": not bool(val & (1 << PIN_RIGHT)),
            "center": not bool(val & (1 << PIN_CENTER)),
        }

    def get_action(self):
        switches = self.read_switches()
        now = time.monotonic()
        
        # Debounce/Repeat logic could be simpler for sokoban
        # Just return the first pressed direction
        if switches["up"]: return DIR_UP
        if switches["down"]: return DIR_DOWN
        if switches["left"]: return DIR_LEFT
        if switches["right"]: return DIR_RIGHT
        return None

    def is_center_pressed(self):
        return self.read_switches()["center"]

class TouchInput:
    def __init__(self, i2c):
        if adafruit_focaltouch is None:
            raise RuntimeError("adafruit_focaltouch required")
        self.i2c = i2c
        self.touch = adafruit_focaltouch.Adafruit_FocalTouch(self.i2c)
        self.start_x = 0
        self.start_y = 0
        self.is_swiping = False
        self.last_tap_time = 0

    def get_action(self):
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
            
        raw_x = points[0]["x"]
        raw_y = points[0]["y"]
        x = 600 - raw_y
        y = raw_x
        
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
        if self.touch.touched and not self.is_swiping:
            now = time.monotonic()
            if now - self.last_tap_time > 0.5:
                self.last_tap_time = now
                return True
        return False

# ---------------------------------------------------------------------------
# Game Logic
# ---------------------------------------------------------------------------

class SokobanGame:
    def __init__(self, level_str_list):
        self.rows = len(level_str_list)
        self.cols = max(len(row) for row in level_str_list)
        self.walls = set()
        self.goals = set()
        self.crates = set()
        self.player = (0, 0)
        self.moves = 0
        self.pushes = 0
        self.history = []
        self.anim = None # Animation state
        self.ANIM_DURATION = 0.20 # Seconds

        
        # Parse level
        for r, row in enumerate(level_str_list):
            for c, char in enumerate(row):
                pos = (c, r)
                if char == 'X':
                    self.walls.add(pos)
                elif char == '+':
                    self.goals.add(pos)
                elif char == '#':
                    self.crates.add(pos)
                elif char == '&':
                    self.goals.add(pos)
                    self.crates.add(pos)
                elif char == '@':
                    self.player = pos
                # ' ' is floor, implied not wall
                
    def width(self): return self.cols
    def height(self): return self.rows
    
    def is_wall(self, pos):
        return pos in self.walls
        
    def update(self):
        """Update animation state. Returns True if animating."""
        if not self.anim:
            return False
            
        now = time.monotonic()
        progress = (now - self.anim['start_time']) / self.ANIM_DURATION
        self.anim['progress'] = min(1.0, progress)
        
        if progress >= 1.0:
            self.finalize_move()
            self.anim = None
            return False
        return True

    def move(self, d):
        if self.anim: return False # Block input while animating
        
        dx, dy = d
        px, py = self.player
        new_pos = (px + dx, py + dy)
        
        if self.is_wall(new_pos):
            return False
            
        if new_pos in self.crates:
            new_crate_pos = (new_pos[0] + dx, new_pos[1] + dy)
            if self.is_wall(new_crate_pos) or new_crate_pos in self.crates:
                return False
                
            # Start Push Anim
            self.anim = {
                'type': 'push',
                'dir': d,
                'start_time': time.monotonic(),
                'progress': 0.0,
                'p_from': self.player,
                'p_to': new_pos,
                'c_from': new_pos,
                'c_to': new_crate_pos
            }
            return True
        else:
            # Start Move Anim
            self.anim = {
                'type': 'move',
                'dir': d,
                'start_time': time.monotonic(),
                'progress': 0.0,
                'p_from': self.player,
                'p_to': new_pos,
                'c_from': None
            }
            return True

    def finalize_move(self):
        anim = self.anim
        d = anim['dir']
        
        if anim['type'] == 'push':
             self.history.append({'type': 'push', 'dir': d, 'crate_from': anim['c_from'], 'crate_to': anim['c_to'], 'player_from': anim['p_from']})
             self.crates.remove(anim['c_from'])
             self.crates.add(anim['c_to'])
             self.player = anim['p_to']
             self.moves += 1
             self.pushes += 1
        else:
             self.history.append({'type': 'move', 'dir': d, 'player_from': anim['p_from']})
             self.player = anim['p_to']
             self.moves += 1
            
    def undo(self):
        if not self.history:
            return False
        action = self.history.pop()
        self.player = action['player_from']
        if action['type'] == 'push':
            self.crates.remove(action['crate_to'])
            self.crates.add(action['crate_from'])
            self.pushes -= 1
        self.moves -= 1
        return True
        
    def is_solved(self):
        return self.crates == self.goals

# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def draw_3d_rect(display, x, y, size, c_face, c_light, c_dark):
    display.fill_rect(x, y, size, size, c_face)
    b = max(1, size // 8)
    # Top/Left Highlight
    display.fill_rect(x, y, size, b, c_light)
    display.fill_rect(x, y, b, size, c_light)
    # Bottom/Right Shadow
    display.fill_rect(x, y+size-b, size, b, c_dark)
    display.fill_rect(x+size-b, y, b, size, c_dark)

def draw_wall(display, x, y, size):
    draw_3d_rect(display, x, y, size, WALL_FACE, WALL_LIGHT, WALL_DARK)
    # Brick detail
    mid = size // 2
    display.fill_rect(x, y + mid, size, 1, WALL_DARK) # Horiz line
    display.fill_rect(x + mid, y, 1, mid, WALL_DARK)   # Vert top
    display.fill_rect(x + mid//2, y + mid, 1, mid, WALL_DARK) # Vert bottom skewed

def draw_crate(display, x, y, size, on_goal):
    cf = CRATE_GOAL_FACE if on_goal else CRATE_FACE
    cl = CRATE_GOAL_LIGHT if on_goal else CRATE_LIGHT
    cd = CRATE_GOAL_DARK if on_goal else CRATE_DARK
    
    inset = 2
    draw_3d_rect(display, x+inset, y+inset, size-2*inset, cf, cl, cd)
    # Detail: Inner box
    inner = size // 3
    off = (size - inner) // 2
    display.rect(x+off, y+off, inner, inner, cd)

def draw_player(display, x, y, size, ticks=0):
    cx, cy = x + size//2, y + size//2
    r = size // 2 - 1
    display.fill_circle(cx, cy, r, PLAYER_BODY)
    
    # Eyes
    eye_r = max(1, size // 5)
    eye_off = size // 4
    
    # Blinking logic
    blink = False
    if ticks > 0:
        # Blink every 4 seconds for 0.15s
        if (ticks % 4.0) < 0.15:
            blink = True
            
    if blink:
        # Closed eyes (line)
        ey = cy - size//6
        w = eye_r * 2
        display.fill_rect(cx - eye_off - eye_r, ey, w, 2, rm690b0.BLACK)
        display.fill_rect(cx + eye_off - eye_r, ey, w, 2, rm690b0.BLACK)
    else:
        # Whites
        display.fill_circle(cx - eye_off, cy - size//6, eye_r, rm690b0.WHITE)
        display.fill_circle(cx + eye_off, cy - size//6, eye_r, rm690b0.WHITE)
        # Pupils
        p_r = max(1, eye_r // 2)
        display.fill_circle(cx - eye_off, cy - size//6, p_r, rm690b0.BLACK)
        display.fill_circle(cx + eye_off, cy - size//6, p_r, rm690b0.BLACK)

def draw_cell(display, game, x, y, offset_x, offset_y, cell_size, ticks=0):
    pos = (x, y)
    px = offset_x + x * cell_size
    py = offset_y + y * cell_size
    
    # Background for cell (Floor or Wall base)
    if pos in game.walls:
        draw_wall(display, px, py, cell_size)
        return # Walls obscure everything
    else:
        display.fill_rect(px, py, cell_size, cell_size, FLOOR_COLOR)
        # Floor detail? dot in corners?
        display.fill_rect(px, py, 1, 1, FLOOR_DOT)
    
    # Goal
    if pos in game.goals and pos not in game.crates and pos != game.player:
         cx = px + cell_size//2
         cy = py + cell_size//2
         # Pulse logic
         pulse = (math.sin(ticks * 5) + 1) / 2 # 0..1
         r_base = cell_size // 5
         r = r_base + int(pulse * 2)
         
         # X mark for goal
         display.fill_circle(cx, cy, r, GOAL_COLOR)
         display.fill_circle(cx, cy, r-2, FLOOR_COLOR) # Ring effect
         display.fill_circle(cx, cy, 2, GOAL_COLOR) # Center dot
         
    # Crate
    if pos in game.crates:
        # If animating push, skip drawing the crate at its starting position (we draw it moving)
        if game.anim and game.anim['type'] == 'push' and pos == game.anim['c_from']:
            pass
        else:
            draw_crate(display, px, py, cell_size, pos in game.goals)
        
    # Player
    if pos == game.player:
        # If animating, skip drawing static player
        if game.anim:
            pass 
        else:
            draw_player(display, px, py, cell_size, ticks)

def draw_game(display, game, offset_x, offset_y, cell_size, ticks=0):
    
    # Draw centered grid background
    width_px = game.cols * cell_size
    height_px = game.rows * cell_size
    
    # Draw all cells
    for r in range(game.rows):
        for c in range(game.cols):
            draw_cell(display, game, c, r, offset_x, offset_y, cell_size, ticks)
            
    # Draw animated entities on top
    if game.anim:
        anim = game.anim
        progress = anim['progress']
        # Helper interp
        def get_px(pos_from, pos_to):
            x = pos_from[0] + (pos_to[0] - pos_from[0]) * progress
            y = pos_from[1] + (pos_to[1] - pos_from[1]) * progress
            return int(offset_x + x * cell_size), int(offset_y + y * cell_size)
            
        # Draw Crate if pushing
        if anim['type'] == 'push':
            cx, cy = get_px(anim['c_from'], anim['c_to'])
            # Determine if target is a goal for color? 
            # It's tricky because visual transition logic. 
            # We use goal status of TARGET if progress > 0.5? Or simply checking if 'c_to' is goal?
            # Let's keep it simple: check if c_to is goal
            on_goal = anim['c_to'] in game.goals
            draw_crate(display, cx, cy, cell_size, on_goal)
            
        # Draw Player
        px, py = get_px(anim['p_from'], anim['p_to'])
        draw_player(display, px, py, cell_size, ticks)

def draw_menu(display, items, selected_idx):
    w, h = display.width, display.height
    
    # Calculate menu dimensions based on items
    item_h = 40
    menu_h = len(items) * item_h + 40
    menu_w = 450

    mx = (w - menu_w) // 2
    my = (h - menu_h) // 2

    # Shadow
    display.fill_rect(mx + 5, my + 5, menu_w, menu_h, MENU_SHADOW)

    # Background
    display.fill_rect(mx, my, menu_w, menu_h, MENU_BG)

    # Border (Double)
    display.rect(mx, my, menu_w, menu_h, rm690b0.WHITE)
    display.rect(mx+2, my+2, menu_w-4, menu_h-4, rm690b0.WHITE)

    # Title or Separator
    display.hline(mx, my + 10, menu_w, rm690b0.WHITE)

    for i, item in enumerate(items):
        y = my + 20 + i * item_h

        # Selection Bar
        if i == selected_idx:
            display.fill_rect(mx + 10, y, menu_w - 20, item_h - 4, MENU_SEL)
            color = rm690b0.GREEN
            prefix = "> "
        else:
            color = rm690b0.WHITE
            prefix = "  "

        display.set_font(FONT_LARGE)
        # Center text
        text = prefix + item
        # Approx width for centering (24x24 font -> ~12-14px char width avg?)
        # Let's just align left with padding
        display.text(mx + 30, y + 4, text, color=color)

def main():
    print("Sokoban starting...")
    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0

    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)
    joystick = None
    touch = None

    try:
        joystick = JoystickInput(i2c)
    except Exception as e:
        print(f"Joystick init error: {e}")

    try:
        touch = TouchInput(i2c)
    except Exception as e:
        print(f"Touch init error: {e}")

    level_idx = 0
    game = None

    def load_level(idx):
        if idx < 0: idx = len(LEVELS) - 1
        if idx >= len(LEVELS): idx = 0
        return idx, SokobanGame(LEVELS[idx])

    level_idx, game = load_level(level_idx)

    try:
        cell_size = 20  # Base size, maybe scale?
        # Max dims: 450x600 (portrait) or 600x450 (landscape)
        # Most levels are small, some are large.
        # Map 62 is 27x19. 600/27 = 22px.
        # Let's verify screen orientation. Snake uses 600 width logic.
        width = display.width # 600?
        height = display.height # 450?

        menu_items = ["RESUME", "UNDO", "RESET", "NEXT LEVEL", "PREV LEVEL", "EXIT"]
        menu_open = False
        menu_sel = 0

        last_act_time = 0
        act_delay = 0.15 # Repeat rate
        solved_timestamp = None
        needs_redraw = True
        bg_dirty = True

        while True:
            # Animation update
            was_animating = game.anim is not None
            animating = game.update()
            if animating or was_animating:
                needs_redraw = True

            # Calculate scaling
            max_w = display.width - 20
            max_h = display.height - 20
            scale_w = max_w // game.cols
            scale_h = max_h // game.rows
            cell_size = min(scale_w, scale_h)
            if cell_size > 40: cell_size = 40

            offset_x = (display.width - game.cols * cell_size) // 2
            offset_y = (display.height - game.rows * cell_size) // 2

            # Drawing (only when needed)
            if needs_redraw:
                if bg_dirty:
                    display.fill_color(BG_COLOR)
                    bg_dirty = False
                if menu_open:
                    draw_menu(display, menu_items, menu_sel)
                else:
                    draw_game(display, game, offset_x, offset_y, cell_size, time.monotonic())
                    display.set_font(FONT_SMALL)
                    display.fill_rect(10, 10, 400, 36, BG_COLOR)
                    display.text(10, 10, f"Level {level_idx+1}/{len(LEVELS)}", color=TEXT_COLOR)
                    display.text(10, 30, f"Moves: {game.moves} Pushes: {game.pushes}", color=TEXT_COLOR)
                    if game.is_solved():
                        display.set_font(FONT_LARGE)
                        display.text(display.width // 2 - 60, display.height // 2, "SOLVED!", color=rm690b0.GREEN)
                display.swap_buffers(copy=True)
                needs_redraw = False
            else:
                time.sleep(0.01)

            # Input Handling
            d = None
            center = False

            if joystick:
                d = joystick.get_action()
                if joystick.is_center_pressed():
                    center = True

            if not d and not center and touch:
                d = touch.get_action()
                if touch.is_center_pressed():
                    center = True

            now = time.monotonic()
            if now - last_act_time < act_delay:
                continue

            if center:
                last_act_time = now
                needs_redraw = True
                if game.is_solved() and not menu_open:
                    level_idx, game = load_level(level_idx + 1)
                    bg_dirty = True
                    solved_timestamp = None
                elif not menu_open:
                    menu_open = True
                    menu_sel = 0
                else:
                    item = menu_items[menu_sel]
                    if item == "RESUME":
                        menu_open = False
                        bg_dirty = True
                    elif item == "UNDO":
                        game.undo()
                        menu_open = False
                        bg_dirty = True
                    elif item == "RESET":
                        _, game = load_level(level_idx)
                        menu_open = False
                        bg_dirty = True
                    elif item == "NEXT LEVEL":
                        level_idx, game = load_level(level_idx + 1)
                        menu_open = False
                        bg_dirty = True
                    elif item == "PREV LEVEL":
                        level_idx, game = load_level(level_idx - 1)
                        menu_open = False
                        bg_dirty = True
                    elif item == "EXIT":
                        break

            elif menu_open:
                if d == DIR_UP:
                    menu_sel = (menu_sel - 1) % len(menu_items)
                    last_act_time = now
                    needs_redraw = True
                elif d == DIR_DOWN:
                    menu_sel = (menu_sel + 1) % len(menu_items)
                    last_act_time = now
                    needs_redraw = True

            elif game.is_solved():
                pass

            elif d:
                if game.move(d):
                    last_act_time = now

            # Auto-advance logic
            if game.is_solved():
                if solved_timestamp is None:
                    solved_timestamp = time.monotonic()
                elif time.monotonic() - solved_timestamp > 2.0:
                    level_idx, game = load_level(level_idx + 1)
                    needs_redraw = True
                    bg_dirty = True
                    solved_timestamp = None
            else:
                solved_timestamp = None

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
        print("Sokoban exited")

if __name__ == "__main__":
    main()
