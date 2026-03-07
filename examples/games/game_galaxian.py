# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
Galaxian Clone for Waveshare ESP32-S3 Touch AMOLED 2.41" (600x450, RM690B0).

Fixed-shooter: player at bottom, alien formation at top, dive-bombing, starfield.
Controls: Joystick (left/right + center=fire) or Touch (swipe=move, tap=fire).
"""

BASE_DIR = "/games"

import sys
import gc
import random
import time

import board
import busio
import rm690b0

try:
    from galaxian.sprites import build_sprites
except ImportError:
    if __file__ == "<stdin>":
        path = BASE_DIR
    else:
        path = "/" + __file__.rsplit("/", 1)[0] if "/" in __file__ else ""
    sys.path.insert(0, path)
    from galaxian.sprites import build_sprites

try:
    import adafruit_focaltouch
except ImportError:
    adafruit_focaltouch = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCREEN_W = 600
SCREEN_H = 450
TARGET_FPS = 30
HUD_HEIGHT = 24

# Formation layout
FORM_COLS = 10
FORM_ROWS = 6
COL_SPACING = 46
ROW_SPACING = 24
FORM_TOP = 70
FORM_X_START = (SCREEN_W - FORM_COLS * COL_SPACING) // 2  # 70

# Player
PLAYER_Y = 410
PLAYER_SPEED = 8
PLAYER_W = 24
PLAYER_H = 24

# Bullets
BULLET_W = 2
BULLET_H = 6
BULLET_SPEED = 10
MAX_ENEMY_BULLETS = 4

# Alien types per row (row 0=top, row 5=bottom)
# Row 0: Flagship (2), Row 1: Guard (6), Rows 2-3: Emissary (8 each), Rows 4-5: Drone (10 each)
ALIEN_SPRITE_W = 16
ALIEN_SPRITE_H = 16

# Stars
STAR_COUNT = 30
MAX_PARTICLES = 35

# Colors
BLACK = 0x0000
WHITE = 0xFFFF
YELLOW = rm690b0.YELLOW if hasattr(rm690b0, 'YELLOW') else 0xFFE0
RED = rm690b0.RED if hasattr(rm690b0, 'RED') else 0xF800
GREEN = rm690b0.GREEN if hasattr(rm690b0, 'GREEN') else 0x07E0

def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BULLET_COLOR = WHITE
ENEMY_BULLET_COLOR = rgb565(255, 100, 100)
HUD_COLOR = WHITE
LIVES_COLOR = rgb565(100, 160, 255)
GRAY_COLOR = rgb565(180, 180, 180)
STAR_COLORS = (rgb565(180, 180, 180), rgb565(220, 220, 220), WHITE)
EXPLOSION_COLORS = (
    rgb565(60, 120, 255),   # drone
    rgb565(180, 60, 255),   # emissary
    rgb565(255, 60, 60),    # guard
    rgb565(255, 220, 40),   # flagship
)

# Font
FONT_HUD = rm690b0.FONT_16x16
FONT_TITLE = rm690b0.FONT_24x24
CHAR_W_HUD = 16
CHAR_W_TITLE = 24

# Scoring
SCORE_IN_FORMATION = (30, 40, 50, 60)  # drone, emissary, guard, flagship
SCORE_DIVING = (60, 80, 100, 150)
SCORE_FLAGSHIP_ESCORT = (150, 200, 300)  # solo, +1 escort, +2 escorts

# Wave config: (dive_interval_frames, max_divers, enemy_bullet_speed, enemy_fire_chance)
WAVE_CONFIG = [
    (105, 1, 3, 0.3),
    (90,  2, 3, 0.4),
    (75,  2, 4, 0.5),
    (60,  3, 4, 0.6),
    (45,  3, 5, 0.7),
]

# ---------------------------------------------------------------------------
# Dive Paths — lists of (dx, dy) per step
# ---------------------------------------------------------------------------
DIVE_SWOOP_L = [
    (0,2),(0,2),(-2,2),(-3,2),(-4,2),(-4,1),(-3,1),
    (-2,2),(-1,3),(0,3),(1,3),(2,2),(2,2),(1,3),(0,3),(0,4),(0,4),(0,4),
]
DIVE_SWOOP_R = [(dx if dx == 0 else -dx, dy) for dx, dy in DIVE_SWOOP_L]

DIVE_STRAIGHT = [
    (0,2),(0,3),(1,3),(-1,3),(1,3),(-1,3),
    (0,4),(0,4),(0,4),(0,4),(0,4),(0,4),(0,4),(0,4),
]

DIVE_FLAGSHIP = [
    (0,1),(0,1),(-2,2),(-3,2),(-4,2),(-4,1),(-3,1),(-2,2),
    (-1,3),(0,3),(1,3),(2,3),(3,2),(3,1),(2,1),(1,2),
    (0,3),(-1,3),(-2,2),(-1,3),(0,3),(0,4),(0,4),(0,4),(0,4),
]

ALL_DIVE_PATHS = [DIVE_SWOOP_L, DIVE_SWOOP_R, DIVE_STRAIGHT]

# ---------------------------------------------------------------------------
# Hardware Input
# ---------------------------------------------------------------------------
PCA9554_ADDR = 0x21
PIN_UP = 0
PIN_DOWN = 1
PIN_RIGHT = 2
PIN_LEFT = 3
PIN_CENTER = 4

DIR_NONE = 0
DIR_LEFT = 1
DIR_RIGHT = 2
DIR_FIRE = 3


class PCA9554:
    def __init__(self, i2c, address=PCA9554_ADDR):
        self._i2c = i2c
        self._addr = address
        self._buf = bytearray(2)

    def init(self):
        self._buf[0] = 3
        self._buf[1] = 0b00011111
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(self._addr, self._buf)
        finally:
            self._i2c.unlock()
        self._buf[0] = 1
        self._buf[1] = 0b11100000
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(self._addr, self._buf)
        finally:
            self._i2c.unlock()

    def read(self):
        self._buf[0] = 0
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto_then_readfrom(
                self._addr, self._buf, self._buf, out_end=1, in_end=1)
            return self._buf[0]
        finally:
            self._i2c.unlock()


class JoystickInput:
    def __init__(self, i2c):
        self.pca = PCA9554(i2c)
        self.pca.init()

    def poll(self):
        try:
            val = self.pca.read()
        except OSError:
            return DIR_NONE
        if val == 0:
            return DIR_NONE
        if not (val & (1 << PIN_LEFT)):
            return DIR_LEFT
        if not (val & (1 << PIN_RIGHT)):
            return DIR_RIGHT
        if not (val & (1 << PIN_CENTER)):
            return DIR_FIRE
        return DIR_NONE


class TouchInput:
    def __init__(self, i2c):
        if adafruit_focaltouch is None:
            raise RuntimeError("adafruit_focaltouch required")
        self.touch = adafruit_focaltouch.Adafruit_FocalTouch(i2c)
        self.start_x = 0
        self.is_touching = False
        self.tap_fired = False

    def poll(self):
        if not self.touch.touched:
            self.is_touching = False
            self.tap_fired = False
            return DIR_NONE
        try:
            points = self.touch.touches
        except:
            return DIR_NONE
        if not points:
            self.is_touching = False
            self.tap_fired = False
            return DIR_NONE

        raw_x = points[0]["x"]
        raw_y = points[0]["y"]
        x = 600 - raw_y
        y = raw_x

        if not self.is_touching:
            self.start_x = x
            self.is_touching = True
            self.tap_fired = False
            return DIR_NONE

        dx = x - self.start_x
        if abs(dx) > 40:
            self.start_x = x
            return DIR_RIGHT if dx > 0 else DIR_LEFT

        if not self.tap_fired and y > 225:
            self.tap_fired = True
            return DIR_FIRE
        return DIR_NONE


# ---------------------------------------------------------------------------
# Alien container
# ---------------------------------------------------------------------------
class Alien:
    __slots__ = ('col', 'row', 'alien_type', 'alive',
                 'diving', 'dive_path', 'dive_step',
                 'x', 'y', 'escort_of')

    def __init__(self, col, row, alien_type):
        self.col = col
        self.row = row
        self.alien_type = alien_type  # 0=drone, 1=emissary, 2=guard, 3=flagship
        self.alive = True
        self.diving = False
        self.dive_path = None
        self.dive_step = 0
        self.x = 0.0
        self.y = 0.0
        self.escort_of = None


# ---------------------------------------------------------------------------
# Explosion particle
# ---------------------------------------------------------------------------
class Particle:
    __slots__ = ('x', 'y', 'dx', 'dy', 'life', 'color')

    def __init__(self, x, y, dx, dy, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.life = 15
        self.color = color


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self, display, sprites):
        self.display = display
        self.sprites = sprites

        # State machine: 0=TITLE, 1=PLAYING, 2=WAVE_CLEAR, 3=GAME_OVER
        self.state = 0
        self.state_timer = 0

        self.score = 0
        self.hi_score = 0
        self.lives = 3
        self.wave = 1

        # Player
        self.player_x = SCREEN_W // 2 - PLAYER_W // 2
        self.hit_flash = 0

        # Bullet (only 1 player bullet at a time)
        self.bullet_x = 0
        self.bullet_y = 0
        self.bullet_active = False

        # Enemy bullets
        self.enemy_bullets = []

        # Formation
        self.aliens = []
        self.form_base_x = FORM_X_START
        self.form_dir = 1
        self.form_speed = 1

        # Diving
        self.dive_timer = 0
        self.dive_interval = 105
        self.max_divers = 1
        self.enemy_bullet_speed = 3
        self.enemy_fire_chance = 0.3

        # Animation
        self.anim_frame = 0
        self.anim_counter = 0

        # Stars
        self.stars = []
        for _ in range(STAR_COUNT):
            sx = random.randint(0, SCREEN_W - 1)
            sy = random.randint(HUD_HEIGHT, SCREEN_H - 1)
            sp = random.choice((1, 2, 3))
            self.stars.append([sx, sy, sp])

        # Explosions (pre-allocated pool — zero runtime alloc)
        self.particles = [Particle(0, 0, 0, 0, 0) for _ in range(MAX_PARTICLES)]
        self.particle_count = 0

        # Alive tracking
        self.alive_count = 0

        # RNG pool (avoid per-frame random.random() in hot loop)
        self._rng_pool = [random.random() for _ in range(64)]
        self._rng_idx = 0

        # Profiler
        self.prof_frame = 0
        self.prof_accum = [0.0] * 6  # clear, stars, aliens, player, hud, swap
        self.prof_total = 0.0

        # Cached HUD strings (avoid str() alloc every frame)
        self._score_str = "0"
        self._hi_str = "0"
        self._prev_score = -1
        self._prev_hi = -1
        self._prev_lives = -1

        # Sprite lookup tables (avoid dict lookups in hot loop)
        self._spr_cache = []
        for f1key, f2key in (('drone_f1', 'drone_f2'),
                              ('emissary_f1', 'emissary_f2'),
                              ('guard_f1', 'guard_f2'),
                              ('flagship_f1', 'flagship_f2')):
            self._spr_cache.append((sprites[f1key][0], sprites[f2key][0]))
        self._spr_player = sprites['player'][0]

        # Cache display methods (bound once, used every frame)
        self._d_fill_color = display.fill_color
        self._d_pixel = display.pixel
        self._d_blit = display.blit_buffer
        self._d_fill_rect = display.fill_rect
        self._d_set_font = display.set_font
        self._d_text = display.text
        self._d_swap = display.swap_buffers

    def init_wave(self):
        gc.collect()
        self.aliens = []
        # Row 0: Flagship — cols 4,5 (2 units, centered)
        for c in range(4, 6):
            self.aliens.append(Alien(c, 0, 3))
        # Row 1: Guard — cols 2-7 (6 units)
        for c in range(2, 8):
            self.aliens.append(Alien(c, 1, 2))
        # Rows 2-3: Emissary — cols 1-8 (8 units each)
        for r in range(2, 4):
            for c in range(1, 9):
                self.aliens.append(Alien(c, r, 1))
        # Rows 4-5: Drone — cols 0-9 (10 units each)
        for r in range(4, 6):
            for c in range(FORM_COLS):
                self.aliens.append(Alien(c, r, 0))

        self.form_base_x = FORM_X_START
        self.form_dir = 1

        # Wave config
        wi = min(self.wave - 1, len(WAVE_CONFIG) - 1)
        cfg = WAVE_CONFIG[wi]
        self.dive_interval = cfg[0]
        self.max_divers = cfg[1]
        self.enemy_bullet_speed = cfg[2]
        self.enemy_fire_chance = cfg[3]
        self.dive_timer = self.dive_interval

        self.alive_count = len(self.aliens)
        self.enemy_bullets = []
        self.bullet_active = False
        self.particle_count = 0

    def start_game(self):
        gc.collect()
        self.score = 0
        self.lives = 3
        self.wave = 1
        self.player_x = SCREEN_W // 2 - PLAYER_W // 2
        self.hit_flash = 0
        self._prev_score = -1
        self._prev_hi = -1
        self._prev_lives = -1
        self.state = 1
        self.init_wave()

    # --- Formation movement ---
    def update_formation(self):
        base_x = self.form_base_x
        min_x = SCREEN_W
        max_x = 0
        for a in self.aliens:
            if a.alive and not a.diving:
                sx = base_x + a.col * COL_SPACING
                if sx < min_x:
                    min_x = sx
                if sx + ALIEN_SPRITE_W > max_x:
                    max_x = sx + ALIEN_SPRITE_W
                a.x = sx
                a.y = FORM_TOP + a.row * ROW_SPACING

        base_x += self.form_dir * self.form_speed
        self.form_base_x = base_x
        if max_x >= SCREEN_W - 10:
            self.form_dir = -1
        elif min_x <= 10:
            self.form_dir = 1

    # --- Diving ---
    def start_dive(self):
        # Count current divers
        num_divers = sum(1 for a in self.aliens if a.alive and a.diving)
        if num_divers >= self.max_divers:
            return

        # Pick random alive non-diving alien
        candidates = [a for a in self.aliens if a.alive and not a.diving]
        if not candidates:
            return

        alien = random.choice(candidates)

        if alien.alien_type == 3:
            # Flagship — takes 0-2 guard escorts
            alien.dive_path = DIVE_FLAGSHIP
            alien.dive_step = 0
            alien.diving = True
            guards = [a for a in self.aliens if a.alive and not a.diving and a.alien_type == 2]
            num_escorts = min(len(guards), random.randint(0, 2))
            for i in range(num_escorts):
                g = guards[i]
                g.diving = True
                g.dive_path = DIVE_FLAGSHIP
                g.dive_step = 0
                g.escort_of = alien
        else:
            path = random.choice(ALL_DIVE_PATHS)
            alien.dive_path = path
            alien.dive_step = 0
            alien.diving = True

    def update_divers(self):
        for a in self.aliens:
            if not a.alive or not a.diving:
                continue
            if a.dive_step < len(a.dive_path):
                dx, dy = a.dive_path[a.dive_step]
                a.x += dx
                a.y += dy
                a.dive_step += 1
            else:
                # Continue straight down
                a.y += 5

            # Enemy fire while diving (RNG pool lookup)
            idx = self._rng_idx
            self._rng_idx = (idx + 1) & 63
            if self._rng_pool[idx] < self.enemy_fire_chance * 0.1:
                if len(self.enemy_bullets) < MAX_ENEMY_BULLETS:
                    self.enemy_bullets.append([
                        int(a.x) + ALIEN_SPRITE_W // 2,
                        int(a.y) + ALIEN_SPRITE_H,
                        self.enemy_bullet_speed])

            # Off screen bottom — return to formation
            if a.y > SCREEN_H + 20:
                a.diving = False
                a.dive_path = None
                a.dive_step = 0
                a.escort_of = None
                a.x = self.form_base_x + a.col * COL_SPACING
                a.y = FORM_TOP + a.row * ROW_SPACING

            # Clamp x to screen
            if a.x < 0:
                a.x = 0
            elif a.x > SCREEN_W - ALIEN_SPRITE_W:
                a.x = SCREEN_W - ALIEN_SPRITE_W

    # --- Bullets ---
    def update_bullets(self):
        # Player bullet
        if self.bullet_active:
            self.bullet_y -= BULLET_SPEED
            if self.bullet_y < 0:
                self.bullet_active = False

        # Enemy bullets (swap-and-pop: O(1) removal)
        eb = self.enemy_bullets
        i = 0
        n = len(eb)
        while i < n:
            b = eb[i]
            b[1] += b[2]
            if b[1] > SCREEN_H:
                n -= 1
                eb[i] = eb[n]
                eb.pop()
            else:
                i += 1

    # --- Collision ---
    def check_collisions(self):
        # Player bullet vs aliens
        if self.bullet_active:
            bx = self.bullet_x
            by = self.bullet_y
            for a in self.aliens:
                if not a.alive:
                    continue
                ax = int(a.x)
                ay = int(a.y)
                if (bx + BULLET_W > ax and bx < ax + ALIEN_SPRITE_W and
                        by + BULLET_H > ay and by < ay + ALIEN_SPRITE_H):
                    # Hit!
                    a.alive = False
                    self.alive_count -= 1
                    self.bullet_active = False

                    # Score
                    if a.diving:
                        if a.alien_type == 3:
                            # Flagship — check escorts
                            escorts = sum(1 for e in self.aliens
                                          if e.escort_of is a and e.alive)
                            idx = min(escorts, 2)
                            pts = SCORE_FLAGSHIP_ESCORT[idx]
                        else:
                            pts = SCORE_DIVING[a.alien_type]
                    else:
                        pts = SCORE_IN_FORMATION[a.alien_type]
                    self.score += pts
                    if self.score > self.hi_score:
                        self.hi_score = self.score

                    # Spawn explosion
                    self._spawn_explosion(ax + ALIEN_SPRITE_W // 2,
                                          ay + ALIEN_SPRITE_H // 2, a.alien_type)

                    # If flagship killed, free escorts
                    if a.alien_type == 3:
                        for e in self.aliens:
                            if e.escort_of is a:
                                e.escort_of = None
                    break

        # Enemy bullets vs player
        px = self.player_x
        py = PLAYER_Y
        eb = self.enemy_bullets
        for i in range(len(eb)):
            b = eb[i]
            if (b[0] + 2 > px and b[0] < px + PLAYER_W and
                    b[1] + 4 > py and b[1] < py + PLAYER_H):
                eb[i] = eb[-1]
                eb.pop()
                self._player_hit()
                break

        # Diving aliens vs player (body collision)
        for a in self.aliens:
            if a.alive and a.diving:
                ax = int(a.x)
                ay = int(a.y)
                if (ax + ALIEN_SPRITE_W > px and ax < px + PLAYER_W and
                        ay + ALIEN_SPRITE_H > py and ay < py + PLAYER_H):
                    a.alive = False
                    self.alive_count -= 1
                    self._spawn_explosion(ax + ALIEN_SPRITE_W // 2,
                                          ay + ALIEN_SPRITE_H // 2, a.alien_type)
                    self._player_hit()
                    break

    def _player_hit(self):
        self.lives -= 1
        self.hit_flash = 10
        self.bullet_active = False
        self.enemy_bullets.clear()
        if self.lives <= 0:
            gc.collect()
            self.state = 3  # GAME_OVER
            self.state_timer = 90

    def _spawn_explosion(self, cx, cy, alien_type):
        c = EXPLOSION_COLORS[alien_type]
        _randint = random.randint
        _particles = self.particles
        _count = self.particle_count
        for _ in range(7):
            if _count >= MAX_PARTICLES:
                break
            p = _particles[_count]
            p.x = cx
            p.y = cy
            p.dx = _randint(-4, 4)
            p.dy = _randint(-4, 4)
            p.life = 15
            p.color = c
            _count += 1
        self.particle_count = _count

    def update_particles(self):
        _particles = self.particles
        i = 0
        n = self.particle_count
        while i < n:
            p = _particles[i]
            p.x += p.dx
            p.y += p.dy
            p.life -= 1
            if p.life <= 0:
                n -= 1
                _particles[i], _particles[n] = _particles[n], _particles[i]
            else:
                i += 1
        self.particle_count = n

    # --- Stars ---
    def update_stars(self):
        for s in self.stars:
            s[1] += s[2]
            if s[1] >= SCREEN_H:
                s[1] = HUD_HEIGHT
                s[0] = random.randint(0, SCREEN_W - 1)

    # --- Main update ---
    def update(self, inp):
        if self.state == 0:
            # TITLE
            if inp == DIR_FIRE or inp == DIR_LEFT or inp == DIR_RIGHT:
                self.start_game()
            return

        if self.state == 3:
            # GAME_OVER
            self.state_timer -= 1
            if self.state_timer <= 0:
                if inp != DIR_NONE:
                    gc.collect()
                    self.state = 0
            return

        if self.state == 2:
            # WAVE_CLEAR
            self.state_timer -= 1
            self.update_stars()
            if self.state_timer <= 0:
                self.wave += 1
                self.init_wave()
                self.state = 1
            return

        # PLAYING
        # Player movement
        if self.hit_flash > 0:
            self.hit_flash -= 1
        else:
            if inp == DIR_LEFT:
                self.player_x -= PLAYER_SPEED
                if self.player_x < 0:
                    self.player_x = 0
            elif inp == DIR_RIGHT:
                self.player_x += PLAYER_SPEED
                if self.player_x > SCREEN_W - PLAYER_W:
                    self.player_x = SCREEN_W - PLAYER_W
            elif inp == DIR_FIRE:
                if not self.bullet_active:
                    self.bullet_active = True
                    self.bullet_x = self.player_x + PLAYER_W // 2 - BULLET_W // 2
                    self.bullet_y = PLAYER_Y - BULLET_H

        # Animation toggle
        self.anim_counter += 1
        if self.anim_counter >= 8:
            self.anim_counter = 0
            self.anim_frame = 1 - self.anim_frame

        self.update_formation()
        self.update_divers()
        self.update_bullets()
        self.check_collisions()
        self.update_particles()
        self.update_stars()

        # Dive timer
        self.dive_timer -= 1
        if self.dive_timer <= 0:
            self.start_dive()
            self.dive_timer = self.dive_interval

        # Check wave clear
        if self.alive_count <= 0:
            self.state = 2  # WAVE_CLEAR
            self.state_timer = 45

    # --- Rendering ---
    def draw(self):
        _mono = time.monotonic
        _blit = self._d_blit
        _fill_rect = self._d_fill_rect
        _fill_color = self._d_fill_color
        _hud_h = HUD_HEIGHT
        _pixel = self._d_pixel
        _set_font = self._d_set_font
        _text = self._d_text
        _swap = self._d_swap

        t0 = _mono()

        # 1. Clear
        _fill_rect(0, _hud_h, SCREEN_W, SCREEN_H - _hud_h, BLACK)
        t1 = _mono()

        # 2. Stars
        _sc = STAR_COLORS
        for s in self.stars:
            _pixel(s[0], s[1], _sc[s[2] - 1])
        t2 = _mono()

        # 3. Aliens (formation + diving)
        af = self.anim_frame
        cache = self._spr_cache
        _ASW = ALIEN_SPRITE_W
        _ASH = ALIEN_SPRITE_H
        for a in self.aliens:
            if not a.alive:
                continue
            ax = int(a.x)
            ay = int(a.y)
            if ay < -_ASH or ay > SCREEN_H:
                continue
            _blit(ax, ay, _ASW, _ASH, cache[a.alien_type][af])

        # Particles
        _parts = self.particles
        for _pi in range(self.particle_count):
            p = _parts[_pi]
            _fill_rect(int(p.x), int(p.y), 3, 3, p.color)

        t3 = _mono()

        # 4. Player
        if self.hit_flash > 0 and (self.hit_flash & 1 == 0):
            pass  # Flash: skip drawing every other frame
        elif self.state == 1 or self.state == 2:
            _blit(self.player_x, PLAYER_Y, PLAYER_W, PLAYER_H, self._spr_player)

        # 5. Bullets
        if self.bullet_active:
            _fill_rect(self.bullet_x, self.bullet_y, BULLET_W, BULLET_H, BULLET_COLOR)
        for b in self.enemy_bullets:
            _fill_rect(b[0], b[1], 2, 4, ENEMY_BULLET_COLOR)

        t4 = _mono()

        # 6. HUD
        if self.score != self._prev_score:
            self._score_str = str(self.score)
            self._prev_score = self.score
        if self.hi_score != self._prev_hi:
            self._hi_str = str(self.hi_score)
            self._prev_hi = self.hi_score
        if self.lives != self._prev_lives:
            self._prev_lives = self.lives

        _fill_rect(0, 0, SCREEN_W, _hud_h, BLACK)
        _set_font(FONT_HUD)
        _text(10, 4, "1UP", color=RED)
        _text(60, 4, self._score_str, color=HUD_COLOR)
        _text(260, 4, "HI", color=RED)
        _text(300, 4, self._hi_str, color=HUD_COLOR)

        _lc = LIVES_COLOR
        for i in range(self.lives):
            _fill_rect(540 + i * 18, 6, 12, 12, _lc)

        # Wave indicator
        if self.state == 2:
            _text(240, 220, "WAVE CLEAR", color=YELLOW)

        t5 = _mono()

        # 7. Swap
        _swap(copy=False)
        t6 = _mono()

        # Profiler accumulation
        pa = self.prof_accum
        pa[0] += t1 - t0
        pa[1] += t2 - t1
        pa[2] += t3 - t2
        pa[3] += t4 - t3
        pa[4] += t5 - t4
        pa[5] += t6 - t5
        self.prof_total += t6 - t0
        self.prof_frame += 1

        n = self.prof_frame
        if n >= 90:
            avg = self.prof_total / n * 1000
            fps = n / self.prof_total if self.prof_total > 0 else 0
            print(f"FPS:{fps:.1f} avg:{avg:.1f}ms "
                  f"clr:{pa[0]/n*1000:.1f} star:{pa[1]/n*1000:.1f} "
                  f"alien:{pa[2]/n*1000:.1f} plyr:{pa[3]/n*1000:.1f} "
                  f"hud:{pa[4]/n*1000:.1f} swap:{pa[5]/n*1000:.1f}")
            self.prof_frame = 0
            self.prof_accum = [0.0] * 6
            self.prof_total = 0.0

    def draw_title(self):
        d = self.display
        d.fill_color(BLACK)

        txt = "GALAXIAN"
        sub = "Press any key"
        tx = (SCREEN_W - len(txt) * 24) // 2
        sx = (SCREEN_W - len(sub) * 16) // 2

        d.set_font(4)
        d.text(tx, 160, txt, color=0x07E0)
        d.set_font(2)
        d.text(sx, 220, sub, color=WHITE)

        if self.hi_score > 0:
            hi = f"BEST {self.hi_score}"
            hx = (SCREEN_W - len(hi) * 16) // 2
            d.text(hx, 260, hi, color=WHITE)

        d.swap_buffers(copy=True)

    def draw_game_over(self):
        d = self.display
        d.fill_color(BLACK)

        for s in self.stars:
            d.pixel(s[0], s[1], STAR_COLORS[s[2] - 1])

        d.set_font(FONT_TITLE)
        txt = "GAME OVER"
        tx = (SCREEN_W - len(txt) * CHAR_W_TITLE) // 2
        d.text(tx, 170, txt, color=RED)

        d.set_font(FONT_HUD)
        sc = f"SCORE  {self.score}"
        sx = (SCREEN_W - len(sc) * CHAR_W_HUD) // 2
        d.text(sx, 230, sc, color=WHITE)

        hi = f"HI SCORE  {self.hi_score}"
        hx = (SCREEN_W - len(hi) * CHAR_W_HUD) // 2
        d.text(hx, 260, hi, color=GRAY_COLOR)

        sub = "PRESS FIRE"
        px = (SCREEN_W - len(sub) * CHAR_W_HUD) // 2
        d.text(px, 320, sub, color=YELLOW)

        d.swap_buffers()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    seed = int(time.monotonic() * 1000) & 0xFFFFFFFF
    random.seed(seed)

    print("\n" + "=" * 50)
    print("  GALAXIAN CLONE")
    print("=" * 50)

    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0
    display.swap_buffers()

    print("Building sprites...")
    sprites = build_sprites()
    print(f"  {len(sprites)} sprites built")

    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)

    joystick = None
    touch = None
    try:
        joystick = JoystickInput(i2c)
        print("Joystick OK")
    except Exception as e:
        print(f"Joystick fail: {e}")
    try:
        touch = TouchInput(i2c)
        print("Touch OK")
    except Exception as e:
        print(f"Touch fail: {e}")

    if not joystick and not touch:
        print("No input devices!")
        display.deinit()
        return

    game = Game(display, sprites)

    _mono = time.monotonic
    _sleep = time.sleep
    frame_time = 1.0 / TARGET_FPS
    gc.collect()

    def get_input():
        d = DIR_NONE
        if joystick:
            d = joystick.poll()
        if d == DIR_NONE and touch:
            d = touch.poll()
        return d

    try:
        title_drawn = False
        go_drawn = False

        while True:
            frame_start = _mono()

            inp = get_input()
            prev_state = game.state
            game.update(inp)

            if game.state == 0:
                if not title_drawn or prev_state != 0:
                    game.draw_title()
                    title_drawn = True
                    go_drawn = False
                _sleep(0.05)
                continue

            if game.state == 3:
                if not go_drawn or prev_state != 3:
                    game.draw_game_over()
                    go_drawn = True
                    title_drawn = False
                _sleep(0.05)
                continue

            title_drawn = False
            go_drawn = False
            game.draw()

            elapsed = _mono() - frame_start
            if elapsed < frame_time:
                _sleep(frame_time - elapsed)

    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"\nCrash: {e}")
    finally:
        display.fill_color(BLACK)
        display.swap_buffers()
        display.deinit()
        try:
            i2c.deinit()
        except:
            pass
        print("Galaxian exited.")


if __name__ == "__main__":
    main()
