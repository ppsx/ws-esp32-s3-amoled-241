# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
High FPS Bouncing Ball Animation (Pre-rendered Sprite with Transparency)
=========================================================================

Demonstrates high-performance sprite rendering using pre-rendered sprites
with transparency. The ball sprite is rendered ONCE at startup, then blitted
with transparent_color=0x0000 for maximum performance.

Instead of clearing the full screen each frame (12.8ms), this version:
1. Clears only the OLD ball position with black fill_rect
2. Blits pre-rendered sprite at NEW position with transparency
3. swap_buffers() flushes only dirty regions

This approach is 5-10× faster than drawing primitives every frame.
"""

import math
import random
import time

import rm690b0

# ============================================================================
# CONFIGURATION
# ============================================================================

DURATION = 15  # Animation duration in seconds
SPEED = 8.0  # Ball speed (pixels per frame)
BALL_RADIUS = 20  # Ball radius in pixels


def pre_render_ball_sprite(radius):
    """
    Pre-render ball sprite ONCE with all effects.

    Returns: (sprite_data, sprite_width, sprite_height, offset_x, offset_y)

    The sprite is rendered with black (0x0000) background for transparency.
    offset_x, offset_y indicate the ball center position within the sprite.
    """
    # Sprite size: radius * 2 + padding for effects
    padding = 4
    sprite_size = radius * 2 + padding
    sprite_w = sprite_size
    sprite_h = sprite_size

    # Center of sprite
    cx = sprite_size // 2
    cy = sprite_size // 2

    print(f"Pre-rendering ball sprite ({sprite_w}×{sprite_h})...")

    # Create sprite buffer (black background for transparency)
    sprite_data = bytearray(sprite_w * sprite_h * 2)

    # Helper: set pixel in sprite buffer (RGB565 little-endian)
    def set_pixel(x, y, rgb565):
        if 0 <= x < sprite_w and 0 <= y < sprite_h:
            idx = (y * sprite_w + x) * 2
            sprite_data[idx] = rgb565 & 0xFF
            sprite_data[idx + 1] = (rgb565 >> 8) & 0xFF

    # 1. Fill background with BLACK (transparent color)
    for i in range(len(sprite_data)):
        sprite_data[i] = 0

    # 2. Draw main ball body (red) - filled circle
    for y in range(sprite_h):
        for x in range(sprite_w):
            dx = x - cx
            dy = y - cy
            dist_sq = dx * dx + dy * dy
            if dist_sq <= radius * radius:
                set_pixel(x, y, rm690b0.RED)  # 0xF800

    # 3. Outer rim (darker red/maroon)
    for angle_deg in range(0, 360, 2):
        angle = math.radians(angle_deg)
        x = int(cx + radius * math.cos(angle))
        y = int(cy + radius * math.sin(angle))
        set_pixel(x, y, 0x8800)

    # 4. Inner highlight circle (orange)
    inner_r = int(radius * 0.7)
    inner_cx = cx - int(radius * 0.15)
    inner_cy = cy - int(radius * 0.15)
    for angle_deg in range(0, 360, 2):
        angle = math.radians(angle_deg)
        x = int(inner_cx + inner_r * math.cos(angle))
        y = int(inner_cy + inner_r * math.sin(angle))
        set_pixel(x, y, 0xFD20)

    # 5. Shine effect - top-left highlight
    shine_x = cx - int(radius * 0.4)
    shine_y = cy - int(radius * 0.4)
    shine_r1 = int(radius * 0.25)
    shine_r2 = int(radius * 0.15)

    # Yellow shine
    for y in range(sprite_h):
        for x in range(sprite_w):
            dx = x - shine_x
            dy = y - shine_y
            if dx * dx + dy * dy <= shine_r1 * shine_r1:
                set_pixel(x, y, 0xFFE0)  # Yellow

    # White center
    for y in range(sprite_h):
        for x in range(sprite_w):
            dx = x - shine_x
            dy = y - shine_y
            if dx * dx + dy * dy <= shine_r2 * shine_r2:
                set_pixel(x, y, rm690b0.WHITE)

    # 6. Small sparkle dots
    sparkle1_x = cx + int(radius * 0.3)
    sparkle1_y = cy + int(radius * 0.2)
    sparkle1_r = int(radius * 0.08)
    for y in range(sprite_h):
        for x in range(sprite_w):
            dx = x - sparkle1_x
            dy = y - sparkle1_y
            if dx * dx + dy * dy <= sparkle1_r * sparkle1_r:
                set_pixel(x, y, 0xFDA0)

    sparkle2_x = cx - int(radius * 0.1)
    sparkle2_y = cy + int(radius * 0.4)
    sparkle2_r = int(radius * 0.08)
    for y in range(sprite_h):
        for x in range(sprite_w):
            dx = x - sparkle2_x
            dy = y - sparkle2_y
            if dx * dx + dy * dy <= sparkle2_r * sparkle2_r:
                set_pixel(x, y, 0xFC00)

    # 7. Shadow effect on bottom
    shadow_y = cy + int(radius * 0.5)
    shadow_r = int(radius * 0.3)
    for y in range(sprite_h):
        for x in range(sprite_w):
            dx = x - cx
            dy = y - shadow_y
            if dx * dx + dy * dy <= shadow_r * shadow_r:
                set_pixel(x, y, 0x4000)

    print(f"✓ Sprite pre-rendered ({len(sprite_data)} bytes)")

    # Return sprite data and center offset
    return sprite_data, sprite_w, sprite_h, cx, cy


class HighFPSBall:
    """High performance bouncing ball using pre-rendered sprite with transparency optimized for DISPLAY_LIST.

    In DISPLAY_LIST mode with copy=False, the command list is cleared every frame.
    To correctly update the screen without full redraw, we compute the AABB of the
    old and new ball positions. We draw a black rect over the AABB, and then the new ball.
    The DL engine will only rasterize and update this minimal AABB.
    """

    def __init__(self, x, y, vx, vy, radius, display_width, display_height, sprite_data, sprite_w, sprite_h, offset_x, offset_y):
        # Float positions for precise motion (prevents cumulative rounding errors)
        self.fx = float(x)
        self.fy = float(y)
        # Int positions for rendering
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.display_width = display_width
        self.display_height = display_height

        # Pre-rendered sprite data
        self.sprite_data = sprite_data
        self.sprite_w = sprite_w
        self.sprite_h = sprite_h
        self.offset_x = offset_x  # Ball center offset within sprite
        self.offset_y = offset_y

        # Only one previous position needed for DISPLAY_LIST (no double-buffer tracking)
        self.prev_x = x
        self.prev_y = y

    def update(self):
        """Update ball position and handle edge bouncing"""
        # Update position using float for precision
        self.fx += self.vx
        self.fy += self.vy
        self.x = int(self.fx)
        self.y = int(self.fy)

        # Bounce off edges with border margin (keep float and int synchronized)
        # Increase border margin to keep aligned AABB completely clear of the border
        border_margin = 10

        if self.x - self.radius <= border_margin:
            self.x = self.radius + border_margin
            self.fx = float(self.radius + border_margin)
            self.vx = abs(self.vx)
        elif self.x + self.radius >= self.display_width - 1 - border_margin:
            self.x = self.display_width - 1 - self.radius - border_margin
            self.fx = float(self.display_width - 1 - self.radius - border_margin)
            self.vx = -abs(self.vx)

        if self.y - self.radius <= border_margin:
            self.y = self.radius + border_margin
            self.fy = float(self.radius + border_margin)
            self.vy = abs(self.vy)
        elif self.y + self.radius >= self.display_height - 1 - border_margin:
            self.y = self.display_height - 1 - self.radius - border_margin
            self.fy = float(self.display_height - 1 - self.radius - border_margin)
            self.vy = -abs(self.vy)

    def update_display(self, display):
        """Update display by computing AABB, erasing it, and drawing new ball"""
        # 1. Compute AABB (Axis-Aligned Bounding Box) of old and new sprite positions
        prev_sx = int(self.prev_x) - self.offset_x
        prev_sy = int(self.prev_y) - self.offset_y
        curr_sx = int(self.x) - self.offset_x
        curr_sy = int(self.y) - self.offset_y

        # Compute combined AABB
        x1 = max(0, min(prev_sx, curr_sx))
        y1 = max(0, min(prev_sy, curr_sy))
        x2 = min(self.display_width, max(prev_sx + self.sprite_w, curr_sx + self.sprite_w))
        y2 = min(self.display_height, max(prev_sy + self.sprite_h, curr_sy + self.sprite_h))

        # Align AABB to 4-pixel boundaries to perfectly match C driver dirty tracking
        x1 = x1 & ~3
        y1 = y1 & ~3
        x2 = min(self.display_width, (x2 + 3) & ~3)
        y2 = min(self.display_height, (y2 + 3) & ~3)

        w = x2 - x1
        h = y2 - y1

        if w > 0 and h > 0:
            # Submit AABB clear (this clears the old ball AND sets black background for whole dirty area)
            display.fill_rect(x1, y1, w, h, rm690b0.BLACK)

        # 2. Draw new ball sprite with transparency
        display.blit_buffer(
            curr_sx, curr_sy,
            self.sprite_w, self.sprite_h,
            self.sprite_data,
            transparent_color=0x0000
        )

        # 3. Update previous position
        self.prev_x = self.x
        self.prev_y = self.y


def main():
    """Main high FPS animation loop"""
    print("\n" + "=" * 70)
    print("  HIGH FPS BOUNCING BALL ANIMATION")
    print("=" * 70)

    # Initialize display
    print("\nInitializing display...")
    display = rm690b0.RM690B0(render_mode=rm690b0.RENDER_DISPLAY_LIST)
    display.init_display()
    display.brightness = 1.0

    # Enable double-buffering for dirty region optimization
    print("Enabling double-buffering with dirty regions...")
    display.swap_buffers()
    print("Display ready for high FPS animation\n")

    # Display dimensions
    width = display.width
    height = display.height

    # Draw static border on BOTH buffers (required for copy=False coherence)
    print("Drawing static border...")
    display.fill_color(rm690b0.BLACK)
    display.rect(0, 0, width, height, 0x4208)  # Dark gray border
    display.swap_buffers()
    display.fill_color(rm690b0.BLACK)
    display.rect(0, 0, width, height, 0x4208)
    print("Border ready\n")

    # Random starting position
    start_x = random.randint(BALL_RADIUS + 20, width - BALL_RADIUS - 20)
    start_y = random.randint(BALL_RADIUS + 20, height - BALL_RADIUS - 20)

    # Random velocity
    vx = SPEED * (random.random() * 2 - 1)
    vy = SPEED * (random.random() * 2 - 1)

    # Ensure minimum velocity
    if abs(vx) < 3:
        vx = 3 if vx >= 0 else -3
    if abs(vy) < 3:
        vy = 3 if vy >= 0 else -3

    # Pre-render ball sprite ONCE (major performance optimization!)
    print("Pre-rendering ball sprite...")
    sprite_data, sprite_w, sprite_h, offset_x, offset_y = pre_render_ball_sprite(BALL_RADIUS)
    print(f"✓ Sprite size: {sprite_w}×{sprite_h}, center offset: ({offset_x}, {offset_y})\n")

    print(f"Configuration:")
    print(f"  Ball radius: {BALL_RADIUS}px")
    print(f"  Starting position: ({start_x}, {start_y})")
    print(f"  Initial velocity: ({vx:.2f}, {vy:.2f})")
    print(f"  Duration: {DURATION} seconds")
    print(f"  Rendering: Pre-rendered sprite with transparency\n")
    print(f"\nHIGH FPS MODE: Using dirty region optimization + sprite blitting!")
    print(f"   • Only clearing old sprite position (not full screen)")
    print(f"   • Using pre-rendered sprite with transparency")
    print(f"   • Only flushing changed regions")

    # Create ball with pre-rendered sprite
    ball = HighFPSBall(
        start_x, start_y, vx, vy, BALL_RADIUS, width, height,
        sprite_data, sprite_w, sprite_h, offset_x, offset_y
    )

    # Animation loop
    start_time = time.monotonic()
    frame_count = 0
    fps_update_interval = 30  # Update FPS display every 30 frames

    # For FPS calculation
    last_fps_time = start_time
    last_fps_frame = 0

    print("Starting animation...\n")

    while time.monotonic() - start_time < DURATION:
        frame_start = time.monotonic()

        # Update physics
        ball.update()

        # Update display (clears AABB and draws new ball)
        ball.update_display(display)

        # Swap and clear list
        display.swap_buffers(copy=False)

        frame_count += 1

        # Calculate and display FPS periodically
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

    # Animation complete
    total_time = time.monotonic() - start_time
    actual_fps = frame_count / total_time

    print("\n" + "=" * 70)
    print("  ANIMATION COMPLETE")
    print("=" * 70)
    print(f"\nPerformance Results:")
    print(f"  Rendering technique: Pre-rendered sprite with transparency")
    print(f"  Sprite size: {sprite_w}×{sprite_h} pixels")
    print(f"  Total frames: {frame_count}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average FPS: {actual_fps:.2f}")
    print(f"\n  Expected performance gain: 5-10× faster than primitive rendering")

    # Clean up
    display.fill_color(rm690b0.BLACK)
    display.swap_buffers()
    display.deinit()

    print("\nAnimation finished!\n")


if __name__ == "__main__":
    main()
