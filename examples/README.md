# CircuitPython Examples for Waveshare ESP32-S3 Touch AMOLED 2.41

This directory contains example scripts demonstrating the RM690B0 display driver and LVGL integration for the Waveshare ESP32-S3 Touch AMOLED 2.41 board.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Directory Structure](#directory-structure)
3. [Display Driver Examples](#display-driver-examples)
4. [LVGL Examples](#lvgl-examples)
5. [Games](#games)
6. [Hardware Tests](#hardware-tests)
7. [Benchmarks](#benchmarks)
8. [Setup Instructions](#setup-instructions)

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
mpremote cp games/game_flappy_bird.py :code.py
mpremote reset

# Using ampy
ampy put games/game_flappy_bird.py /code.py
ampy reset
```

---

## Directory Structure

Examples are organized into subdirectories by category:

### `test_gfx/` - Legacy rm690b0 API Tests
Examples using the original `rm690b0` display driver API:
- `test_basic_gfx.py` - Graphics primitives and text rendering
- `test_all_fonts.py` - All 7 built-in fonts showcase
- `test_rotation.py` - Display rotation test

### `test_gfx_displayio/` - Modern displayio API Tests
Examples using the new `displayio` + `adafruit_rm690b0` panel driver:
- `test_basic_gfx.py` - displayio-based graphics test
- `test_rotation.py` - displayio rotation test

### `benchmark_gfx/` - Legacy API Benchmarks
Performance tests for the original `rm690b0` driver:
- `benchmark_gfx_display.py` - Display primitives benchmark
- `benchmark_simple_flush.py` - DMA/flush stress test
- `benchmark_text.py` - Text rendering performance
- `benchmark_gfx_conversion.py` - Image conversion benchmark
- `benchmark_sd_gfx.py` - SD card + graphics combined test
- `benchmark_animation_bg.py` / `benchmark_animation_nobg.py` - Animation tests
- `benchmark_gfx_simple.py` - Simplified graphics benchmark

### `benchmark_gfx_displayio/` - Modern API Benchmarks
Performance tests for the new displayio-based driver (same tests as above, using new API)

### `benchmark_sd/` - SD Card Benchmarks
- `benchmark_sdcard.py` - SD card read/write performance
- `benchmark_sdcard_freq_sweep.py` - Frequency sweep test

### `games/` - Complete Game Implementations
- `game_flappy_bird.py` - Flappy Bird clone
- `game_snake.py` - Classic Snake
- `game_pacman.py` - Full Pac-Man with ghost AI
- `game_sokoban.py` - Puzzle game
- `game_minesweeper.py` - Minesweeper clone

### `test_lvgl/` - LVGL Widget Examples
- `lvgl_test_gui.py` - Complete widget demo
- `lvgl_icons_example.py` - FontAwesome icons
- `lvgl_test_symbols.py` - Symbol catalog
- `lvgl_test_ttf.py` - TrueType font test

### `test_other/` - Hardware Tests
- `test_board_hardware.py` - Comprehensive hardware test
- `test_hw_nav_switch.py` - Navigation switch test
- `test_espnow.py` - ESP-NOW wireless test

### `gfx/` - Test Images
- BMP, JPEG, and RAW format test images (cerber, cyborg)

### `lib/` - Helper Libraries
- `lvgl_symbols.py` - LVGL symbol constants
- `display_compat.py` - Compatibility layer for old API

### `fonts/` - Font Files
- TrueType fonts for LVGL examples

---

These examples use the standalone `rm690b0` display driver (no LVGL).

### test_basic_gfx.py

**Description:** Interactive test of native text rendering with all built-in fonts.

**Features:**

- Tests all 7 built-in fonts (8×8 to 32×48)
- Text rendering with colors and backgrounds
- Graphics primitives (lines, rectangles, circles)
- Interactive prompts between tests

**Usage:**

```python
# Legacy API
from test_gfx import test_basic_gfx

# displayio API
from test_gfx_displayio import test_basic_gfx
```

**Key Concepts:**
- **Legacy:** Font selection with `set_font()`, text with `text()`, `swap_buffers()`
- **displayio:** `displayio.Bitmap`, `bitmaptools`, `adafruit_display_text.Label`

---

### test_all_fonts.py

**Location:** `test_gfx/test_all_fonts.py`

**Description:** Comprehensive showcase of all 7 native bitmap fonts (legacy API only).

**Features:**

- Displays each font with sample text
- Shows all fonts together for size comparison
- Tests rendering performance
- Demonstrates font colors and backgrounds
- Cycles through each font individually
- Shows memory usage statistics

**Usage:**

```python
from test_gfx import test_all_fonts
```

**Fonts Available:**

- Font 0: 8×8 monospace (760 bytes) - Debug/logs
- Font 1: 16×16 Liberation Sans (30 KB) - Standard UI
- Font 2: 16×24 Liberation Mono Bold (45 KB) - Readable UI
- Font 3: 24×24 monospace (68 KB) - Headers
- Font 4: 24×32 monospace (91 KB) - Large headers
- Font 5: 32×32 monospace (121 KB) - Big display
- Font 6: 32×48 monospace (182 KB) - Huge display

---

### test_rotation.py

**Location:** `test_gfx/test_rotation.py` (legacy) or `test_gfx_displayio/test_rotation.py` (displayio)

**Description:** Verifies display rotation functionality.

**Features:**

- Loads `cyborg.jpg` from `/gfx/` directory
- Rotates display to 0°, 90°, 180°, 270°
- Demonstrates rotation support in driver
- Includes brightness fading effect

**Usage:**

```python




**Features:**

- Frame rate monitoring
- Optimized rendering
- Performance metrics

**Usage:**

```python
import test_animation
```

**Key Concepts:**

- Frame timing optimization
- `swap_buffers(copy=False)` for performance
- FPS calculation

---



**Features:**

- Background image loading (BMP/JPEG)
- Image + graphics compositing
- Performance with complex scenes

**Usage:**

```python
import test_animation_bg
# Requires image files under /gfx (cerber/cyborg)
```

**Key Concepts:**

- `blit_jpeg()` for images
- Layered rendering
- Performance with images

---

## LVGL Examples (rm690b0_lvgl)

These examples use the LVGL integration for rich UI widgets.

### lvgl_test_gui.py

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
import lvgl_test_gui
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

### lvgl_test_symbols.py

**Description:** Test and display all available LVGL symbols.

**Features:**

- Complete symbol catalog
- Visual symbol reference
- Copy-paste ready constants

**Usage:**

```python
import lvgl_test_symbols
```

---

### lvgl_test_ttf.py

**Description:** Demonstrates loading and scaling TrueType fonts.

**Features:**

- Dynamic font loading from .ttf files
- Multiple sizes from single file (24, 32, 48, 64px)
- Text coloring
- Interactive size/color toggle

**Usage:**

```python
import lvgl_test_ttf
# Tap "Color" button to cycle styles
```

---

## Games

**Location:** `games/`

Complete game implementations using the display and touch/joystick input.

### code.py

**Location:** `code.py` (root of examples/)

**Description:** Main menu launcher for games.

**Features:**

- Touch-based menu interface
- Game selection with visual feedback
- Automatically loads games from `games/` directory

**Usage:**

- Automatically runs on device boot
- Touch buttons to select game
- Returns to menu after game exits

---

### game_flappy_bird.py

**Location:** `games/game_flappy_bird.py`

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
from games import game_flappy_bird
game_flappy_bird.main()
# Or select from code.py menu
```

**Game Mechanics:**

- Bird falls with gravity
- Tap to flap upward
- Avoid pipes
- Score increases as you pass pipes
- Game gets faster as score increases

---

### game_snake.py

**Location:** `games/game_snake.py`

**Description:** Classic Snake game with joystick or touch controls.

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
from games import game_snake
game_snake.main()
# Or select from code.py menu
```

**Game Mechanics:**

- Snake moves continuously in current direction
- Eat red food to grow and score points
- Game speeds up as you score more
- Hit walls or yourself = game over

---

### game_pacman.py

**Location:** `games/game_pacman.py`

**Description:** Full-featured Pac-Man clone with multiple maps.

**Features:**

- 5 Maps (Classic + 4 Ms. Pac-Man variants)
- Complete Ghost AI (Blinky, Pinky, Inky, Clyde)
- Scatter / Chase / Frightened modes
- Power Pellets and Ghost eating

**Controls:**

- **Joystick/Swipe:** Change direction

**Usage:**

```python
from games import game_pacman
game_pacman.main()
```

---

### game_sokoban.py

**Location:** `games/game_sokoban.py`

**Description:** Classic puzzle game where you push crates to goals.

**Features:**

- Multiple levels (from Bansoko)
- Animated movement
- Unlimited Undo system
- Auto-advance levels
- In-game menu

**Controls:**

- **Joystick/Swipe:** Move
- **Center/Tap:** Open Menu / Select
- **Menu Options:** Undo, Reset, Next/Prev Level

**Usage:**

```python
from games import game_sokoban
game_sokoban.main()
# Requires games/game_sokoban_levels.py
```

---

### game_minesweeper.py

**Location:** `games/game_minesweeper.py`

**Description:** Full-featured Minesweeper clone.

**Features:**

- recursive flood-fill for empty areas
- Flagging system
- Timer and mine counter
- Win/Loss animations

**Controls:**

- **Joystick:** Move cursor
- **Button Short / Tap:** Toggle Flag
- **Button Long / Long Press:** Reveal Tile
- **Smiley Face:** Restart Game

**Usage:**

```python
from games import game_minesweeper
game_minesweeper.main()
```

---

## Hardware Tests

**Location:** `test_other/`

Tests for specific hardware peripherals and sensors.

### test_hw_nav_switch.py

**Location:** `test_other/test_hw_nav_switch.py`

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
from test_other import test_hw_nav_switch
# Press switches to see LED changes
```

---

### test_espnow.py

**Location:** `test_other/test_espnow.py`

**Description:** ESP-NOW wireless communication test.

**Features:**

- Peer-to-peer communication
- Message sending/receiving
- Network setup

**Usage:**

```python
from test_other import test_espnow
# Requires two ESP32 devices
```

---

### test_board_hardware.py

**Location:** `test_other/test_board_hardware.py`

**Description:** Comprehensive hardware test suite.

**Features:**

- Display test
- Touch test
- I2C device scanning
- GPIO testing
- Memory check

**Usage:**

```python
from test_other import test_board_hardware
# Interactive test menu
```

---

## Benchmarks

Performance measurement and optimization tools.

**Locations:**
- `benchmark_gfx/` - Legacy rm690b0 API benchmarks
- `benchmark_gfx_displayio/` - Modern displayio API benchmarks
- `benchmark_sd/` - SD card performance tests

### Graphics & Display Benchmarks

#### benchmark_gfx_conversion.py

**Location:** `benchmark_gfx/benchmark_gfx_conversion.py` (legacy) or `benchmark_gfx_displayio/benchmark_gfx_conversion.py` (displayio)

**Description:** Comprehensive image conversion benchmark suite (RAW/BMP/JPEG → framebuffer).

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
# Legacy API
from benchmark_gfx import benchmark_gfx_conversion

# displayio API
from benchmark_gfx_displayio import benchmark_gfx_conversion
```

**Sample Output:**

```text
Full screen fill: 25.3 ms
Circle (r=50): 2.1 ms
Text "Hello" (16×16): 1.2 ms
JPEG decode: 145 ms
```

---

**Description:** Full display primitive benchmark derived from the comprehensive graphics test suite. Measures fill operations, line/circle drawing, rectangles, text fill paths, and overall FPS impact.

**Features:**

- Tests every primitive size bucket (tiny → full screen)
- Reports average time, ops/sec, and star rating
- Includes memory usage snapshot
- Highlights regressions against baseline thresholds

**Usage:**

```python
# Legacy API
from benchmark_gfx import benchmark_gfx_display

# displayio API
from benchmark_gfx_displayio import benchmark_gfx_display
```

---

#### benchmark_simple_flush.py

**Description:** Lightweight stress test that targets high-bandwidth DMA operations. It runs full-screen `fill_color`, multiple `fill_rect` variants (full screen, full-width×64 rows, centered 64 px column), `blit_buffer`, and `circle`/`fill_circle`, first in single-buffer mode and then in double-buffer mode.

**Why it matters:** Exercises the most recent driver optimizations (DMA scheduling, `fill_rect_pixels`, span cache for circles), so regressions in throughput or buffer synchronization become visible immediately.

**Usage:**

```python
import benchmark_simple_flush
# Result table (Avg ms + MP/s) printed to console
```

**Tip:** Capture results before and after firmware changes to quantify the impact of each tweak.

---

### benchmark_sdcard.py

**Description:** Comparison benchmark script for testing SD card performance (Write, Read, Read-ZeroCopy).

**Features:**

- Write speed test (64KB chunks)
- Read speed test (standard allocation)
- Read speed test (zero-copy into pre-allocated buffer)
- Detailed speed reporting in KB/s or MB/s

**Usage:**

```python
from benchmark_sd import benchmark_sdcard
# Benchmark runs automatically on import
```

**Key Operations:**

- Mounting VFS with optimized settings
- Large block file operations
- GC management for consistent timing

---

#### benchmark_sdcard_freq_sweep.py

**Location:** `benchmark_sd/benchmark_sdcard_freq_sweep.py`

**Description:** SD card frequency sweep test for finding optimal SDIO clock frequency.

**Usage:**

```python
from benchmark_sd import benchmark_sdcard_freq_sweep
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

#### Method 1: USB Drive (CIRCUITPY)

```bash
# Mount device as USB drive
cp game_flappy_bird.py /media/CIRCUITPY/code.py
```

#### Method 2: mpremote

```bash
pip install mpremote
mpremote cp game_flappy_bird.py :code.py
mpremote reset
```

#### Method 3: ampy

```bash
pip install adafruit-ampy
ampy --port /dev/ttyACM0 put game_flappy_bird.py /code.py
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

| Component     | Specification                  |
| ------------- | ------------------------------ |
| **MCU**       | ESP32-S3                       |
| **Flash**     | 16 MB                          |
| **PSRAM**     | 8 MB                           |
| **Display**   | RM690B0 AMOLED, 600×450 pixels |
| **Interface** | QSPI (80 MHz)                  |
| **Touch**     | FT6336U, I2C (address 0x38)    |
| **I2C**       | GPIO47 (SDA), GPIO48 (SCL)     |
| **Color**     | RGB565 (16-bit)                |

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

- `test_gfx/test_basic_gfx.py` - Native text and graphics primitives
- `test_gfx/test_all_fonts.py` - All 7 fonts showcase
- `test_gfx/test_rotation.py` - Display rotation test
- `test_gfx_displayio/test_basic_gfx.py` - displayio-based graphics

### Games

- `games/game_flappy_bird.py` - Flappy Bird clone with physics
- `games/game_snake.py` - Classic Snake with joystick
- `games/game_pacman.py` - Full Pac-Man with ghost AI
- `games/game_sokoban.py` - Puzzle game with undo system
- `games/game_minesweeper.py` - Complete Minesweeper

### LVGL Examples

- `test_lvgl/lvgl_test_gui.py` - Complete widget demo
- `test_lvgl/lvgl_icons_example.py` - FontAwesome icons
- `test_lvgl/lvgl_test_ttf.py` - TrueType fonts

### Hardware Tests

- `test_other/test_hw_nav_switch.py` - 5-way switch + RGB LED
- `test_other/test_board_hardware.py` - Complete hardware check
- `test_other/test_espnow.py` - ESP-NOW wireless test

### Benchmarks

- `benchmark_gfx/benchmark_gfx_conversion.py` - Image conversion (legacy API)
- `benchmark_gfx_displayio/benchmark_gfx_conversion.py` - Image conversion (displayio API)
- `benchmark_gfx/benchmark_gfx_display.py` - Display primitives performance
- `benchmark_gfx/benchmark_simple_flush.py` - DMA flush stress test
- `benchmark_sd/benchmark_sdcard.py` - SD card read/write speed

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
