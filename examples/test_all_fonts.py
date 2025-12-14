import time

import rm690b0

# Initialize display
display = rm690b0.RM690B0()
display.init_display()
display.swap_buffers()

print("=" * 60)
print("RM690B0 All Fonts Test")
print("=" * 60)

# Font configurations: (id, name, width, height)
fonts = [
    (rm690b0.FONT_8x8, "8x8", 8, 8),
    (rm690b0.FONT_16x16, "16x16", 16, 16),
    (rm690b0.FONT_16x24, "16x24", 16, 24),
    (rm690b0.FONT_24x24, "24x24", 24, 24),
    (rm690b0.FONT_24x32, "24x32", 24, 32),
    (rm690b0.FONT_32x32, "32x32", 32, 32),
    (rm690b0.FONT_32x48, "32x48", 32, 48),
]

# Test each font
for font_id, font_name, width, height in fonts:
    print(f"\n[Font {font_id}] Testing {font_name} ({width}x{height})...")

    display.fill_color(rm690b0.BLACK)
    display.set_font(font_id)

    # Title
    display.text(10, 10, f"Font {font_id}: {font_name}", rm690b0.WHITE)

    # Sample text at appropriate size
    y_pos = 10 + height + 5

    if height <= 16:
        # Small fonts - show more text
        display.text(10, y_pos, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", rm690b0.CYAN)
        y_pos += height
        display.text(10, y_pos, "abcdefghijklmnopqrstuvwxyz", rm690b0.GREEN)
        y_pos += height
        display.text(10, y_pos, "0123456789 !@#$%^&*()", rm690b0.YELLOW)
    elif height <= 24:
        # Medium fonts
        display.text(10, y_pos, "ABCDEFGHIJKLMNOP", rm690b0.CYAN)
        y_pos += height
        display.text(10, y_pos, "abcdefghijklmnop", rm690b0.GREEN)
        y_pos += height
        display.text(10, y_pos, "0123456789", rm690b0.YELLOW)
    elif height <= 32:
        # Large fonts
        display.text(10, y_pos, "ABCDEFGH", rm690b0.CYAN)
        y_pos += height
        display.text(10, y_pos, "abcdefgh", rm690b0.GREEN)
        y_pos += height
        display.text(10, y_pos, "01234567", rm690b0.YELLOW)
    else:
        # Very large fonts
        display.text(10, y_pos, "ABCDEF", rm690b0.CYAN)
        y_pos += height
        display.text(10, y_pos, "abcdef", rm690b0.GREEN)
        y_pos += height
        display.text(10, y_pos, "012345", rm690b0.YELLOW)

    display.swap_buffers()
    time.sleep(2)

# Size comparison - show all fonts with same text
print("\n[Comparison] Showing all fonts with 'Hello'...")
display.fill_color(rm690b0.BLACK)

y_pos = 5
for font_id, font_name, width, height in fonts:
    if y_pos + height > display.height:
        break
    display.set_font(font_id)
    display.text(5, y_pos, "Hello!", rm690b0.WHITE)
    y_pos += height + 2

display.swap_buffers()
time.sleep(3)

# Performance test
print("\n[Performance] Testing rendering speed...")
display.fill_color(rm690b0.BLACK)

for font_id, font_name, width, height in fonts:
    display.set_font(font_id)
    start = time.monotonic()
    for i in range(10):
        display.text(10, 10, "Test", rm690b0.WHITE)
    elapsed = time.monotonic() - start
    print(
        f"  Font {font_id} ({font_name}): {elapsed:.3f}s for 10 renders ({elapsed / 10 * 1000:.1f}ms each)"
    )

# Color test with medium font
print("\n[Colors] Testing colors with 16x16 font...")
display.fill_color(rm690b0.BLACK)
display.set_font(rm690b0.FONT_16x16)

colors = [
    (rm690b0.WHITE, "WHITE"),
    (rm690b0.RED, "RED"),
    (rm690b0.GREEN, "GREEN"),
    (rm690b0.BLUE, "BLUE"),
    (rm690b0.YELLOW, "YELLOW"),
    (rm690b0.CYAN, "CYAN"),
    (rm690b0.MAGENTA, "MAGENTA"),
]

y_pos = 10
for color, name in colors:
    display.text(10, y_pos, name, color)
    y_pos += 18

display.swap_buffers()
time.sleep(2)

# Background test
print("\n[Background] Testing background colors...")
display.fill_color(rm690b0.BLACK)
display.set_font(rm690b0.FONT_16x24)

display.text(10, 10, "White on Red", rm690b0.WHITE, rm690b0.RED)
display.text(10, 40, "Black on Cyan", rm690b0.BLACK, rm690b0.CYAN)
display.text(10, 70, "Yellow on Blue", rm690b0.YELLOW, rm690b0.BLUE)
display.text(10, 100, "Green on Black", rm690b0.GREEN, rm690b0.BLACK)

display.swap_buffers()
time.sleep(2)

# Mixed sizes demo
print("\n[Demo] Mixed font sizes...")
display.fill_color(rm690b0.BLACK)

display.set_font(rm690b0.FONT_32x48)  # Largest
display.text(10, 10, "Big", rm690b0.WHITE)

display.set_font(rm690b0.FONT_24x24)  # Medium
display.text(10, 65, "Medium Text", rm690b0.CYAN)

display.set_font(rm690b0.FONT_16x16)  # Small
display.text(10, 95, "Small details here", rm690b0.YELLOW)

display.set_font(rm690b0.FONT_8x8)  # Tiny
display.text(10, 115, "Tiny: Status, debug, logs", rm690b0.GREEN)

display.swap_buffers()
time.sleep(3)

# Final summary
display.fill_color(rm690b0.BLACK)
display.set_font(rm690b0.FONT_8x8)
display.text(10, 10, "Font Test Summary", rm690b0.WHITE)
display.text(10, 20, "=" * 70, rm690b0.CYAN)

y_pos = 30
for font_id, font_name, width, height in fonts:
    text = f"{font_id}: {font_name:8s} ({width:2d}x{height:2d})"
    display.text(10, y_pos, text, rm690b0.GREEN)
    y_pos += 10

display.text(10, y_pos + 10, "All 7 fonts available!", rm690b0.YELLOW)
display.text(10, y_pos + 20, "Use display.set_font(0-6)", rm690b0.MAGENTA)
display.swap_buffers()

print("\n" + "=" * 60)
print("Font test complete!")
print("=" * 60)
print("\nAvailable fonts:")
for font_id, font_name, width, height in fonts:
    chars_per_line = display.width // width
    lines_per_screen = display.height // height
    print(
        f"  {font_id}: {font_name:8s} ({width:2d}x{height:2d}) - ~{chars_per_line:2d} chars/line, ~{lines_per_screen:2d} lines/screen"
    )

print("\nUsage:")
print("  display.set_font(rm690b0.FONT_8x8)    # 8x8 - debug/logs")
print("  display.set_font(rm690b0.FONT_16x16)  # 16x16 - standard UI")
print("  display.set_font(rm690b0.FONT_16x24)  # 16x24 - readable UI")
print("  display.set_font(rm690b0.FONT_24x24)  # 24x24 - headers")
print("  display.set_font(rm690b0.FONT_24x32)  # 24x32 - large headers")
print("  display.set_font(rm690b0.FONT_32x32)  # 32x32 - big display")
print("  display.set_font(rm690b0.FONT_32x48)  # 32x48 - huge display")

print("\nPress Ctrl+C to exit")

# Keep display on
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting...")
    display.deinit()
