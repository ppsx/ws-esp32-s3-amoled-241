"""
Bouncing Ball Animation
=======================

A fancy bouncing ball with complex design that bounces around the screen.

Features:
- Random starting position and direction
- Realistic edge bouncing
- Complex ball design with multiple layers
- Smooth double-buffered animation
- Runs for 10 seconds

Usage:
    python bouncing_ball.py
"""

import rm690b0
import time
import random


# ============================================================================
# CONFIGURATION
# ============================================================================

DURATION = 15  # Animation duration in seconds
SPEED = 9      # Ball speed (pixels per frame)


class Ball:
    """A fancy bouncing ball with complex design"""

    def __init__(self, x, y, vx, vy, radius, display_width, display_height):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.display_width = display_width
        self.display_height = display_height

    def update(self):
        """Update ball position and handle edge bouncing"""
        # Update position
        self.x += self.vx
        self.y += self.vy

        # Bounce off edges
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = abs(self.vx)  # Reverse direction (move right)
        elif self.x + self.radius >= self.display_width:
            self.x = self.display_width - self.radius
            self.vx = -abs(self.vx)  # Reverse direction (move left)

        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy = abs(self.vy)  # Reverse direction (move down)
        elif self.y + self.radius >= self.display_height:
            self.y = self.display_height - self.radius
            self.vy = -abs(self.vy)  # Reverse direction (move up)

    def draw(self, display):
        """Draw the fancy ball with multiple layers"""
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

        # Shine effect - top-left highlight (bright white/yellow)
        shine_x = x - int(r * 0.4)
        shine_y = y - int(r * 0.4)
        display.fill_circle(shine_x, shine_y, int(r * 0.25), 0xFFE0)  # Yellow
        display.fill_circle(
            shine_x, shine_y, int(r * 0.15), rm690b0.WHITE
        )  # White center

        # Small sparkle dots
        display.fill_circle(
            x + int(r * 0.3), y + int(r * 0.2), int(r * 0.08), 0xFDA0
        )  # Small orange dot
        display.fill_circle(
            x - int(r * 0.1), y + int(r * 0.4), int(r * 0.08), 0xFC00
        )  # Small red dot

        # Shadow effect on bottom (darker)
        shadow_y = y + int(r * 0.5)
        display.fill_circle(x, shadow_y, int(r * 0.3), 0x4000)  # Dark shadow


def main():
    """Main animation loop"""
    print("\n" + "=" * 70)
    print("  BOUNCING BALL ANIMATION")
    print("=" * 70)

    # Initialize display
    print("\nInitializing display...")
    display = rm690b0.RM690B0()
    display.init_display()
    display.brightness = 1.0

    # Enable double-buffering for smooth animation
    print("Enabling double-buffering...")
    display.swap_buffers()
    print("✓ Display ready for animation\n")

    # Display dimensions
    width = display.width
    height = display.height

    # Ball parameters
    ball_radius = 30

    # Random starting position (not too close to edges)
    start_x = random.randint(ball_radius + 20, width - ball_radius - 20)
    start_y = random.randint(ball_radius + 20, height - ball_radius - 20)

    # Random velocity using configured speed
    angle = random.uniform(0, 6.28)  # Random angle in radians (0 to 2π)
    vx = SPEED * (random.random() * 2 - 1)  # Random between -SPEED and +SPEED
    vy = SPEED * (random.random() * 2 - 1)

    # Ensure we have some minimum velocity
    if abs(vx) < 2:
        vx = 2 if vx >= 0 else -2
    if abs(vy) < 2:
        vy = 2 if vy >= 0 else -2

    print(f"Ball radius: {ball_radius}px")
    print(f"Starting position: ({start_x}, {start_y})")
    print(f"Initial velocity: ({vx:.2f}, {vy:.2f})")
    print(f"\nAnimation running for {DURATION} seconds...")
    print("Watch the fancy ball bounce around!\n")

    # Create ball
    ball = Ball(start_x, start_y, vx, vy, ball_radius, width, height)

    # Animation loop
    start_time = time.monotonic()
    frame_count = 0
    target_fps = 30
    frame_time = 1.0 / target_fps

    while time.monotonic() - start_time < DURATION:
        frame_start = time.monotonic()

        # Clear screen (black background)
        display.fill_color(rm690b0.BLACK)

        # Update ball physics
        ball.update()

        # Draw the fancy ball
        ball.draw(display)

        # Draw screen border for reference
        display.rect(0, 0, width, height, 0x4208)  # Dark gray border

        # Draw FPS counter (optional)
        elapsed = time.monotonic() - start_time
        remaining = DURATION - elapsed
        if frame_count % 30 == 0:  # Update every 30 frames
            current_fps = frame_count / elapsed if elapsed > 0 else 0
            print(
                f"Frame {frame_count:4d} | FPS: {current_fps:5.1f} | Time remaining: {remaining:4.1f}s"
            )

        # Swap buffers for smooth display
        display.swap_buffers(copy=False)

        frame_count += 1

        # Frame rate limiting
        frame_elapsed = time.monotonic() - frame_start
        if frame_elapsed < frame_time:
            time.sleep(frame_time - frame_elapsed)

    # Animation complete
    total_time = time.monotonic() - start_time
    actual_fps = frame_count / total_time

    print("\n" + "=" * 70)
    print("  ANIMATION COMPLETE")
    print("=" * 70)
    print(f"\nTotal frames: {frame_count}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average FPS: {actual_fps:.2f}")
    print(f"Target FPS: {target_fps}")
    print(f"Performance: {(actual_fps / target_fps * 100):.1f}%")

    # Clean up
    display.fill_color(rm690b0.BLACK)
    display.swap_buffers()
    display.deinit()

    print("\n✓ Animation finished!\n")


if __name__ == "__main__":
    main()
