# LVGL Python Widget API Test
# Phase 5.4: Python Bindings Verification
#
# This script demonstrates creating a UI using Python classes (Label, Button)
# wrapping the underlying LVGL widgets.

import gc
import time

import board
import busio
import rm690b0
import rm690b0_lvgl

# Icon constants (LVGL FontAwesome symbols as UTF-8 Unicode)
SYMBOL_WIFI = "\uf1eb"
SYMBOL_SETTINGS = "\uf013"
SYMBOL_BATTERY_FULL = "\uf240"
SYMBOL_HOME = "\uf015"
SYMBOL_KEYBOARD = "\uf11c"

print("=" * 60)
print("LVGL Python GUI Test")
print("=" * 60)

# 1. Initialize Display System
print("Initializing display...")
display = rm690b0.RM690B0()
display.init_display()

print("Initializing LVGL...")
lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()
lvgl.init_rendering()

# Get display dimensions dynamically
SCREEN_WIDTH = display.width
SCREEN_HEIGHT = display.height
print(f"Display dimensions: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

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

# 3. Create UI using Python Widgets
print("Creating Widgets...")


# ============================================================================
# Temporary label
# ============================================================================
loading = rm690b0_lvgl.Label(text="Loading...")
loading.x = (SCREEN_WIDTH - 64) // 2
loading.y = (SCREEN_HEIGHT - 8) // 2
loading.set_text_color(0x000000)
time.sleep(0.03)
lvgl.task_handler()

# ============================================================================
# TITLE - Centered at top
# ============================================================================
title = rm690b0_lvgl.Label("Widget Demo")
print("Creating title label...")

print("Loading TTF font from: fonts/calibri.ttf")
print("This may take a moment...")
#gc.collect()  # Free up memory before loading font
print(f"Free memory before font load: {gc.mem_free()} bytes")
#font = rm690b0_lvgl.Font("fonts/calibri.ttf", 24)
print("✓ Font loaded successfully")
#gc.collect()
print(f"Free memory after font load: {gc.mem_free()} bytes")
print("Setting font to title...")
#title.set_style_text_font(font)
print("✓ Font applied to title")
time.sleep(0.03)
lvgl.task_handler()

title.x = (SCREEN_WIDTH - 120) // 2  # Center horizontally
title.y = 10
title.set_text_color(0x000080)  # Navy Blue

# Remove temporary label
loading.delete()

# ============================================================================
# STATUS BAR - Define early so callbacks can reference it
# ============================================================================
status_lbl = rm690b0_lvgl.Label(text="Ready - All widgets initialized")
status_lbl.x = 20
status_lbl.y = SCREEN_HEIGHT - 30
status_lbl.set_text_color(0x606060)


# ============================================================================
# Progress Bar with Button (Container Demo)
# ============================================================================
# Create Container
prog_cont = rm690b0_lvgl.Container()
prog_cont.x = 20
prog_cont.y = 40
prog_cont.width = 390
prog_cont.height = 70
prog_cont.set_style_bg_color(0xE0E0E0)
prog_cont.set_padding(10)
prog_cont.set_flex_flow(rm690b0_lvgl.FLEX_FLOW_ROW)
prog_cont.set_flex_align(
    rm690b0_lvgl.FLEX_ALIGN_SPACE_BETWEEN,
    rm690b0_lvgl.FLEX_ALIGN_CENTER,
    rm690b0_lvgl.FLEX_ALIGN_CENTER,
)

# Progress Bar Section
bar_lbl = rm690b0_lvgl.Label(text="Progress: 0%")
bar_lbl.set_text_color(0x000000)
bar_lbl.set_parent(prog_cont)  # Add to container

bar = rm690b0_lvgl.Bar(min_value=0, max_value=100)
bar.width = 180
bar.height = 20
bar.value = 0
bar.set_parent(prog_cont)  # Add to container


def update_bar(btn):
    current = bar.value
    if current >= 100:
        bar.value = 0
    else:
        bar.value = min(current + 20, 100)
    bar_lbl.text = f"Progress: {bar.value}%"
    status_lbl.text = f"Bar: {bar.value}%"
    print(f"Bar value: {bar.value}")


btn_bar = rm690b0_lvgl.Button(text="+20%")
btn_bar.width = 40
btn_bar.height = 40
btn_bar.set_style_bg_color(0x0080FF)  # Blue
btn_bar.on_click = update_bar
btn_bar.set_parent(prog_cont)  # Add to container


# ============================================================================
# Counter with Buttons
# ============================================================================
counter_val = 0
counter_lbl = rm690b0_lvgl.Label(text="Count: 0")
counter_lbl.x = 30
counter_lbl.y = 140
counter_lbl.set_text_color(0x000000)


def on_inc_click(btn):
    global counter_val
    counter_val += 1
    counter_lbl.text = f"Count: {counter_val}"
    status_lbl.text = "Incremented!"
    print(f"Button clicked! Count: {counter_val}")


def on_reset_click(btn):
    global counter_val
    counter_val = 0
    counter_lbl.text = f"Count: {counter_val}"
    status_lbl.text = "Reset!"
    print("Reset clicked!")


btn_inc = rm690b0_lvgl.Button(text="Count Up")
btn_inc.x = 30
btn_inc.y = 165
btn_inc.width = 120
btn_inc.height = 45
btn_inc.set_style_bg_color(0x00AA00)  # Green
btn_inc.on_click = on_inc_click

btn_rst = rm690b0_lvgl.Button(text="Reset")
btn_rst.x = 160
btn_rst.y = 165
btn_rst.width = 120
btn_rst.height = 45
btn_rst.set_style_bg_color(0xFF0000)  # Red
btn_rst.on_click = on_reset_click


# ============================================================================
# Slider with Controls
# ============================================================================
slider_lbl = rm690b0_lvgl.Label(text="Slider: 50")
slider_lbl.x = 310
slider_lbl.y = 130
slider_lbl.set_text_color(0x000000)


def on_slider_change(slider):
    value = slider.value
    slider_lbl.text = f"Slider: {value}"
    status_lbl.text = f"Slider: {value}"
    print(f"Slider value: {value}")


slider = rm690b0_lvgl.Slider(min_value=0, max_value=100)
slider.x = 310
slider.y = 156
slider.width = 250
slider.height = 16
slider.on_change = on_slider_change
slider.value = 50


def set_slider_min(btn):
    slider.value = 0
    status_lbl.text = "Slider: Min"


def set_slider_max(btn):
    slider.value = 100
    status_lbl.text = "Slider: Max"


btn_slider_min = rm690b0_lvgl.Button(text="Min")
btn_slider_min.x = 310
btn_slider_min.y = 180
btn_slider_min.width = 76
btn_slider_min.height = 36
btn_slider_min.on_click = set_slider_min

btn_slider_max = rm690b0_lvgl.Button(text="Max")
btn_slider_max.x = 396
btn_slider_max.y = 180
btn_slider_max.width = 76
btn_slider_max.height = 36
btn_slider_max.on_click = set_slider_max


# ============================================================================
# Roller Selector
# ============================================================================
roller_lbl = rm690b0_lvgl.Label(text="Mode: Normal")
roller_lbl.x = 30
roller_lbl.y = 280
roller_lbl.set_text_color(0x000000)


def on_roller_change(roller_obj):
    selected_text = roller_obj.selected_str
    roller_lbl.text = f"Mode: {selected_text}"
    status_lbl.text = f"Mode set to {selected_text}"
    print(f"Roller selection: {selected_text} (index {roller_obj.selected})")


roller = rm690b0_lvgl.Roller(options="Normal\nEco\nPerformance\nCustom")
roller.x = 30
roller.y = 306
roller.width = 160
roller.visible_row_count = 3
roller.on_change = on_roller_change
roller.selected = 0


# ============================================================================
# Toggles (Checkboxes and Switch)
# ============================================================================
# Checkbox 1
checkbox1_lbl = rm690b0_lvgl.Label(text="Feature: OFF")
checkbox1_lbl.x = 30
checkbox1_lbl.y = 220
checkbox1_lbl.set_text_color(0x000000)


def on_checkbox1_change(cb):
    checked = cb.checked
    checkbox1_lbl.text = f"Feature: {'ON' if checked else 'OFF'}"
    status_lbl.text = f"Feature: {'ON' if checked else 'OFF'}"
    print(f"Checkbox 1: {checked}")


checkbox1 = rm690b0_lvgl.Checkbox(text="Enable")
checkbox1.x = 30
checkbox1.y = 246
checkbox1.on_change = on_checkbox1_change

# Checkbox 2
checkbox2_lbl = rm690b0_lvgl.Label(text="Auto: ON")
checkbox2_lbl.x = 160
checkbox2_lbl.y = 220
checkbox2_lbl.set_text_color(0x000000)


def on_checkbox2_change(cb):
    checked = cb.checked
    checkbox2_lbl.text = f"Auto: {'ON' if checked else 'OFF'}"
    status_lbl.text = f"Auto: {'ON' if checked else 'OFF'}"
    print(f"Checkbox 2: {checked}")


checkbox2 = rm690b0_lvgl.Checkbox(text="Update")
checkbox2.x = 160
checkbox2.y = 246
checkbox2.on_change = on_checkbox2_change
checkbox2.checked = True  # Start checked

# Switch
switch_lbl = rm690b0_lvgl.Label(text="WiFi: OFF")
switch_lbl.x = 270
switch_lbl.y = 220
switch_lbl.set_text_color(0x000000)


def on_switch_change(sw):
    state = sw.checked
    switch_lbl.text = f"WiFi: {'ON' if state else 'OFF'}"
    status_lbl.text = f"WiFi: {'Connected' if state else 'Disconnected'}"
    print(f"WiFi Switch: {state}")


switch = rm690b0_lvgl.Switch()
switch.x = 270
switch.y = 246
switch.on_change = on_switch_change


# ============================================================================
# Arc (Circular Knob)
# ============================================================================
arc_lbl = rm690b0_lvgl.Label(text="Volume: 50")
arc_lbl.x = 220
arc_lbl.y = 280
arc_lbl.set_text_color(0x000000)


def on_arc_change(arc):
    arc_lbl.text = f"Volume: {arc.value}"
    status_lbl.text = f"Volume: {arc.value}"
    print(f"Arc value: {arc.value}")


arc = rm690b0_lvgl.Arc(min_value=0, max_value=100)
arc.x = 210
arc.y = 310
arc.width = 100
arc.height = 100
arc.on_change = on_arc_change
arc.value = 50


# ============================================================================
# Dropdown Menu
# ============================================================================
dropdown_lbl = rm690b0_lvgl.Label(text="Theme: Light")
dropdown_lbl.x = 420
dropdown_lbl.y = 40
dropdown_lbl.set_text_color(0x000000)


def on_dropdown_change(dd):
    dropdown_lbl.text = f"Theme: {dd.text}"
    status_lbl.text = f"Theme changed to {dd.text}"
    print(f"Dropdown: {dd.text} (index: {dd.selected})")


dropdown = rm690b0_lvgl.Dropdown(options="Light\nDark\nAuto\nCustom")
dropdown.x = 420
dropdown.y = 70
dropdown.width = 150
dropdown.on_change = on_dropdown_change
dropdown.selected = 0


# ============================================================================
# Spinner (Loading Indicator)
# ============================================================================
spinner_lbl = rm690b0_lvgl.Label(text="Activity")
spinner_lbl.x = 500
spinner_lbl.y = 180
spinner_lbl.set_text_color(0x444444)

spinner = rm690b0_lvgl.Spinner(time=800, arc_length=120)
spinner.x = 500
spinner.y = 200
spinner.width = 50
spinner.height = 50


# ============================================================================
# Icon Labels (LVGL symbols are font glyphs, use Label)
# ============================================================================
# WiFi icon
wifi_icon = rm690b0_lvgl.Label(text=SYMBOL_WIFI)
wifi_icon.x = 50
wifi_icon.y = 114
wifi_icon.set_text_color(0x0000FF)  # Blue

# Settings icon
settings_icon = rm690b0_lvgl.Label(text=SYMBOL_SETTINGS)
settings_icon.x = 100
settings_icon.y = 114
settings_icon.set_text_color(0x808080)  # Gray

# Battery icon
battery_icon = rm690b0_lvgl.Label(text=SYMBOL_BATTERY_FULL)
battery_icon.x = 150
battery_icon.y = 114
battery_icon.set_text_color(0x00AA00)  # Green

# Home icon
home_icon = rm690b0_lvgl.Label(text=SYMBOL_HOME)
home_icon.x = 200
home_icon.y = 114
home_icon.set_text_color(0xFF6600)  # Orange


# ============================================================================
# List Widget
# ============================================================================
list_lbl = rm690b0_lvgl.Label(text="List: -")
list_lbl.x = 330
list_lbl.y = 280
list_lbl.set_text_color(0x000000)

list_w = rm690b0_lvgl.List()
list_w.x = 330
list_w.y = 306
list_w.width = 120
list_w.height = 100


def on_list_btn_click(btn):
    list_lbl.text = f"List: {btn.text}"
    status_lbl.text = f"List selected: {btn.text}"
    print(f"List item clicked: {btn.text}")


list_w.add_text("Actions")
btn1 = list_w.add_btn(text="Open", icon=None)
btn1.on_click = on_list_btn_click
btn2 = list_w.add_btn(text="Save", icon=None)
btn2.on_click = on_list_btn_click
btn3 = list_w.add_btn(text="Delete", icon=None)
btn3.on_click = on_list_btn_click


# ============================================================================
# Spinbox
# ============================================================================
spinbox_lbl = rm690b0_lvgl.Label(text="Spinbox: 0")
spinbox_lbl.x = 470
spinbox_lbl.y = 280
spinbox_lbl.set_text_color(0x000000)

spinbox = rm690b0_lvgl.Spinbox()
spinbox.x = 470
spinbox.y = 350
spinbox.width = 90
spinbox.height = 40
spinbox.set_range(-100, 100)
spinbox.set_digit_format(3, 0)
spinbox.set_step(5)


def on_spinbox_change(sb):
    val = sb.value
    spinbox_lbl.text = f"Spinbox: {val}"
    status_lbl.text = f"Spinbox value: {val}"
    print(f"Spinbox: {val}")


spinbox.on_change = on_spinbox_change


def spin_inc(btn):
    spinbox.increment()


def spin_dec(btn):
    spinbox.decrement()


btn_spin_inc = rm690b0_lvgl.Button(text="+")
btn_spin_inc.x = 470
btn_spin_inc.y = 306
btn_spin_inc.width = 40
btn_spin_inc.height = 40
btn_spin_inc.on_click = spin_inc

btn_spin_dec = rm690b0_lvgl.Button(text="-")
btn_spin_dec.x = 520
btn_spin_dec.y = 306
btn_spin_dec.width = 40
btn_spin_dec.height = 40
btn_spin_dec.on_click = spin_dec


# ============================================================================
# Message Box Demo
# ============================================================================
mbox = None


def on_mbox_click(idx):
    global mbox
    if idx == 0:
        status_lbl.text = "Msgbox: OK"
    elif idx == 1:
        status_lbl.text = "Msgbox: Cancel"
    else:
        status_lbl.text = "Msgbox: Closed"

    if mbox:
        mbox.close()
        mbox = None


def show_msgbox(btn):
    global mbox
    if mbox:
        return

    btns = ["OK", "Cancel", ""]
    mbox = rm690b0_lvgl.Msgbox(
        title="Message",
        text="This is a modal dialog.\nInteract to close.",
        buttons=btns,
        close_btn=True,
    )
    mbox.on_click = on_mbox_click


btn_msg = rm690b0_lvgl.Button(text="Message")
btn_msg.x = 370
btn_msg.y = 230
btn_msg.width = 100
btn_msg.height = 40
btn_msg.set_style_bg_color(0x6A5ACD)  # SlateBlue
btn_msg.on_click = show_msgbox


# ============================================================================
# Additional Widgets Display Area
# ============================================================================
info_lbl = rm690b0_lvgl.Label(text="Touch any widget to interact")
info_lbl.x = 380
info_lbl.y = 420
info_lbl.set_text_color(0x404040)


# ============================================================================
# Tabview Demo
# ============================================================================
tv = rm690b0_lvgl.Tabview(tab_pos=rm690b0_lvgl.DIR_TOP, tab_size=30)
tv.x = 20
tv.y = 450
tv.width = 300
tv.height = 160


def on_tab_change(tv_obj):
    idx = tv_obj.active_tab
    status_lbl.text = f"Tab changed to {idx}"
    print(f"Tab changed: {idx}")


tv.on_change = on_tab_change

# Add Tabs
tab1 = tv.add_tab("Tab A")
tab2 = tv.add_tab("Tab B")
tab3 = tv.add_tab("Tab C")

# Add content to Tab 1
lbl_t1 = rm690b0_lvgl.Label(text="Content A")
lbl_t1.set_parent(tab1)
lbl_t1.x = 5
lbl_t1.y = 5

btn_t1 = rm690b0_lvgl.Button(text="Btn A")
btn_t1.set_parent(tab1)
btn_t1.x = 5
btn_t1.y = 30
btn_t1.width = 60
btn_t1.height = 30

# Add content to Tab 2
lbl_t2 = rm690b0_lvgl.Label(text="Content B")
lbl_t2.set_parent(tab2)
lbl_t2.x = 5
lbl_t2.y = 5
lbl_t2.set_text_color(0xFF0000)

# Add content to Tab 3
lbl_t3 = rm690b0_lvgl.Label(text="Content C")
lbl_t3.set_parent(tab3)
lbl_t3.x = 5
lbl_t3.y = 5


# ============================================================================
# Table Demo
# ============================================================================
table = rm690b0_lvgl.Table()
table.x = 340
table.y = 450
table.width = 140
table.height = 160

# Setup columns
table.set_col_cnt(2)
table.set_row_cnt(3)
table.set_col_width(0, 60)
table.set_col_width(1, 60)

# Fill data
table.set_cell_value(0, 0, "ID")
table.set_cell_value(0, 1, "Val")
table.set_cell_value(1, 0, "A1")
table.set_cell_value(1, 1, "42")
table.set_cell_value(2, 0, "B2")
table.set_cell_value(2, 1, "99")


# ============================================================================
# Data Visualization Demo (Chart + Scale + Canvas + Line)
# ============================================================================
chart_lbl = rm690b0_lvgl.Label(text="Chart: Temperature vs Humidity")
chart_lbl.x = 20
chart_lbl.y = 830
chart_lbl.set_text_color(0x202020)

chart = rm690b0_lvgl.Chart(chart_type=rm690b0_lvgl.CHART_TYPE_LINE)
chart.x = 20
chart.y = 860
chart.width = SCREEN_WIDTH - 40
chart.height = 150
chart.point_count = 12
chart.set_range(rm690b0_lvgl.CHART_AXIS_PRIMARY_Y, 0, 100)

temp_series = chart.add_series(0xFF6600)
humid_series = chart.add_series(0x0066FF)
temp_series.set_points([22, 34, 40, 38, 47, 55, 60, 64, 70, 72, 74, 78])
humid_series.set_points([78, 74, 72, 69, 65, 63, 60, 58, 55, 52, 50, 48])
chart_step = 0


def update_chart_series(_=None):
    global chart_step
    next_temp = (22 + (chart_step * 11)) % 100
    next_hum = max(25, 80 - ((chart_step * 7) % 55))
    temp_series.append(next_temp)
    humid_series.append(next_hum)
    status_lbl.text = f"Chart updated: T={next_temp}°C / H={next_hum}%"
    chart_step += 1


btn_chart = rm690b0_lvgl.Button(text="Update Chart")
btn_chart.x = SCREEN_WIDTH - 150
btn_chart.y = 830
btn_chart.width = 120
btn_chart.height = 30
btn_chart.on_click = update_chart_series

# Gauge / Scale demo
scale_lbl = rm690b0_lvgl.Label(text="Gauge: 90°")
scale_lbl.x = 20
scale_lbl.y = 1020
scale_lbl.set_text_color(0x202020)

scale = rm690b0_lvgl.Scale(min_value=0, max_value=180)
scale.x = 10
scale.y = 1050
scale.width = 190
scale.height = 190
scale.set_ticks(41, 2, 10, 0x555555)
scale.set_major_ticks(5, 4, 18, 0xFFFFFF, 12)
scale.value = 90


def nudge_scale(_=None):
    new_val = (scale.value + 18) % 181
    scale.value = new_val
    scale_lbl.text = f"Gauge: {new_val}°"
    status_lbl.text = f"Gauge updated to {new_val}°"


btn_gauge = rm690b0_lvgl.Button(text="Next Gauge")
btn_gauge.x = 20
btn_gauge.y = 1236
btn_gauge.width = 150
btn_gauge.height = 34
btn_gauge.on_click = nudge_scale

# Canvas drawing
canvas_lbl = rm690b0_lvgl.Label(text="Canvas Trail")
canvas_lbl.x = 220
canvas_lbl.y = 1020
canvas_lbl.set_text_color(0x202020)

canvas = rm690b0_lvgl.Canvas(180, 130, rm690b0_lvgl.IMG_CF_TRUE_COLOR)
canvas.x = 220
canvas.y = 1050


def refresh_canvas(_=None):
    canvas.fill_bg(0x101010)
    canvas.draw_line(
        [(10, 120), (40, 20), (70, 80), (110, 30), (160, 110)], color=0x00FFAA, width=4
    )
    for offset in range(0, 170, 15):
        canvas.set_px(offset, (offset // 2) % 120, 0xFFFFFF)
    status_lbl.text = "Canvas refreshed"


refresh_canvas()

btn_canvas = rm690b0_lvgl.Button(text="Redraw Canvas")
btn_canvas.x = 230
btn_canvas.y = 1196
btn_canvas.width = 160
btn_canvas.height = 34
btn_canvas.on_click = refresh_canvas

# Polyline Line widget
line_lbl = rm690b0_lvgl.Label(text="Polyline Demo")
line_lbl.x = 430
line_lbl.y = 1020
line_lbl.set_text_color(0x202020)

line = rm690b0_lvgl.Line()
line.x = 420
line.y = 1050
line.set_points([(0, 120), (40, 40), (80, 100), (120, 20), (160, 90)])
line.line_width = 3
line.line_color = 0xFF00FF
line.y_invert = True


# ============================================================================
# Textarea
# ============================================================================
def on_textarea_change(ta):
    print(f"Textarea updated: {ta.text}")
    status_lbl.text = f"Text: {ta.text}"


ta = rm690b0_lvgl.Textarea()
ta.x = 20
ta.y = 580
ta.width = 260
ta.height = 140
ta.placeholder = "Tap to start typing..."
ta.on_change = on_textarea_change


# ============================================================================
# Buttonmatrix
# ============================================================================
def on_btnm_click(btnm):
    btn_idx = btnm.selected_btn
    btn_text = btnm.selected_btn_text
    print(f"Buttonmatrix: Btn {btn_idx} -> '{btn_text}'")
    status_lbl.text = f"Keypad: {btn_text or btn_idx}"


keys = [
    "1",
    "2",
    "3",
    "\n",
    "4",
    "5",
    "6",
    "\n",
    "7",
    "8",
    "9",
    "\n",
    "*",
    "0",
    "#",
    "",
]

btnm = rm690b0_lvgl.Buttonmatrix(keys)
btnm.x = 280
btnm.y = 620
btnm.width = 200
btnm.height = 200
btnm.on_click = on_btnm_click


# ============================================================================
# On-screen Keyboard Overlay (created on demand so it starts hidden)
# ============================================================================
KEYBOARD_HEIGHT = 200
KEYBOARD_MARGIN = 12
KEYBOARD_LAYER_HEIGHT = KEYBOARD_HEIGHT + KEYBOARD_MARGIN + 24
keyboard_visible = False
keyboard_layer = None
keyboard = None
current_scroll_y = 0
previous_scroll_y = 0


def _scroll_screen_to(y):
    global current_scroll_y
    if y < 0:
        y = 0
    current_scroll_y = y
    lvgl.scroll_screen(y=y)


def _keyboard_anchor_y():
    print("anchor", ta.y, ta.height, KEYBOARD_MARGIN)
    return ta.y + ta.height + KEYBOARD_MARGIN


def _ensure_keyboard_objects():
    global keyboard_layer, keyboard
    if keyboard_layer is not None and keyboard is not None:
        return

    layer = rm690b0_lvgl.Container()
    layer.width = SCREEN_WIDTH
    layer.height = 0  # start collapsed so it doesn't affect layout
    layer.x = 0
    layer.y = _keyboard_anchor_y()
    layer.set_style_bg_color(0x000000)
    layer.set_style_bg_opa(0)

    kb = rm690b0_lvgl.Keyboard()
    kb.set_parent(layer)
    kb.width = 0
    kb.height = 0
    kb.x = 0
    kb.y = 0
    kb.set_style_bg_color(0x101010)
    kb.set_style_bg_opa(235)
    kb.set_popovers(True)

    keyboard_layer = layer
    keyboard = kb
    keyboard.on_change = on_keyboard_change


def hide_keyboard(_=None, *, clear_text=False):
    global keyboard_visible, keyboard_layer, keyboard, previous_scroll_y
    if keyboard_layer is None or keyboard is None:
        return
    if clear_text:
        ta.text = ""
    keyboard.set_textarea(None)
    keyboard_layer.y = _keyboard_anchor_y()
    keyboard_layer.height = 0
    keyboard.width = 0
    keyboard.height = 0
    keyboard_visible = False
    status_lbl.text = "Keyboard hidden"
    _scroll_screen_to(previous_scroll_y)
    previous_scroll_y = current_scroll_y


def show_keyboard(_=None):
    global keyboard_visible, previous_scroll_y
    if keyboard_visible:
        return
    previous_scroll_y = lvgl.get_scroll_y()
    _ensure_keyboard_objects()
    anchor_y = _keyboard_anchor_y()
    keyboard_layer.height = KEYBOARD_LAYER_HEIGHT
    keyboard_layer.y = anchor_y
    keyboard.width = SCREEN_WIDTH - 20
    keyboard.height = KEYBOARD_HEIGHT
    keyboard.x = 0
    keyboard.y = KEYBOARD_MARGIN
    keyboard_visible = True
    keyboard.set_textarea(ta)
    status_lbl.text = "Keyboard ready"
    scroll_y = anchor_y + KEYBOARD_LAYER_HEIGHT - SCREEN_HEIGHT
    print("show keyboard", keyboard_layer.y, keyboard_layer.height, SCREEN_HEIGHT)
    if scroll_y < 0:
        scroll_y = 0
    _scroll_screen_to(scroll_y)


# Ensure textarea focus/submit control keyboard visibility
ta.on_focus = show_keyboard
ta.on_submit = lambda ta_obj: hide_keyboard(clear_text=False)


def on_keyboard_change(kb):
    if kb.selected_btn_text == SYMBOL_KEYBOARD:
        hide_keyboard(clear_text=True)


# ============================================================================
# Image Widget (64x64 JPEG)
# ============================================================================
# image_lbl = rm690b0_lvgl.Label(text="Image:")
# image_lbl.x = 30
# image_lbl.y = 310
# image_lbl.set_text_color(0x000000)
#
# try:
#    with open("/cyborg.jpg", "rb") as f:
#        jpeg_data = f.read()
#
#    img = rm690b0_lvgl.Image()
#    img.x = -64
#    img.y = 234
#    img.load_jpeg(jpeg_data)
#    img.set_zoom(64)  # Zoom to 25% (64/256 = 0.25, LVGL zoom: 256=100%)


print("UI Created. Starting Main Loop...")
print(f"Display: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
print("Layout: Organized in rows with grouped widgets")
print(
    "Widgets: Labels, Buttons, Slider, Checkbox, Switch, Bar, Arc, Dropdown, Roller, Spinner, Container, Icons, Msgbox, List, Spinbox, Tabview, Table, Buttonmatrix, Textarea, Keyboard, Image (64x64)"
)
print("")
print("Touch any widget to interact:")
print("  - Message: Click to show modal message box")
print("  - List: Click items in scrollable list")
print("  - Spinbox: Use +/- buttons to change value")
print("  - Tabview: Switch between tabs")
print("  - Progress Bar: Click +25% button")
print("  - Counter: Click Count Up or Reset")
print("  - Slider: Drag slider or click Min/Max")
print("  - Roller: Flick the selector to choose a mode")
print("  - Spinner: Watch the animated loading indicator")
print("  - Checkboxes: Toggle Feature and Auto")
print("  - Switch: Toggle WiFi on/off")
print("  - Arc: Rotate the circular knob for volume")
print("  - Dropdown: Select theme from menu")
print(
    "  - Textarea: Tap the field to show the on-screen keyboard, then tap the ✓ key to submit and hide it"
)
print("  - Icons: Status icons displayed using Labels (WiFi, Settings, Battery, Home)")
print("  - Chart: Press 'Update Chart' to append live telemetry")
print("  - Scale: Use 'Next Gauge' to rotate the meter needle")
print("  - Canvas: Press 'Redraw Canvas' to regenerate the sparkline")
print("  - Line: Static polyline rendered using the Line widget")

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
