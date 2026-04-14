# Copyright (c) 2026 Przemyslaw Patrick Socha

"""
Frogger Clone for Waveshare ESP32-S3 Touch AMOLED 2.41" (RM690B0, 600x450).
Uses BMP sprite assets from frogger/ directory.
Controls: Touch swipe + I2C joystick (PCA9554).
"""

import gc
import random
import struct
import time

import board
import busio
import rm690b0

try:
    import adafruit_focaltouch
except ImportError:
    adafruit_focaltouch = None

# ==========================================================================
# Display & Grid
# ==========================================================================
SCREEN_W = 600
SCREEN_H = 450
CELL = 30
ROWS = 14
COLS = 20

# ==========================================================================
# Row layout (screen top to bottom, row 0 = y=0 = top of screen)
# ==========================================================================
ROW_HUD_TOP = 0     # y=0:   Score, lives
ROW_HOME = 1        # y=30:  Home bays
ROW_RIVER5 = 2      # y=60:  River top lane (logs)
ROW_RIVER4 = 3      # y=90:  River (turtles, some diving)
ROW_RIVER3 = 4      # y=120: River (long logs)
ROW_RIVER2 = 5      # y=150: River (logs)
ROW_RIVER1 = 6      # y=180: River bottom lane (turtles)
ROW_MEDIAN = 7      # y=210: Safe green median
ROW_ROAD4 = 8       # y=240: Road top lane (cars)
ROW_ROAD3 = 9       # y=270: Road (cars)
ROW_ROAD2 = 10      # y=300: Road (cars)
ROW_ROAD1 = 11      # y=330: Road bottom lane (trucks)
ROW_START = 12      # y=360: Frog start
ROW_HUD_BOT = 13    # y=390: Time bar, High score (60px tall)

ROAD_ROWS = {ROW_ROAD1, ROW_ROAD2, ROW_ROAD3, ROW_ROAD4}
RIVER_ROWS = {ROW_RIVER1, ROW_RIVER2, ROW_RIVER3, ROW_RIVER4, ROW_RIVER5}
SAFE_ROWS = {ROW_START, ROW_MEDIAN}

# Home bay hit ranges (inclusive) and visual centers
HOME_BAY_X_RANGES = (
    (40, 87),
    (158, 205),
    (276, 323),
    (394, 441),
    (512, 559),
)
HOME_X = [64, 182, 300, 418, 536]

# Visual alignment offsets against static background.bmp
ROAD_OBJ_Y_OFFSET = 10
FROG_LAND_Y_OFFSET = 10
FROG_START_EXTRA_Y = 4
HOME_FROG_X_SHIFT = 0
LONGEST_LOG_SPRITE = "log-2"

# HUD positions
SCORE_X = 130
SCORE_Y = 8
HIGH_SCORE_Y = 402
TIME_BAR_X = 160
TIME_BAR_Y = 382
TIME_BAR_H = 18
TIME_BAR_RIGHT_PAD = 4

# Difficulty profiles inferred from original gameplay capture
# S1: early game, S2: mid game, S3: late game
DIFFICULTY_SPEED_PROFILES = (
    {
        "road1": 1.45,  # ROW_ROAD1 (bottom trucks)
        "road2": -1.63, # ROW_ROAD2
        "road3": 2.83,  # ROW_ROAD3 (race car lane)
        "road4": -1.51, # ROW_ROAD4 (top road lane)
        "river1": -0.80, # ROW_RIVER1 (turtles-3)
        "river2": 1.20,  # ROW_RIVER2 (shortest logs)
        "river3": 3.10,  # ROW_RIVER3 (longest logs)
        "river4": -1.00, # ROW_RIVER4 (turtles-4)
        "river5": 1.00,  # ROW_RIVER5 (top medium logs)
        "race_cars": 1,
        "trucks": 3,
        "enemy_mult": 1.0,
        "t3_dive": False,
        "t4_dive": True,
        "bonus_log": True,
        "bay_bonus": True,
        "bay_croc": False,
        "snake2": False,
        "snake1": False,
        "beaver": False,
        "croc_logs": False,
    },
    {
        "road1": 1.14,
        "road2": -1.50,
        "road3": 5.70,
        "road4": -1.90,
        "river1": -1.20,
        "river2": 1.50,
        "river3": 1.77,
        "river4": -1.00,
        "river5": 1.44,
        "race_cars": 2,
        "trucks": 4,
        "enemy_mult": 1.1,
        "t3_dive": True,
        "t4_dive": True,
        "bonus_log": True,
        "bay_bonus": True,
        "bay_croc": True,
        "snake2": True,
        "snake1": True,
        "beaver": True,
        "croc_logs": False,
    },
    {
        "road1": 1.15,
        "road2": -1.35,
        "road3": 5.42,
        "road4": -1.42,
        "river1": -1.60,
        "river2": 1.35,
        "river3": 1.45,
        "river4": -1.00,
        "river5": 1.78,
        "race_cars": 2,
        "trucks": 4,
        "enemy_mult": 1.2,
        "t3_dive": True,
        "t4_dive": True,
        "bonus_log": True,
        "bay_bonus": True,
        "bay_croc": True,
        "snake2": True,
        "snake1": True,
        "beaver": True,
        "croc_logs": True,
    },
)

# ==========================================================================
# Directions & States
# ==========================================================================
DIR_NONE = 0
DIR_UP = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4

ST_PLAYING = 0
ST_DYING = 1
ST_DROWN = 2
ST_GAME_OVER = 3
ST_LEVEL_COMPLETE = 4

# ==========================================================================
# Pre-computed sprite name tables (avoid per-frame f-string allocations)
# ==========================================================================
_SCORE_N = tuple(f"score-{i}" for i in range(10))
_HISCORE_N = tuple(f"high-score-{i}" for i in range(10))
_DEATH_N = (None, "death-1", "death-2", "death-3", "death-4")
_DROWN_N = (None, "drown-1", "drown-2", "drown-3", "drown-4", "drown-5")
_CROC_N = (None, "crocodile-1", "crocodile-2")
_SNAKE2_R = (None,) + tuple(f"snake-2-{i}" for i in range(1, 9))
_SNAKE2_L = (None,) + tuple(f"snake-2-{i}-l" for i in range(1, 9))
_SNAKE1_R = (None,) + tuple(f"snake-1-{i}" for i in range(1, 9))
_SNAKE1_L = (None,) + tuple(f"snake-1-{i}-l" for i in range(1, 9))

# _FROG_N[direction][has_bonus][anim_frame] — 1-indexed frames
_FROG_N = (
    None,  # DIR_NONE
    (  # DIR_UP
        (None, "frog-v-1", "frog-v-2", "frog-v-3", "frog-v-4", "frog-v-5", "frog-v-6"),
        (None, "frog-bv-1", "frog-bv-2", "frog-bv-3", "frog-bv-4", "frog-bv-5", "frog-bv-6"),
    ),
    (  # DIR_DOWN
        (None, "frog-vd-1", "frog-vd-2", "frog-vd-3", "frog-vd-4", "frog-vd-5", "frog-vd-6"),
        (None, "frog-bvd-1", "frog-bvd-2", "frog-bvd-3", "frog-bvd-4", "frog-bvd-5", "frog-bvd-6"),
    ),
    (  # DIR_LEFT
        (None, "frog-h-1", "frog-h-2", "frog-h-3", "frog-h-4", "frog-h-5", "frog-h-6"),
        (None, "frog-bh-1", "frog-bh-2", "frog-bh-3", "frog-bh-4", "frog-bh-5", "frog-bh-6"),
    ),
    (  # DIR_RIGHT
        (None, "frog-hl-1", "frog-hl-2", "frog-hl-3", "frog-hl-4", "frog-hl-5", "frog-hl-6"),
        (None, "frog-bhl-1", "frog-bhl-2", "frog-bhl-3", "frog-bhl-4", "frog-bhl-5", "frog-bhl-6"),
    ),
)

# ==========================================================================
# Timing
# ==========================================================================
TARGET_FPS = 30
FRAME_TIME = 1.0 / TARGET_FPS
JUMP_FRAMES = 7
DEATH_FRAMES = 20
DROWN_FRAMES = 25
LEVEL_COMPLETE_FRAMES = 0

# Diving turtle animation states (from original sprite sheets)
# 1 = fully submerged (blank water), 7->8 are dive-in bubbles, 2->6 emerge.
DIVE_SUBMERGED_FRAME = 1
DIVE_START_FRAME = 7
DIVE_END_FRAME = 6

# Bay events (bonus frog / crocodile in home bays)
BAY_EVENT_DURATION = TARGET_FPS * 5     # 5s visible
BAY_COOLDOWN_MIN = TARGET_FPS * 6       # 6s min between events
BAY_COOLDOWN_MAX = TARGET_FPS * 10      # 10s max

# Bonus frog on log (no auto-expire; spawn controlled by cooldown only)
BONUS_LOG_COOLDOWN_MIN = TARGET_FPS * 12
BONUS_LOG_COOLDOWN_MAX = TARGET_FPS * 20

# ==========================================================================
# Colors & Transparency
# ==========================================================================
def _rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def _swap16(v):
    return ((v & 0xFF) << 8) | ((v >> 8) & 0xFF)

# Magenta as transparent color in byte-swapped format (for convert_bmp output)
TRANSPARENT = _swap16(_rgb565(255, 0, 255))  # 0x1FF8

# Standard RGB565 for fill_rect (not swapped)
C_GREEN = _rgb565(0, 200, 0)
C_RED = _rgb565(200, 0, 0)
C_BLACK = 0x0000
C_TIME_BAR = _rgb565(0x68, 0x1b, 0x23)

# ==========================================================================
# BMP Loading
# ==========================================================================
def bmp_size(data):
    """Extract (width, height) from BMP header."""
    w = struct.unpack_from('<i', data, 18)[0]
    h = abs(struct.unpack_from('<i', data, 22)[0])
    return w, h


def load_sprite(display, path):
    """Load BMP file, convert to RGB565 via C-level convert_bmp.
    Returns (width, height, bytearray)."""
    with open(path, "rb") as f:
        data = f.read()
    w, h = bmp_size(data)
    buf = bytearray(w * h * 2)
    display.convert_bmp(data, buf)
    return w, h, buf


def flip_h(buf, w, h):
    """Create horizontally mirrored copy of RGB565 buffer."""
    out = bytearray(len(buf))
    for row in range(h):
        rs = row * w * 2
        for col in range(w):
            src = rs + col * 2
            dst = rs + (w - 1 - col) * 2
            out[dst] = buf[src]
            out[dst + 1] = buf[src + 1]
    return out


def flip_v(buf, w, h):
    """Create vertically mirrored copy of RGB565 buffer."""
    out = bytearray(len(buf))
    row_sz = w * 2
    for row in range(h):
        src = row * row_sz
        dst = (h - 1 - row) * row_sz
        out[dst:dst + row_sz] = buf[src:src + row_sz]
    return out


# ==========================================================================
# Input: Joystick helpers (shared joystick module adapter)
# ==========================================================================
def _joy_direction(joy):
    """Read shared Joystick and return a DIR_* constant."""
    state = joy.read()
    if state["up"]:
        return DIR_UP
    if state["down"]:
        return DIR_DOWN
    if state["left"]:
        return DIR_LEFT
    if state["right"]:
        return DIR_RIGHT
    return DIR_NONE


def _joy_center(joy):
    """Return True if joystick center button is pressed."""
    return joy.read()["center"]


# ==========================================================================
# Input: Touch (swipe-based)
# ==========================================================================
class TouchInput:
    def __init__(self, i2c):
        self.touch = adafruit_focaltouch.Adafruit_FocalTouch(i2c)
        self.sx = 0
        self.sy = 0
        self.swiping = False
        self.last_tap = 0
        try:
            import settings
            self._rotation = settings.rotation
        except ImportError:
            self._rotation = 0

    def _map(self, raw_x, raw_y):
        if self._rotation == 180:
            return raw_y, 450 - raw_x
        return 600 - raw_y, raw_x

    def get_input(self):
        if not self.touch.touched:
            self.swiping = False
            return DIR_NONE
        try:
            pts = self.touch.touches
        except Exception:
            return DIR_NONE
        if not pts:
            self.swiping = False
            return DIR_NONE

        x, y = self._map(pts[0]["x"], pts[0]["y"])

        if not self.swiping:
            self.sx = x
            self.sy = y
            self.swiping = True
            return DIR_NONE

        dx = x - self.sx
        dy = y - self.sy

        if abs(dx) > abs(dy):
            if abs(dx) > 30:
                self.sx = x
                self.sy = y
                return DIR_RIGHT if dx > 0 else DIR_LEFT
        else:
            if abs(dy) > 30:
                self.sx = x
                self.sy = y
                return DIR_DOWN if dy > 0 else DIR_UP
        return DIR_NONE

    def check_center(self):
        if self.touch.touched and not self.swiping:
            now = time.monotonic()
            if now - self.last_tap > 0.5:
                self.last_tap = now
                return True
        return False


# ==========================================================================
# Sprite Manager — loads all BMP assets at startup
# ==========================================================================
class Sprites:
    def __init__(self, display, bmp_dir):
        self.display = display
        self.dir = bmp_dir
        self._cache = {}   # name -> (w, h, buf)
        self.bg_buf = None   # Pre-converted RGB565 background
        self.bg_w = 0
        self.bg_h = 0

    def _load(self, name, filename=None):
        if name in self._cache:
            return
        path = self.dir + "/" + (filename or name + ".bmp")
        try:
            w, h, buf = load_sprite(self.display, path)
            self._cache[name] = (w, h, buf)
        except Exception as e:
            print(f"  WARN: {path}: {e}")

    def get(self, name):
        """Get sprite data: (w, h, buf) or None."""
        return self._cache.get(name)

    def _make_flip_h(self, src, dst):
        """Create horizontally flipped copy of sprite."""
        data = self._cache.get(src)
        if data:
            w, h, buf = data
            self._cache[dst] = (w, h, flip_h(buf, w, h))

    def _make_flip_v(self, src, dst):
        """Create vertically flipped copy of sprite."""
        data = self._cache.get(src)
        if data:
            w, h, buf = data
            self._cache[dst] = (w, h, flip_v(buf, w, h))

    def load_all(self, progress_fn=None):
        print("Loading sprites...")
        t0 = time.monotonic()
        _total = 142  # total sprites (disk + flipped)
        _n = 0

        def _prog(n):
            nonlocal _n
            _n = n
            if progress_fn:
                progress_fn(n, _total)

        # Background — pre-convert to RGB565 (avoids BMP decode every frame)
        with open(self.dir + "/background.bmp", "rb") as f:
            raw = f.read()
        w, h = bmp_size(raw)
        self.bg_buf = bytearray(w * h * 2)
        self.display.convert_bmp(raw, self.bg_buf)
        self.bg_w = w
        self.bg_h = h
        del raw
        gc.collect()
        _prog(1)

        # Frog (6 vertical + 6 horizontal frames)
        for i in range(1, 7):
            self._load(f"frog-v-{i}", f"frogger-vertical-{i}.bmp")
            self._load(f"frog-h-{i}", f"frogger-horizontal-{i}.bmp")
        gc.collect()
        _prog(13)

        # Bonus frog (6 vertical + 6 horizontal frames)
        for i in range(1, 7):
            self._load(f"frog-bv-{i}", f"frogger-bonus-vertical-{i}.bmp")
            self._load(f"frog-bh-{i}", f"frogger-bonus-horizontal-{i}.bmp")
        gc.collect()
        _prog(25)

        # Vehicles
        for i in range(1, 4):
            self._load(f"car-{i}")
            self._load(f"truck-{i}")
        gc.collect()
        _prog(31)

        # Logs
        for i in range(1, 4):
            self._load(f"log-{i}")
        _prog(34)

        # Turtles (groups of 3: 3 normal + 8 diving frames)
        for i in range(1, 4):
            self._load(f"t3n{i}", f"turtles-3-normal-{i}.bmp")
        for i in range(1, 9):
            self._load(f"t3d{i}", f"turtles-3-diving-{i}.bmp")
        gc.collect()
        _prog(45)

        # Turtles (groups of 4: 3 normal + 8 diving frames)
        for i in range(1, 4):
            self._load(f"t4n{i}", f"turtles-4-normal-{i}.bmp")
        for i in range(1, 9):
            self._load(f"t4d{i}", f"turtles-4-diving-{i}.bmp")
        gc.collect()
        _prog(56)

        # Score & high-score digits
        for i in range(10):
            self._load(f"score-{i}")
            self._load(f"high-score-{i}")
        _prog(76)

        # HUD elements
        self._load("life")
        self._load("game-over")
        self._load("exit-frogger")
        self._load("exit-bonus")
        self._load("exit-crocodile")
        _prog(81)

        # Death/drown animations
        for i in range(1, 5):
            self._load(f"death-{i}")
        for i in range(1, 6):
            self._load(f"drown-{i}")
        gc.collect()
        _prog(90)

        # Enemies
        self._load("beaver")
        for i in range(1, 9):
            self._load(f"snake-1-{i}")
            self._load(f"snake-2-{i}")
        self._load("crocodile-1")
        self._load("crocodile-2")
        gc.collect()
        _prog(109)

        # Create flipped versions for directional sprites
        for i in range(1, 7):
            self._make_flip_h(f"frog-h-{i}", f"frog-hl-{i}")
            self._make_flip_h(f"frog-bh-{i}", f"frog-bhl-{i}")
            self._make_flip_v(f"frog-v-{i}", f"frog-vd-{i}")
            self._make_flip_v(f"frog-bv-{i}", f"frog-bvd-{i}")
        gc.collect()
        _prog(133)

        for i in range(1, 9):
            self._make_flip_h(f"snake-2-{i}", f"snake-2-{i}-l")
            self._make_flip_h(f"snake-1-{i}", f"snake-1-{i}-l")
        self._make_flip_h("beaver", "beaver-l")
        gc.collect()
        _prog(142)

        dt = time.monotonic() - t0
        print(f"  Loaded {len(self._cache)} sprites in {dt:.1f}s")


# ==========================================================================
# Lane Object — a single moving entity on a lane (car/truck/log/turtle group)
# ==========================================================================
class LaneObj:
    __slots__ = (
        "x", "w", "sprite_name", "is_safe",
        "is_croc",
        "can_dive", "diving", "dive_timer", "dive_period",
        "anim_prefix", "anim_count", "anim_frame", "anim_speed", "anim_timer",
        "dive_anim_prefix", "dive_anim_count",
        "_anim_names", "_dive_names",
    )

    def __init__(self, x, w, sprite_name, is_safe=False,
                 is_croc=False,
                 can_dive=False, dive_period=0,
                 anim_prefix="", anim_count=1, anim_speed=8,
                 dive_anim_prefix="", dive_anim_count=8):
        self.x = float(x)
        self.w = w
        self.sprite_name = sprite_name
        self.is_safe = is_safe
        self.is_croc = is_croc
        self.can_dive = can_dive
        self.dive_period = dive_period
        self.dive_timer = random.randint(0, max(1, dive_period)) if can_dive else 0
        self.diving = False
        self.anim_prefix = anim_prefix
        self.anim_count = anim_count
        self.anim_frame = random.randint(1, max(1, anim_count))
        self.anim_speed = anim_speed
        self.anim_timer = random.randint(0, anim_speed)
        self.dive_anim_prefix = dive_anim_prefix
        self.dive_anim_count = dive_anim_count
        self._anim_names = (
            tuple(f"{anim_prefix}{i}" for i in range(1, anim_count + 1))
            if anim_count > 1 and anim_prefix else ()
        )
        self._dive_names = (
            tuple(f"{dive_anim_prefix}{i}" for i in range(1, dive_anim_count + 1))
            if dive_anim_prefix else ()
        )

    def is_submerged(self):
        return (self.can_dive and self.diving
                and self.anim_frame == DIVE_SUBMERGED_FRAME)

    def current_sprite(self):
        if self.can_dive and self.diving:
            if self.is_submerged():
                return None
            frame = min(self.anim_frame, self.dive_anim_count)
            return self._dive_names[frame - 1] if self._dive_names else None
        if self._anim_names:
            frame = min(self.anim_frame, len(self._anim_names))
            return self._anim_names[frame - 1]
        return self.sprite_name


# ==========================================================================
# Lane — one row of moving objects
# ==========================================================================
class Lane:
    __slots__ = ("row", "speed", "objects", "is_river")

    def __init__(self, row, speed, is_river=False):
        self.row = row
        self.speed = speed
        self.objects = []
        self.is_river = is_river

    @property
    def y(self):
        return self.row * CELL

    def update(self):
        for obj in self.objects:
            obj.x += self.speed

            # Wrapping
            if self.speed > 0 and obj.x > SCREEN_W:
                obj.x = -float(obj.w)
            elif self.speed < 0 and obj.x + obj.w < 0:
                obj.x = float(SCREEN_W)

            # Animation cycling
            obj.anim_timer += 1
            if obj.anim_timer >= obj.anim_speed:
                obj.anim_timer = 0
                if obj.can_dive and obj.diving:
                    if obj.anim_frame == DIVE_START_FRAME:
                        obj.anim_frame = 8
                    elif obj.anim_frame == 8:
                        obj.anim_frame = DIVE_SUBMERGED_FRAME
                    elif obj.anim_frame == DIVE_SUBMERGED_FRAME:
                        if obj.dive_timer <= 0:
                            obj.anim_frame = 2
                    elif 2 <= obj.anim_frame < DIVE_END_FRAME:
                        obj.anim_frame += 1
                    elif obj.anim_frame == DIVE_END_FRAME:
                        obj.diving = False
                        obj.anim_frame = 1
                        obj.dive_timer = obj.dive_period
                else:
                    obj.anim_frame += 1
                    total = max(1, obj.anim_count)
                    if obj.anim_frame > total:
                        obj.anim_frame = 1

            # Diving logic
            if obj.can_dive:
                if obj.diving:
                    if obj.anim_frame == DIVE_SUBMERGED_FRAME:
                        obj.dive_timer -= 1
                else:
                    obj.dive_timer -= 1
                    if obj.dive_timer <= 0:
                        obj.diving = True
                        obj.dive_timer = TARGET_FPS * 3  # 3s submerged
                        obj.anim_frame = DIVE_START_FRAME
                        obj.anim_timer = 0


# ==========================================================================
# Frog (Player)
# ==========================================================================
class Frog:
    __slots__ = (
        "gx", "gy", "px", "py", "direction",
        "jumping", "jfx", "jfy", "jtx", "jty", "jf",
        "alive", "furthest_row", "on_obj", "has_bonus", "anim_frame",
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.gx = COLS // 2
        self.gy = ROW_START
        self.px = float(self.gx * CELL)
        self.py = float(self.gy * CELL)
        self.direction = DIR_UP
        self.jumping = False
        self.jfx = 0.0
        self.jfy = 0.0
        self.jtx = 0.0
        self.jty = 0.0
        self.jf = 0
        self.alive = True
        self.furthest_row = ROW_START
        self.on_obj = None
        self.has_bonus = False
        self.anim_frame = 1

    def start_jump(self, direction):
        if self.jumping:
            return False
        dx, dy = 0, 0
        if direction == DIR_UP:
            dy = -1
        elif direction == DIR_DOWN:
            dy = 1
        elif direction == DIR_LEFT:
            dx = -1
        elif direction == DIR_RIGHT:
            dx = 1
        else:
            return False

        nx = self.gx + dx
        ny = self.gy + dy

        if nx < 0 or nx >= COLS or ny < ROW_HOME or ny > ROW_START:
            return False

        self.direction = direction
        self.jumping = True
        self.jfx = self.px
        self.jfy = self.py
        self.jtx = float(nx * CELL)
        self.jty = float(ny * CELL)
        self.jf = 0
        self.gx = nx
        self.gy = ny
        self.anim_frame = 1
        return True

    def update_jump(self):
        if not self.jumping:
            return
        self.jf += 1
        t = self.jf / JUMP_FRAMES
        self.anim_frame = min(6, 1 + int(t * 5))
        if t >= 1.0:
            t = 1.0
            self.jumping = False
            self.anim_frame = 1
        self.px = self.jfx + (self.jtx - self.jfx) * t
        self.py = self.jfy + (self.jty - self.jfy) * t


# ==========================================================================
# FroggerGame — main game logic with difficulty progression
# ==========================================================================
class FroggerGame:
    def __init__(self, display, sprites, joystick, touch):
        self.d = display
        self.spr = sprites
        self.joy = joystick
        self.tch = touch

        self.frog = Frog()
        self.lanes = []

        # Home bays
        self.home_bays = [False] * 5
        self.home_bonus = [False] * 5
        self.home_event = [0] * 5         # 0=none, 1=bonus, 2=croc
        self.home_event_timer = [0] * 5
        self.bay_cooldown = BAY_COOLDOWN_MAX

        # Scoring & progression
        self.score = 0
        self.high_score = 0
        self.lives = 5
        self.level = 1
        self.frogs_in_level = 0
        self.frogs_delivered = 0
        self.frog_time_max = 0
        self.time_left = 0
        self.state = ST_PLAYING
        self.state_timer = 0

        # Bonus frog on log
        self.bonus_log_obj = None
        self.bonus_log_lane = None
        self.bonus_log_timer = 0
        self.bonus_log_cooldown = BONUS_LOG_COOLDOWN_MAX

        # Snake-2 (median enemy, level 3+)
        self.snake2_active = False
        self.snake2_x = 0.0
        self.snake2_speed = 1.5
        self.snake2_frame = 1
        self.snake2_anim_timer = 0

        # Snake-1 (on log, level 4+)
        self.snake1_active = False
        self.snake1_obj = None
        self.snake1_lane = None
        self.snake1_frame = 1
        self.snake1_anim_timer = 0
        self.snake1_rel_x = 0.0
        self.snake1_dir = 1
        self.snake1_speed = 0.0

        # Beaver (river, swims between logs)
        self.beaver_active = False
        self.beaver_x = -100.0
        self.beaver_row = ROW_RIVER3
        self.beaver_lane = None
        self.beaver_anchor_obj = None

        # Crocodile on logs (level 6+)
        self.croc_logs = []         # [(lane, obj), ...]
        self.croc_frame = 1
        self.croc_timer = 0
        self.croc_mouth_open = False

        # Sprite widths cache
        self._sprite_w = {}
        for name in ("car-1", "car-2", "car-3", "truck-1",
                      "log-1", "log-2", "log-3", "t3n1", "t4n1",
                      "beaver", "snake-1-1", "snake-2-1", "crocodile-1"):
            info = sprites.get(name)
            if info:
                self._sprite_w[name] = info[0]

        self._setup_lanes()

    # ------------------------------------------------------------------
    # Difficulty helpers
    # ------------------------------------------------------------------
    def _sw(self, name, default=48):
        return self._sprite_w.get(name, default)

    def _difficulty_tier(self):
        if self.level <= 2:
            return 0
        if self.level <= 4:
            return 1
        return 2

    def _difficulty_profile(self):
        return DIFFICULTY_SPEED_PROFILES[self._difficulty_tier()]

    def _frog_time(self):
        secs = max(20, 30 - (self.level - 1) * 2)
        return secs * TARGET_FPS

    # ------------------------------------------------------------------
    # Lane setup
    # ------------------------------------------------------------------
    def _setup_lanes(self):
        self.lanes = []
        profile = self._difficulty_profile()
        # Keep dive pacing tied to overall movement intensity.
        river_scale = max(0.6, min(2.0, abs(profile["river3"]) / 3.0))

        # ---- ROAD LANES (rows 11->8) ----

        # Row 11: Trucks, right
        lane = Lane(ROW_ROAD1, profile["road1"])
        tw = self._sw("truck-1", 60)
        truck_count = profile["trucks"]
        truck_spacing = (SCREEN_W + tw) // truck_count
        for i in range(truck_count):
            lane.objects.append(LaneObj(
                i * truck_spacing, tw, "truck-1",
                anim_prefix="truck-", anim_count=3, anim_speed=10))
        self.lanes.append(lane)

        # Row 10: Cars type 2, left
        lane = Lane(ROW_ROAD2, profile["road2"])
        cw2 = self._sw("car-2", 48)
        c2_spacing = (SCREEN_W + cw2) // 3
        for i in range(3):
            lane.objects.append(LaneObj(i * c2_spacing, cw2, "car-2"))
        self.lanes.append(lane)

        # Row 9: Race car lane (2nd from top road)
        lane = Lane(ROW_ROAD3, profile["road3"])
        cw3 = self._sw("car-3", 48)
        race_count = profile["race_cars"]
        if race_count <= 1:
            lane.objects.append(LaneObj((SCREEN_W - cw3) // 2, cw3, "car-3"))
        else:
            race_spacing = (SCREEN_W + cw3) // race_count
            for i in range(race_count):
                lane.objects.append(LaneObj(i * race_spacing, cw3, "car-3"))
        self.lanes.append(lane)

        # Row 8: Cars type 1, left
        lane = Lane(ROW_ROAD4, profile["road4"])
        cw1 = self._sw("car-1", 48)
        c1_spacing = (SCREEN_W + cw1) // 3
        for i in range(3):
            lane.objects.append(LaneObj(i * c1_spacing, cw1, "car-1"))
        self.lanes.append(lane)

        # ---- RIVER LANES (rows 6->2) ----

        # Row 6: Turtles-3, left
        t3_dive = profile["t3_dive"]
        t3_period = max(TARGET_FPS * 3, int(TARGET_FPS * 8 / river_scale)) if t3_dive else 0
        lane = Lane(ROW_RIVER1, profile["river1"], is_river=True)
        t3w = self._sw("t3n1", 90)
        t3s = (SCREEN_W + t3w) // 3
        for i in range(3):
            lane.objects.append(LaneObj(
                i * t3s, t3w, "t3n1", is_safe=True,
                can_dive=t3_dive, dive_period=t3_period,
                anim_prefix="t3n", anim_count=3, anim_speed=12,
                dive_anim_prefix="t3d", dive_anim_count=8))
        self.lanes.append(lane)

        # Row 5: Shortest logs, right (slower than longest logs)
        lane = Lane(ROW_RIVER2, profile["river2"], is_river=True)
        lsw = self._sw("log-3", 124)
        lss = (SCREEN_W + lsw) // 3 + 40
        for i in range(3):
            lane.objects.append(LaneObj(i * lss, lsw, "log-3", is_safe=True))
        self.lanes.append(lane)

        # Row 4: Longest logs, right — large spacing to avoid overlap
        lane = Lane(ROW_RIVER3, profile["river3"], is_river=True)
        llw = self._sw("log-2", 284)
        # Keep logs opposite on wrap cycle to avoid "one right behind another".
        lls = (SCREEN_W + llw) // 2
        for i in range(2):
            lane.objects.append(LaneObj(i * lls, llw, "log-2", is_safe=True))
        self.lanes.append(lane)

        # Row 3: Turtles-4, left
        t4_dive = profile["t4_dive"]
        t4_period = max(TARGET_FPS * 3, int(TARGET_FPS * 7 / river_scale)) if t4_dive else 0
        lane = Lane(ROW_RIVER4, profile["river4"], is_river=True)
        t4w = self._sw("t4n1", 120)
        t4s = (SCREEN_W + t4w) // 3
        for i in range(3):
            can_dive = t4_dive and (i == 1)
            lane.objects.append(LaneObj(
                i * t4s, t4w, "t4n1", is_safe=True,
                can_dive=can_dive, dive_period=t4_period,
                anim_prefix="t4n", anim_count=3, anim_speed=12,
                dive_anim_prefix="t4d", dive_anim_count=8))
        self.lanes.append(lane)

        # Row 2 (top): Medium logs, right
        lane = Lane(ROW_RIVER5, profile["river5"], is_river=True)
        lmw = self._sw("log-1", 156)
        lms = (SCREEN_W + lmw) // 3 + 30
        for i in range(3):
            lane.objects.append(LaneObj(i * lms, lmw, "log-1", is_safe=True))
        self.lanes.append(lane)

        # Setup enemies for this level
        self._init_enemies()

    def _init_enemies(self):
        """Configure enemies based on current level."""
        profile = self._difficulty_profile()
        m = profile["enemy_mult"]

        # Floating crocodiles: replace selected logs with crocodile bodies.
        self.croc_logs = []
        if profile["croc_logs"]:
            cw = self._sw("crocodile-1", 128)
            candidates = []
            for lane in self.lanes:
                if lane.is_river and lane.speed > 0:
                    for obj in lane.objects:
                        if (obj.sprite_name.startswith("log-")
                                and abs(obj.w - cw) <= 40):
                            candidates.append((abs(obj.w - cw), lane, obj))
            candidates.sort(key=lambda item: item[0])
            used_rows = set()
            for _, lane, obj in candidates:
                if lane.row in used_rows:
                    continue
                old_w = obj.w
                obj.is_croc = True
                obj.w = cw
                # Keep crocodile head at the previous log's front edge.
                obj.x += old_w - cw
                self.croc_logs.append((lane, obj))
                used_rows.add(lane.row)
                if len(self.croc_logs) >= 3:
                    break
        croc_objs = {obj for _, obj in self.croc_logs}

        # Snake-2 on median
        self.snake2_active = profile["snake2"]
        if self.snake2_active:
            self.snake2_x = -50.0
            self.snake2_speed = 1.5 * m
            self.snake2_frame = 1
            self.snake2_anim_timer = 0

        # Snake-1 on log
        self.snake1_active = False
        self.snake1_obj = None
        self.snake1_lane = None
        self.snake1_rel_x = 0.0
        self.snake1_dir = 1
        self.snake1_speed = 0.0
        if profile["snake1"]:
            log_candidates = []
            for lane in self.lanes:
                if lane.is_river:
                    for obj in lane.objects:
                        if (obj.sprite_name == LONGEST_LOG_SPRITE
                                and obj not in croc_objs):
                            log_candidates.append((lane, obj))
            if log_candidates:
                self.snake1_active = True
                self.snake1_lane, self.snake1_obj = random.choice(log_candidates)
                self.snake1_frame = 1
                self.snake1_anim_timer = 0
                sw = self._sw("snake-1-1", 30)
                max_rel = max(0.0, float(self.snake1_obj.w - sw))
                self.snake1_rel_x = max_rel * 0.5
                self.snake1_dir = random.choice((-1, 1))
                self.snake1_speed = 0.9 * m

        # Beaver
        self.beaver_active = profile["beaver"]
        self.beaver_lane = None
        self.beaver_anchor_obj = None
        if self.beaver_active:
            self.beaver_row = ROW_RIVER3
            self.beaver_lane = self._get_lane(self.beaver_row)
            if self.beaver_lane and len(self.beaver_lane.objects) >= 2:
                self.beaver_anchor_obj = random.choice(self.beaver_lane.objects)
                bx = self._beaver_between_logs_x()
                if bx is not None:
                    self.beaver_x = bx
                else:
                    self.beaver_active = False
            else:
                self.beaver_active = False

        # Croc animation reset
        self.croc_frame = 1
        self.croc_timer = 0
        self.croc_mouth_open = False

        # Bay events reset
        self.home_event = [0] * 5
        self.home_event_timer = [0] * 5
        self.bay_cooldown = random.randint(BAY_COOLDOWN_MIN, BAY_COOLDOWN_MAX)

        # Bonus on log reset
        self.bonus_log_obj = None
        self.bonus_log_lane = None
        self.bonus_log_timer = 0
        self.bonus_log_cooldown = random.randint(
            BONUS_LOG_COOLDOWN_MIN, BONUS_LOG_COOLDOWN_MAX)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def get_input(self):
        d = DIR_NONE
        if self.joy:
            d = _joy_direction(self.joy)
        if d == DIR_NONE and self.tch:
            d = self.tch.get_input()
        return d

    def check_any(self):
        if self.joy and _joy_center(self.joy):
            return True
        if self.tch and self.tch.check_center():
            return True
        return self.get_input() != DIR_NONE

    def _get_lane(self, row):
        for lane in self.lanes:
            if lane.row == row:
                return lane
        return None

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self):
        # Death/drown animation
        if self.state in (ST_DYING, ST_DROWN):
            self.state_timer -= 1
            if self.state_timer <= 0:
                if self.lives <= 0:
                    self.state = ST_GAME_OVER
                    self.game_over_x = -200.0
                else:
                    self._respawn()
            return

        # Game over — lanes keep animating
        if self.state == ST_GAME_OVER:
            for lane in self.lanes:
                lane.update()
            return

        # Level complete pause
        if self.state == ST_LEVEL_COMPLETE:
            # Keep scene alive during short level transition
            for lane in self.lanes:
                lane.update()
            self._update_enemies()
            self.state_timer -= 1
            if self.state_timer <= 0:
                # Short blackout while rebuilding next level state
                self.d.fill_color(C_BLACK)
                self.d.swap_buffers(copy=False)
                self._next_level()
            return

        # ---- ST_PLAYING ----

        for lane in self.lanes:
            lane.update()

        self.frog.update_jump()

        # River drift
        if not self.frog.jumping and self.frog.gy in RIVER_ROWS:
            lane = self._get_lane(self.frog.gy)
            if lane:
                obj = self._find_obj_under_frog(lane)
                if obj and obj.is_safe and not obj.is_submerged():
                    self.frog.px += lane.speed
                    self.frog.on_obj = obj
                    if self.frog.px < -CELL or self.frog.px > SCREEN_W:
                        self._kill("drown")
                        return
                    self.frog.gx = max(0, min(COLS - 1, int(self.frog.px / CELL + 0.5)))
                else:
                    self.frog.on_obj = None
                    self._kill("drown")
                    return

        # Collision (road/home)
        if not self.frog.jumping:
            self._check_collisions()
        if self.state != ST_PLAYING:
            return

        # Bay events, bonus on log, enemies
        self._update_bay_events()
        self._update_bonus_log()
        self._update_enemies()
        if self.state != ST_PLAYING:
            return

        # Timer countdown
        self.time_left -= 1
        if self.time_left <= 0:
            self._kill("death")

    # ------------------------------------------------------------------
    # Bay events (bonus frog / crocodile in home bays)
    # ------------------------------------------------------------------
    def _update_bay_events(self):
        profile = self._difficulty_profile()

        # Tick active events
        for i in range(5):
            if self.home_event[i] != 0:
                self.home_event_timer[i] -= 1
                if self.home_event_timer[i] <= 0:
                    self.home_event[i] = 0

        # Keep at most one visible bonus event and one croc event.
        bonus_slots = [i for i, ev in enumerate(self.home_event) if ev == 1]
        croc_slots = [i for i, ev in enumerate(self.home_event) if ev == 2]
        for idx in bonus_slots[1:]:
            self.home_event[idx] = 0
            self.home_event_timer[idx] = 0
        for idx in croc_slots[1:]:
            self.home_event[idx] = 0
            self.home_event_timer[idx] = 0

        if not profile["bay_bonus"] and not profile["bay_croc"]:
            return

        # Spawn cooldown
        self.bay_cooldown -= 1
        if self.bay_cooldown > 0:
            return
        self.bay_cooldown = random.randint(BAY_COOLDOWN_MIN, BAY_COOLDOWN_MAX)

        empty = [i for i in range(5)
                 if not self.home_bays[i] and self.home_event[i] == 0]
        if not empty:
            return

        has_bonus = any(ev == 1 for ev in self.home_event)
        has_croc = any(ev == 2 for ev in self.home_event)
        spawn_bonus = profile["bay_bonus"] and not has_bonus
        spawn_croc = profile["bay_croc"] and not has_croc
        if not spawn_bonus and not spawn_croc:
            return

        idx = random.choice(empty)
        if spawn_croc and spawn_bonus and random.random() < 0.35:
            self.home_event[idx] = 2  # crocodile
        elif spawn_bonus:
            self.home_event[idx] = 1  # bonus
        elif spawn_croc:
            self.home_event[idx] = 2  # crocodile
        if self.home_event[idx] != 0:
            self.home_event_timer[idx] = BAY_EVENT_DURATION

    # ------------------------------------------------------------------
    # Bonus frog on log
    # ------------------------------------------------------------------
    def _bonus_log_rect(self):
        obj = self.bonus_log_obj
        lane = self.bonus_log_lane
        if not obj or not lane:
            return None
        info = self.spr.get("frog-bv-1")
        bw, bh = (info[0], info[1]) if info else (32, 30)
        bx = int(obj.x + obj.w // 2 - bw // 2)
        by = lane.y + 2
        return bx, by, bw, bh

    def _frog_touches_bonus_log(self):
        if self.bonus_log_obj is None or self.bonus_log_lane is None:
            return False
        if self.frog.on_obj is not self.bonus_log_obj:
            return False

        rect = self._bonus_log_rect()
        if rect is None:
            return False
        bx, by, bw, bh = rect

        # Reuse compact frog hitbox shape used by obstacle collisions.
        fx = self.frog.px + 1
        fy = self.frog.py + 4
        fw = 28
        fh = 22
        return (fx + fw > bx + 2 and fx < bx + bw - 2
                and fy + fh > by + 2 and fy < by + bh - 2)

    def _update_bonus_log(self):
        if not self._difficulty_profile()["bonus_log"]:
            return

        if self.bonus_log_obj is not None:
            if not self.frog.jumping and self._frog_touches_bonus_log():
                # Collected! Frog turns pink — bonus awarded on delivery
                self.frog.has_bonus = True
                self.bonus_log_obj = None
                self.bonus_log_lane = None
        else:
            self.bonus_log_cooldown -= 1
            if self.bonus_log_cooldown <= 0:
                croc_objs = {obj for _, obj in self.croc_logs}
                candidates = []
                for lane in self.lanes:
                    if lane.is_river:
                        for obj in lane.objects:
                            if (obj.sprite_name.startswith("log-")
                                    and obj not in croc_objs
                                    and obj is not self.snake1_obj):
                                candidates.append((lane, obj))
                if candidates:
                    self.bonus_log_lane, self.bonus_log_obj = random.choice(candidates)
                    self.bonus_log_timer = 0
                self.bonus_log_cooldown = random.randint(
                    BONUS_LOG_COOLDOWN_MIN, BONUS_LOG_COOLDOWN_MAX)

    # ------------------------------------------------------------------
    # Enemies
    # ------------------------------------------------------------------
    def _beaver_between_logs_x(self):
        lane = self.beaver_lane
        if not lane or len(lane.objects) < 2:
            return None

        bw = self._sw("beaver", 30)
        left = self.beaver_anchor_obj
        if left not in lane.objects:
            left = lane.objects[0]
            self.beaver_anchor_obj = left

        gap_start = left.x + left.w
        gap_w = None
        for obj in lane.objects:
            if obj is left:
                continue
            d = obj.x - gap_start
            if d <= 0:
                d += SCREEN_W
            if gap_w is None or d < gap_w:
                gap_w = d
        if gap_w is None:
            return None
        if gap_w <= bw + 8:
            return None

        bx = gap_start + (gap_w - bw) * 0.5
        while bx < -bw:
            bx += SCREEN_W
        while bx > SCREEN_W:
            bx -= SCREEN_W
        return bx

    def _update_enemies(self):
        # Snake-2 on median
        if self.snake2_active:
            self.snake2_x += self.snake2_speed
            if self.snake2_x > SCREEN_W - 30:
                self.snake2_speed = -abs(self.snake2_speed)
            elif self.snake2_x < 0:
                self.snake2_speed = abs(self.snake2_speed)
            self.snake2_anim_timer += 1
            if self.snake2_anim_timer >= 6:
                self.snake2_anim_timer = 0
                self.snake2_frame = self.snake2_frame % 8 + 1
            # Collision
            if (self.state == ST_PLAYING and not self.frog.jumping
                    and self.frog.gy == ROW_MEDIAN):
                sw = self._sw("snake-2-1", 30)
                if (self.frog.px + 26 > self.snake2_x + 4
                        and self.frog.px + 4 < self.snake2_x + sw - 4):
                    self._kill("death")
                    return

        # Snake-1 on log
        if self.snake1_active and self.snake1_obj is not None:
            sw = self._sw("snake-1-1", 30)
            max_rel = max(0.0, float(self.snake1_obj.w - sw))
            if max_rel > 0:
                self.snake1_rel_x += self.snake1_dir * self.snake1_speed
                if self.snake1_rel_x <= 0.0:
                    self.snake1_rel_x = 0.0
                    self.snake1_dir = 1
                elif self.snake1_rel_x >= max_rel:
                    self.snake1_rel_x = max_rel
                    self.snake1_dir = -1

            self.snake1_anim_timer += 1
            if self.snake1_anim_timer >= 6:
                self.snake1_anim_timer = 0
                self.snake1_frame = self.snake1_frame % 8 + 1
            if (self.state == ST_PLAYING and not self.frog.jumping
                    and self.frog.on_obj is self.snake1_obj):
                snake_x = self.snake1_obj.x + self.snake1_rel_x
                if (self.frog.px + 26 > snake_x + 4
                        and self.frog.px + 4 < snake_x + sw - 4):
                    self._kill("death")
                    return

        # Beaver
        if self.beaver_active:
            bx = self._beaver_between_logs_x()
            if bx is not None:
                self.beaver_x = bx
            bw = self._sw("beaver", 30)
            if (self.state == ST_PLAYING and not self.frog.jumping
                    and self.frog.gy == self.beaver_row):
                if (self.frog.px + 26 > self.beaver_x + 4
                        and self.frog.px + 4 < self.beaver_x + bw - 4):
                    self._kill("death")
                    return

        # Crocodile mouth animation
        if self.croc_logs:
            self.croc_timer += 1
            if self.croc_timer >= TARGET_FPS * 2:
                self.croc_timer = 0
                self.croc_mouth_open = not self.croc_mouth_open
                self.croc_frame = 2 if self.croc_mouth_open else 1
            # Collision: frog on croc log + near head + mouth open
            if (self.croc_mouth_open and self.state == ST_PLAYING
                    and not self.frog.jumping):
                for _, obj in self.croc_logs:
                    if self.frog.on_obj is obj:
                        if self.frog.px + 15 > obj.x + obj.w - 30:
                            self._kill("death")
                            return

    # ------------------------------------------------------------------
    # Collision helpers
    # ------------------------------------------------------------------
    def _find_obj_under_frog(self, lane):
        fx = self.frog.px + CELL // 2
        for obj in lane.objects:
            if obj.x <= fx <= obj.x + obj.w:
                if obj.is_submerged():
                    continue
                return obj
        return None

    def _check_collisions(self):
        row = self.frog.gy

        if row == ROW_HOME:
            self._check_home()
            return

        if row in ROAD_ROWS:
            lane = self._get_lane(row)
            if lane:
                frog_x = self.frog.px + 1
                frog_y = self.frog.py + 4
                for obj in lane.objects:
                    obj_y = lane.y + 3
                    if (frog_x + 28 > obj.x + 4 and
                            frog_x < obj.x + obj.w - 4 and
                            frog_y + 22 > obj_y and
                            frog_y < obj_y + CELL - 6):
                        self._kill("death")
                        return

    def _check_home(self):
        fx_center = int(self.frog.px + CELL // 2)
        for i, (x1, x2) in enumerate(HOME_BAY_X_RANGES):
            if x1 <= fx_center <= x2:
                # Already occupied
                if self.home_bays[i]:
                    self._kill("death")
                    return

                # Crocodile in bay = death
                if self.home_event[i] == 2:
                    self.home_event[i] = 0
                    self._kill("death")
                    return

                # Fill bay
                self.home_bays[i] = True
                pts = 200
                # Bonus event in bay
                if self.home_event[i] == 1:
                    pts += 200
                    self.home_event[i] = 0
                # Pink frog delivery
                if self.frog.has_bonus:
                    self.home_bonus[i] = True
                    pts += 200
                pts += (self.time_left // TARGET_FPS) * 10
                self.score += pts
                self.frogs_delivered += 1
                self.frogs_in_level += 1

                if all(self.home_bays):
                    self.score += 1000
                    self.state = ST_LEVEL_COMPLETE
                    self.state_timer = LEVEL_COMPLETE_FRAMES
                else:
                    self._respawn()
                return

        # Missed all bays — landed on bush
        self._kill("death")

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    def _kill(self, death_type):
        self.frog.alive = False
        self.lives -= 1
        if death_type == "drown":
            self.state = ST_DROWN
            self.state_timer = DROWN_FRAMES
        else:
            self.state = ST_DYING
            self.state_timer = DEATH_FRAMES

    def _respawn(self):
        self.frog.reset()
        self.frog_time_max = self._frog_time()
        self.time_left = self.frog_time_max
        self.state = ST_PLAYING
        # Clear bonus from log on respawn
        self.bonus_log_obj = None
        self.bonus_log_lane = None

    def _next_level(self):
        self.level += 1
        self.frogs_in_level = 0
        self.home_bays = [False] * 5
        self.home_bonus = [False] * 5
        self._setup_lanes()
        self._respawn()

    def handle_input(self, direction):
        if self.state != ST_PLAYING or direction == DIR_NONE:
            return
        if self.frog.start_jump(direction):
            if direction == DIR_UP and self.frog.gy < self.frog.furthest_row:
                self.score += 10
                self.frog.furthest_row = self.frog.gy

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
        d = self.d
        spr = self.spr
        _mono = time.monotonic

        # 1. Background (pre-converted RGB565, no BMP decode per frame)
        _t0 = _mono()
        d.blit_buffer(0, 0, spr.bg_w, spr.bg_h, spr.bg_buf, dest_is_swapped=True)
        _t1 = _mono()

        # 2. Home bays (filled + events)
        self._draw_home_bays()

        # 3. Lane objects — inlined for speed (avoids ~60 Python function calls)
        _cache = spr._cache
        _bb = d.blit_buffer
        _TR = TRANSPARENT
        _SW = SCREEN_W
        _C = CELL
        _RO = ROAD_OBJ_Y_OFFSET
        _cf = self.croc_frame
        for lane in self.lanes:
            ly = lane.row * _C
            is_riv = lane.is_river
            for obj in lane.objects:
                if obj.is_croc:
                    sn = _CROC_N[_cf]
                else:
                    sn = obj.current_sprite()
                if not sn:
                    continue
                data = _cache.get(sn)
                if not data:
                    continue
                w, h, buf = data
                x = int(obj.x)
                if x + w <= 0 or x >= _SW:
                    continue
                y = ly + (_C - h) // 2
                if not is_riv:
                    y += _RO
                if x >= 0 and x + w <= _SW:
                    _bb(x, y, w, h, buf, dest_is_swapped=True, transparent_color=_TR)
                else:
                    sx1 = max(0, -x)
                    sx2 = min(w, _SW - x)
                    dx = max(0, x)
                    if sx2 > sx1:
                        _bb(dx, y, w, h, buf, dest_is_swapped=True,
                            transparent_color=_TR,
                            src_x1=sx1, src_y1=0, src_x2=sx2, src_y2=h)
        _t2 = _mono()

        # 4. Overlay sprites on logs: bonus frog, snake-1
        if self.bonus_log_obj is not None:
            self._draw_bonus_log()
        if self.snake1_active and self.snake1_obj is not None:
            self._draw_snake1()

        # 5. Beaver on river
        if self.beaver_active:
            lane_speed = self.beaver_lane.speed if self.beaver_lane else 0.0
            bname = "beaver-l" if lane_speed < 0 else "beaver"
            info = self.spr.get(bname)
            bh = info[1] if info else 24
            by = self.beaver_row * CELL + (CELL - bh) // 2
            self._blit(bname, int(self.beaver_x), by)

        # 6. Snake-2 on median
        if self.snake2_active:
            name = (_SNAKE2_L if self.snake2_speed < 0 else _SNAKE2_R)[self.snake2_frame]
            info = self.spr.get(name)
            sh = info[1] if info else 24
            sy = ROW_MEDIAN * CELL + (CELL - sh) // 2
            self._blit(name, int(self.snake2_x), sy)
        _t3 = _mono()

        # 8. HUD
        self._draw_hud()
        _t4 = _mono()

        # 9. GAME OVER on longest log
        if self.state == ST_GAME_OVER:
            lane = self._get_lane(ROW_RIVER3)
            if lane and lane.objects:
                obj = lane.objects[0]
                go_info = self.spr.get("game-over")
                if go_info:
                    go_w, go_h = go_info[0], go_info[1]
                    go_x = int(obj.x + (obj.w - go_w) // 2)
                    go_y = lane.y + (CELL - go_h) // 2
                    self._blit("game-over", go_x, go_y)

        # 10. Frog (or death/drown animation) drawn last
        if self.frog.alive:
            self._draw_frog()
        elif self.state == ST_DYING:
            elapsed = DEATH_FRAMES - self.state_timer
            frame = min(4, max(1, 1 + elapsed * 4 // DEATH_FRAMES))
            self._blit(_DEATH_N[frame], int(self.frog.px), int(self.frog.py))
        elif self.state == ST_DROWN:
            elapsed = DROWN_FRAMES - self.state_timer
            frame = min(5, max(1, 1 + elapsed * 5 // DROWN_FRAMES))
            self._blit(_DROWN_N[frame], int(self.frog.px), int(self.frog.py))

        _t5 = _mono()
        d.swap_buffers(copy=False)
        _t6 = _mono()

        # Timing data (ms) — stored for periodic log
        self._dt_bg = int((_t1 - _t0) * 1000)
        self._dt_lanes = int((_t2 - _t1) * 1000)
        self._dt_enemies = int((_t3 - _t2) * 1000)
        self._dt_hud = int((_t4 - _t3) * 1000)
        self._dt_frog = int((_t5 - _t4) * 1000)
        self._dt_swap = int((_t6 - _t5) * 1000)

    def _blit(self, name, x, y, transparent=True):
        data = self.spr.get(name)
        if not data:
            return
        w, h, buf = data

        if x + w <= 0 or x >= SCREEN_W or y + h <= 0 or y >= SCREEN_H:
            return

        if x >= 0 and x + w <= SCREEN_W and y >= 0 and y + h <= SCREEN_H:
            if transparent:
                self.d.blit_buffer(x, y, w, h, buf,
                                   dest_is_swapped=True,
                                   transparent_color=TRANSPARENT)
            else:
                self.d.blit_buffer(x, y, w, h, buf, dest_is_swapped=True)
            return

        sx1 = max(0, -x)
        sy1 = max(0, -y)
        sx2 = min(w, SCREEN_W - x)
        sy2 = min(h, SCREEN_H - y)
        dx = max(0, x)
        dy = max(0, y)

        if sx2 > sx1 and sy2 > sy1:
            if transparent:
                self.d.blit_buffer(dx, dy, w, h, buf,
                                   dest_is_swapped=True,
                                   transparent_color=TRANSPARENT,
                                   src_x1=sx1, src_y1=sy1,
                                   src_x2=sx2, src_y2=sy2)
            else:
                self.d.blit_buffer(dx, dy, w, h, buf,
                                   dest_is_swapped=True,
                                   src_x1=sx1, src_y1=sy1,
                                   src_x2=sx2, src_y2=sy2)

    def _draw_lane_obj(self, obj, lane):
        if obj.is_croc:
            sprite_name = _CROC_N[self.croc_frame]
        else:
            sprite_name = obj.current_sprite()
        if not sprite_name:
            return
        info = self.spr.get(sprite_name)
        if not info:
            return
        if lane.is_river:
            y = lane.y + (CELL - info[1]) // 2
        else:
            y = lane.y + (CELL - info[1]) // 2 + ROAD_OBJ_Y_OFFSET
        self._blit(sprite_name, int(obj.x), y)

    def _draw_frog(self):
        frog = self.frog
        dir_entry = _FROG_N[frog.direction]
        if dir_entry is None:
            return
        bonus_idx = 1 if frog.has_bonus else 0
        frame = min(frog.anim_frame, 6)
        name = dir_entry[bonus_idx][frame]
        info = self.spr.get(name)
        if not info:
            return
        if frog.gy in RIVER_ROWS:
            y = int(frog.py) + (CELL - info[1]) // 2
        else:
            y = int(frog.py) + (CELL - info[1]) // 2 + FROG_LAND_Y_OFFSET
            if frog.gy == ROW_START:
                y += FROG_START_EXTRA_Y
        self._blit(name, int(frog.px), y)

    def _draw_home_bays(self):
        for i in range(5):
            bx = HOME_X[i]
            by = ROW_HOME * CELL
            if self.home_bays[i]:
                name = "exit-frogger"
            elif self.home_event[i] == 1:
                name = "exit-bonus"
            elif self.home_event[i] == 2:
                name = "exit-crocodile"
            else:
                continue
            info = self.spr.get(name)
            if info:
                self._blit(name, bx - info[0] // 2 + HOME_FROG_X_SHIFT,
                           by + (CELL - info[1]) // 2)

    def _draw_bonus_log(self):
        rect = self._bonus_log_rect()
        if rect is None:
            return
        bx, by, _, _ = rect
        self._blit("frog-bv-1", bx, by)

    def _draw_snake1(self):
        obj = self.snake1_obj
        lane = self.snake1_lane
        if not obj or not lane:
            return
        sx = int(obj.x + self.snake1_rel_x)
        name = (_SNAKE1_L if self.snake1_dir < 0 else _SNAKE1_R)[self.snake1_frame]
        info = self.spr.get(name)
        sh = info[1] if info else 24
        sy = lane.y + (CELL - sh) // 2
        self._blit(name, sx, sy)

    def _draw_hud(self):
        # Score digits (top-left)
        score_str = f"{self.score:06d}"
        dw = 16
        d0 = self.spr.get(_SCORE_N[0])
        if d0:
            dw = d0[0]
        sx = SCORE_X
        for ch in score_str:
            self._blit(_SCORE_N[int(ch)], sx, SCORE_Y)
            sx += dw

        # Lives (top-right)
        life_info = self.spr.get("life")
        if life_info:
            lw, lh = life_info[0], life_info[1]
            gap = lw * 2
            total_w = self.lives * lw + max(0, self.lives - 1) * gap
            lx = SCREEN_W - total_w - 20
            ly = (CELL - lh) // 2
            for i in range(self.lives):
                self._blit("life", lx + i * (lw + gap), ly)

        # Time bar (bottom HUD, same line as "TIME" label)
        if self.frog_time_max > 0:
            time_frac = max(0, self.time_left / self.frog_time_max)
        else:
            time_frac = 1.0
        bar_max_w = SCREEN_W - TIME_BAR_X - TIME_BAR_RIGHT_PAD
        bar_w = int(bar_max_w * time_frac)
        if bar_w > 0:
            self.d.fill_rect(TIME_BAR_X, TIME_BAR_Y, bar_w, TIME_BAR_H, C_TIME_BAR)

        # High-score digits (bottom HUD, lower line)
        hi = max(self.high_score, self.score)
        hi_str = f"{hi:06d}"
        hdw = 16
        hd0 = self.spr.get(_HISCORE_N[0])
        if hd0:
            hdw = hd0[0]
        hx = 288
        for ch in hi_str:
            self._blit(_HISCORE_N[int(ch)], hx, HIGH_SCORE_Y)
            hx += hdw


# ==========================================================================
# Main
# ==========================================================================
def main(display=None):
    random.seed(int(time.monotonic() * 1000) & 0xFFFFFFFF)

    print("\n" + "=" * 40)
    print("  FROGGER — Waveshare ESP32-S3 AMOLED")
    print("=" * 40)

    # Init display (explicit double buffering when available)
    display_owned = display is None
    if display_owned:
        if hasattr(rm690b0, "BUFFER_DOUBLE"):
            display = rm690b0.RM690B0(buffer_mode=rm690b0.BUFFER_DOUBLE)
        else:
            display = rm690b0.RM690B0()
        display.init_display()
        try:
            import settings
            display.rotation = settings.rotation
        except ImportError:
            pass
        display.brightness = 1.0
    display.fill_color(C_BLACK)
    display.swap_buffers()

    # Determine BMP directory from script location
    if __file__ == "<stdin>":
        base = "/games"
    else:
        base = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."
    bmp_dir = base + "/frogger"

    # Shared I2C bus for joystick + touch
    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)

    joystick = None
    touch = None
    try:
        from joystick import Joystick
        joystick = Joystick(i2c=i2c)
        print("Joystick OK")
    except Exception as e:
        print(f"Joystick: {e}")
    try:
        if adafruit_focaltouch:
            touch = TouchInput(i2c)
            print("Touch OK")
    except Exception as e:
        print(f"Touch: {e}")

    if not joystick and not touch:
        print("No input devices!")
        if display_owned:
            display.deinit()
        return

    # Loading screen
    display.fill_color(C_BLACK)
    display.set_font(4)  # 24x32
    display.text(216, 170, "FROGGER", 0x07E0)
    display.set_font(2)  # 16x24
    display.text(232, 220, "Loading...", 0xFFFF)
    # Bar outline
    bar_x, bar_y, bar_max = 100, 260, 400
    display.fill_rect(bar_x - 2, bar_y - 2, bar_max + 4, 18, 0x4208)
    display.fill_rect(bar_x, bar_y, bar_max, 14, C_BLACK)
    display.swap_buffers(copy=True)

    def _loading_progress(loaded, total):
        pct = loaded / total if total > 0 else 0
        w = int(bar_max * pct)
        if w > 0:
            display.fill_rect(bar_x, bar_y, w, 14, 0x07E0)
        display.swap_buffers(copy=True)

    # Load all sprite assets
    sprites = Sprites(display, bmp_dir)
    sprites.load_all(progress_fn=_loading_progress)

    game = FroggerGame(display, sprites, joystick, touch)

    try:
        while True:
            # --- New game ---
            game.score = 0
            game.lives = 5
            game.level = 1
            game.frogs_in_level = 0
            game.frogs_delivered = 0
            game.home_bays = [False] * 5
            game.home_bonus = [False] * 5
            game._setup_lanes()
            game.frog.reset()
            game.frog_time_max = game._frog_time()
            game.time_left = game.frog_time_max
            game.state = ST_PLAYING

            game.draw()

            # Debounce
            while game.check_any():
                display.swap_buffers()
                time.sleep(0.05)

            # --- Game loop ---
            last = time.monotonic()
            log_t = last
            fps_count = 0
            fps_min_dt = 1.0
            fps_max_dt = 0.0
            fps_sum_dt = 0.0

            while True:
                now = time.monotonic()
                if now - last >= FRAME_TIME:
                    frame_dt = now - last
                    # Keep pacing stable under jitter; avoid drift over time.
                    last += FRAME_TIME
                    if now - last > FRAME_TIME * 4:
                        last = now

                    _mono = time.monotonic

                    _ti0 = _mono()
                    inp = game.get_input()
                    _ti1 = _mono()

                    if game.state == ST_GAME_OVER:
                        if game.check_any():
                            break
                    else:
                        game.handle_input(inp)

                    _tu0 = _mono()
                    game.update()
                    _tu1 = _mono()
                    game.draw()
                    _td1 = _mono()

                    # FPS tracking
                    fps_count += 1
                    frame_actual = _td1 - now
                    if frame_actual < fps_min_dt:
                        fps_min_dt = frame_actual
                    if frame_actual > fps_max_dt:
                        fps_max_dt = frame_actual
                    fps_sum_dt += frame_actual

                    if _td1 - log_t >= 3.0:
                        avg_dt = fps_sum_dt / fps_count if fps_count else 0
                        avg_fps = 1.0 / avg_dt if avg_dt > 0 else 0
                        dt_inp = int((_ti1 - _ti0) * 1000)
                        dt_upd = int((_tu1 - _tu0) * 1000)
                        dt_draw = int((_td1 - _tu1) * 1000)
                        print(f"FPS:{avg_fps:.0f} "
                              f"inp:{dt_inp} upd:{dt_upd} "
                              f"draw:{dt_draw}[bg:{game._dt_bg} "
                              f"lane:{game._dt_lanes} "
                              f"enm:{game._dt_enemies} "
                              f"hud:{game._dt_hud} "
                              f"frg:{game._dt_frog} "
                              f"swp:{game._dt_swap}]ms")
                        log_t = _td1
                        fps_count = 0
                        fps_min_dt = 1.0
                        fps_max_dt = 0.0
                        fps_sum_dt = 0.0
                else:
                    time.sleep(0.001)

            # Update high score
            if game.score > game.high_score:
                game.high_score = game.score

    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if joystick:
            joystick.deinit()
        i2c.deinit()
        display.fill_color(C_BLACK)
        display.swap_buffers()
        if display_owned:
            display.deinit()
        print("Frogger exited")


if __name__ == "__main__":
    main()
