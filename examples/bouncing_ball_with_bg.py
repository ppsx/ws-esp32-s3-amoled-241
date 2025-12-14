"""
Bouncing Ball with Background Image
====================================

Combines background image loading with high FPS bouncing ball animation.
Background is loaded from /cerber.raw and the ball bounces over it.

Usage:
    python bouncing_ball_with_background.py
"""

import rm690b0
import time
import random


# ============================================================================
# CONFIGURATION
# ============================================================================

DURATION = 15  # Animation duration in seconds
SPEED = 8.0  # Ball speed (pixels per frame)
TARGET_FPS = 60  # Target frame rate
BALL_RADIUS = 20  # Ball radius in pixels
BACKGROUND_PATH = "/cerber.raw"  # Background image path
WIDTH = 600
HEIGHT = 450


class HighFPSBall:
    """High performance bouncing ball using dirty region optimization"""

    def __init__(self, x, y, vx, vy, radius, display_width, display_height, background):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.display_width = display_width
        self.display_height = display_height
        self.background = background

        # Track previous position for efficient clearing
        self.prev_x = x
        self.prev_y = y

    def update(self):
        """Update ball position and handle edge bouncing"""
        # Store previous position before updating
        self.prev_x = self.x
        self.prev_y = self.y

        # Update position
        self.x += self.vx
        self.y += self.vy

        # Bounce off edges
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = abs(self.vx)
        elif self.x + self.radius >= self.display_width:
            self.x = self.display_width - self.radius
            self.vx = -abs(self.vx)

        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy = abs(self.vy)
        elif self.y + self.radius >= self.display_height:
            self.y = self.display_height - self.radius
            self.vy = -abs(self.vy)

    def clear_previous(self, display):
        """Restore background at previous ball position"""
        x = int(self.prev_x)
        y = int(self.prev_y)
        r = self.radius + 2  # Slightly larger to ensure clean erase

        # Calculate the region to restore
        x1 = max(0, x - r)
        y1 = max(0, y - r)
        x2 = min(self.display_width, x + r)
        y2 = min(self.display_height, y + r)
        w = x2 - x1
        h = y2 - y1

        if w > 0 and h > 0:
            # Extract the region from background buffer
            region = bytearray(w * h * 2)
            for row in range(h):
                src_offset = ((y1 + row) * self.display_width + x1) * 2
                dst_offset = row * w * 2
                region[dst_offset : dst_offset + w * 2] = self.background[
                    src_offset : src_offset + w * 2
                ]

            # Blit the background region back
            display.blit_buffer(x1, y1, w, h, region)

    def draw(self, display):
        """Draw the fancy ball at current position"""
        x = int(self.x)
        y = int(self.y)
        r = self.radius

        # Main ball body (red)
        display.fill_circle(x, y, r, rm690b0.RED)

        # Outer rim (darker red/maroon)
        display.circle(x, y, r, 0x8800)

        # Inner highlight circle (orange)
        inner_r = int(r * 0.7)
        display.circle(x - int(r * 0.15), y - int(r * 0.15), inner_r, 0xFD20)

        # Shine effect - top-left highlight
        shine_x = x - int(r * 0.4)
        shine_y = y - int(r * 0.4)
        display.fill_circle(shine_x, shine_y, int(r * 0.25), 0xFFE0)  # Yellow
        display.fill_circle(shine_x, shine_y, int(r * 0.15), rm690b0.WHITE)  # White

        # Small sparkle dots
        display.fill_circle(x + int(r * 0.3), y + int(r * 0.2), int(r * 0.08), 0xFDA0)
        display.fill_circle(x - int(r * 0.1), y + int(r * 0.4), int(r * 0.08), 0xFC00)

        # Shadow effect on bottom
        shadow_y = y + int(r * 0.5)
        display.fill_circle(x, shadow_y, int(r * 0.3), 0x4000)


def load_background(path):
    """Load background image from RAW RGB565 file"""
    print(f"Loading background from {path}...")
    fb = bytearray(WIDTH * HEIGHT * 2)
    with open(path, "rb") as f:
        read = f.readinto(fb)
        if read != len(fb):
            raise RuntimeError("Background file is the wrong size")
    print("✓ Background loaded")
    return fb


def main():
    """Main animation loop with background"""
    print("\n" + "=" * 70)
    print("  BOUNCING BALL WITH BACKGROUND IMAGE")
    print("=" * 70)

    # Initialize display
    print("\nInitializing display...")
    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0

    # Enable double-buffering
    print("Enabling double-buffering...")
    display.swap_buffers()
    print("✓ Display ready\n")

    # Load background
    background = load_background(BACKGROUND_PATH)

    # Display background
    print("Displaying background...")
    display.blit_buffer(0, 0, WIDTH, HEIGHT, background)
    display.swap_buffers()
    print("✓ Background displayed\n")

    # Random starting position
    start_x = random.randint(BALL_RADIUS + 20, WIDTH - BALL_RADIUS - 20)
    start_y = random.randint(BALL_RADIUS + 20, HEIGHT - BALL_RADIUS - 20)

    # Random velocity
    vx = SPEED * (random.random() * 2 - 1)
    vy = SPEED * (random.random() * 2 - 1)

    # Ensure minimum velocity
    if abs(vx) < 3:
        vx = 3 if vx >= 0 else -3
    if abs(vy) < 3:
        vy = 3 if vy >= 0 else -3

    print(f"Configuration:")
    print(f"  Ball radius: {BALL_RADIUS}px")
    print(f"  Starting position: ({start_x}, {start_y})")
    print(f"  Initial velocity: ({vx:.2f}, {vy:.2f})")
    print(f"  Target FPS: {TARGET_FPS}")
    print(f"  Duration: {DURATION} seconds\n")

    # Create ball
    ball = HighFPSBall(start_x, start_y, vx, vy, BALL_RADIUS, WIDTH, HEIGHT, background)

    # Animation loop
    start_time = time.monotonic()
    frame_count = 0
    target_frame_time = 1.0 / TARGET_FPS
    fps_update_interval = 30

    # For FPS calculation
    last_fps_time = start_time
    last_fps_frame = 0

    print("🚀 Starting animation...\n")

    while time.monotonic() - start_time < DURATION:
        frame_start = time.monotonic()

        # Restore background at old ball position
        ball.clear_previous(display)

        # Update physics
        ball.update()

        # Draw ball at new position
        ball.draw(display)

        # Swap buffers
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

        # Frame rate limiting
        frame_elapsed = time.monotonic() - frame_start
        if frame_elapsed < target_frame_time:
            time.sleep(target_frame_time - frame_elapsed)

    # Animation complete
    total_time = time.monotonic() - start_time
    actual_fps = frame_count / total_time

    print("\n" + "=" * 70)
    print("  ANIMATION COMPLETE")
    print("=" * 70)
    print(f"\n📊 Performance Results:")
    print(f"  Total frames: {frame_count}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average FPS: {actual_fps:.2f}")
    print(f"  Target FPS: {TARGET_FPS}")
    print(f"  Achievement: {(actual_fps / TARGET_FPS * 100):.1f}%")

    # Clean up
    display.fill_color(rm690b0.BLACK)
    display.swap_buffers()
    display.deinit()

    print("\n✓ Animation finished!\n")


if __name__ == "__main__":
    main()
