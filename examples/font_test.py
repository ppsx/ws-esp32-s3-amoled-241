import time

import rm690b0

# Initialize display
display = rm690b0.RM690B0()
display.init_display()
display.swap_buffers()

print("=" * 60)
print("RM690B0 Font Comparison Test")
print("=" * 60)

# Test 1: 8x8 Font
print("\n[1/5] Testing 8x8 monospace font...")
display.fill_color(rm690b0.BLACK)
display.set_font(0)
display.text(10, 10, "8x8 Monospace Font", rm690b0.WHITE)
display.text(10, 20, "=" * 50, rm690b0.CYAN)
display.text(10, 30, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", rm690b0.GREEN)
display.text(10, 40, "abcdefghijklmnopqrstuvwxyz", rm690b0.YELLOW)
display.text(10, 50, "0123456789", rm690b0.MAGENTA)
display.text(10, 60, "!@#$%^&*()_+-=[]{}|;':\",./<>?", rm690b0.CYAN)
display.text(10, 80, "Small, compact font", rm690b0.WHITE)
display.text(10, 90, "8 pixels wide x 8 pixels tall", rm690b0.WHITE)
display.text(10, 100, "Best for: debug output, logs", rm690b0.DARK_GRAY)
display.swap_buffers()
time.sleep(3)

# Test 2: 16x16 Font
print("[2/5] Testing 16x16 Liberation Sans font...")
display.fill_color(rm690b0.BLACK)
display.set_font(1)
display.text(10, 10, "16x16 Liberation Sans", rm690b0.WHITE)
display.text(10, 30, "ABCDEFGHIJKLMNOP", rm690b0.GREEN)
display.text(10, 50, "abcdefghijklmnop", rm690b0.YELLOW)
display.text(10, 70, "0123456789", rm690b0.MAGENTA)
display.text(10, 90, "!@#$%^&*()", rm690b0.CYAN)
display.text(10, 110, "Larger, cleaner", rm690b0.WHITE)
display.text(10, 130, "16x16 pixels", rm690b0.WHITE)
display.text(10, 150, "Best for: UI, menus", rm690b0.DARK_GRAY)
display.swap_buffers()
time.sleep(3)

# Test 3: Side-by-side comparison
print("[3/5] Side-by-side comparison...")
display.fill_color(rm690b0.BLACK)
display.set_font(0)
display.text(10, 10, "8x8:", rm690b0.WHITE)
display.text(50, 10, "The quick brown fox", rm690b0.CYAN)
display.text(50, 20, "jumps over lazy dog", rm690b0.CYAN)

display.set_font(1)
display.text(10, 50, "16x16:", rm690b0.WHITE)
display.text(100, 50, "Quick Brown", rm690b0.CYAN)
display.text(100, 70, "Fox Jumps!", rm690b0.CYAN)

display.set_font(0)
display.text(10, 120, "Notice the size difference!", rm690b0.YELLOW)
display.swap_buffers()
time.sleep(3)

# Test 4: Background colors
print("[4/5] Testing background colors...")
display.fill_color(rm690b0.BLACK)

display.set_font(0)
display.text(10, 10, "8x8 with BG:", rm690b0.WHITE)
display.text(10, 25, " White on Red ", rm690b0.WHITE, rm690b0.RED)
display.text(10, 35, " Green on Blue ", rm690b0.GREEN, rm690b0.BLUE)
display.text(10, 45, " Yellow on Black ", rm690b0.YELLOW, rm690b0.BLACK)

display.set_font(1)
display.text(10, 70, "16x16 with BG:", rm690b0.WHITE)
display.text(10, 90, " Alert! ", rm690b0.WHITE, rm690b0.RED)
display.text(10, 110, " Info ", rm690b0.BLACK, rm690b0.CYAN)
display.text(10, 130, " Success ", rm690b0.WHITE, rm690b0.GREEN)

display.swap_buffers()
time.sleep(3)

# Test 5: Performance comparison
print("[5/5] Performance test (100 iterations)...")
display.fill_color(rm690b0.BLACK)
display.set_font(0)
display.text(10, 10, "Running performance test...", rm690b0.WHITE)
display.swap_buffers()

# Test 8x8 font speed
display.set_font(0)
start = time.monotonic()
for i in range(100):
    display.text(10, 30, "8x8 test string", rm690b0.CYAN)
elapsed_8x8 = time.monotonic() - start

# Test 16x16 font speed
display.set_font(1)
start = time.monotonic()
for i in range(100):
    display.text(10, 60, "16x16 test", rm690b0.GREEN)
elapsed_16x16 = time.monotonic() - start

# Display results
display.fill_color(rm690b0.BLACK)
display.set_font(0)
display.text(10, 10, "Performance Results:", rm690b0.WHITE)
display.text(10, 25, f"8x8:   {elapsed_8x8:.3f}s (100 renders)", rm690b0.CYAN)
display.text(10, 35, f"16x16: {elapsed_16x16:.3f}s (100 renders)", rm690b0.GREEN)
ratio = elapsed_16x16 / elapsed_8x8 if elapsed_8x8 > 0 else 0
display.text(10, 45, f"Ratio: {ratio:.2f}x slower", rm690b0.YELLOW)
display.text(10, 60, "(16x16 has 4x more pixels)", rm690b0.DARK_GRAY)
display.swap_buffers()

print("\nPerformance Results:")
print(f"  8x8 font:   {elapsed_8x8:.3f}s")
print(f"  16x16 font: {elapsed_16x16:.3f}s")
print(f"  Ratio:      {ratio:.2f}x slower")
print("\nExpected: ~4x slower (16x16 has 4x more pixels)")

time.sleep(5)

# Final summary
display.fill_color(rm690b0.BLACK)
display.set_font(0)
display.text(10, 10, "Font Test Summary", rm690b0.WHITE)
display.text(10, 25, "=" * 50, rm690b0.CYAN)
display.text(10, 35, "Font 0: 8x8 monospace", rm690b0.GREEN)
display.text(10, 45, "  - Compact, dense", rm690b0.DARK_GRAY)
display.text(10, 55, "  - Fast rendering", rm690b0.DARK_GRAY)
display.text(10, 65, "  - Best for: debug/logs", rm690b0.DARK_GRAY)
display.text(10, 80, "Font 1: 16x16 Liberation Sans", rm690b0.YELLOW)
display.text(10, 90, "  - Larger, cleaner", rm690b0.DARK_GRAY)
display.text(10, 100, "  - Better readability", rm690b0.DARK_GRAY)
display.text(10, 110, "  - Best for: UI/menus", rm690b0.DARK_GRAY)
display.text(10, 125, "=" * 50, rm690b0.CYAN)
display.text(10, 140, "Test complete!", rm690b0.WHITE)
display.swap_buffers()

print("\n" + "=" * 60)
print("Font test complete!")
print("=" * 60)
print("\nTo use fonts in your code:")
print("  display.set_font(0)  # 8x8 monospace")
print("  display.set_font(1)  # 16x16 Liberation Sans")
print("\nPress Ctrl+C to exit")

# Keep display on
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting...")
    display.deinit()
