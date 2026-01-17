import gc
import time

import board
import busio
import rm690b0
import rm690b0_lvgl

SINGLE_SIZE = False

gc.collect()
print(f"Free memory before start: {gc.mem_free()} bytes")

print("Initializing display...")
display = rm690b0.RM690B0()
display.init_display()

print("Initializing LVGL...")
lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()

lvgl.init_rendering()

i2c = None

# 2. Initialize Touch
print("Initializing Touch...")
try:
    i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)
    lvgl.init_touch(i2c)
    print("✓ Touch initialized")
except Exception as e:
    print(f"Warning: Touch init failed: {e}")
    print("Note: Touch pins should be board.TP_SCL and board.TP_SDA")

SCREEN_WIDTH = display.width
SCREEN_HEIGHT = display.height
print(f"Display dimensions: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

txt_colors = [0xFF0000, 0x00FF00, 0x0000FF]
txt_color_idx = 0

title = rm690b0_lvgl.Label("Testing fonts")
title.x = 10
title.y = 10
title.set_text_color(txt_colors[txt_color_idx])

print("Loading TTF font from: fonts/calibri.ttf")
print("This may take a moment...")
font_idx = 0
if SINGLE_SIZE:
    fonts = [rm690b0_lvgl.Font("fonts/calibri.ttf", 48)]
else:
    with open("fonts/calibri.ttf", "rb") as f:
        font_data = f.read()
    fonts = [
        rm690b0_lvgl.Font(font_data, 24),
        rm690b0_lvgl.Font(font_data, 32),
        rm690b0_lvgl.Font(font_data, 48),
        rm690b0_lvgl.Font(font_data, 64),
    ]

print("✓ Font loaded successfully")

title.set_style_text_font(fonts[0])

time.sleep(0.03)
lvgl.task_handler()


def on_click(btn):
    global txt_color_idx, font_idx
    print("Button clicked")
    txt_color_idx = (txt_color_idx + 1) % len(txt_colors)
    title.set_text_color(txt_colors[txt_color_idx])
    if not SINGLE_SIZE:
        font_idx = (font_idx + 1) % len(fonts)
        title.set_style_text_font(fonts[font_idx])
    

btn = rm690b0_lvgl.Button(text="Color")
btn.x = SCREEN_WIDTH - 120 - 10
btn.y = 10
btn.width = 120
btn.height = 45
btn.set_style_bg_color(0x008080)
btn.on_click = on_click


try:
    while True:
        lvgl.task_handler()
        time.sleep(0.05)  # 50ms - required for touch responsiveness with images

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    # Cleanup
    if i2c:
        i2c.deinit()
    lvgl.deinit()
    display.deinit()
    gc.collect()
    print(f"Free memory at the end: {gc.mem_free()} bytes")
