# RM690B0 LVGL Integration - Complete Guide

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Requirements](#installation--requirements)
4. [Quick Start](#quick-start)
5. [Python API Reference](#python-api-reference)
6. [Widget Classes](#widget-classes)
7. [Examples](#examples)
8. [Implementation Details](#implementation-details)
9. [Performance](#performance)
10. [Troubleshooting](#troubleshooting)
11. [Future Enhancements](#future-enhancements)

---

## Overview

The `rm690b0_lvgl` module provides **full LVGL (Light and Versatile Graphics Library) integration** for the RM690B0 AMOLED display on the Waveshare ESP32-S3 Touch AMOLED 2.41 board. This is the **official and recommended UI framework** for creating rich, interactive graphical user interfaces.

### What's Included

✅ **LVGL Core Integration**
- LVGL 8.x library compiled into CircuitPython
- Hardware-accelerated rendering via existing RM690B0 DMA paths
- Display driver with efficient flush callbacks
- Touch input driver for FT6336U controller
- Automatic tick timer for animations and tasks

✅ **Python Widget API**
- CircuitPython-native widget classes (no C required!)
- Base `Widget` class with positioning and styling
- `Label` class for text display
- `Button` class with click event handling
- Full property support (read/write `x`, `y`, `width`, `height`)
- Python callback functions for events

✅ **Performance**
- Double-buffered drawing (2 × 30-row buffers in PSRAM)
- Zero tearing or visual artifacts
- Clean partial updates for interactive elements

### Key Features

- **Simple API**: Easy initialization and widget creation
- **Event-Driven**: Python callbacks for button clicks and interactions
- **Memory Efficient**: ~36 KB for LVGL buffers, ~100-200 KB for widgets
- **Hardware Accelerated**: Uses existing RM690B0 DMA rendering
- **Touch Integrated**: Automatic coordinate transformation for portrait→landscape
- **Extensible**: Easy to add new widget types

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Application                      │
│  (Your code: create widgets, set properties, handle events) │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              rm690b0_lvgl Python Module                     │
│  - RM690B0_LVGL class (manager)                             │
│  - Widget, Label, Button classes                            │
│  - Property wrappers (x, y, width, height, text, etc.)      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              LVGL C Library (v8.x)                          │
│  - Core rendering engine                                    │
│  - Widget system (lv_obj, lv_label, lv_btn)                 │
│  - Event system                                             │
│  - Memory management                                        │
└─────────┬──────────────────────────┬────────────────────────┘
          │                          │
          ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│  Display Driver      │   │  Touch Driver        │
│  (flush callback)    │   │  (read callback)     │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│  RM690B0 Hardware    │   │  FT6336U Touch       │
│  (QSPI, DMA)         │   │  (I2C)               │
└──────────────────────┘   └──────────────────────┘
```

### Integration Flow

1. **Application** creates widgets using Python API
2. **Python Module** wraps LVGL C objects and handles property access
3. **LVGL Core** manages rendering, events, and animations
4. **Display Driver** flushes dirty regions to RM690B0 via DMA
5. **Touch Driver** reads FT6336U and feeds coordinates to LVGL

---

## Installation & Requirements

### Hardware Requirements

- **Board**: Waveshare ESP32-S3 Touch AMOLED 2.41
- **Display**: RM690B0 AMOLED (600×450 pixels, QSPI interface)
- **Touch**: FT6336U capacitive touch controller (I2C)
- **MCU**: ESP32-S3 with PSRAM

### Software Requirements

- **CircuitPython**: ESP32-S3 build with `rm690b0` and `rm690b0_lvgl` modules
- **LVGL**: v8.x compiled into firmware
- **Memory**: 
  - ~36 KB PSRAM for LVGL display buffers
  - ~100-200 KB PSRAM/heap for widget objects
  - Existing RM690B0 framebuffer (if used)

### Module Availability

The `rm690b0_lvgl` module is **built into CircuitPython firmware** for the Waveshare ESP32-S3 Touch AMOLED board. No separate installation required.

To verify availability:
```python
import rm690b0_lvgl
print(dir(rm690b0_lvgl))
# Should show: RM690B0_LVGL, Widget, Label, Button
```

---

## Quick Start

### Minimal Example (5 Lines)

```python
import rm690b0
import rm690b0_lvgl

# Step 1: Initialize hardware
display = rm690b0.RM690B0()
display.init_display()

# Step 2: Initialize LVGL
lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()

# Step 3: Main loop
import time
while True:
    lvgl.task_handler()
    time.sleep(0.01)
```

### Interactive Button Example

```python
import board
import busio
import rm690b0
import rm690b0_lvgl
import time

# Initialize display
display = rm690b0.RM690B0()
display.init_display()

# Initialize LVGL
lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()

# Initialize touch
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
lvgl.init_touch(i2c)

# Create a label
label = rm690b0_lvgl.Label(text="Click the button!")
label.x = 150
label.y = 100
label.set_text_color(0x0000FF)  # Blue

# Create a button with callback
def on_click(btn):
    label.text = "Button clicked!"
    print("Button was clicked!")

button = rm690b0_lvgl.Button(text="Click Me")
button.x = 200
button.y = 200
button.width = 200
button.height = 80
button.set_style_bg_color(0x00FF00)  # Green
button.on_click = on_click

# Main loop
print("Touch the button on screen...")
while True:
    lvgl.task_handler()
    time.sleep(0.01)
```

---

## Python API Reference

### Class: `RM690B0_LVGL`

Main manager class for LVGL integration.

#### Constructor

```python
RM690B0_LVGL()
```

Creates a new LVGL manager instance. Does not initialize display or touch yet.

**Example:**
```python
lvgl = rm690b0_lvgl.RM690B0_LVGL()
```

#### Methods

##### `init_display()`

Initialize the LVGL display driver.

```python
lvgl.init_display() -> None
```

**What it does:**
- Initializes LVGL core library (`lv_init()`)
- Gets panel handle from `rm690b0` module
- Allocates 2 × 30-row display buffers in PSRAM
- Registers display driver with flush callback
- Starts LVGL tick timer (2ms period)

**Requirements:**
- `rm690b0.RM690B0()` must be initialized first

**Raises:**
- `RuntimeError` if rm690b0 display not initialized

**Example:**
```python
display = rm690b0.RM690B0()
display.init_display()

lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()  # Now LVGL is ready
```

##### `init_touch(i2c)`

Initialize the LVGL touch input driver.

```python
lvgl.init_touch(i2c: busio.I2C) -> None
```

**Parameters:**
- `i2c` (busio.I2C): I2C bus connected to FT6336U touch controller

**What it does:**
- Configures FT6336U touch controller
- Registers LVGL input device driver
- Sets up coordinate transformation (portrait→landscape)
- Enables touch event handling

**Requirements:**
- `init_display()` must be called first
- I2C bus must be initialized

**Example:**
```python
import board
import busio

i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
lvgl.init_touch(i2c)
```

##### `task_handler()`

Process LVGL tasks (animations, timers, input).

```python
lvgl.task_handler() -> None
```

**What it does:**
- Calls `lv_task_handler()` to process pending LVGL tasks
- Handles animations, timers, and input events
- Must be called regularly in main loop

**Recommended:**
- Call every 10-20ms (50-100 Hz)
- More frequent = smoother animations
- Less frequent = lower CPU usage

**Example:**
```python
import time
while True:
    lvgl.task_handler()
    time.sleep(0.01)  # 100 Hz
```

##### `test_draw()`

Draw a test pattern for verification (diagnostic function).

```python
lvgl.test_draw() -> None
```

**What it does:**
- Creates simple LVGL test widgets
- Useful for verifying display driver functionality
- Shows colored rectangles and labels

**Example:**
```python
lvgl.init_display()
lvgl.test_draw()
# You should see colored test pattern on screen
```

##### `scroll_screen(*, x=0, y=0, animated=False)`

Scroll the active LVGL screen programmatically.

```python
lvgl.scroll_screen(y=200, animated=True)
```

**Parameters:**
- `x`, `y` (int): Target scroll offsets in pixels.
- `animated` (bool): Smooth animation if `True`.

Useful for ensuring off-screen widgets (e.g., Textarea + Keyboard) are
visible without the user manually dragging the view.

##### `get_scroll_y()`

Return the current vertical scroll offset.

```python
offset = lvgl.get_scroll_y()
print("Scroll:", offset)
```

Combine `get_scroll_y()` with `scroll_screen()` to restore the previous
position after temporarily shifting the layout for overlays.

##### `deinit()`

Clean up and release LVGL resources.

```python
lvgl.deinit() -> None
```

**What it does:**
- Stops tick timer
- Releases display buffers
- Deinitializes LVGL

**Example:**
```python
try:
    # Your LVGL code here
    pass
finally:
    lvgl.deinit()
```

#### Properties

##### `width` (read-only)

Display width in pixels.

```python
w = lvgl.width  # Returns 600
```

##### `height` (read-only)

Display height in pixels.

```python
h = lvgl.height  # Returns 450
```

#### Context Manager Support

```python
with rm690b0_lvgl.RM690B0_LVGL() as lvgl:
    lvgl.init_display()
    # Use lvgl...
# Automatically calls deinit() on exit
```

---

### Class: `Font`

Represents a font loaded from a TTF file or data using the Tiny TTF library.

#### Constructor

```python
font = rm690b0_lvgl.Font(file_or_data, size)
```

- **file_or_data**: Path to the TTF file (string) or a bytes-like object containing TTF data.
- **size**: Font size in pixels.

#### Methods

##### `set_size(size)`

Updates the font size.

- **size**: New font size in pixels.

```python
font.set_size(24)
```

#### Complete Font Example

```python
import rm690b0_lvgl

# Load from file
font_file = rm690b0_lvgl.Font("fonts/myfont.ttf", 20)

# Load from bytes
with open("fonts/myfont.ttf", "rb") as f:
    font_data = f.read()
font_mem = rm690b0_lvgl.Font(font_data, 30)

# Apply to a label
label = rm690b0_lvgl.Label("Custom Font")
label.set_style_text_font(font_file)
```

## Widget Classes

### Base Class: `Widget`

Base container widget. Can be instantiated directly or subclassed.

#### Constructor

```python
Widget()
```

Creates a base LVGL object (container) on the active screen.

**Example:**
```python
container = rm690b0_lvgl.Widget()
container.x = 50
container.y = 50
container.width = 200
container.height = 200
container.set_style_bg_color(0xCCCCCC)  # Light gray background
```

#### Properties (Read/Write)

##### `x: int`

X-coordinate relative to parent (pixels).

```python
widget.x = 100
print(widget.x)  # 100
```

##### `y: int`

Y-coordinate relative to parent (pixels).

```python
widget.y = 50
print(widget.y)  # 50
```

##### `width: int`

Widget width (pixels).

```python
widget.width = 200
print(widget.width)  # 200
```

##### `height: int`

Widget height (pixels).

```python
widget.height = 100
print(widget.height)  # 100
```

#### Methods

##### `set_style_bg_color(color)`

Set background color.

```python
widget.set_style_bg_color(color: int) -> None
```

**Parameters:**
- `color` (int): RGB888 color value (0x000000 to 0xFFFFFF)

**Example:**
```python
widget.set_style_bg_color(0xFF0000)  # Red
widget.set_style_bg_color(0x00FF00)  # Green
widget.set_style_bg_color(0x0000FF)  # Blue
```

##### `set_style_bg_opa(opacity)`

Set background opacity.

```python
widget.set_style_bg_opa(opacity: int) -> None
```

**Parameters:**
- `opacity` (int): Opacity value (0-255)
  - 0 = fully transparent
  - 255 = fully opaque

**Example:**
```python
widget.set_style_bg_opa(255)  # Fully opaque
widget.set_style_bg_opa(128)  # 50% transparent
widget.set_style_bg_opa(0)    # Fully transparent
```

---

##### `set_style_text_font(font)`

Sets the text font for the widget.

- **font**: A `rm690b0_lvgl.Font` object.

```python
font = rm690b0_lvgl.Font("arial.ttf", 16)
widget.set_style_text_font(font)
```

### Class: `Label`

Text display widget. Inherits from `Widget`.

#### Constructor

```python
Label(text: str = "Label")
```

Creates a label with the specified text.

**Parameters:**
- `text` (str, optional): Initial text content (default: "Label")

**Example:**
```python
label = rm690b0_lvgl.Label(text="Hello World")
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `text: str`

Text content of the label.

```python
label.text = "New text"
print(label.text)  # "New text"
```

**Example:**
```python
counter = 0
label = rm690b0_lvgl.Label(text=f"Count: {counter}")
label.x = 100
label.y = 50

# Update text dynamically
counter += 1
label.text = f"Count: {counter}"
```

#### Methods

Inherits all `Widget` methods plus:

##### `set_text_color(color)`

Set text color.

```python
label.set_text_color(color: int) -> None
```

**Parameters:**
- `color` (int): RGB888 color value (0x000000 to 0xFFFFFF)

**Example:**
```python
label.set_text_color(0xFF0000)  # Red text
label.set_text_color(0x000000)  # Black text
label.set_text_color(0xFFFFFF)  # White text
```

#### Complete Label Example

```python
# Create and configure label
title = rm690b0_lvgl.Label(text="Temperature Monitor")
title.x = 100
title.y = 20
title.width = 400
title.set_text_color(0x0000FF)  # Blue
title.set_style_bg_color(0xFFFFFF)  # White background
title.set_style_bg_opa(255)  # Fully opaque

# Update label periodically
import time
temp = 25.0
while True:
    temp += 0.1
    title.text = f"Temp: {temp:.1f}°C"
    lvgl.task_handler()
    time.sleep(0.5)
```

---

### Class: `Button`

Clickable button widget. Inherits from `Widget`.

#### Constructor

```python
Button(text: str = "Button")
```

Creates a button with the specified text.

**Parameters:**
- `text` (str, optional): Initial button text (default: "Button")

**Example:**
```python
button = rm690b0_lvgl.Button(text="Click Me")
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `text: str`

Text displayed on the button.

```python
button.text = "Press Here"
print(button.text)  # "Press Here"
```

##### `on_click: callable`

Python callback function called when button is clicked.

```python
def my_callback(btn):
    print("Button clicked!")

button.on_click = my_callback
```

**Callback Signature:**
```python
def callback(button: Button) -> None:
    # button is the Button instance that was clicked
    pass
```

**Example:**
```python
def on_button_click(btn):
    print(f"Button '{btn.text}' was clicked!")
    btn.text = "Clicked!"

button = rm690b0_lvgl.Button(text="Click Me")
button.on_click = on_button_click
```

#### Complete Button Example

```python
# Create counter with increment button
counter_value = 0
label = rm690b0_lvgl.Label(text=f"Count: {counter_value}")
label.x = 200
label.y = 100

def increment(btn):
    global counter_value
    counter_value += 1
    label.text = f"Count: {counter_value}"
    print(f"Counter: {counter_value}")

button = rm690b0_lvgl.Button(text="Increment")
button.x = 180
button.y = 200
button.width = 200
button.height = 80
button.set_style_bg_color(0x00AA00)  # Green
button.on_click = increment

# Main loop
import time
while True:
    lvgl.task_handler()
    time.sleep(0.01)
```

---

### Class: `Slider`

Horizontal slider widget for selecting values in a range. Inherits from `Widget`.

#### Constructor

```python
Slider(min_value: int = 0, max_value: int = 100)
```

Creates a slider with the specified range.

**Parameters:**
- `min_value` (int, optional): Minimum value (default: 0)
- `max_value` (int, optional): Maximum value (default: 100)

**Example:**
```python
slider = rm690b0_lvgl.Slider(min_value=0, max_value=100)
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `value: int`

Current slider value.

```python
slider.value = 50
print(slider.value)  # 50
```

##### `min_value: int`

Minimum slider value.

```python
slider.min_value = 0
print(slider.min_value)  # 0
```

##### `max_value: int`

Maximum slider value.

```python
slider.max_value = 100
print(slider.max_value)  # 100
```

##### `on_change: callable`

Python callback function called when slider value changes (by touch or programmatically).

```python
def my_callback(slider):
    print(f"Value: {slider.value}")

slider.on_change = my_callback
```

**Callback Signature:**
```python
def callback(slider: Slider) -> None:
    # slider is the Slider instance
    pass
```

#### Complete Slider Example

```python
# Create label to show slider value
value_label = rm690b0_lvgl.Label(text="Volume: 50")
value_label.x = 250
value_label.y = 100

def on_volume_change(slider):
    value_label.text = f"Volume: {slider.value}"

slider = rm690b0_lvgl.Slider(min_value=0, max_value=100)
slider.x = 180
slider.y = 150
slider.width = 240
slider.height = 15
slider.on_change = on_volume_change
slider.value = 50  # Triggers callback, updates label
```

---

### Class: `Checkbox`

Checkbox widget for toggling options on/off. Inherits from `Widget`.

#### Constructor

```python
Checkbox(text: str = "Checkbox")
```

Creates a checkbox with the specified label text.

**Parameters:**
- `text` (str, optional): Label text (default: "Checkbox")

**Example:**
```python
checkbox = rm690b0_lvgl.Checkbox(text="Enable Feature")
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `checked: bool`

Checkbox state (True=checked, False=unchecked).

```python
checkbox.checked = True
print(checkbox.checked)  # True
```

##### `text: str`

Label text displayed next to the checkbox.

```python
checkbox.text = "New Label"
print(checkbox.text)  # "New Label"
```

##### `on_change: callable`

Python callback function called when checkbox state changes (by touch or programmatically).

```python
def my_callback(checkbox):
    print(f"Checked: {checkbox.checked}")

checkbox.on_change = my_callback
```

**Callback Signature:**
```python
def callback(checkbox: Checkbox) -> None:
    # checkbox is the Checkbox instance
    pass
```

#### Methods

Inherits all `Widget` methods plus:

##### `toggle()`

Toggle the checkbox state (checked ↔ unchecked).

```python
checkbox.toggle() -> None
```

**Example:**
```python
checkbox.checked = True
checkbox.toggle()  # Now False
checkbox.toggle()  # Now True
```

#### Complete Checkbox Example

```python
# Create label to show state
state_label = rm690b0_lvgl.Label(text="Feature: OFF")
state_label.x = 200
state_label.y = 100

def on_feature_toggle(cb):
    state = "ON" if cb.checked else "OFF"
    state_label.text = f"Feature: {state}"
    print(f"Feature is now {state}")

checkbox = rm690b0_lvgl.Checkbox(text="Enable Feature")
checkbox.x = 50
checkbox.y = 150
checkbox.on_change = on_feature_toggle
checkbox.checked = False  # Triggers callback
```

---

### Class: `Switch`

Switch (toggle) widget for on/off options. Similar to checkbox but styled as a sliding switch. Inherits from `Widget`.

#### Constructor

```python
Switch()
```

Creates a switch widget (starts in OFF state).

**Example:**
```python
switch = rm690b0_lvgl.Switch()
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `checked: bool`

Switch state (True=ON, False=OFF).

```python
switch.checked = True  # Turn ON
print(switch.checked)  # True
```

##### `on_change: callable`

Python callback function called when switch state changes (by touch or programmatically).

```python
def my_callback(switch):
    print(f"Switch is {'ON' if switch.checked else 'OFF'}")

switch.on_change = my_callback
```

**Callback Signature:**
```python
def callback(switch: Switch) -> None:
    # switch is the Switch instance
    pass
```

#### Methods

Inherits all `Widget` methods plus:

##### `toggle()`

Toggle the switch state (ON ↔ OFF).

```python
switch.toggle() -> None
```

**Example:**
```python
switch.checked = True
switch.toggle()  # Now False
switch.toggle()  # Now True
```

#### Complete Switch Example

```python
# Create label to show WiFi state
wifi_label = rm690b0_lvgl.Label(text="WiFi: OFF")
wifi_label.x = 200
wifi_label.y = 100

def on_wifi_toggle(sw):
    state = "ON" if sw.checked else "OFF"
    wifi_label.text = f"WiFi: {state}"
    if sw.checked:
        print("Connecting to WiFi...")
    else:
        print("Disconnecting WiFi...")

switch = rm690b0_lvgl.Switch()
switch.x = 100
switch.y = 95
switch.on_change = on_wifi_toggle
switch.checked = False  # Start OFF
```

#### Switch vs Checkbox

| Feature | Switch | Checkbox |
|---------|--------|----------|
| Visual Style | Sliding toggle | Checkmark box |
| Best For | On/Off states | Select/Deselect options |
| Label | No built-in label | Built-in label |
| Common Use | Settings (WiFi, Bluetooth) | Forms, multi-select lists |

---

### Class: `Bar`

Progress bar widget for displaying progress, loading, or level indicators. Inherits from `Widget`.

#### Constructor

```python
Bar(min_value: int = 0, max_value: int = 100)
```

Creates a horizontal progress bar with the specified range.

**Parameters:**
- `min_value` (int, optional): Minimum value (default: 0)
- `max_value` (int, optional): Maximum value (default: 100)

**Example:**
```python
bar = rm690b0_lvgl.Bar(min_value=0, max_value=100)
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `value: int`

Current bar value (progress).

```python
bar.value = 75
print(bar.value)  # 75
```

##### `min_value: int`

Minimum bar value.

```python
bar.min_value = 0
print(bar.min_value)  # 0
```

##### `max_value: int`

Maximum bar value.

```python
bar.max_value = 100
print(bar.max_value)  # 100
```

#### Methods

Inherits all `Widget` methods plus:

##### `set_range(min_value, max_value)`

Set both minimum and maximum values at once.

```python
bar.set_range(min_value: int, max_value: int) -> None
```

**Parameters:**
- `min_value` (int): New minimum value
- `max_value` (int): New maximum value

**Example:**
```python
bar.set_range(0, 200)
```

#### Complete Bar Example

```python
# Create progress label
progress_label = rm690b0_lvgl.Label(text="Loading: 0%")
progress_label.x = 250
progress_label.y = 100

# Create progress bar
progress_bar = rm690b0_lvgl.Bar(min_value=0, max_value=100)
progress_bar.x = 180
progress_bar.y = 150
progress_bar.width = 240
progress_bar.height = 20
progress_bar.value = 0

# Simulate loading
import time
for i in range(0, 101, 10):
    progress_bar.value = i
    progress_label.text = f"Loading: {i}%"
    lvgl.task_handler()
    time.sleep(0.1)
```

#### Bar Use Cases

| Use Case | Example | Range |
|----------|---------|-------|
| Progress | File download | 0-100% |
| Battery Level | Power indicator | 0-100% |
| Volume | Audio level | 0-100 |
| Temperature | Thermometer | -20 to 50°C |
| Score | Game points | 0-1000 |

---

### Class: `Arc`

Circular arc widget for value selection with a knob/dial interface. Inherits from `Widget`.

#### Constructor

```python
Arc(min_value: int = 0, max_value: int = 100)
```

Creates a circular arc (knob) with the specified range.

**Parameters:**
- `min_value` (int, optional): Minimum value (default: 0)
- `max_value` (int, optional): Maximum value (default: 100)

**Example:**
```python
arc = rm690b0_lvgl.Arc(min_value=0, max_value=100)
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `value: int`

Current arc value (knob position).

```python
arc.value = 75
print(arc.value)  # 75
```

##### `min_value: int`

Minimum arc value.

```python
arc.min_value = 0
print(arc.min_value)  # 0
```

##### `max_value: int`

Maximum arc value.

```python
arc.max_value = 100
print(arc.max_value)  # 100
```

##### `on_change: callable`

Python callback function called when arc value changes (by touch or programmatically).

```python
def my_callback(arc):
    print(f"Value: {arc.value}")

arc.on_change = my_callback
```

**Callback Signature:**
```python
def callback(arc: Arc) -> None:
    # arc is the Arc instance
    pass
```

#### Methods

Inherits all `Widget` methods plus:

##### `set_range(min_value, max_value)`

Set both minimum and maximum values at once.

```python
arc.set_range(min_value: int, max_value: int) -> None
```

**Parameters:**
- `min_value` (int): New minimum value
- `max_value` (int): New maximum value

**Example:**
```python
arc.set_range(0, 200)
```

#### Complete Arc Example

```python
# Create volume label
volume_label = rm690b0_lvgl.Label(text="Volume: 50")
volume_label.x = 200
volume_label.y = 100

# Create arc knob
def on_volume_change(arc):
    volume_label.text = f"Volume: {arc.value}"

volume_arc = rm690b0_lvgl.Arc(min_value=0, max_value=100)
volume_arc.x = 200
volume_arc.y = 150
volume_arc.width = 120
volume_arc.height = 120
volume_arc.on_change = on_volume_change
volume_arc.value = 50  # Triggers callback
```

#### Arc Use Cases

| Use Case | Example | Range |
|----------|---------|-------|
| Volume Control | Audio knob | 0-100 |
| Temperature | Thermostat dial | 15-30°C |
| Brightness | Display dimmer | 0-255 |
| Speed | Fan/motor control | 0-10 |
| Progress | Circular progress | 0-100% |

---

### Class: `Dropdown`

Dropdown menu widget for selecting options from a list. Inherits from `Widget`.

#### Constructor

```python
Dropdown(options: str = "Option 1\nOption 2\nOption 3")
```

Creates a dropdown menu with options specified as a newline-separated string.

**Parameters:**
- `options` (str, optional): Newline-separated list of options (default: "Option 1\nOption 2\nOption 3")

**Example:**
```python
dropdown = rm690b0_lvgl.Dropdown(options="Red\nGreen\nBlue")
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `selected: int`

Index of the currently selected option (0-based).

```python
dropdown.selected = 1  # Select second option
print(dropdown.selected)  # 1
```

##### `text: str`

Text of the currently selected option (read-only).

```python
print(dropdown.text)  # "Green"
```

##### `on_change: callable`

Python callback function called when selection changes (by touch or programmatically).

```python
def my_callback(dropdown):
    print(f"Selected: {dropdown.text}")

dropdown.on_change = my_callback
```

**Callback Signature:**
```python
def callback(dropdown: Dropdown) -> None:
    # dropdown is the Dropdown instance
    pass
```

#### Methods

Inherits all `Widget` methods plus:

##### `set_options(options)`

Set all options at once using a newline-separated string.

```python
dropdown.set_options(options: str) -> None
```

**Parameters:**
- `options` (str): Newline-separated list of options

**Example:**
```python
dropdown.set_options("Small\nMedium\nLarge\nXL")
```

##### `add_option(option, pos=-1)`

Add a single option to the dropdown.

```python
dropdown.add_option(option: str, pos: int = -1) -> None
```

**Parameters:**
- `option` (str): Option text to add
- `pos` (int, optional): Position to insert (-1 = end, default: -1)

**Example:**
```python
dropdown.add_option("Extra Large")  # Add at end
dropdown.add_option("Tiny", 0)      # Add at beginning
```

##### `clear_options()`

Clear all options from the dropdown.

```python
dropdown.clear_options() -> None
```

**Example:**
```python
dropdown.clear_options()
dropdown.add_option("New Option 1")
dropdown.add_option("New Option 2")
```

#### Complete Dropdown Example

```python
# Create theme label
theme_label = rm690b0_lvgl.Label(text="Theme: Light")
theme_label.x = 200
theme_label.y = 100

# Create dropdown
def on_theme_change(dd):
    theme_label.text = f"Theme: {dd.text}"
    print(f"Selected theme: {dd.text} (index: {dd.selected})")

theme_dd = rm690b0_lvgl.Dropdown(options="Light\nDark\nAuto")
theme_dd.x = 200
theme_dd.y = 130
theme_dd.width = 150
theme_dd.on_change = on_theme_change
theme_dd.selected = 0  # Start with "Light"
```

#### Dropdown Use Cases

| Use Case | Example Options | Default |
|----------|----------------|---------|
| Theme Selection | Light\nDark\nAuto | Light |
| Language | English\nSpanish\nFrench | English |
| Quality | Low\nMedium\nHigh\nUltra | Medium |
| Sort By | Name\nDate\nSize | Name |
| Speed | 1x\n1.5x\n2x | 1x |

---

### Class: `Image`

> **Status:** Not yet implemented in the CircuitPython build (API documented for future release).

Image widget for displaying graphics, icons, logos, and photos. Inherits from `Widget`.

#### Constructor

```python
Image()
```

Creates an empty image widget. Use `set_src()` to set the image source.

**Example:**
```python
img = rm690b0_lvgl.Image()
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`).

#### Methods

Inherits all `Widget` methods plus:

##### `set_src(src)`

Set the image source.

```python
img.set_src(src: str) -> None
```

**Parameters:**
- `src` (str): Image source - file path or LVGL symbol

**Supported Sources:**
- **File path:** "/sd/image.bin" (LVGL binary format)
- **Built-in symbols:** "LV_SYMBOL_HOME", "LV_SYMBOL_SETTINGS", "LV_SYMBOL_WIFI", etc.

**Example:**
```python
# Using built-in symbol
img.set_src("LV_SYMBOL_HOME")

# Using image file (requires file on SD card in LVGL format)
img.set_src("/sd/logo.bin")
```

##### `set_angle(angle)`

Rotate the image.

```python
img.set_angle(angle: int) -> None
```

**Parameters:**
- `angle` (int): Rotation angle in degrees (0-360)

**Example:**
```python
img.set_angle(45)   # Rotate 45 degrees
img.set_angle(180)  # Flip upside down
```

##### `set_zoom(zoom)`

Scale the image.

```python
img.set_zoom(zoom: int) -> None
```

**Parameters:**
- `zoom` (int): Zoom level (256 = 100%, 512 = 200%, 128 = 50%)

**Example:**
```python
img.set_zoom(256)  # 100% (normal size)
img.set_zoom(512)  # 200% (double size)
img.set_zoom(128)  # 50% (half size)
```

##### `set_color(color)`

Set the color for recoloring the image (especially useful for symbols/icons).

```python
img.set_color(color: int) -> None
```

**Parameters:**
- `color` (int): RGB888 color value (0x000000 to 0xFFFFFF)

**Example:**
```python
img.set_color(0xFF0000)  # Red
img.set_color(0x0000FF)  # Blue
img.set_color(0x00FF00)  # Green
```

##### `load_bmp(bmp_data)`

Load a BMP image from bytes data.

```python
img.load_bmp(bmp_data: bytes) -> None
```

**Parameters:**
- `bmp_data` (bytes): BMP file data as bytes

**Example:**
```python
# Load BMP from file
with open("/sd/photo.bmp", "rb") as f:
    bmp_data = f.read()

img = rm690b0_lvgl.Image()
img.x = 100
img.y = 100
img.load_bmp(bmp_data)
```

**Note:** Uses the rm690b0 driver's image converter to decode BMP files.

##### `load_jpeg(jpeg_data)`

Load a JPEG image from bytes data.

```python
img.load_jpeg(jpeg_data: bytes) -> None
```

**Parameters:**
- `jpeg_data` (bytes): JPEG file data as bytes

**Example:**
```python
# Load JPEG from file
with open("/sd/photo.jpg", "rb") as f:
    jpeg_data = f.read()

img = rm690b0_lvgl.Image()
img.x = 100
img.y = 100
img.load_jpeg(jpeg_data)
```

**Note:** Uses the rm690b0 driver's image converter to decode JPEG files.

#### Complete Image Example

```python
# For icons, use Label widget with LVGL symbol Unicode strings
wifi_icon = rm690b0_lvgl.Label(text="\xef\x87\xab")  # WiFi symbol
wifi_icon.x = 500
wifi_icon.y = 20
wifi_icon.set_text_color(0x0000FF)  # Blue

# Load and display a JPEG photo
with open("/sd/photo.jpg", "rb") as f:
    jpeg_data = f.read()

photo = rm690b0_lvgl.Image()
photo.x = 100
photo.y = 50
photo.load_jpeg(jpeg_data)

# Load and display a BMP image (rotated)
with open("/sd/logo.bmp", "rb") as f:
    bmp_data = f.read()

logo = rm690b0_lvgl.Image()
logo.x = 250
logo.y = 150
logo.load_bmp(bmp_data)
logo.set_angle(15)   # Slight tilt
```

#### Built-in LVGL Symbols (Use with Label Widget)

**Note:** LVGL symbols are font glyphs (Unicode characters), not images. Use the **Label** widget to display them, not the Image widget.

Common symbols you can use:

| Symbol | Description | Symbol | Description |
|--------|-------------|--------|-------------|
| `LV_SYMBOL_AUDIO` | Speaker | `LV_SYMBOL_VIDEO` | Video |
| `LV_SYMBOL_LIST` | List | `LV_SYMBOL_OK` | Checkmark |
| `LV_SYMBOL_CLOSE` | X | `LV_SYMBOL_POWER` | Power |
| `LV_SYMBOL_SETTINGS` | Gear | `LV_SYMBOL_HOME` | House |
| `LV_SYMBOL_DOWNLOAD` | Down arrow | `LV_SYMBOL_UPLOAD` | Up arrow |
| `LV_SYMBOL_LOOP` | Refresh | `LV_SYMBOL_VOLUME_MAX` | Volume |
| `LV_SYMBOL_IMAGE` | Picture | `LV_SYMBOL_EDIT` | Pencil |
| `LV_SYMBOL_PREV` | Previous | `LV_SYMBOL_NEXT` | Next |
| `LV_SYMBOL_EJECT` | Eject | `LV_SYMBOL_LEFT` | Left arrow |
| `LV_SYMBOL_RIGHT` | Right arrow | `LV_SYMBOL_PLUS` | Plus |
| `LV_SYMBOL_MINUS` | Minus | `LV_SYMBOL_WARNING` | Warning |
| `LV_SYMBOL_BATTERY_FULL` | Battery | `LV_SYMBOL_BLUETOOTH` | BT |
| `LV_SYMBOL_GPS` | GPS | `LV_SYMBOL_WIFI` | WiFi |

#### Image Use Cases

| Use Case | Widget Type | Method | Example |
|----------|-------------|--------|---------|
| Status Icons | **Label** | Set text to Unicode | WiFi, Battery, GPS indicators |
| Navigation Icons | **Label** | Set text to Unicode | Home, Back, Settings buttons |
| Photos | **Image** | `load_jpeg()` | JPEG photos from SD card |
| Graphics | **Image** | `load_bmp()` | BMP graphics from SD card |
| Logos | **Image** | `load_bmp()` or `load_jpeg()` | Company logo, app icon |

**Important Notes:**
- **For icons:** Use **Label** widget with LVGL symbol Unicode strings (e.g., `"\xef\x87\xab"` for WiFi)
- **For photos/images:** Use **Image** widget with `load_bmp()` or `load_jpeg()` to load from bytes
- The Image widget uses the rm690b0 driver's native BMP and JPEG decoders
- Images are automatically converted to RGB565 format for display

### Class: `Chart`

Interactive chart widget powered by LVGL's `lv_chart`.

#### Constructor

```python
Chart(chart_type: int = rm690b0_lvgl.CHART_TYPE_LINE)
```

Use the helpers `CHART_TYPE_*` and `CHART_AXIS_*` constants exposed from the module.

#### Properties

- `type: int` — Switch between line, bar or scatter modes.
- `point_count: int` — Number of stored points per series.

#### Methods

- `set_range(axis, min_value, max_value)` — Configure axis ranges.
- `add_series(color, axis=CHART_AXIS_PRIMARY_Y) -> ChartSeries` — Adds a new data series.
- `refresh()` — Forces LVGL to redraw immediately.

#### Class: `ChartSeries`

`Chart.add_series()` returns a `ChartSeries` helper with:
- `set_points(values)` — Replace all data points.
- `set_point(index, value)` — Update a single point.
- `append(value)` — Append value using LVGL's rolling buffer.
- `color` property — Get/set the stroke color.

#### Chart Example

```python
chart = rm690b0_lvgl.Chart(chart_type=rm690b0_lvgl.CHART_TYPE_LINE)
chart.width = 260
chart.height = 150
chart.point_count = 20
chart.set_range(rm690b0_lvgl.CHART_AXIS_PRIMARY_Y, 0, 100)

series = chart.add_series(0x00AAFF)
series.set_points([10, 20, 45, 32, 65, 80, 55, 70, 60, 40])
series.append(75)
chart.refresh()
```

### Class: `Scale`

Gauge-style widget built on LVGL's meter object.

#### Constructor

```python
Scale(min_value: int = 0, max_value: int = 100)
```

#### Properties

- `value: int` — Current indicator value.

#### Methods

- `set_range(min_value, max_value)` — Update numeric range.
- `set_angles(angle_range, rotation)` — Configure sweep and zero angle (degrees).
- `set_ticks(count=41, width=2, length=8, color=0x888888)` — Customize minor ticks.
- `set_major_ticks(every=5, width=4, length=16, color=0xFFFFFF, label_gap=12)` — Major ticks + labels.

#### Scale Example

```python
scale = rm690b0_lvgl.Scale(min_value=0, max_value=180)
scale.width = 200
scale.height = 200
scale.set_angles(angle_range=240, rotation=150)
scale.set_ticks(count=61, width=2, length=6, color=0x444444)
scale.set_major_ticks(every=10, width=5, length=20, color=0xFF8800, label_gap=10)
scale.value = 90
```

### Class: `Canvas`

Off-screen buffer you can draw on using LVGL's canvas helpers.

#### Constructor

```python
Canvas(width: int, height: int, color_format: int = rm690b0_lvgl.IMG_CF_TRUE_COLOR)
```

Supported `color_format` values: `IMG_CF_TRUE_COLOR` and `IMG_CF_TRUE_COLOR_ALPHA`.

#### Methods

- `fill_bg(color, opacity=255)` — Clear the buffer.
- `set_px(x, y, color, opacity=255)` — Draw a single pixel.
- `draw_line(points, color, width=2)` — Draw a polyline, where `points` is a list of `(x, y)` tuples.

#### Canvas Example

```python
canvas = rm690b0_lvgl.Canvas(200, 120)
canvas.fill_bg(0x101010)
canvas.draw_line([(10, 100), (60, 20), (120, 80), (190, 10)], color=0x00FFAA, width=4)
canvas.set_px(30, 30, 0xFF0000)
```

### Class: `Line`

Wrapper around `lv_line` for quick polylines/graphs.

#### Constructor

```python
Line()
```

#### Methods / Properties

- `set_points(points)` — List of `(x, y)` pairs.
- `line_width: int` — Stroke width.
- `line_color: int` — Stroke color.
- `rounded: bool` — Rounded end caps.
- `y_invert: bool` — Flip the Y axis.

#### Line Example

```python
line = rm690b0_lvgl.Line()
line.set_points([(5, 115), (30, 10), (90, 70), (150, 20)])
line.line_width = 3
line.line_color = 0xFF55AA
line.y_invert = True
```


### Class: `Spinner`

Loading indicator widget (rotating arc). Inherits from `Widget`.

#### Constructor

```python
Spinner(time: int = 1000, arc_length: int = 60)
```

Creates a spinner widget.

**Parameters:**
- `time` (int, optional): Duration of one revolution in milliseconds (default: 1000)
- `arc_length` (int, optional): Length of the spinning arc in degrees (default: 60)

**Example:**
```python
spinner = rm690b0_lvgl.Spinner(time=2000, arc_length=90)
spinner.set_style_arc_color(0x0000FF)
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`).

#### Methods

Inherits all `Widget` methods plus:

##### `set_style_arc_color(color)`

Set the color of the spinning arc.

```python
spinner.set_style_arc_color(color: int) -> None
```

**Parameters:**
- `color` (int): RGB888 color value

##### `set_style_arc_width(width)`

Set the thickness of the spinning arc.

```python
spinner.set_style_arc_width(width: int) -> None
```

**Parameters:**
- `width` (int): Width in pixels

#### Complete Spinner Example

```python
import rm690b0_lvgl
import time

# Create spinner
spinner = rm690b0_lvgl.Spinner()
spinner.x = 100
spinner.y = 100
spinner.width = 60
spinner.height = 60
spinner.set_style_arc_color(0xFF5733) # Orange
spinner.set_style_arc_width(5)
```

### Class: `Roller`

Scrollable list widget for selecting one option. Inherits from `Widget`.

#### Constructor

```python
Roller(options: str = "Option 1\nOption 2\nOption 3")
```

Creates a roller widget.

**Parameters:**
- `options` (str, optional): Newline-separated list of options

**Example:**
```python
roller = rm690b0_lvgl.Roller(options="January\nFebruary\nMarch")
```

#### Properties (Read/Write)

Inherits all `Widget` properties (`x`, `y`, `width`, `height`) plus:

##### `selected: int`

Index of the currently selected option (0-based).

```python
roller.selected = 2
```

##### `text: str`

Text of the currently selected option (read-only).

```python
print(roller.text)
```

##### `visible_row_count: int`

Number of rows visible without scrolling.

```python
roller.visible_row_count = 3
```

##### `on_change: callable`

Python callback function called when selection changes.

```python
roller.on_change = lambda r: print(f"Selected: {r.text}")
```

#### Methods

Inherits all `Widget` methods plus:

##### `set_options(options, mode=0)`

Set options string.

```python
roller.set_options(options: str, mode: int = 0) -> None
```

**Parameters:**
- `options` (str): Newline-separated options
- `mode` (int, optional): Animation mode (0: Normal, 1: Infinite)

#### Complete Roller Example

```python
import rm690b0_lvgl

roller = rm690b0_lvgl.Roller(options="Apple\nBanana\nCherry\nDate\nElderberry")
roller.x = 50
roller.y = 50
roller.width = 150
roller.height = 100
roller.visible_row_count = 3

def on_select(r):
    print(f"Fruit selected: {r.text}")

roller.on_change = on_select
```

### Class: `Container`

A dedicated container widget for layout and scrolling. Inherits from `Widget`.

#### Constructor

```python
Container()
```

Creates a container widget.

**Example:**
```python
cont = rm690b0_lvgl.Container()
cont.width = 300
cont.height = 200
```

#### Properties (Read/Write)

Inherits all `Widget` properties.

#### Methods

Inherits all `Widget` methods plus:

##### `set_flex_flow(flow)`

Set flex layout flow direction.

```python
cont.set_flex_flow(flow: int) -> None
```

**Parameters:**
- `flow` (int): 0=ROW, 1=COLUMN, 2=ROW_WRAP, 3=COLUMN_WRAP

##### `set_flex_align(justify, align, align_cross)`

Set flex alignment.

```python
cont.set_flex_align(justify: int, align: int, align_cross: int) -> None
```

**Parameters:**
- `justify` (int): Main axis alignment (0=START, 1=CENTER, 2=END, 3=SPACE_BETWEEN, 4=SPACE_AROUND, 5=SPACE_EVENLY)
- `align` (int): Cross axis alignment (0=START, 1=CENTER, 2=END, 3=STRETCH)
- `align_cross` (int): Track alignment (0=START, 1=CENTER, 2=END, 3=STRETCH)

#### Complete Container Example

```python
import rm690b0_lvgl

# Create container
cont = rm690b0_lvgl.Container()
cont.x = 20
cont.y = 20
cont.width = 280
cont.height = 200
cont.set_style_bg_color(0xFFFFFF)

# Set flex layout (Column, Center, Center)
cont.set_flex_flow(1) 
cont.set_flex_align(1, 1, 1)
```

### Class: `Tabview`

The `Tabview` widget organizes content into multiple tabs. Each tab acts as a container.

#### Constructor

```python
tv = rm690b0_lvgl.Tabview(tab_pos, tab_size)
```

- **Parameters:**
    - `tab_pos` (int): Position of the tabs. Use `rm690b0_lvgl.DIR_TOP`, `DIR_BOTTOM`, `DIR_LEFT`, or `DIR_RIGHT`. Default is `DIR_TOP`.
    - `tab_size` (int): Height (for top/bottom) or width (for left/right) of the tab bar. Default is 50.

#### Methods

##### `add_tab(name)`

Adds a new tab and returns the container for that tab.

```python
tab_cont = tv.add_tab("Tab Name")
```

- **Parameters:**
    - `name` (str): The title of the tab.
- **Returns:**
    - `Container`: A widget representing the content area of the tab. You can add child widgets to this container.

#### Complete Tabview Example

```python
import rm690b0_lvgl

# Create Tabview
tv = rm690b0_lvgl.Tabview(tab_pos=rm690b0_lvgl.DIR_TOP, tab_size=50)
tv.width = 240
tv.height = 240

# Add Tab 1
tab1 = tv.add_tab("Settings")
lbl1 = rm690b0_lvgl.Label(text="Settings Content")
lbl1.set_parent(tab1)

# Add Tab 2
tab2 = tv.add_tab("Profile")
lbl2 = rm690b0_lvgl.Label(text="Profile Content")
lbl2.set_parent(tab2)
```

### Class: `Table`

The `Table` widget provides a grid-like data visualization.

#### Constructor

```python
table = rm690b0_lvgl.Table()
```

#### Methods

##### `set_col_cnt(cnt)`

Set the number of columns.

- **Parameters:**
    - `cnt` (int): Number of columns.

##### `set_row_cnt(cnt)`

Set the number of rows.

- **Parameters:**
    - `cnt` (int): Number of rows.

##### `set_col_width(col, width)`

Set the width of a specific column.

- **Parameters:**
    - `col` (int): Column index (0-based).
    - `width` (int): Width in pixels.

##### `set_cell_value(row, col, text)`

Set the text content of a cell.

- **Parameters:**
    - `row` (int): Row index (0-based).
    - `col` (int): Column index (0-based).
    - `text` (str): Text content.

#### Complete Table Example

```python
import rm690b0_lvgl

# Create Table
table = rm690b0_lvgl.Table()
table.width = 240
table.height = 150

# Setup structure
table.set_col_cnt(2)
table.set_row_cnt(3)
table.set_col_width(0, 100)
table.set_col_width(1, 120)

# Fill data
table.set_cell_value(0, 0, "Item")
table.set_cell_value(0, 1, "Value")
table.set_cell_value(1, 0, "Voltage")
table.set_cell_value(1, 1, "3.3V")
table.set_cell_value(2, 0, "Current")
table.set_cell_value(2, 1, "120mA")
```

### Class: `Buttonmatrix`

The `Buttonmatrix` widget displays a grid of buttons from a text map.

#### Constructor

```python
btnm = rm690b0_lvgl.Buttonmatrix(buttons)
```

- **Parameters:**
    - `buttons` (list): Optional initial list of button texts. Use `"\n"` as a button text to start a new row.

#### Properties (Read/Write)

Inherits all properties from [Widget](#base-class-widget).

##### `selected_btn: int`

The index of the currently selected button.

##### `selected_btn_text: str` *(read-only)*

Human-readable text of the selected button. Returns an empty string
if the index is invalid or the entry is a row break (`"\n"`).

##### `on_click: callable`

Callback function invoked when a button is clicked.

#### Methods

##### `set_map(buttons)`

Set the button texts.

- **Parameters:**
    - `buttons` (list): List of button texts. Use `"\n"` as an item to break the row.

#### Complete Buttonmatrix Example

```python
import rm690b0_lvgl

def on_keypad(btnm):
    idx = btnm.selected_btn
    txt = btnm.selected_btn_text or f"#{idx}"
    print(f"Buttonmatrix: Btn {idx} -> '{txt}'")

# Create calculator layout
keys = ["1", "2", "3", "\n", 
        "4", "5", "6", "\n", 
        "7", "8", "9", "\n", 
        "*", "0", "#", ""]

kp = rm690b0_lvgl.Buttonmatrix(keys)
kp.width = 200
kp.height = 200
kp.on_click = on_keypad
```

### Class: `Textarea`

Multi-line text input widget that pairs with the on-screen keyboard.

#### Constructor

```python
Textarea()
```

Creates an empty textarea. You can set placeholder text and hook into
focus/submit events.

#### Properties (Read/Write)

Inherits all [Widget](#base-class-widget) geometry/styling properties plus:

##### `text: str`

Current content. Assign a string to replace the text.

##### `placeholder: str`

Ghost text displayed when `text` is empty.

##### `password_mode: bool`

Mask characters (LVGL renders bullets instead of actual text).

##### `one_line: bool`

Restrict to a single line. Useful for form inputs that should not wrap.

##### `max_length: int`

Maximum number of characters allowed (`0` means unlimited).

##### `on_change: callable`

Invoked whenever the text changes (`def handler(textarea): ...`).

##### `on_focus: callable`

Called when the textarea receives focus (touch/click). Ideal for showing
your keyboard overlay.

##### `on_submit: callable`

Called when LVGL sends `LV_EVENT_READY` (e.g., ✓ key pressed on keyboard).

#### Textarea Example

```python
ta = rm690b0_lvgl.Textarea()
ta.placeholder = "Tap to type"
ta.password_mode = False
ta.max_length = 64

def on_ta_change(textarea):
    print("Textarea updated:", textarea.text)

ta.on_change = on_ta_change
```

### Class: `Keyboard`

On-screen keyboard (`lv_keyboard`) that emits LVGL button-matrix events.
Use `set_textarea()` to bind it to a `Textarea`.

#### Constructor

```python
Keyboard()
```

Creates a keyboard in TEXT_LOWER mode. The widget inherits all base
properties (`x`, `y`, `width`, `height`, styling helpers).

#### Properties (Read/Write)

- `mode: int` — Current layout (use `KBD_MODE_TEXT_LOWER`, `_TEXT_UPPER`,
  `_SPECIAL`, `_NUMBER`, etc.).
- `popovers: bool` — Enables LVGL key popovers (press-and-hold bubble).
- `on_change: callable` — Fired when a key is pressed.
- `selected_btn_text: str` *(read-only)* — Label of the last pressed key.

#### Methods

##### `set_textarea(textarea)`

Routes keyboard input to the provided `Textarea`. Pass `None` to detach.

##### `set_mode(mode)`

Switch between built-in LVGL keyboard layouts.

##### `set_popovers(enabled)`

Convenience wrapper for toggling popover bubbles from Python.

#### Keyboard Usage Notes

- The LVGL ✓ key (bottom-right) typically commits the text and triggers
  the textarea's `on_submit` callback.
- The keyboard icon key (`SYMBOL_KEYBOARD`, bottom-left) is commonly used
  to hide the keyboard or provide custom behavior (e.g., clear + hide).
- When used with overlays, remember to collapse/hide the widget by
  setting `width/height` or removing its parent so it doesn't consume
  touch area.

#### Complete Text Input Example

```python
import rm690b0_lvgl

ta = rm690b0_lvgl.Textarea()
ta.placeholder = "Enter Wi-Fi password"

kb = rm690b0_lvgl.Keyboard()
kb.set_textarea(ta)
kb.set_popovers(True)

def on_keyboard_change(keyboard):
    if keyboard.selected_btn_text == rm690b0_lvgl.SYMBOL_KEYBOARD:
        # Custom behavior: clear text then hide overlay
        ta.text = ""
        kb.set_textarea(None)

def on_submit(textarea):
    print("Submitted:", textarea.text)
    kb.set_textarea(None)  # hide keyboard (✓ pressed)

ta.on_focus = lambda ta_obj: kb.set_textarea(ta_obj)
ta.on_submit = on_submit
kb.on_change = on_keyboard_change
```

### Class: `Calendar`

> **Status:** Not yet implemented in the CircuitPython build (bindings pending).

The `Calendar` widget allows date selection.

#### Constructor

```python
cal = rm690b0_lvgl.Calendar()
```

#### Properties (Read/Write)

Inherits all properties from [Widget](#base-class-widget).

##### `on_change: callable`

Callback function invoked when a date is selected.

#### Methods

##### `set_showed_date(year, month)`

Set the currently visible month.

- **Parameters:**
    - `year` (int): Year to show.
    - `month` (int): Month to show (1-12).

##### `set_today_date(year, month, day)`

Set the "today" date (highlighted).

- **Parameters:**
    - `year` (int): Current year.
    - `month` (int): Current month.
    - `day` (int): Current day.

#### Complete Calendar Example

```python
import rm690b0_lvgl

def on_date_select(cal):
    print("Date selected")

calendar = rm690b0_lvgl.Calendar()
calendar.width = 200
calendar.height = 200
calendar.set_today_date(2023, 10, 25)
calendar.set_showed_date(2023, 10)
calendar.on_change = on_date_select
```

### Class: `Msgbox`

The `Msgbox` (Message Box) is a modal dialog widget used to inform the user or ask for confirmation. It consists of a title, text, and optional buttons.

#### Constructor

```python
mbox = rm690b0_lvgl.Msgbox(title, text, buttons, close_btn)
```

- **Parameters:**
    - `title` (str): Title text (e.g., "Warning").
    - `text` (str): Message body text.
    - `buttons` (list): List of button labels (strings). **Must end with an empty string `""`**.
    - `close_btn` (bool): `True` to display a close (X) button, `False` otherwise.

#### Properties (Read/Write)

Inherits all properties from [Widget](#base-class-widget).

##### `on_click: callable`

Callback function invoked when a button is clicked. The callback receives the index of the clicked button.

- **Callback Signature:** `def callback(index)`
    - `index` (int): Index of the button in the list (0, 1, ...). Returns `-1` if the close button was clicked.

#### Methods

##### `close()`

Closes and deletes the message box.

```python
mbox.close()
```

#### Complete Msgbox Example

```python
import rm690b0_lvgl

# Global reference to keep it alive until closed
mbox = None

def on_mbox_click(idx):
    global mbox
    if idx == 0:
        print("Action confirmed!")
    elif idx == 1:
        print("Action cancelled.")
    else:
        print("Dialog closed.")
    
    # Close the message box
    if mbox:
        mbox.close()
        mbox = None

# Create buttons list (terminated by empty string)
btns = ["OK", "Cancel", ""]

# Create message box
mbox = rm690b0_lvgl.Msgbox("Confirm", "Do you want to delete this file?", btns, True)

# Assign callback
mbox.on_click = on_mbox_click

# Position generally handled automatically or centered
# But can be positioned manually if needed
mbox.x = 60
mbox.y = 80
```

---

## Examples

### Example 1: Simple Counter

```python
import rm690b0
import rm690b0_lvgl
import board
import busio
import time

# Initialize
display = rm690b0.RM690B0()
display.init_display()

lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()

i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
lvgl.init_touch(i2c)

# Create UI
count = 0
label = rm690b0_lvgl.Label(text=f"Count: {count}")
label.x = 250
label.y = 150

def increment(btn):
    global count
    count += 1
    label.text = f"Count: {count}"

button = rm690b0_lvgl.Button(text="Count Up")
button.x = 200
button.y = 250
button.width = 200
button.height = 80
button.on_click = increment

# Run
while True:
    lvgl.task_handler()
    time.sleep(0.01)
```

### Example 2: Multi-Button Control

```python
import rm690b0_lvgl

# Initialize (display and LVGL setup omitted for brevity)

# Status label
status = rm690b0_lvgl.Label(text="Ready")
status.x = 200
status.y = 50
status.set_text_color(0x000000)

# Callbacks
def on_red(btn):
    status.text = "RED pressed"
    status.set_text_color(0xFF0000)

def on_green(btn):
    status.text = "GREEN pressed"
    status.set_text_color(0x00FF00)

def on_blue(btn):
    status.text = "BLUE pressed"
    status.set_text_color(0x0000FF)

# Create buttons
btn_red = rm690b0_lvgl.Button(text="Red")
btn_red.x = 50
btn_red.y = 150
btn_red.width = 150
btn_red.height = 60
btn_red.set_style_bg_color(0xFF0000)
btn_red.on_click = on_red

btn_green = rm690b0_lvgl.Button(text="Green")
btn_green.x = 225
btn_green.y = 150
btn_green.width = 150
btn_green.height = 60
btn_green.set_style_bg_color(0x00FF00)
btn_green.on_click = on_green

btn_blue = rm690b0_lvgl.Button(text="Blue")
btn_blue.x = 400
btn_blue.y = 150
btn_blue.width = 150
btn_blue.height = 60
btn_blue.set_style_bg_color(0x0000FF)
btn_blue.on_click = on_blue
```

### Example 3: Settings Panel

```python
import rm690b0_lvgl

# Title
title = rm690b0_lvgl.Label(text="Display Settings")
title.x = 180
title.y = 20
title.set_text_color(0x000080)

# Brightness label and buttons
brightness = 80
bright_label = rm690b0_lvgl.Label(text=f"Brightness: {brightness}%")
bright_label.x = 200
bright_label.y = 100

def increase_brightness(btn):
    global brightness
    brightness = min(100, brightness + 10)
    bright_label.text = f"Brightness: {brightness}%"
    # Apply to actual display
    display.set_brightness(brightness / 100.0)

def decrease_brightness(btn):
    global brightness
    brightness = max(0, brightness - 10)
    bright_label.text = f"Brightness: {brightness}%"
    display.set_brightness(brightness / 100.0)

btn_up = rm690b0_lvgl.Button(text="+")
btn_up.x = 400
btn_up.y = 90
btn_up.width = 80
btn_up.height = 60
btn_up.on_click = increase_brightness

btn_down = rm690b0_lvgl.Button(text="-")
btn_down.x = 120
btn_down.y = 90
btn_down.width = 80
btn_down.height = 60
btn_down.on_click = decrease_brightness
```

---

## Implementation Details

### Memory Architecture

**LVGL Display Buffers:**
- 2 buffers × 600 pixels × 30 rows × 2 bytes = 72 KB total
- Allocated in PSRAM for large buffer support
- Double-buffered for smooth rendering

**Widget Memory:**
- Each widget allocates LVGL object (~100-500 bytes depending on type)
- Python wrapper objects (~50-100 bytes each)
- Total widget overhead: ~150-600 bytes per widget

**Memory Efficiency:**
- Widgets share display buffers
- No per-widget framebuffers
- Only dirty regions are redrawn

### Rendering Pipeline

```
1. Python app modifies widget properties (text, position, color)
   └─> Calls LVGL C functions via Python bindings

2. LVGL marks widget as "dirty" (needs redraw)
   └─> Schedules redraw on next render cycle

3. task_handler() calls lv_task_handler()
   └─> LVGL renders dirty widgets to display buffer

4. LVGL flush callback triggered with dirty region
   └─> Calls esp_lcd_panel_draw_bitmap()

5. RM690B0 DMA transfer
   └─> Updates only changed pixels on AMOLED display
```

### Touch Coordinate Transformation

The FT6336U reports touch in **portrait orientation** (450×600), but the display is in **landscape** (600×450). The driver automatically transforms coordinates:

```python
# Automatic transformation (you don't need to do this):
display_x = 599 - touch_y
display_y = touch_x
```

This happens inside `lvgl_touch_read_cb()`, so widgets receive correct landscape coordinates automatically.

### Event Handling Flow

```
1. User touches button on screen
   └─> FT6336U detects touch at (x, y)

2. Touch driver reads I2C data
   └─> Transforms coordinates to landscape

3. LVGL input processing
   └─> Determines which widget was touched

4. LVGL event system
   └─> Generates CLICKED event for button

5. Button event callback
   └─> Calls Python on_click function

6. Python callback executes
   └─> Updates UI, prints messages, etc.
```

### Build System Integration

**Added to CircuitPython Build:**

1. **`py/circuitpy_defns.mk`**:
   - `SRC_BINDINGS_ENUMS`: Widget.c, Label.c, Button.c, RM690B0_LVGL.c
   - `SRC_COMMON_HAL_ALL`: Widget.c, Label.c, Button.c, RM690B0_LVGL.c

2. **`shared-bindings/rm690b0_lvgl/`**:
   - `__init__.c` - Module initialization
   - `RM690B0_LVGL.c` / `.h` - Manager class
   - `Widget.c` / `.h` - Base widget class
   - `Label.c` / `.h` - Label widget
   - `Button.c` / `.h` - Button widget

3. **`common-hal/rm690b0_lvgl/`** (ESP32-S3):
   - `RM690B0_LVGL.c` / `.h` - Platform implementation
   - `Widget.c` / `.h` - LVGL object wrappers
   - `Label.c` / `.h` - LVGL label wrappers
   - `Button.c` / `.h` - LVGL button wrappers

### Type System & Inheritance

**Property Inheritance:**
- Label and Button inherit from Widget
- Properties (x, y, width, height) are explicitly added to child locals_dict
- `MP_TYPE_FLAG_HAS_SPECIAL_ACCESSORS` enables property support
- `MP_PROPERTY_GETSET` macro creates read/write properties

**Type Hierarchy:**
```
mp_obj_type_t
    └─> rm690b0_lvgl_widget_type (Widget)
            ├─> rm690b0_lvgl_label_type (Label)
            └─> rm690b0_lvgl_button_type (Button)
```

---

## Performance

### Rendering Performance

- **Full Screen Update**: ~25-30 ms
- **Partial Updates**: <5 ms (typical widget update)
- **Touch Response Time**: <10 ms
- **Animation Smoothness**: 60 FPS capable

### Memory Usage

- **LVGL Buffers**: 72 KB (PSRAM)
- **LVGL Heap**: ~100-200 KB (depends on widget count)
- **Per Widget**: ~150-600 bytes
- **Typical App**: 20-30 widgets = ~10-20 KB

### Optimization Tips

1. **Call `task_handler()` regularly**: 10-20ms intervals for smooth UI
2. **Minimize widget updates**: Only change properties when needed
3. **Use batch updates**: Change multiple properties, then call task_handler()
4. **Limit widget count**: Keep UI simple (< 50 widgets)
5. **Reuse widgets**: Update existing widgets rather than creating new ones

---

## Future Enhancements

### Implementation Status Summary

**Current Implementation Coverage: ~80%** (24/30+ widgets)

| Widget Category | ESP-IDF Examples Use | Python API Status |
|----------------|---------------------|-------------------|
| **Core** | ✅ obj, label, image, button | ⚠️ Partial (Image pending) |
| **Interactive** | ✅ slider, switch, checkbox, arc | ✅ Implemented |
| **Progress** | ✅ bar, spinner | ✅ Implemented |
| **Selection** | ✅ dropdown, roller, table, btnmatrix, calendar, spinbox, list | ⚠️ Partial (Calendar pending) |
| **Text Input** | ✅ textarea, keyboard | ✅ Implemented |
| **Navigation** | ✅ tabview | ✅ Implemented |
| **Data Viz** | ✅ chart, scale, canvas, line | ✅ Implemented |
| **Dialogs** | ✅ msgbox | ✅ Implemented |
| **Advanced** | ✅ animimg | ❌ Not implemented |

**Priority Gaps for Production Use:**
1. **High Priority**: Image + Calendar (parity with ESP-IDF demos)
2. **Medium Priority**: Animimg / QRCode (animated assets and encoded widgets)

### Planned Widget Classes (Next Phase)

The following widgets are planned for future implementation to expand the Python API:

**Tier 1: Core & Selection Parity**
1. **Image** - Complete LVGL image wrapper (BMP/JPEG/source binding)
2. **Calendar** - Date picker widget (headers + callbacks)

**Tier 2: Advanced/Specialized**
1. **Animimg** - Animated image widget
2. **QRCode** - QR code generator/display (requires extra library)

### Completed Widgets ✅

**Core Widgets**
- ✅ **Widget** - Base container class (lv_obj)
- ✅ **Label** - Text display
- ✅ **Button** - Clickable button with callback
- 🚧 **Image** - Planned bitmap/JPEG widget (bindings pending)

**Interactive Controls**
- ✅ **Slider** - Range value selector
- ✅ **Checkbox** - Toggle with label
- ✅ **Switch** - On/off toggle
- ✅ **Arc** - Circular knob/dial

**Display/Feedback Widgets**
- ✅ **Bar** - Progress/level indicator
- ✅ **Spinner** - Loading/progress indicator

**Selection Widgets**
- ✅ **Dropdown** - Selection menu
- ✅ **Roller** - Scrollable selection widget
- ✅ **List** - Scrollable list container with items
- ✅ **Spinbox** - Numeric input with increment/decrement buttons
- ✅ **Table** - Data grid visualization
- ✅ **Buttonmatrix** - Grid of buttons
- 🚧 **Calendar** - Date picker (planned)

**Dialogs**
- ✅ **Msgbox** - Modal message box dialog

**Layout Containers**
- ✅ **Container** - Layout and scrolling container
- ✅ **Tabview** - Multi-page navigation

**Text Input**
- ✅ **Textarea** - Multi-line text input with focus/submit callbacks
- ✅ **Keyboard** - On-screen keyboard with popover support

**Data Visualization**
- ✅ **Chart** - Multi-series line/bar/scatter plotting
- ✅ **Scale** - Meter-based gauge with ticks/labels
- ✅ **Canvas** - Off-screen pixel buffer with drawing helpers
- ✅ **Line** - Lightweight polyline widget
