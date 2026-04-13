# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Minesweeper Clone for Waveshare ESP32-S3 Touch AMOLED 2.41
Features:
- Touch & Joystick control
- Recursion (Flood Fill)
- Long-press to flag
- Modern Dark UI
"""

import time
import random
import board
import busio
import rm690b0
import gc

try:
    import adafruit_focaltouch
except ImportError:
    adafruit_focaltouch = None

# ---------------------------------------------------------------------------
# Hardware & Config
# ---------------------------------------------------------------------------
# Display resolution
WIDTH = 600
HEIGHT = 450

# Grid Settings
COLS = 16
ROWS = 10
# Tile size based on screen usage
# Top bar: 50px
# Remaining: 400px. 400 / 10 = 40px per tile.
# Width: 600. 16 * 40 = 640 (Too wide).
# Let's try 36px tiles.
# 16 * 36 = 576 (Fits with margin).
# 10 * 36 = 360.
# Margin logic later.
TILE_SIZE = 35
GRID_W = COLS * TILE_SIZE
GRID_H = ROWS * TILE_SIZE
OFFSET_X = (WIDTH - GRID_W) // 2
OFFSET_Y = 60 # Leave space for top bar

MINES_COUNT = 25
MINE_VALUE = 9

# ---------------------------------------------------------------------------
# Colors (RGB565 Helper)
# ---------------------------------------------------------------------------
def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

# Palette
C_BG            = rgb565(20, 20, 25)
C_SPLASH_BG     = 0x0000
C_BAR_BG        = rgb565(30, 30, 40)
C_TEXT          = rgb565(240, 240, 240)

# Tile Colors (Hidden)
C_TILE_HID_FACE = rgb565(60, 60, 75)
C_TILE_HID_LIT  = rgb565(90, 90, 110)
C_TILE_HID_DRK  = rgb565(30, 30, 40)

# Tile Colors (Revealed)
C_TILE_REV_BG   = rgb565(15, 15, 20)  # Very dark for pressed

# Numbers (Standard Minesweeper Colors)
C_NUMS = [
    0,                      # 0 (Unused)
    rgb565(80, 180, 255),   # 1 Blue
    rgb565(80, 255, 80),    # 2 Green
    rgb565(255, 80, 80),    # 3 Red
    rgb565(150, 80, 255),   # 4 Purple
    rgb565(255, 180, 50),   # 5 Maroon/Orange
    rgb565(50, 200, 200),   # 6 Cyan
    rgb565(200, 200, 200),  # 7 Black/Grey
    rgb565(100, 100, 100)   # 8 Grey
]

C_FLAG_POLE = rgb565(200, 200, 200)
C_FLAG_FABRIC = rgb565(255, 50, 50)
C_MINE_BODY = rgb565(20, 20, 20)
C_MINE_SPIKE = rgb565(100, 50, 50)
C_EXPLOSION = rgb565(255, 100, 0)
C_CURSOR = rgb565(255, 255, 0)

FONT_LARGE = rm690b0.FONT_24x24
FONT_SMALL = rm690b0.FONT_16x16

# ---------------------------------------------------------------------------
# Input Handling
# ---------------------------------------------------------------------------
class TouchInput:
    def __init__(self, i2c):
        self.tp = adafruit_focaltouch.Adafruit_FocalTouch(i2c)
        self.last_pos = None
        self.press_start = 0
        
    def get_action(self):
        # Return (x, y, is_long_press, is_release)
        # We need to detect:
        # - Tap (Release < 300ms)
        # - Long Press (Hold > 300ms)
        
        if not self.tp.touched:
            if self.last_pos:
                # Released
                dur = time.monotonic() - self.press_start
                pos = self.last_pos
                self.last_pos = None
                is_long = dur > 0.4
                return (pos[0], pos[1], is_long, True) # True = Release action
            return None
        
        try:
            p = self.tp.touches[0]
            # Map coords: 600x450 landscape. Controller is 450x600 portrait.
            # Touch X (0-450) -> Y
            # Touch Y (0-600) -> 600 - Y -> X
            tx = 600 - p['y']
            ty = p['x']
            
            if self.last_pos is None:
                self.press_start = time.monotonic()
                
            self.last_pos = (tx, ty)
            
            # Check for immediate feedback on long press?
            # For now, act on release or explicit long hold trigger?
            # Creating a 'held' event might vary.
            # Let's simple logic: Act on Release.
            # But visuals for flagging are better if they happen while holding?
            # Let's simpler: Release logic.
            return None 
            
        except:
            return None

# ---------------------------------------------------------------------------
# Game Logic
# ---------------------------------------------------------------------------
class MinesweeperGame:
    def __init__(self, cols, rows, mines):
        self.cols = cols
        self.rows = rows
        self.mines_count = mines
        self.cell_count = cols * rows
        self.data = bytearray(self.cell_count)  # 0-8, MINE_VALUE=mine
        self.state = bytearray(self.cell_count)  # 0=Hidden, 1=Revealed, 2=Flagged
        self.dirty = bytearray([1]) * self.cell_count
        self._needs_draw = True
        self.first_click = True
        self.game_over = False
        self.won = False
        self.start_time = 0
        self.end_time = 0
        self.flags_placed = 0
        self.cursor = [cols//2, rows//2]

    def idx(self, x, y):
        return y * self.cols + x

    def place_mines(self, safe_x, safe_y):
        placed = 0
        while placed < self.mines_count:
            x = random.randint(0, self.cols-1)
            y = random.randint(0, self.rows-1)
            idx = self.idx(x, y)
            # Ensure not on safe spot and neighbors
            if self.data[idx] == MINE_VALUE:
                continue
            if abs(x - safe_x) <= 1 and abs(y - safe_y) <= 1:
                continue

            self.data[idx] = MINE_VALUE
            placed += 1

        # Calc numbers
        for r in range(self.rows):
            for c in range(self.cols):
                idx = self.idx(c, r)
                if self.data[idx] == MINE_VALUE:
                    continue
                cnt = 0
                for dy in [-1,0,1]:
                    for dx in [-1,0,1]:
                        if dx==0 and dy==0:
                            continue
                        nx, ny = c+dx, r+dy
                        if 0<=nx<self.cols and 0<=ny<self.rows and self.data[self.idx(nx, ny)] == MINE_VALUE:
                            cnt += 1
                self.data[idx] = cnt

    def reveal(self, x, y):
        idx = self.idx(x, y)
        if self.state[idx] != 0:
            return # Already revealed or flagged
        if self.game_over:
            return

        if self.first_click:
            self.place_mines(x, y)
            self.first_click = False
            self.start_time = time.monotonic()

        self.state[idx] = 1 # Reveal
        self.dirty[idx] = 1
        self._needs_draw = True

        if self.data[idx] == MINE_VALUE:
            self.game_over = True
            self.won = False
            self.end_time = time.monotonic()
            self.mark_all_dirty()
            return

        if self.data[idx] == 0:
            # Flood fill
            stack = [(x,y)]
            while stack:
                cx, cy = stack.pop()
                for dy in [-1,0,1]:
                    for dx in [-1,0,1]:
                        nx, ny = cx+dx, cy+dy
                        if 0<=nx<self.cols and 0<=ny<self.rows:
                            nidx = self.idx(nx, ny)
                            if self.state[nidx] == 0:
                                self.state[nidx] = 1
                                self.dirty[nidx] = 1
                                if self.data[nidx] == 0:
                                    stack.append((nx, ny))

        self.check_win()

    def flag(self, x, y):
        if self.game_over:
            return
        idx = self.idx(x, y)
        # Toggle flag
        st = self.state[idx]
        if st == 0:
            self.state[idx] = 2
            self.flags_placed += 1
            self.dirty[idx] = 1
            self._needs_draw = True
        elif st == 2:
            self.state[idx] = 0
            self.flags_placed -= 1
            self.dirty[idx] = 1
            self._needs_draw = True

    def check_win(self):
        hidden_cnt = 0
        for st in self.state:
            if st == 0 or st == 2:
                hidden_cnt += 1
        if hidden_cnt == self.mines_count:
            self.game_over = True
            self.won = True
            self.end_time = time.monotonic()
            self.mark_all_dirty()

    def mark_all_dirty(self):
        self.dirty[:] = b'' * self.cell_count
        self._needs_draw = True

    def get_time(self):
        if self.first_click: return 0
        if self.game_over: return self.end_time - self.start_time
        return time.monotonic() - self.start_time

# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def draw_3d_rect(display, x, y, size, c_face, c_lit, c_drk):
    display.fill_rect(x, y, size, size, c_face)
    border = size//8
    if border<1: border=1
    # Highlight
    display.fill_rect(x, y, size, border, c_lit)
    display.fill_rect(x, y, border, size, c_lit)
    # Shadow
    display.fill_rect(x, y+size-border, size, border, c_drk)
    display.fill_rect(x+size-border, y, border, size, c_drk)

def draw_flag(display, x, y, size):
    # Pole
    px, py = x + size//3, y + size//5
    ph = size - size//3
    display.fill_rect(px, py, 2, ph, C_FLAG_POLE)
    # Base
    display.fill_rect(px-2, py+ph, 6, 2, C_FLAG_POLE)
    # Flag
    fw = size//2
    fh = size//3
    display.fill_rect(px+2, py, fw, fh, C_FLAG_FABRIC)
    
def draw_mine(display, x, y, size, exploded=False):
    cx, cy = x + size//2, y + size//2
    r = size//3
    if exploded:
        display.fill_rect(x+1, y+1, size-2, size-2, C_EXPLOSION)
    
    display.fill_circle(cx, cy, r, C_MINE_BODY)
    # Spikes
    l = size//2 - 2
    display.fill_rect(cx-1, cy-l, 2, l*2, C_MINE_SPIKE)
    display.fill_rect(cx-l, cy-1, l*2, 2, C_MINE_SPIKE)
    # Diagonals
    d = int(l * 0.707)
    # Simplified drawing for diagonals? No line primitive. 
    # Skip diagonals, simple cross mine is clean enough.

def draw_digit(display, val, x, y, size):
    sval = str(val)
    # Center text roughly
    display.text(x + size//4, y + 2, sval, color=C_NUMS[val])
    
def draw_tile(display, game, c, r, x, y, size, force_reveal=False):
    idx = game.idx(c, r)
    st = game.state[idx]
    val = game.data[idx]
    
    # 0=Hidden, 1=Revealed, 2=Flagged
    if st == 0 and not force_reveal:
        draw_3d_rect(display, x, y, size, C_TILE_HID_FACE, C_TILE_HID_LIT, C_TILE_HID_DRK)
    elif st == 2 and not force_reveal:
        draw_3d_rect(display, x, y, size, C_TILE_HID_FACE, C_TILE_HID_LIT, C_TILE_HID_DRK)
        draw_flag(display, x, y, size)
    elif st == 1 or force_reveal:
        # Revealed
        bg = C_TILE_REV_BG
        if val == MINE_VALUE and st == 1: bg = C_EXPLOSION # Exploded mine logic handled inside draw_mine call usually
        
        display.fill_rect(x, y, size, size, bg)
        display.rect(x, y, size, size, rgb565(30,30,40)) # Subtle border
        
        if val == MINE_VALUE:
            draw_mine(display, x, y, size, exploded=(st==1))
        elif val > 0:
            draw_digit(display, val, x, y, size)

def draw_ui(display, game):
    display.fill_rect(0, 0, WIDTH, 50, C_BAR_BG)
    display.set_font(FONT_LARGE)
    
    # Mines left
    rem = game.mines_count - game.flags_placed
    display.text(20, 15, f"Mines: {rem}", color=C_TEXT)
    
    # Time
    t = int(game.get_time())
    ts = f"{t:03d}"
    display.text(WIDTH - 100, 15, ts, color=C_TEXT)
    
    # Face/Status
    status = ":)"
    c = rgb565(255, 255, 0)
    if game.game_over:
        if game.won: 
            status = "WIN!"
            c = rgb565(50, 255, 50)
        else: 
            status = "X_X"
            c = rgb565(255, 50, 50)
    
    display.text(WIDTH//2 - 40, 15, status, color=c)

def draw_overlay(display, text, subtext, color):
    w, h = 300, 100
    x = (WIDTH - w)//2
    y = (HEIGHT - h)//2
    
    # Shadow styling
    display.fill_rect(x-4, y-4, w+8, h+8, C_BG)
    display.rect(x-4, y-4, w+8, h+8, color)
    
    display.set_font(FONT_LARGE)
    display.text(x + 20, y + 20, text, color=color)
    
    display.set_font(FONT_SMALL)
    display.text(x + 40, y + 60, subtext, color=C_TEXT)


def draw_start_screen(display):
    title = "MINESWEEPER"
    prompt = "Press any key"
    title_x = (WIDTH - len(title) * 24) // 2
    prompt_x = (WIDTH - len(prompt) * 16) // 2

    display.fill_color(C_SPLASH_BG)
    display.set_font(FONT_LARGE)
    display.text(title_x, 160, title, color=0x07E0)
    display.set_font(FONT_SMALL)
    display.text(prompt_x, 220, prompt, color=C_TEXT)
    display.swap_buffers(copy=True)


def wait_for_start(joy, touch):
    idle_since = None
    press_since = None
    idle_required = 0.12
    press_required = 0.06

    def pressed():
        j = joy.read()
        if j['up'] or j['down'] or j['left'] or j['right'] or j['center']:
            return True
        if touch.tp.touched:
            return True
        return False

    while True:
        now = time.monotonic()
        if not pressed():
            if idle_since is None:
                idle_since = now
            elif now - idle_since >= idle_required:
                break
        else:
            idle_since = None
        time.sleep(0.01)

    while True:
        now = time.monotonic()
        if pressed():
            if press_since is None:
                press_since = now
            elif now - press_since >= press_required:
                break
        else:
            press_since = None
        time.sleep(0.01)

    while pressed():
        time.sleep(0.01)


def main(display=None):
    print("Minesweeper Clone Starting...")
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

    i2c = busio.I2C(board.TP_SCL, board.TP_SDA)
    touch = TouchInput(i2c)
    from joystick import Joystick
    joy = Joystick(i2c=i2c)

    # Fill background on both buffers
    display.fill_color(C_BG)
    display.swap_buffers(copy=True)

    draw_start_screen(display)
    wait_for_start(joy, touch)

    try:
        game = MinesweeperGame(COLS, ROWS, MINES_COUNT)

        last_draw = 0
        needs_redraw_ui = True

        cursor_vis = False # Hide cursor until joystick used
        prev_cursor = [game.cursor[0], game.cursor[1]]
        joy_btn_pressed = False
        joy_press_start = 0
        joy_dir_active = None
        joy_repeat_at = 0
        joy_repeat_initial = 0.22
        joy_repeat_interval = 0.12

        # Stabilize sensors
        time.sleep(0.5)

        while True:
            now = time.monotonic()

            # Input
            t_action = touch.get_action() # (x, y, long, released)
            j_state = joy.read()

            # Touch Handling
            if t_action:
                tx, ty, is_long, is_rel = t_action
                if is_rel:
                    # Handle Game Over Restart
                    if game.game_over:
                        game = MinesweeperGame(COLS, ROWS, MINES_COUNT)
                        prev_cursor = [game.cursor[0], game.cursor[1]]
                        needs_redraw_ui = True
                        # Debounce slightly
                        time.sleep(0.2)
                        continue

                    # Map to grid
                    if tx >= OFFSET_X and tx < OFFSET_X + GRID_W and \
                       ty >= OFFSET_Y and ty < OFFSET_Y + GRID_H:
                        gx = (tx - OFFSET_X) // TILE_SIZE
                        gy = (ty - OFFSET_Y) // TILE_SIZE

                        # Update cursor to touched pos (optional, keep hidden if touch only)
                        game.cursor = [gx, gy]
                        # cursor_vis = True # Uncomment if you want touch to show cursor

                        # Prevent Joystick phantom click conflict
                        joy_btn_pressed = False

                        if is_long:
                            game.reveal(gx, gy) # Long press = Reveal
                        else:
                            game.flag(gx, gy)   # Short press = Flag

                        needs_redraw_ui = True

                    # Check Face reset
                    if ty < 50 and tx > WIDTH//2 - 50 and tx < WIDTH//2 + 50:
                        game = MinesweeperGame(COLS, ROWS, MINES_COUNT)
                        prev_cursor = [game.cursor[0], game.cursor[1]]
                        needs_redraw_ui = True

            # Joystick Handling
            move_dir = None
            if j_state['right']:
                move_dir = 'right'
            elif j_state['left']:
                move_dir = 'left'
            elif j_state['down']:
                move_dir = 'down'
            elif j_state['up']:
                move_dir = 'up'

            moved = False
            if move_dir is None:
                joy_dir_active = None
            else:
                should_move = False
                if move_dir != joy_dir_active:
                    joy_dir_active = move_dir
                    joy_repeat_at = now + joy_repeat_initial
                    should_move = True
                elif now >= joy_repeat_at:
                    joy_repeat_at = now + joy_repeat_interval
                    should_move = True

                if should_move:
                    if move_dir == 'right':
                        game.cursor[0] = min(game.cols-1, game.cursor[0]+1)
                    elif move_dir == 'left':
                        game.cursor[0] = max(0, game.cursor[0]-1)
                    elif move_dir == 'down':
                        game.cursor[1] = min(game.rows-1, game.cursor[1]+1)
                    elif move_dir == 'up':
                        game.cursor[1] = max(0, game.cursor[1]-1)
                    moved = True

            if moved:
                cursor_vis = True
                # Mark old and new cursor tiles dirty
                game.dirty[game.idx(prev_cursor[0], prev_cursor[1])] = 1
                game.dirty[game.idx(game.cursor[0], game.cursor[1])] = 1
                game._needs_draw = True
                prev_cursor = [game.cursor[0], game.cursor[1]]

            # Joystick Button
            if j_state['center']:
                if not joy_btn_pressed:
                    joy_btn_pressed = True
                    joy_press_start = now
            else:
                if joy_btn_pressed:
                    # Released
                    joy_btn_pressed = False

                    # Handle Game Over Restart
                    if game.game_over:
                        game = MinesweeperGame(COLS, ROWS, MINES_COUNT)
                        prev_cursor = [game.cursor[0], game.cursor[1]]
                        needs_redraw_ui = True
                        continue

                    dur = now - joy_press_start
                    cx, cy = game.cursor

                    if dur > 0.4:
                        game.reveal(cx, cy) # Long press = Reveal
                    else:
                        game.flag(cx, cy)   # Short press = Flag

                    needs_redraw_ui = True

            # Draw
            ui_drawn = False
            if needs_redraw_ui or (now - last_draw > 1.0): # Update time every sec
                draw_ui(display, game)
                last_draw = now
                needs_redraw_ui = False
                ui_drawn = True

            if game._needs_draw:
                display.set_font(FONT_LARGE)
                for r in range(ROWS):
                    for c in range(COLS):
                        idx = game.idx(c, r)
                        if not game.dirty[idx]:
                            continue
                        game.dirty[idx] = 0
                        xx = OFFSET_X + c * TILE_SIZE
                        yy = OFFSET_Y + r * TILE_SIZE

                        force_rev = game.game_over and (game.data[idx] == MINE_VALUE)
                        draw_tile(display, game, c, r, xx, yy, TILE_SIZE, force_reveal=force_rev)

                        # Cursor Highlight
                        if cursor_vis and c == game.cursor[0] and r == game.cursor[1]:
                            display.rect(xx, yy, TILE_SIZE, TILE_SIZE, C_CURSOR)
                            display.rect(xx+1, yy+1, TILE_SIZE-2, TILE_SIZE-2, C_CURSOR)

                # Draw Game Over Overlay
                if game.game_over:
                     msg = "VICTORY!" if game.won else "GAME OVER"
                     col = rgb565(50, 255, 50) if game.won else rgb565(255, 50, 50)
                     draw_overlay(display, msg, "TAP TO RESTART", col)

                display.swap_buffers(copy=True)
                game._needs_draw = False

            elif ui_drawn:
                display.swap_buffers(copy=True)

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
        print("Minesweeper exited")

if __name__ == "__main__":
    main()
