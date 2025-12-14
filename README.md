# RM690B0 Driver & LVGL Integration for ESP32-S3

CircuitPython display driver and LVGL integration for the **Waveshare ESP32-S3 Touch AMOLED 2.41** board.

**Based on official CircuitPython 10.0.3** with custom RM690B0 display driver and LVGL integration.

![Board](https://img.shields.io/badge/Board-Waveshare%20ESP32--S3%20Touch%20AMOLED%202.41-blue)
![CircuitPython](https://img.shields.io/badge/CircuitPython-10.0.3-purple)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green)

---

## Overview

This repository contains comprehensive documentation, examples, and tools for the RM690B0 AMOLED display driver on the Waveshare ESP32-S3 Touch AMOLED 2.41 board.

### Hardware Specifications

| Component | Specification |
|-----------|---------------|
| **Board** | Waveshare ESP32-S3 Touch AMOLED 2.41 |
| **MCU** | ESP32-S3 (Dual-core Xtensa LX7) |
| **Flash** | 16 MB |
| **PSRAM** | 8 MB |
| **Display** | RM690B0 AMOLED, 600×450 pixels |
| **Interface** | QSPI (80 MHz) |
| **Touch** | FT6336U I2C Capacitive Touch |
| **Color Format** | RGB565 (16-bit) |

### What's Included

- 📚 **Comprehensive Documentation** - Complete API references and technical guides
- 🎮 **Example Applications** - Games, UI demos, and hardware tests
- 🔤 **Font Tools** - TTF to bitmap converter with validation
- 🚀 **Production Ready** - Stable driver with proven performance

---

## Repository Structure

### 📁 [`docs/`](docs/)

Complete technical documentation for the RM690B0 driver and LVGL integration.

**Key Documents:**
- **[RM690B0_DRIVER.md](docs/RM690B0_DRIVER.md)** - Complete API reference for standalone display driver
- **[RM690B0_LVGL.md](docs/RM690B0_LVGL.md)** - LVGL integration guide with Python widget API
- **[TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md)** - Deep technical details, performance, DMA, touch integration
- **[project_status_summary.md](docs/project_status_summary.md)** - Project status and roadmap

### 📁 [`examples/`](examples/)

Ready-to-run example scripts demonstrating display and LVGL features.

**Includes:**
- 🎨 Display driver examples (graphics, text, images)
- 🖼️ LVGL widget demonstrations
- 🎮 Complete games (Flappy Bird, Snake)
- 🔧 Hardware tests (touch, I2C devices, SD card)
- ⚡ Performance benchmarks

See [examples/README.md](examples/README.md) for complete list and usage instructions.

### 📁 [`fonts/`](fonts/)

TTF to RM690B0 bitmap font converter with tools and documentation.

**Features:**
- Convert any TrueType font to RM690B0 format
- Configurable font sizes (8×8 to 64×64+)
- Font validation and preview tools
- Complete documentation and examples

See [fonts/README.md](fonts/README.md) for usage guide.

### 📁 [`build/`](build/)

Build scripts and configuration for compiling CircuitPython with RM690B0 support.

**Contains:**
- `build_waveshare.sh` - Automated build script for ESP32-S3
- `requirements.txt` - Python dependencies for building

**Quick Build Guide:**

```bash
# 1. Copy build files to CircuitPython directory
cp build/* /path/to/circuitpython/

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Install ESP-IDF prerequisites (first time only)
./build_waveshare.sh prerequisites

# 5. Set up ESP-IDF environment (to avoid reinitialization)
source ports/espressif/esp-idf/export.sh

# 6. Build and flash firmware
./build_waveshare.sh rebuild && ./build_waveshare.sh flash
```

See build scripts for additional options and commands.

---

## Driver Features

### Standalone Display Driver (`rm690b0`)

✅ **Production Ready** - Stable and optimized  
✅ **Hardware Accelerated** - DMA-backed rendering  
✅ **Native Text Rendering** - 7 built-in bitmap fonts  
✅ **Image Support** - BMP and JPEG (hardware decoder)  
✅ **Complete Graphics API** - Lines, circles, rectangles, fills  
✅ **Double Buffering** - Zero tearing, smooth animations  
✅ **Fast Performance** - 60+ FPS capable

**Built-in Fonts:**
- Font 0: 8×8 monospace (760 B)
- Font 1: 16×16 Liberation Mono Bold (30 KB)
- Font 2: 16×24 Liberation Mono Bold (45 KB)
- Font 3: 24×24 Liberation Mono Bold (68 KB)
- Font 4: 24×32 Liberation Mono Bold (91 KB)
- Font 5: 32×32 Liberation Mono Bold (121 KB)
- Font 6: 32×48 Liberation Mono Bold (182 KB)

### LVGL Integration (`rm690b0_lvgl`)

✅ **Rich Widget Library** - Buttons, sliders, labels, and more  
✅ **TTF Font Support** - Load custom TrueType fonts  
✅ **Touch Integration** - Automatic coordinate transformation  
✅ **Python API** - Pythonic widget classes with properties  
✅ **Event Handling** - Callbacks for user interactions  
✅ **Flexible Layouts** - Flex containers and positioning

**Available Widgets:**
- Label, Button, Slider, Checkbox, Switch
- Bar, Arc, Dropdown, Roller, Spinner
- Container, Tabview, Table, Buttonmatrix
- Textarea, Keyboard, Chart, Canvas
- And many more...

**Note:** LVGL integration is functional but has a known stability issue under heavy GC pressure. See project status for details.

---

## Quick Start

### 1. Get CircuitPython Source

Clone the forked CircuitPython repository (based on official 10.0.3) with RM690B0 support:

**Main Branch (Stable):**
```bash
git clone https://github.com/ppsx/circuitpython.git -b rm690b0-driver-clean
```

**LVGL Branch (Work-in-Progress):**
```bash
git clone https://github.com/ppsx/circuitpython.git -b lvgl
```

### 2. Build and Flash

**Quick Build (using provided scripts):**

```bash
# Copy build files to CircuitPython directory
cp build/* /path/to/circuitpython/

# Set up and build
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
./build_waveshare.sh prerequisites
source ports/espressif/esp-idf/export.sh
./build_waveshare.sh rebuild && ./build_waveshare.sh flash
```

**Manual Build:**

```bash
# Follow standard CircuitPython build instructions, then flash
esptool.py --chip esp32s3 --port /dev/ttyACM0 write_flash 0x0 firmware.bin
```

See [`build/`](build/) directory for automated build scripts.

### 3. Run Examples

Copy any example to your device as `code.py`:

```bash
# Mount device, then copy
cp examples/flappy_bird_clone.py /media/CIRCUITPY/code.py

# Or use mpremote
mpremote cp examples/snake_game.py :code.py
mpremote reset
```

### 4. Basic Usage

**Display Driver:**
```python
import rm690b0

display = rm690b0.RM690B0()
display.init_display()

display.fill_color(0xF800)  # Red screen
display.set_font(1)         # 16×16 font
display.text(50, 200, "Hello, World!", 0xFFFF)
display.swap_buffers()
```

**LVGL Widgets:**
```python
import rm690b0_lvgl

lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()
lvgl.init_rendering()

label = rm690b0_lvgl.Label("Hello LVGL", x=50, y=50)
button = rm690b0_lvgl.Button("Click Me", x=100, y=150)
button.on_click = lambda e: print("Clicked!")

while True:
    lvgl.task_handler()
    time.sleep(0.01)
```

---

## Performance

### Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Full screen fill | ~25 ms | Hardware limited by DMA |
| Circle (r=50) | ~2 ms | Optimized Bresenham |
| Text "Hello World" (16×16) | ~1.2 ms | Native font rendering |
| 100×100 rectangle | ~0.5 ms | DMA accelerated |
| JPEG decode | ~145 ms | Hardware decoder |

---

## Documentation

### Complete Guides

- **[RM690B0_DRIVER.md](docs/RM690B0_DRIVER.md)** - Display driver API reference (1,562 lines)
- **[RM690B0_LVGL.md](docs/RM690B0_LVGL.md)** - LVGL integration guide (2,820 lines)
- **[TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md)** - Technical deep dive (1,355 lines)

### Quick References

- **[examples/README.md](examples/README.md)** - All examples documented
- **[fonts/README.md](fonts/README.md)** - Font converter guide
- **[project_status_summary.md](docs/project_status_summary.md)** - Current status and roadmap

---

## Example Applications

### Games

- **[code.py](examples/code.py)** - Main menu launcher with touch UI
- **[flappy_bird_clone.py](examples/flappy_bird_clone.py)** - Complete Flappy Bird game
- **[snake_game.py](examples/snake_game.py)** - Snake with joystick control

### Display Demos

- **[bouncing_ball_60fps.py](examples/bouncing_ball_60fps.py)** - Smooth 60 FPS animation
- **[font_test.py](examples/font_test.py)** - All 7 built-in fonts showcase
- **[test_gui.py](examples/test_gui.py)** - Complete LVGL widget demo

### Hardware Tests

- **[navigation_switch_test.py](examples/navigation_switch_test.py)** - 5-way switch + RGB LED
- **[board_test_suite.py](examples/board_test_suite.py)** - Complete hardware validation
- **[unified_benchmark.py](examples/unified_benchmark.py)** - Performance measurements

---

## Font Tools

### TTF to Bitmap Converter

Convert any TrueType font to RM690B0 bitmap format:

```bash
# Install dependencies
pip install Pillow

# Convert font
python fonts/ttf_to_rm690b0.py font.ttf -w 16 -t 16 -o font_16x16.h

# Validate
python fonts/test_converted_font.py font_16x16.h --char A
```

See [fonts/README.md](fonts/README.md) for complete documentation.

---

## Hardware Support

### Required Hardware

- **Waveshare ESP32-S3 Touch AMOLED 2.41** board
- USB-C cable for programming/power

### Optional Peripherals

- **SparkFun Qwiic Navigation Switch** (for Snake game)
- **SD Card** (for image loading demos)
- **Additional I2C devices** (tested in examples)

### Pin Configuration

| Function | GPIO | Notes |
|----------|------|-------|
| **Display QSPI** | 9-14, 21, 16 | See TECHNICAL_NOTES.md |
| **Touch I2C SDA** | 47 | FT6336U at 0x38 |
| **Touch I2C SCL** | 48 | |
| **SD Card SPI** | 2, 4-6 | Optional |

---

## CircuitPython Branches

**Both branches are based on official CircuitPython 10.0.3**

### Main Driver Branch (Stable)

**Repository:** https://github.com/ppsx/circuitpython/tree/rm690b0-driver-clean

**Status:** ✅ Production Ready

**Features:**
- Complete standalone RM690B0 driver
- Native text rendering (7 fonts)
- Graphics primitives
- Image support (BMP/JPEG)
- Stable and optimized
- Based on CircuitPython 10.0.3

### LVGL Integration Branch (Work-in-Progress)

**Repository:** https://github.com/ppsx/circuitpython/tree/lvgl

**Status:** ⚠️ Functional with Known Issues

**Features:**
- Full LVGL 8.x integration
- Python widget API
- TTF font support
- Touch integration
- Rich UI capabilities
- Based on CircuitPython 10.0.3

**Known Issue:** LVGL+touch can lose responsiveness under heavy GC pressure. Avoid frequent `gc.collect()` calls in UI loop.

---

## Project Status

### Production Ready Components

✅ **RM690B0 standalone driver** - Stable, fast, complete  
✅ **Native text rendering** - 7 embedded fonts, TTF converter  
✅ **Graphics primitives** - All functions optimized  
✅ **Image support** - BMP and hardware-accelerated JPEG  
✅ **Documentation** - Comprehensive guides and examples  
✅ **Example applications** - Games and demos working

### Work-in-Progress Components

⚠️ **LVGL integration** - Functional but GC/touch stability issue  
⚠️ **Additional widgets** - Some LVGL widgets need Python bindings

### Recommendations

- **Use standalone driver** for production applications
- **Use LVGL** for prototyping and rich UIs (with caution)
- **Load TTF fonts** once at startup, not repeatedly
- **Avoid `gc.collect()`** in LVGL main loop

See [project_status_summary.md](docs/project_status_summary.md) for detailed status.

---

## Contributing

Contributions are welcome! Please:

1. Fork the appropriate CircuitPython branch
2. Create a feature branch
3. Test on actual hardware
4. Submit pull request with description

---

## License

This project is licensed under the **MIT License**.

### CircuitPython Base

This project is based on CircuitPython 10.0.3, which is licensed under the MIT License. The RM690B0 driver and LVGL integration additions follow the same MIT License.

### Font Licenses

Built-in fonts use Liberation fonts (SIL OFL 1.1). See font headers for details.

### MIT License

```
MIT License

Copyright (c) 2025 RM690B0 Driver Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Links

### Repositories

- **Main Driver Branch:** https://github.com/ppsx/circuitpython/tree/rm690b0-driver-clean
- **LVGL Branch:** https://github.com/ppsx/circuitpython/tree/lvgl

### Documentation

- **[Complete Documentation](docs/)** - All technical guides
- **[Example Scripts](examples/)** - Ready-to-run demos
- **[Font Tools](fonts/)** - TTF converter

### Hardware

- **Waveshare ESP32-S3 Touch AMOLED 2.41** - Official product page: https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-2.41

---

## Credits

Developed for the Waveshare ESP32-S3 Touch AMOLED 2.41 board with CircuitPython.

**Based On:**
- Official CircuitPython 10.0.3

**Key Components:**
- RM690B0 AMOLED display driver
- LVGL 8.x integration
- FT6336U touch controller
- ESP32-S3 MCU

---

## Support

For issues, questions, or contributions:

1. Check existing documentation in `docs/`
2. Review examples in `examples/`
3. See troubleshooting sections in guides
4. Open issue on appropriate CircuitPython branch

---

**Enjoy building with RM690B0 on ESP32-S3!** 🎉
