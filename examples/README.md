# CircuitPython Examples for Waveshare ESP32-S3 Touch AMOLED 2.41

This directory contains example scripts demonstrating the RM690B0 display driver and LVGL integration for the Waveshare ESP32-S3 Touch AMOLED 2.41 board.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Display Driver Examples (rm690b0)](#display-driver-examples-rm690b0)
3. [LVGL Examples (rm690b0_lvgl)](#lvgl-examples-rm690b0_lvgl)
4. [Games](#games)
5. [Hardware Tests](#hardware-tests)
6. [Benchmarks](#benchmarks)
7. [Setup Instructions](#setup-instructions)

---

## Quick Start

### Basic Display Test

```python
import rm690b0

display = rm690b0.RM690B0()
display.init_display()

display.fill_color(0xF800)  # Red screen
display.swap_buffers()
```

### Run an Example

Copy any example to your device as `code.py`:

```bash
# Using mpremote
mpremote cp flappy_bird_clone.py :code.py
mpremote reset

# Using ampy
ampy put flappy_bird_clone.py /code.py
ampy reset
```

---

## Display Driver Examples (rm690b0)

These examples use the standalone `rm690b0` display driver (no LVGL).

### basic_test.py

**Description:** Interactive test of native text rendering with all built-in fonts.

**Features:**
- Tests all 7 built-in fonts (8×8 to 32×48)
- Text rendering with colors and backgrounds
- Graphics primitives (lines, rectangles, circles)
- Interactive prompts between tests

**Usage:**
```python
import basic_test
# Follow on-screen prompts
```

**Key Concepts:**
- Font selection with `set_font()`
- Text rendering with `text()`
- Graphics primitives
- Double buffering with `swap_buffers()`

---

### font_test.py

**Description:** Comprehensive test of all 7 native bitmap fonts.

**Features:**
- Displays all fonts on a single screen
- Shows character samples for each font
- Demonstrates font sizing and spacing

**Usage:**
```python
import font_test
```

**Fonts Tested:**
- Font 0: 8×8 monospace
- Font 1: 16×16 Liberation Sans
- Font 2: 16×24 Liberation Mono Bold
- Font 3: 24×24 monospace
- Font 4: 24×32 monospace
- Font 5: 32×32 monospace
- Font 6: 32×48 monospace

---

### test_all_fonts.py

**Description:** Cycle through all fonts with visual comparison.

**Features:**
- Shows each font with identical text
- Automatic cycling with timing
- Memory usage monitoring

**Usage:**
```python
import test_all_fonts
```

---

### bouncing_ball.py

**Description:** Simple bouncing ball animation demonstrating basic graphics.

**Features:**
- Circle drawing and filling
- Basic physics simulation
- Frame timing

**Usage:**
```python
import bouncing_ball
```

**Key Concepts:**
- `fill_circle()` for shapes
- Animation loops
- Basic physics

---

### bouncing_ball_60fps.py

**Description:** Optimized bouncing ball targeting 60 FPS.

**Features:**
- Frame rate monitoring
- Optimized rendering
- Performance metrics

**Usage:**
```python
import bouncing_ball_60fps
```

**Key Concepts:**
- Frame timing optimization
- `swap_buffers(copy=False)` for performance
- FPS calculation

---

### bouncing_ball_with_bg.py

**Description:** Bouncing ball with background image.

**Features:**
- Background image loading (BMP/JPEG)
- Image + graphics compositing
- Performance with complex scenes

**Usage:**
```python
import bouncing_ball_with_bg
# Requires image files: cerber.jpg or cyborg.jpg
```

**Key Concepts:**
- `blit_jpeg()` for images
- Layered rendering
- Performance with images

---

## LVGL Examples (rm690b0_lvgl)

These examples use the LVGL integration for rich UI widgets.

### test_gui.py

**Description:** Comprehensive LVGL widget demonstration.

**Features:**
- All major LVGL widgets
- TTF font loading and rendering
- Touch input handling
- Event callbacks
- Custom styling
- Flex layouts

**Widgets Demonstrated:**
- Label (text display)
- Button (with callbacks)
- Slider (value selection)
- Checkbox (toggles)
- Switch (on/off)
- Bar (progress indicators)
- Arc (circular sliders)
- Dropdown (selection lists)
- Roller (scrolling selection)
- Textarea (text input)
- Keyboard (on-screen keyboard)
- Container (layouts)
- And more...

**Usage:**
```python
import test_gui
# Interact with widgets via touch
```

**TTF Font Requirements:**
- Place fonts in `fonts/` directory
- Example: `fonts/calibri.ttf`
- Keep fonts under 500KB for best performance

**Key Concepts:**
- LVGL widget creation
- TTF font loading
- Touch event handling
- Widget styling
- Layout management

---

### lvgl_icons_example.py

**Description:** Demonstrates LVGL's built-in FontAwesome icons.

**Features:**
- Icon display (home, heart, settings, etc.)
- Icon + text labels
- Symbol reference

**Usage:**
```python
import lvgl_icons_example
```

**Available Icons:**
- Home, User, Settings, WiFi
- Battery, Bluetooth, Volume
- Play, Pause, Stop
- And many more...

**Key Concepts:**
- Using LVGL symbols
- Icon fonts
- Symbol constants from `lib/lvgl_symbols.py`

---

### test_symbols.py

**Description:** Test and display all available LVGL symbols.

**Features:**
- Complete symbol catalog
- Visual symbol reference
- Copy-paste ready constants

**Usage:**
```python
import test_symbols
```

---

## Games

Complete game implementations using the display and touch input.

### code.py

**Description:** Main menu launcher for games.

**Features:**
- Touch-based menu interface
- Game selection (Flappy Bird, Snake)
- Clean UI with visual feedback

**Usage:**
- Automatically runs on device boot
- Touch buttons to select game

**Menu Options:**
1. **Flappy Bird** - Tap-to-flap game
2. **Snake** - Joystick-controlled snake
3. **Exit** - Return to REPL

---

### flappy_bird_clone.py

**Description:** Complete Flappy Bird clone with touch controls.

**Features:**
- Tap to flap gameplay
- Scrolling pipes with collision detection
- Score tracking and best score
- Progressive difficulty (speed increases)
- Smooth 60 FPS animation
- HUD with score display
- Game over screen

**Controls:**
- **Tap screen** - Flap wings

**Usage:**
```python
import flappy_bird_clone
# Or select from code.py menu
```

**Game Mechanics:**
- Bird falls with gravity
- Tap to flap upward
- Avoid pipes
- Score increases as you pass pipes
- Game gets faster as score increases

---

### snake_game.py

**Description:** Classic Snake game with joystick controls.

**Features:**
- Joystick-based directional control
- Food collection and growth
- Score tracking and best score
- Progressive difficulty (speed increases)
- Collision detection (walls, self)
- Grid-based movement

**Controls:**
- **Joystick UP/DOWN/LEFT/RIGHT** - Change direction
- **CENTER button** - Start/restart game

**Hardware Required:**
- SparkFun Qwiic Navigation Switch (I2C address 0x21)

**Usage:**
```python
import snake_game
# Or select from code.py menu
```

**Game Mechanics:**
- Snake moves continuously in current direction
- Eat red food to grow and score points
- Game speeds up as you score more
- Hit walls or yourself = game over

---

## Hardware Tests

Tests for specific hardware peripherals and sensors.

### navigation_switch_test.py

**Description:** Test SparkFun Qwiic Navigation Switch with RGB LED support.

**Features:**
- 5-way navigation switch testing
- RGB LED control
- Real-time input display
- LED color changes based on direction

**Hardware:**
- SparkFun Qwiic Navigation Switch (PRT-27576)
- Modified I2C address: 0x21 (default 0x20)
- Connected via QWIIC port

**Controls:**
- UP/DOWN/LEFT/RIGHT switches
- CENTER button
- RGB LED (red, green, blue)

**Usage:**
```python
import navigation_switch_test
# Press switches to see LED changes
```

---

### sparkfun_joystick_test.py

**Description:** Test analog joystick input.

**Features:**
- X/Y axis position reading
- Button press detection
- Real-time coordinate display

**Hardware:**
- SparkFun Qwiic Joystick
- I2C interface

**Usage:**
```python
import sparkfun_joystick_test
```

---

### espsdcard_test.py

**Description:** SD card read/write test using espsdcard module.

**Features:**
- SD card mounting
- File operations (read/write)
- Directory listing
- Performance testing

**Usage:**
```python
import espsdcard_test
# Requires SD card inserted
```

**Key Operations:**
- Mount/unmount
- File creation and reading
- Directory operations
- Error handling

---

### espnow_test.py

**Description:** ESP-NOW wireless communication test.

**Features:**
- Peer-to-peer communication
- Message sending/receiving
- Network setup

**Usage:**
```python
import espnow_test
# Requires two ESP32 devices
```

---

### board_test_suite.py

**Description:** Comprehensive hardware test suite.

**Features:**
- Display test
- Touch test
- I2C device scanning
- GPIO testing
- Memory check

**Usage:**
```python
import board_test_suite
# Interactive test menu
```

---

## Benchmarks

Performance measurement and optimization tools.

### unified_benchmark.py

**Description:** Comprehensive performance benchmark suite.

**Features:**
- Graphics primitive benchmarks
- Text rendering speed tests
- Image loading performance
- Memory usage monitoring
- Frame rate measurements

**Benchmarks:**
- Full screen fill
- Rectangle drawing (filled/outline)
- Circle drawing (filled/outline)
- Line drawing
- Text rendering (all fonts)
- Image loading (BMP/JPEG)
- DMA transfer performance

**Usage:**
```python
import unified_benchmark
# Results printed to console
```

**Sample Output:**
```
Full screen fill: 25.3 ms
Circle (r=50): 2.1 ms
Text "Hello" (16×16): 1.2 ms
JPEG decode: 145 ms
```

---

## Setup Instructions

### 1. Install CircuitPython

Flash the custom CircuitPython build with RM690B0 support:

```bash
# Flash using esptool
esptool.py --chip esp32s3 --port /dev/ttyACM0 write_flash 0x0 circuitpython.bin
```

### 2. Upload Examples

**Method 1: USB Drive (CIRCUITPY)**
```bash
# Mount device as USB drive
cp flappy_bird_clone.py /media/CIRCUITPY/code.py
```

**Method 2: mpremote**
```bash
pip install mpremote
mpremote cp flappy_bird_clone.py :code.py
mpremote reset
```

**Method 3: ampy**
```bash
pip install adafruit-ampy
ampy --port /dev/ttyACM0 put flappy_bird_clone.py /code.py
ampy --port /dev/ttyACM0 reset
```

### 3. Upload Fonts (for LVGL examples)

```bash
# Create fonts directory
mpremote mkdir :fonts

# Upload TTF font
mpremote cp fonts/calibri.ttf :fonts/calibri.ttf
```

### 4. Upload Images (for image examples)

```bash
# Upload images
mpremote cp cerber.jpg :cerber.jpg
mpremote cp cyborg.jpg :cyborg.jpg
```

### 5. Upload Libraries (if needed)

```bash
# Create lib directory
mpremote mkdir :lib

# Upload lvgl_symbols helper
mpremote cp lib/lvgl_symbols.py :lib/lvgl_symbols.py
```

---

## Font Optimization

For faster TTF font loading and reduced memory usage:

```bash
# Install fonttools
pip install fonttools

# Subset to Latin characters only
pyftsubset calibri.ttf \
  --output-file=calibri-subset.ttf \
  --unicodes="U+0020-007F,U+00A0-00FF"

# This can reduce file size from 2MB to ~50KB
```

---

## Included Assets

### Images

- `cerber.bmp` - BMP format test image
- `cerber.jpg` - JPEG format test image (same content)
- `cyborg.bmp` - BMP format test image
- `cyborg.jpg` - JPEG format test image (same content)

**Note:** PNG and RAW formats also available for some images.

### Fonts

- `fonts/calibri.ttf` - Sample TTF font for LVGL examples

### Libraries

- `lib/lvgl_symbols.py` - LVGL FontAwesome symbol constants

---

## Programming Patterns

### Native Display (rm690b0)

```python
import rm690b0

# Initialize
display = rm690b0.RM690B0()
display.init_display()

# Draw
display.fill_color(0x0000)
display.set_font(1)
display.text(10, 10, "Hello", 0xFFFF)

# Update screen
display.swap_buffers()
```

### LVGL Widgets (rm690b0_lvgl)

```python
import rm690b0_lvgl
import gc

# Initialize
lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()
lvgl.init_rendering()

# Load font (free memory first)
gc.collect()
font = rm690b0_lvgl.Font("fonts/calibri.ttf", 24)

# Create widget
label = rm690b0_lvgl.Label("Hello LVGL", x=50, y=50)
label.set_style_text_font(font)

# Main loop
while True:
    lvgl.task_handler()  # Process events
    time.sleep(0.01)
```

### Touch Input (via LVGL)

```python
import rm690b0_lvgl

lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()
lvgl.init_rendering()

# Touch is initialized automatically by init_rendering()

# Create button with callback
def on_click(event):
    print("Button clicked!")

button = rm690b0_lvgl.Button("Click Me", x=100, y=100)
button.on_click = on_click

while True:
    lvgl.task_handler()  # Handles touch events
    time.sleep(0.01)
```

### Touch Input (Direct, without LVGL)

```python
import board
import busio
import adafruit_focaltouch

# Initialize I2C and touch controller
i2c = busio.I2C(board.TP_SCL, board.TP_SDA)
touch = adafruit_focaltouch.Adafruit_FocalTouch(i2c)

# Read touch
if touch.touched:
    points = touch.touches
    if points:
        x = points[0]["x"]
        y = points[0]["y"]
        print(f"Touch at ({x}, {y})")
```

**Note:** Touch coordinates from FT6336U are in portrait orientation (450×600). When using with landscape display (600×450), apply coordinate transformation:
```python
display_x = 600 - touch_y
display_y = touch_x
```

---

## Troubleshooting

### Issue: Module not found

**Solution:** Ensure CircuitPython build has RM690B0 support compiled in.

### Issue: Touch not working

**Solution:** 
- Check I2C wiring (SDA=GPIO47, SCL=GPIO48)
- Verify FT6336U at address 0x38
- For LVGL: Call `init_rendering()` after `init_display()`

### Issue: Font file not found

**Solution:**
- Upload fonts to `/fonts/` directory
- Check file path in code
- Verify file exists: `mpremote ls :fonts/`

### Issue: Memory error loading TTF

**Solution:**
- Call `gc.collect()` before loading font
- Use smaller/subsetted fonts (<500KB)
- Load fonts once at startup, not repeatedly

### Issue: Display shows nothing

**Solution:**
- Check `init_display()` was called
- Check `swap_buffers()` was called after drawing
- Verify brightness: `display.brightness = 1.0`

### Issue: LVGL widgets not visible

**Solution:**
- Call `init_rendering()` after `init_display()`
- Call `task_handler()` in main loop
- Check widget coordinates are on-screen

### Issue: Slow performance

**Solution:**
- Use `swap_buffers(copy=False)` for full redraws
- Batch drawing operations before swapping
- Avoid frequent `gc.collect()` calls
- Use native fonts instead of TTF when possible

---

## Performance Tips

1. **Use native fonts** for debug/status text (10-500× faster than TTF)
2. **Batch drawing operations** before calling `swap_buffers()`
3. **Use `copy=False`** when redrawing entire screen
4. **Load TTF fonts once** at startup, reuse instances
5. **Call `gc.collect()`** before heavy operations, not during
6. **Use appropriate widget updates** (change properties, don't recreate)
7. **Minimize touch polling** (10-20ms interval is sufficient)

---

## Hardware Specifications

**Board:** Waveshare ESP32-S3 Touch AMOLED 2.41

| Component | Specification |
|-----------|---------------|
| **MCU** | ESP32-S3 |
| **Flash** | 16 MB |
| **PSRAM** | 8 MB |
| **Display** | RM690B0 AMOLED, 600×450 pixels |
| **Interface** | QSPI (80 MHz) |
| **Touch** | FT6336U, I2C (address 0x38) |
| **I2C** | GPIO47 (SDA), GPIO48 (SCL) |
| **Color** | RGB565 (16-bit) |

---

## Additional Resources

- **Display Driver Documentation:** `../docs/RM690B0_DRIVER.md`
- **LVGL Integration Guide:** `../docs/RM690B0_LVGL.md`
- **Technical Notes:** `../docs/TECHNICAL_NOTES.md`
- **Project Status:** `../docs/project_status_summary.md`
- **Font Converter:** `../fonts/README.md`

---

## Example Gallery

### Simple Examples
- `basic_test.py` - Native text and fonts
- `font_test.py` - Font showcase
- `bouncing_ball.py` - Basic animation

### Advanced Examples  
- `test_gui.py` - Complete LVGL UI
- `flappy_bird_clone.py` - Full game with physics
- `snake_game.py` - Grid-based game with joystick

### Hardware Tests
- `navigation_switch_test.py` - 5-way switch + RGB LED
- `espsdcard_test.py` - SD card operations
- `board_test_suite.py` - Complete hardware check

### Benchmarks
- `unified_benchmark.py` - Performance measurements

---

## Contributing

When adding new examples:
1. Include docstring with description and usage
2. Add example to this README
3. Test on actual hardware
4. Document hardware requirements
5. Include error handling

---

## License

Examples are provided as part of the RM690B0 driver project. See main project LICENSE for details.