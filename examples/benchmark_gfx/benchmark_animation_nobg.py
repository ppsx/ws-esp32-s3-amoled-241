# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
High FPS Bouncing Ball Animation
=================================

Demonstrates animation using dirty region tracking.

Instead of clearing the full screen each frame (12.8ms), this version:
1. Clears only the OLD ball position
2. Draws ball at NEW position
3. swap_buffers() flushes only dirty regions
"""

import random
import time

import rm690b0

# ============================================================================
# CONFIGURATION
# ============================================================================

DURATION = 15  # Animation duration in seconds
SPEED = 8.0  # Ball speed (pixels per frame)
BALL_RADIUS = 20  # Ball radius in pixels


class HighFPSBall:
    """High performance bouncing ball using dirty region optimization"""

    def __init__(self, x, y, vx, vy, radius, display_width, display_height):
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

        # Track previous position for efficient clearing
        self.prev_x = x
        self.prev_y = y

    def update(self):
        """Update ball position and handle edge bouncing"""
        # Store previous position BEFORE updating (original structure)
        self.prev_x = self.x
        self.prev_y = self.y

        # Update position using float for precision
        self.fx += self.vx
        self.fy += self.vy
        self.x = int(self.fx)
        self.y = int(self.fy)

        # Bounce off edges with border margin (keep float and int synchronized)
        # Border is at x=0, x=width-1, y=0, y=height-1
        # Keep ball at least 2px away to protect border + clear region
        border_margin = 2

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

    def clear_previous(self, display):
        """Clear previous ball position with black, protecting border"""
        x = int(self.prev_x)
        y = int(self.prev_y)
        r = self.radius + 2  # Slightly larger to ensure clean erase

        # Calculate clear region, clamped to avoid touching border (2px margin)
        x1 = max(2, x - r)  # Leave 2px margin for border
        y1 = max(2, y - r)
        x2 = min(self.display_width - 3, x + r)  # Leave 2px margin from border
        y2 = min(self.display_height - 3, y + r)

        # Width/height must include x2/y2 pixel (+1 because fill_rect is inclusive)
        w = x2 - x1 + 1
        h = y2 - y1 + 1

        if w > 0 and h > 0:
            # Fast clear with fill_rect (native rm690b0, much faster!)
            display.fill_rect(x1, y1, w, h, rm690b0.BLACK)

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


def main():
    """Main high FPS animation loop"""
    print("\n" + "=" * 70)
    print("  HIGH FPS BOUNCING BALL ANIMATION")
    print("=" * 70)

    # Initialize display
    print("\nInitializing display...")
    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0

    # Enable double-buffering for dirty region optimization
    print("Enabling double-buffering with dirty regions...")
    display.swap_buffers()
    print("Display ready for high FPS animation\n")

    # Display dimensions
    width = display.width
    height = display.height

    # Draw static border once
    print("Drawing static border...")
    display.fill_color(rm690b0.BLACK)
    display.rect(0, 0, width, height, 0x4208)  # Dark gray border
    display.swap_buffers()
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

    print(f"Configuration:")
    print(f"  Ball radius: {BALL_RADIUS}px")
    print(f"  Starting position: ({start_x}, {start_y})")
    print(f"  Initial velocity: ({vx:.2f}, {vy:.2f})")
    print(f"  Duration: {DURATION} seconds\n")
    print(f"\nHIGH FPS MODE: Using dirty region optimization!")
    print(f"   • Only clearing old ball position (not full screen)")
    print(f"   • Only flushing changed regions")

    # Create ball
    ball = HighFPSBall(start_x, start_y, vx, vy, BALL_RADIUS, width, height)

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

        # Clear old ball position (protecting border with 1px margin)
        ball.clear_previous(display)

        # Update physics
        ball.update()

        # Draw ball at NEW position
        ball.draw(display)

        # CRITICAL: use copy=False since we're doing incremental updates
        # This avoids 27ms memcpy overhead
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
    print(f"  Total frames: {frame_count}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average FPS: {actual_fps:.2f}")

    # Clean up
    display.fill_color(rm690b0.BLACK)
    display.swap_buffers()
    display.deinit()

    print("\nAnimation finished!\n")


if __name__ == "__main__":
    main()
