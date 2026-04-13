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
# Colors (RGB565)
def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

FONT_SMALL = rm690b0.FONT_16x16
FONT_LARGE = rm690b0.FONT_24x24

# Modern/Arcade Palette
BG_COLOR = 0x0000                  # Black
FLOOR_COLOR = 0x0000                 # Black floor

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
FLOOR_DOT = 0x0000
MENU_SHADOW = rgb565(10, 10, 10)
MENU_BG = rgb565(30, 30, 40)
MENU_SEL = rgb565(60, 60, 80)

# Directions
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

# ---------------------------------------------------------------------------
# Joystick helpers (wrapping shared joystick module)
# ---------------------------------------------------------------------------

def joystick_get_action(js):
    """Read joystick and return direction tuple or None."""
    switches = js.read()
    if switches["up"]: return DIR_UP
    if switches["down"]: return DIR_DOWN
    if switches["left"]: return DIR_LEFT
    if switches["right"]: return DIR_RIGHT
    return None

def joystick_is_center_pressed(js):
    """Return True if center button is pressed."""
    return js.read()["center"]

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

def goal_radius(cell_size):
    return max(2, cell_size // 5 + 1)


def draw_cell(display, game, x, y, offset_x, offset_y, cell_size, ticks=0):
    pos = (x, y)
    px = offset_x + x * cell_size
    py = offset_y + y * cell_size

    if pos in game.walls:
        draw_wall(display, px, py, cell_size)
        return

    display.fill_rect(px, py, cell_size, cell_size, FLOOR_COLOR)

    if pos in game.goals and pos not in game.crates and pos != game.player:
        cx = px + cell_size // 2
        cy = py + cell_size // 2
        r = goal_radius(cell_size)
        display.fill_circle(cx, cy, r, GOAL_COLOR)
        display.fill_circle(cx, cy, max(0, r - 2), FLOOR_COLOR)
        display.fill_circle(cx, cy, 2, GOAL_COLOR)

    if pos in game.crates:
        if not (game.anim and game.anim['type'] == 'push' and pos == game.anim['c_from']):
            draw_crate(display, px, py, cell_size, pos in game.goals)

    if pos == game.player and not game.anim:
        draw_player(display, px, py, cell_size, ticks)


def draw_cells(display, game, cells, offset_x, offset_y, cell_size, ticks=0):
    for c, r in cells:
        if 0 <= c < game.cols and 0 <= r < game.rows:
            draw_cell(display, game, c, r, offset_x, offset_y, cell_size, ticks)


def draw_anim_entities(display, game, offset_x, offset_y, cell_size, ticks=0):
    if not game.anim:
        return

    anim = game.anim
    progress = anim['progress']

    def get_px(pos_from, pos_to):
        x = pos_from[0] + (pos_to[0] - pos_from[0]) * progress
        y = pos_from[1] + (pos_to[1] - pos_from[1]) * progress
        return int(offset_x + x * cell_size), int(offset_y + y * cell_size)

    if anim['type'] == 'push':
        cx, cy = get_px(anim['c_from'], anim['c_to'])
        draw_crate(display, cx, cy, cell_size, anim['c_to'] in game.goals)

    px, py = get_px(anim['p_from'], anim['p_to'])
    draw_player(display, px, py, cell_size, ticks)


def draw_game(display, game, offset_x, offset_y, cell_size, ticks=0):
    all_cells = ((c, r) for r in range(game.rows) for c in range(game.cols))
    draw_cells(display, game, all_cells, offset_x, offset_y, cell_size, ticks)
    draw_anim_entities(display, game, offset_x, offset_y, cell_size, ticks)


def get_anim_cells(game):
    if not game.anim:
        return set()
    cells = {game.anim['p_from'], game.anim['p_to']}
    if game.anim['type'] == 'push':
        cells.add(game.anim['c_from'])
        cells.add(game.anim['c_to'])
    return cells


def compute_layout(display, game):
    max_w = display.width - 20
    max_h = display.height - 20
    scale_w = max_w // game.cols
    scale_h = max_h // game.rows
    cell_size = min(scale_w, scale_h)
    if cell_size > 40:
        cell_size = 40
    offset_x = (display.width - game.cols * cell_size) // 2
    offset_y = (display.height - game.rows * cell_size) // 2
    return cell_size, offset_x, offset_y


def draw_hud(display, level_idx, total_levels, moves, pushes):
    display.set_font(FONT_SMALL)
    display.fill_rect(0, 8, display.width, 22, BG_COLOR)
    display.text(10, 10,
                 f"Level {level_idx+1}/{total_levels}   Moves: {moves}   Pushes: {pushes}",
                 color=TEXT_COLOR)


def draw_solved_banner(display):
    banner_w = 240
    banner_h = 54
    bx = (display.width - banner_w) // 2
    by = (display.height - banner_h) // 2 - 6
    display.fill_rect(bx + 4, by + 4, banner_w, banner_h, MENU_SHADOW)
    display.fill_rect(bx, by, banner_w, banner_h, MENU_BG)
    display.rect(bx, by, banner_w, banner_h, rm690b0.GREEN)
    display.rect(bx + 2, by + 2, banner_w - 4, banner_h - 4, rm690b0.WHITE)
    display.set_font(FONT_LARGE)
    display.text(bx + 44, by + 15, "SOLVED!", color=rm690b0.GREEN)


def draw_start_screen(display):
    title = "SOKOBAN"
    prompt = "Press any key"
    title_x = (display.width - len(title) * 24) // 2
    prompt_x = (display.width - len(prompt) * 16) // 2

    display.fill_color(BG_COLOR)
    display.set_font(4)
    display.text(title_x, 160, title, 0x07E0)
    display.set_font(2)
    display.text(prompt_x, 220, prompt, 0xFFFF)
    display.swap_buffers(copy=True)


def any_start_input(joystick, touch):
    if joystick:
        try:
            if any(joystick.read().values()):
                return True
        except Exception:
            pass
    if touch:
        try:
            return bool(touch.touch.touched)
        except Exception:
            pass
    return False


def wait_for_start(joystick, touch):
    released_since = 0.0
    while True:
        active = any_start_input(joystick, touch)
        now = time.monotonic()
        if not active:
            if released_since == 0.0:
                released_since = now
            elif now - released_since >= 0.15:
                break
        else:
            released_since = 0.0
        time.sleep(0.01)

    pressed_since = 0.0
    while True:
        active = any_start_input(joystick, touch)
        now = time.monotonic()
        if active:
            if pressed_since == 0.0:
                pressed_since = now
            elif now - pressed_since >= 0.06:
                break
        else:
            pressed_since = 0.0
        time.sleep(0.01)

    released_since = 0.0
    while True:
        active = any_start_input(joystick, touch)
        now = time.monotonic()
        if not active:
            if released_since == 0.0:
                released_since = now
            elif now - released_since >= 0.10:
                return
        else:
            released_since = 0.0
        time.sleep(0.01)


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

    # Border
    display.rect(mx, my, menu_w, menu_h, rm690b0.WHITE)

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

def main(display=None):
    print("Sokoban starting...")
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
    draw_start_screen(display)

    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)
    joystick = None
    touch = None

    try:
        from joystick import Joystick
        joystick = Joystick(i2c=i2c)
    except Exception as e:
        print(f"Joystick init error: {e}")

    try:
        touch = TouchInput(i2c)
    except Exception as e:
        print(f"Touch init error: {e}")

    wait_for_start(joystick, touch)

    level_idx = 0
    game = None

    def load_level(idx):
        if idx < 0:
            idx = len(LEVELS) - 1
        if idx >= len(LEVELS):
            idx = 0
        return idx, SokobanGame(LEVELS[idx])

    level_idx, game = load_level(level_idx)

    try:
        menu_items = ["RESUME", "UNDO", "RESET", "NEXT LEVEL", "PREV LEVEL", "EXIT"]
        menu_open = False
        menu_sel = 0

        last_act_time = 0
        act_delay = 0.15
        solved_timestamp = None
        full_redraw = True
        bg_dirty = True
        hud_dirty = True
        dirty_cells = set()
        center_down_since = 0.0
        center_armed = True
        center_debounce = 0.06
        last_solved = game.is_solved()
        cell_size, offset_x, offset_y = compute_layout(display, game)

        while True:
            was_animating = game.anim is not None
            dirty_cells.update(get_anim_cells(game))
            animating = game.update()
            dirty_cells.update(get_anim_cells(game))
            if animating or was_animating:
                full_redraw = False
            if was_animating and not animating:
                hud_dirty = True

            is_solved = game.is_solved()
            if is_solved != last_solved:
                last_solved = is_solved
                full_redraw = True
                bg_dirty = True
                hud_dirty = True
                dirty_cells.clear()

            if bg_dirty or full_redraw or dirty_cells or hud_dirty:
                ticks = time.monotonic()
                if bg_dirty:
                    display.fill_color(BG_COLOR)
                    bg_dirty = False
                    full_redraw = True

                if menu_open:
                    draw_menu(display, menu_items, menu_sel)
                else:
                    if full_redraw:
                        draw_game(display, game, offset_x, offset_y, cell_size, ticks)
                    else:
                        draw_cells(display, game, dirty_cells, offset_x, offset_y, cell_size, ticks)
                        draw_anim_entities(display, game, offset_x, offset_y, cell_size, ticks)

                    if hud_dirty or full_redraw:
                        draw_hud(display, level_idx, len(LEVELS), game.moves, game.pushes)
                        hud_dirty = False

                    if is_solved:
                        draw_solved_banner(display)

                display.swap_buffers(copy=True)
                dirty_cells.clear()
                full_redraw = False
            else:
                time.sleep(0.001)

            d = None
            center_down = False

            if joystick:
                d = joystick_get_action(joystick)
                if joystick_is_center_pressed(joystick):
                    center_down = True

            if not d and not center_down and touch:
                d = touch.get_action()
                if touch.is_center_pressed():
                    center_down = True

            now = time.monotonic()
            if center_down:
                if center_down_since == 0.0:
                    center_down_since = now
                center = center_armed and (now - center_down_since) >= center_debounce
            else:
                center_down_since = 0.0
                center_armed = True
                center = False

            if now - last_act_time < act_delay:
                continue

            if center:
                center_armed = False
                last_act_time = now
                if game.is_solved() and not menu_open:
                    level_idx, game = load_level(level_idx + 1)
                    cell_size, offset_x, offset_y = compute_layout(display, game)
                    menu_open = False
                    bg_dirty = True
                    full_redraw = True
                    hud_dirty = True
                    dirty_cells.clear()
                    solved_timestamp = None
                    last_solved = game.is_solved()
                elif not menu_open:
                    menu_open = True
                    menu_sel = 0
                    full_redraw = True
                    bg_dirty = True
                    dirty_cells.clear()
                else:
                    item = menu_items[menu_sel]
                    if item == "RESUME":
                        menu_open = False
                        bg_dirty = True
                        full_redraw = True
                        dirty_cells.clear()
                    elif item == "UNDO":
                        game.undo()
                        menu_open = False
                        bg_dirty = True
                        full_redraw = True
                        hud_dirty = True
                        dirty_cells.clear()
                        last_solved = game.is_solved()
                    elif item == "RESET":
                        _, game = load_level(level_idx)
                        cell_size, offset_x, offset_y = compute_layout(display, game)
                        menu_open = False
                        bg_dirty = True
                        full_redraw = True
                        hud_dirty = True
                        dirty_cells.clear()
                        solved_timestamp = None
                        last_solved = game.is_solved()
                    elif item == "NEXT LEVEL":
                        level_idx, game = load_level(level_idx + 1)
                        cell_size, offset_x, offset_y = compute_layout(display, game)
                        menu_open = False
                        bg_dirty = True
                        full_redraw = True
                        hud_dirty = True
                        dirty_cells.clear()
                        solved_timestamp = None
                        last_solved = game.is_solved()
                    elif item == "PREV LEVEL":
                        level_idx, game = load_level(level_idx - 1)
                        cell_size, offset_x, offset_y = compute_layout(display, game)
                        menu_open = False
                        bg_dirty = True
                        full_redraw = True
                        hud_dirty = True
                        dirty_cells.clear()
                        solved_timestamp = None
                        last_solved = game.is_solved()
                    elif item == "EXIT":
                        break

            elif menu_open:
                if d == DIR_UP:
                    menu_sel = (menu_sel - 1) % len(menu_items)
                    last_act_time = now
                    full_redraw = True
                    bg_dirty = True
                elif d == DIR_DOWN:
                    menu_sel = (menu_sel + 1) % len(menu_items)
                    last_act_time = now
                    full_redraw = True
                    bg_dirty = True

            elif game.is_solved():
                pass

            elif d:
                if game.move(d):
                    last_act_time = now
                    dirty_cells.update(get_anim_cells(game))
                    hud_dirty = True

            if game.is_solved():
                if solved_timestamp is None:
                    solved_timestamp = time.monotonic()
                elif time.monotonic() - solved_timestamp > 2.0:
                    level_idx, game = load_level(level_idx + 1)
                    cell_size, offset_x, offset_y = compute_layout(display, game)
                    bg_dirty = True
                    full_redraw = True
                    hud_dirty = True
                    dirty_cells.clear()
                    solved_timestamp = None
                    last_solved = game.is_solved()
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
        if display_owned:
            display.deinit()
        try:
            i2c.deinit()
        except:
            pass
        print("Sokoban exited")

if __name__ == "__main__":
    main()
