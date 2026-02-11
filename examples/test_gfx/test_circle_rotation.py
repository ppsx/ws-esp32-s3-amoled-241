# Copyright (c) 2025 Przemyslaw Patrick Socha
#
# Test: circle/fill_circle rotation correctness
# Verifies that circle primitives render correctly at all rotations (0/90/180/270)
# and don't cause buffer overflow when logical coords exceed physical bounds.

import time
import rm690b0

display = rm690b0.RM690B0()
display.init_display()
display.swap_buffers()  # enable double-buffering

COLORS = [rm690b0.RED, rm690b0.GREEN, rm690b0.CYAN, rm690b0.YELLOW]
ROTATIONS = [0, 90, 180, 270]

# --- Test 1: Circle outline at each rotation ---
input("Test 1: Circle outline at each rotation. Press Enter...")
for i, angle in enumerate(ROTATIONS):
    display.rotation = angle
    display.fill_color(rm690b0.BLACK)
    w, h = display.width, display.height

    # Center circle
    display.circle(w // 2, h // 2, 80, COLORS[i])
    # Corner reference: small rect at top-left
    display.fill_rect(0, 0, 20, 20, rm690b0.WHITE)
    # Label
    display.set_font(rm690b0.FONT_16x16)
    display.text(30, 2, f"rot={angle}", rm690b0.WHITE)

    display.swap_buffers()
    input(f"  rotation={angle} — Press Enter...")

# --- Test 2: Filled circle at each rotation ---
input("Test 2: Filled circle at each rotation. Press Enter...")
for i, angle in enumerate(ROTATIONS):
    display.rotation = angle
    display.fill_color(rm690b0.BLACK)
    w, h = display.width, display.height

    display.fill_circle(w // 2, h // 2, 100, COLORS[i])
    display.fill_rect(0, 0, 20, 20, rm690b0.WHITE)
    display.set_font(rm690b0.FONT_16x16)
    display.text(30, 2, f"rot={angle}", rm690b0.WHITE)

    display.swap_buffers()
    input(f"  rotation={angle} — Press Enter...")

# --- Test 3: Edge cases — circle partially off-screen at rotation 90 ---
input("Test 3: Edge cases (partial circles, rot=90). Press Enter...")
display.rotation = 90
display.fill_color(rm690b0.BLACK)
w, h = display.width, display.height

# Top-left corner
display.fill_circle(0, 0, 80, rm690b0.RED)
display.circle(0, 0, 100, rm690b0.BROWN)

# Bottom-right corner
display.fill_circle(w - 1, h - 1, 80, rm690b0.GREEN)
display.circle(w - 1, h - 1, 100, rm690b0.DARK_GREEN)

# Center reference
display.circle(w // 2, h // 2, 30, rm690b0.WHITE)

display.set_font(rm690b0.FONT_8x8)
display.text(w // 2 - 40, h // 2 - 4, "rot=90", rm690b0.WHITE)

display.swap_buffers()
input("  Press Enter...")

# --- Test 4: Edge cases — circle partially off-screen at rotation 270 ---
input("Test 4: Edge cases (partial circles, rot=270). Press Enter...")
display.rotation = 270
display.fill_color(rm690b0.BLACK)
w, h = display.width, display.height

display.fill_circle(0, 0, 80, rm690b0.CYAN)
display.fill_circle(w - 1, h - 1, 80, rm690b0.YELLOW)
display.circle(w // 2, h // 2, 50, rm690b0.WHITE)

display.set_font(rm690b0.FONT_8x8)
display.text(w // 2 - 44, h // 2 - 4, "rot=270", rm690b0.WHITE)

display.swap_buffers()
input("  Press Enter...")

# --- Test 5: Large circle at rotation 90 (stress test — max logical y) ---
input("Test 5: Large circle at rot=90 (stress). Press Enter...")
display.rotation = 90
display.fill_color(rm690b0.BLACK)
w, h = display.width, display.height

# Large radius that extends to near-max logical coords
display.fill_circle(w // 2, h // 2, min(w, h) // 2 - 10, rm690b0.BLUE)
display.circle(w // 2, h // 2, min(w, h) // 2 - 10, rm690b0.WHITE)

display.swap_buffers()
input("  Press Enter...")

# --- Test 6: Multiple small circles at rotation 180 ---
input("Test 6: Grid of circles at rot=180. Press Enter...")
display.rotation = 180
display.fill_color(rm690b0.BLACK)
w, h = display.width, display.height

for cx in range(40, w, 80):
    for cy in range(40, h, 80):
        display.fill_circle(cx, cy, 30, rm690b0.DARK_GRAY)
        display.circle(cx, cy, 30, rm690b0.WHITE)

display.swap_buffers()
input("  Press Enter...")

# --- Cleanup ---
display.rotation = 0
display.fill_color(rm690b0.BLACK)
display.swap_buffers()
display.deinit()
print("All tests passed (no crash).")
