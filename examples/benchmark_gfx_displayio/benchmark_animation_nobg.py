"""
High FPS Bouncing Ball Animation — displayio version with pre-rendered sprites
===============================================================================

Demonstrates high-performance animation using:
- Pre-rendered ball sprites (rendered once, blitted every frame)
- Dirty region tracking (only refresh changed pixels)
- 2-pixel alignment for RM690B0 hardware
- Float+int position tracking for smooth motion
"""

import math
import random
import time

import board
import displayio
import bitmaptools
from rm690b0 import RM690B0, create_qspi_bus

# ============================================================================
# CONFIGURATION
# ============================================================================

DURATION = 15  # Animation duration in seconds
SPEED = 8.0  # Ball speed (pixels per frame)
BALL_RADIUS = 20
WIDTH = 600
HEIGHT = 450


def fill_circle(bitmap, cx, cy, r, color):
    """Draw a filled circle using scan lines with 2-pixel X alignment."""
    w = bitmap.width
    h = bitmap.height
    for dy in range(-r, r + 1):
        py = cy + dy
        if py < 0 or py >= h:
            continue
        dx = int(math.sqrt(r * r - dy * dy))
        # 2-pixel alignment for RM690B0 hardware
        x1 = max(0, cx - dx) & ~1  # Round down to even
        x2 = min(w, (cx + dx + 2) & ~1)  # Round up to even
        if x2 <= x1:
            x2 = min(w, x1 + 2)
        if x1 < x2:
            bitmaptools.fill_region(bitmap, x1, py, x2, py + 1, color)


def draw_circle(bitmap, cx, cy, r, color):
    """Draw a circle outline using Bresenham."""
    w = bitmap.width
    h = bitmap.height
    x = 0
    y = r
    d = 3 - 2 * r
    while x <= y:
        for px, py in (
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x),
            (cx + y, cy - x), (cx - y, cy - x),
        ):
            if 0 <= px < w and 0 <= py < h:
                bitmap[px, py] = color
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1


def pre_render_ball_sprite(radius):
    """Pre-render ball sprite with all details (shine, shadow, etc.)."""
    size = radius * 2 + 4  # +4 for 2px padding on each side
    sprite = displayio.Bitmap(size, size, 65536)
    sprite.fill(0x0000)  # Black background (will be treated as transparent)

    # Center of sprite
    cx = radius + 2
    cy = radius + 2

    # Draw all ball elements
    fill_circle(sprite, cx, cy, radius, 0xF800)  # Main red circle
    draw_circle(sprite, cx, cy, radius, 0x8800)  # Dark red outline

    inner_r = int(radius * 0.7)
    draw_circle(sprite, cx - int(radius * 0.15), cy - int(radius * 0.15), inner_r, 0xFD20)

    shine_x = cx - int(radius * 0.4)
    shine_y = cy - int(radius * 0.4)
    fill_circle(sprite, shine_x, shine_y, int(radius * 0.25), 0xFFE0)
    fill_circle(sprite, shine_x, shine_y, int(radius * 0.15), 0xFFFF)

    fill_circle(sprite, cx + int(radius * 0.3), cy + int(radius * 0.2), max(1, int(radius * 0.08)), 0xFDA0)
    fill_circle(sprite, cx - int(radius * 0.1), cy + int(radius * 0.4), max(1, int(radius * 0.08)), 0xFC00)

    shadow_y = cy + int(radius * 0.5)
    fill_circle(sprite, cx, shadow_y, int(radius * 0.3), 0x4000)

    return sprite


def _mark_ball_dirty(bitmap, prev_x, prev_y, x, y, radius):
    """Mark dirty region covering both previous and current ball positions."""
    # Calculate bounding box that includes both positions
    r = radius + 2  # sprite padding
    x1 = min(prev_x, x) - r
    y1 = min(prev_y, y) - r
    x2 = max(prev_x, x) + r
    y2 = max(prev_y, y) + r

    # 2-pixel X alignment for RM690B0 hardware
    x1 = max(0, x1) & ~1  # Round down to even
    y1 = max(0, y1)
    x2 = min(WIDTH, (x2 + 1) & ~1)  # Round up to even
    y2 = min(HEIGHT, y2)

    # Ensure minimum size
    if x2 <= x1:
        x2 = min(WIDTH, x1 + 2)
    if y2 <= y1:
        y2 = min(HEIGHT, y1 + 1)

    # Mark region as dirty
    bitmap.dirty(x1=x1, y1=y1, x2=x2, y2=y2)


class HighFPSBall:
    """High performance bouncing ball using pre-rendered sprites."""

    def __init__(self, x, y, vx, vy, radius, canvas, bg_bitmap):
        # Float positions for precise motion
        self.fx = float(x)
        self.fy = float(y)
        # Int positions (aligned) for rendering
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.canvas = canvas
        self.bg = bg_bitmap  # Background with border
        self.display_width = canvas.width
        self.display_height = canvas.height
        self.prev_x = x
        self.prev_y = y

        # Pre-render ball sprite once (huge performance boost!)
        print(f"Pre-rendering ball sprite ({radius * 2 + 4}x{radius * 2 + 4})...")
        self.sprite = pre_render_ball_sprite(radius)
        print("Sprite ready!")

    def update(self):
        # Update float positions
        self.fx += self.vx
        self.fy += self.vy

        # Convert to int with 2-pixel alignment for RM690B0 hardware stability
        self.x = int(self.fx) & ~1
        self.y = int(self.fy) & ~1

        # Wall collisions with position correction to prevent sprite clipping
        # IMPORTANT: Correct BOTH float and int positions to prevent drift
        margin = 2  # Small margin, border is protected by background restore
        if self.x - self.radius <= 0:
            self.fx = float(self.radius + margin)
            self.x = self.radius + margin
            self.vx = abs(self.vx)
        elif self.x + self.radius >= self.display_width - 1:
            self.fx = float(self.display_width - self.radius - margin)
            self.x = self.display_width - self.radius - margin
            self.vx = -abs(self.vx)

        if self.y - self.radius <= 0:
            self.fy = float(self.radius + margin)
            self.y = self.radius + margin
            self.vy = abs(self.vy)
        elif self.y + self.radius >= self.display_height - 1:
            self.fy = float(self.display_height - self.radius - margin)
            self.y = self.display_height - self.radius - margin
            self.vy = -abs(self.vy)

    def clear_previous(self):
        """Restore background at previous ball position."""
        x = int(self.prev_x)
        y = int(self.prev_y)
        r = self.radius + 2

        # Calculate region with 2-pixel X alignment for RM690B0 hardware
        x1 = max(0, x - r) & ~1  # Round down to even
        y1 = max(0, y - r)
        x2 = min(self.display_width, (x + r + 1) & ~1)  # Round up to even
        y2 = min(self.display_height, y + r)

        # Ensure x2 > x1 (minimum 2-pixel width)
        if x2 <= x1:
            x2 = min(self.display_width, x1 + 2)

        w = x2 - x1
        h = y2 - y1

        if w > 0 and h > 0:
            # Restore background (with border!)
            bitmaptools.blit(self.canvas, self.bg, x1, y1, x1=x1, y1=y1, x2=x2, y2=y2)

    def draw(self):
        """Blit pre-rendered sprite to canvas."""
        x = int(self.x)
        y = int(self.y)
        r = self.radius

        # Calculate sprite position (sprite has 2px padding)
        sprite_x = x - r - 2
        sprite_y = y - r - 2

        # Blit sprite (skip_source_index=0x0000 treats black as transparent)
        bitmaptools.blit(
            self.canvas, self.sprite, sprite_x, sprite_y, skip_source_index=0x0000
        )


def main():
    print("\n" + "=" * 70)
    print("  HIGH FPS BOUNCING BALL ANIMATION (optimized)")
    print("=" * 70)

    # Initialize display
    print("\nInitializing display...")
    displayio.release_displays()
    bus = create_qspi_bus(board)
    display = RM690B0(bus)
    try:
        display.brightness = 1.0
    except RuntimeError:
        pass

    # Create canvas and background bitmap
    canvas = displayio.Bitmap(WIDTH, HEIGHT, 65536)
    bg_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 65536)  # Read-only background

    cc = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565)
    tg = displayio.TileGrid(canvas, pixel_shader=cc)
    group = displayio.Group()
    group.append(tg)
    display.root_group = group
    print("Display ready\n")

    # Create background with border
    print("Creating background with border...")
    bg_bitmap.fill(0x0000)  # Black
    bitmaptools.draw_line(bg_bitmap, 0, 0, WIDTH - 1, 0, 0x4208)  # Top
    bitmaptools.draw_line(bg_bitmap, 0, HEIGHT - 1, WIDTH - 1, HEIGHT - 1, 0x4208)  # Bottom
    bitmaptools.draw_line(bg_bitmap, 0, 0, 0, HEIGHT - 1, 0x4208)  # Left
    bitmaptools.draw_line(bg_bitmap, WIDTH - 1, 0, WIDTH - 1, HEIGHT - 1, 0x4208)  # Right

    # Copy background to canvas once
    bitmaptools.blit(canvas, bg_bitmap, 0, 0)
    display.refresh()
    print("Background ready\n")

    # Random starting position and velocity
    start_x = random.randint(BALL_RADIUS + 20, WIDTH - BALL_RADIUS - 20)
    start_y = random.randint(BALL_RADIUS + 20, HEIGHT - BALL_RADIUS - 20)
    vx = SPEED * (random.random() * 2 - 1)
    vy = SPEED * (random.random() * 2 - 1)
    if abs(vx) < 3:
        vx = 3 if vx >= 0 else -3
    if abs(vy) < 3:
        vy = 3 if vy >= 0 else -3

    print(f"Configuration:")
    print(f"  Ball radius: {BALL_RADIUS}px")
    print(f"  Starting position: ({start_x}, {start_y})")
    print(f"  Initial velocity: ({vx:.2f}, {vy:.2f})")
    print(f"  Duration: {DURATION} seconds\n")

    ball = HighFPSBall(start_x, start_y, vx, vy, BALL_RADIUS, canvas, bg_bitmap)

    # Animation loop
    start_time = time.monotonic()
    frame_count = 0
    fps_update_interval = 30
    last_fps_time = start_time
    last_fps_frame = 0

    print("Starting animation...\n")

    while time.monotonic() - start_time < DURATION:
        frame_start = time.monotonic()

        # Save previous position BEFORE update (after collision correction from previous frame)
        ball.prev_x = ball.x
        ball.prev_y = ball.y

        ball.clear_previous()  # Restores background (with border!)
        ball.update()
        ball.draw()

        # Mark only changed region as dirty (huge performance boost!)
        _mark_ball_dirty(canvas, ball.prev_x, ball.prev_y, ball.x, ball.y, BALL_RADIUS)
        display.refresh()

        frame_count += 1

        if frame_count % fps_update_interval == 0:
            current_time = time.monotonic()
            elapsed = current_time - last_fps_time
            frames_rendered = frame_count - last_fps_frame
            current_fps = frames_rendered / elapsed if elapsed > 0 else 0
            remaining = DURATION - (current_time - start_time)
            print(
                f"Frame {frame_count:4d} | FPS: {current_fps:6.1f} | Remaining: {remaining:4.1f}s"
            )
            last_fps_time = current_time
            last_fps_frame = frame_count

        # NO THROTTLING - let it run as fast as possible!

    total_time = time.monotonic() - start_time
    actual_fps = frame_count / total_time

    print("\n" + "=" * 70)
    print("  ANIMATION COMPLETE")
    print("=" * 70)
    print(f"\nPerformance Results:")
    print(f"  Total frames: {frame_count}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average FPS: {actual_fps:.2f}")

    canvas.fill(0)
    display.refresh()
    displayio.release_displays()
    print("\nAnimation finished!\n")


if __name__ == "__main__":
    main()
