# RM690B0 Driver & LVGL Integration for ESP32-S3

CircuitPython display driver and LVGL integration for the **Waveshare ESP32-S3 Touch AMOLED 2.41** board.

**Based on official CircuitPython 10.0.3** with custom RM690B0 display driver and LVGL integration.

![Board](https://img.shields.io/badge/Board-Waveshare%20ESP32--S3%20Touch%20AMOLED%202.41-blue)
![CircuitPython](https://img.shields.io/badge/CircuitPython-10.0.3-purple)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green)

---

## Overview

Complete CircuitPython support for the Waveshare ESP32-S3 Touch AMOLED 2.41 board featuring:

- **Production-ready display driver** (`rm690b0`) with native text rendering
- **LVGL 8.x integration** (`rm690b0_lvgl`) with Python widget API
- **7 built-in fonts** (8×8 to 32×48 pixels)
- **Hardware-accelerated graphics** (DMA, JPEG decoder)
- **25+ example applications** (games, demos, tests)
- **Comprehensive documentation** (6,700+ lines)

### Hardware Specifications

| Component     | Specification                        |
| ------------- | ------------------------------------ |
| **Board**     | Waveshare ESP32-S3 Touch AMOLED 2.41 |
| **MCU**       | ESP32-S3 (Dual-core Xtensa LX7)      |
| **Flash**     | 16 MB                                |
| **PSRAM**     | 8 MB                                 |
| **Display**   | RM690B0 AMOLED, 600×450 pixels       |
| **Interface** | QSPI (80 MHz)                        |
| **Touch**     | FT6336U I2C Capacitive Touch         |

---

## Repository Structure

### 📁 [`docs/`](docs/) - Complete Documentation

- **[RM690B0_DRIVER.md](docs/RM690B0_DRIVER.md)** (1,668 lines) - Display driver API reference
- **[RM690B0_LVGL.md](docs/RM690B0_LVGL.md)** (3,234 lines) - LVGL integration guide
- **[TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md)** (1,655 lines) - Architecture and troubleshooting
- **[project_status_summary.md](docs/project_status_summary.md)** - Current project status
- **[README.md](docs/README.md)** - Documentation index

### 📁 [`examples/`](examples/) - 25+ Ready-to-Run Examples

**Display Driver Examples:**

- `test_basic_gfx.py` - Interactive graphics and fonts
- `test_all_fonts.py` - All 7 fonts showcase
- `test_animation.py` - 60 FPS animation
- `test_sd_gfx.py` - BMP/JPEG loading

**LVGL Examples:**

- `lvgl_test_gui.py` - Complete widget demo
- `lvgl_test_symbols.py` - LVGL symbols

**Games:**

- `game_flappy_bird.py` - Flappy Bird clone
- `game_snake.py` - Snake (touchscreen)
- `game_pacman.py` - Pac-Man

**Hardware Tests:**

- `test_board_hardware.py` - Complete validation
- `test_hw_nav_switch.py` - I2C joystick
- `test_espnow.py` - ESP-NOW validation

**Benchmarks:**

- `benchmark_gfx_conversion.py` - Image conversion performance
- `benchmark_gfx_display.py` - Primitive throughput
- `benchmark_simple_flush.py` - DMA/flush stress test

See [examples/README.md](examples/README.md) for complete documentation.

### 📁 [`fonts/`](fonts/) - TTF to Bitmap Converter

Convert any TrueType font to RM690B0 format:

- `ttf_to_rm690b0.py` - Font converter
- `test_converted_font.py` - Font validator
- Complete documentation in [fonts/README.md](fonts/README.md)

### 📁 [`firmware/`](firmware/) - Pre-built Firmware

Two versions available:

- `firmware-rm690b0.bin` - Stable (display driver only)
- `firmware-rm690b0-lvgl.bin` - Beta (with LVGL)

See [firmware/README.md](firmware/README.md) for flashing instructions.

### 📁 [`build/`](build/) - Build Scripts

- `build_waveshare.sh` - Automated build script
- `requirements.txt` - Python dependencies

---

## Quick Start

### Option A: Use Pre-built Firmware (Fastest)

1. **Download firmware:**
   - Stable: `firmware/firmware-rm690b0.bin`
   - Beta (LVGL): `firmware/firmware-rm690b0-lvgl.bin`

2. **Flash to board:**

   ```bash
   esptool.py --chip esp32s3 -p /dev/ttyACM0 \
     --baud 921600 write_flash 0x0 firmware/firmware-rm690b0.bin
   ```

3. **Deploy examples:**

   ```bash
   cp examples/test_all_fonts.py /media/CIRCUITPY/code.py
   ```

**See [firmware/README.md](firmware/README.md) for detailed instructions.**

### Option B: Build from Source

1. **Clone repository:**

   ```bash
   # Stable branch
   git clone https://github.com/ppsx/circuitpython.git -b rm690b0-driver-clean

   # Or LVGL branch
   git clone https://github.com/ppsx/circuitpython.git -b lvgl
   ```

2. **Build:**

   ```bash
   cd circuitpython
   make -C ports/espressif BOARD=waveshare_esp32_s3_amoled_241
   ```

3. **Flash:**

   ```bash
   make -C ports/espressif BOARD=waveshare_esp32_s3_amoled_241 flash
   ```

---

## Basic Usage

### Display Driver (rm690b0)

```python
import rm690b0

# Initialize
display = rm690b0.RM690B0()
display.init_display()

# Draw graphics
display.fill_color(rm690b0.BLACK)
display.fill_circle(300, 225, 100, rm690b0.RED)

# Draw text
display.set_font(rm690b0.FONT_16x16)
display.text(50, 200, "Hello, World!", rm690b0.WHITE)

# Update display
display.swap_buffers()
```

### LVGL Widgets (rm690b0_lvgl)

```python
import time
import board
import busio
import rm690b0
import rm690b0_lvgl

# Initialize
display = rm690b0.RM690B0()
display.init_display()

lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()

i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)
lvgl.init_touch(i2c)

# Create widgets
button = rm690b0_lvgl.Button(text="Click Me")
button.x = 200
button.y = 200
button.on_click = lambda btn: print("Clicked!")

# Main loop
while True:
    lvgl.task_handler()
    time.sleep(0.01)
```

**See [docs/RM690B0_DRIVER.md](docs/RM690B0_DRIVER.md) and [docs/RM690B0_LVGL.md](docs/RM690B0_LVGL.md) for complete API documentation.**

---

## Features

### Standalone Display Driver (`rm690b0`)

✅ **Production Ready** - Stable and optimized  
✅ **Native Text** - 7 built-in fonts (8×8 to 32×48)  
✅ **Graphics** - Lines, circles, rectangles, fills  
✅ **Images** - BMP and JPEG with hardware decoder  
✅ **Double Buffering** - Zero tearing animations  
✅ **Performance** - 60+ FPS capable

### LVGL Integration (`rm690b0_lvgl`)

✅ **Rich Widgets** - 20+ widget types  
✅ **TTF Fonts** - Custom font support  
✅ **Touch Input** - Automatic coordinate transformation  
✅ **Event System** - Python callbacks  
⚠️ **Beta Status** - Functional with known GC/touch issue

**Available Widgets:** Label, Button, Slider, Checkbox, Switch, Bar, Arc, Dropdown, Roller, Spinner, Container, Tabview, Table, Buttonmatrix, Textarea, Keyboard, Chart, Canvas, Image, Calendar, Msgbox, and more.

---

## Performance

| Operation        | Time    | Notes                 |
| ---------------- | ------- | --------------------- |
| Full screen fill | ~25 ms  | Hardware DMA limit    |
| Circle (r=50)    | ~2 ms   | Optimized algorithm   |
| Text (16×16)     | ~1.2 ms | Native font rendering |
| JPEG decode      | ~145 ms | Hardware decoder      |

**See [docs/TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md) for detailed benchmarks.**

---

## Hardware

### Required

- Waveshare ESP32-S3 Touch AMOLED 2.41 board
- USB-C cable (data-capable)

### Optional

- SparkFun Qwiic Joystick (digital I2C)
- microSD card
- Additional I2C devices

### Pin Configuration

| Function     | GPIO               | Device   | I2C Address |
| ------------ | ------------------ | -------- | ----------- |
| Display QSPI | 9-14, 21, 16       | RM690B0  | -           |
| Touch I2C    | 47 (SDA), 48 (SCL) | FT6336U  | 0x38        |
| RTC I2C      | 47, 48             | PCF85063 | 0x51        |
| IMU I2C      | 47, 48             | QMI8658C | 0x6B        |
| IO Expander  | 47, 48             | PCA9554  | 0x20        |
| SD Card SPI  | 2, 4-6             | Optional | -           |

**See [docs/TECHNICAL_NOTES.md#pin-configuration](docs/TECHNICAL_NOTES.md) for complete details.**

---

## Documentation

| Document                                      | Description                      |
| --------------------------------------------- | -------------------------------- |
| [RM690B0_DRIVER.md](docs/RM690B0_DRIVER.md)   | Complete display driver API      |
| [RM690B0_LVGL.md](docs/RM690B0_LVGL.md)       | LVGL widgets and integration     |
| [TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md) | Architecture and troubleshooting |
| [examples/README.md](examples/README.md)      | All examples documentation       |
| [firmware/README.md](firmware/README.md)      | Flashing instructions            |
| [fonts/README.md](fonts/README.md)            | Font converter guide             |

---

## CircuitPython Branches

### Main Branch (Stable) ✅

**Repository:** <https://github.com/ppsx/circuitpython/tree/rm690b0-driver-clean>

**Status:** Production Ready  
**Use for:** Production applications, games, embedded displays

### LVGL Branch (Beta) ⚠️

**Repository:** <https://github.com/ppsx/circuitpython/tree/lvgl>

**Status:** Functional with known GC/touch issue  
**Use for:** Prototyping, rich UIs, widget-based interfaces

---

## Project Status

**Phase 5:** ✅ Complete  
**Phase 6:** 🚧 In Progress (Documentation + Widget Expansion)

### Production Ready ✅

- rm690b0 driver - Stable and fast
- Native text system - 7 fonts + converter
- Graphics primitives - All optimized
- Image support - BMP/JPEG working
- Documentation - 6,700+ lines
- Examples - 25+ demos

### Known Issues ⚠️

- **LVGL+touch freeze** under heavy GC pressure
- **Workaround:** Avoid `gc.collect()` in UI loop, load TTF fonts once at startup

**See [docs/project_status_summary.md](docs/project_status_summary.md) for complete status.**

---

## Troubleshooting

**Display shows nothing:**

- Check `display.init_display()` was called
- Try `display.brightness = 1.0`

**Touch not working:**

- Use `board.TP_SCL` and `board.TP_SDA` (not `board.SCL/SDA`)
- Initialize after display: `lvgl.init_touch(i2c)`

**LVGL touch freezes:**

- Avoid `gc.collect()` in main loop
- Load TTF fonts once at startup

**Memory errors:**

- Use `swap_buffers(copy=False)` for animations
- Close files after reading

**See [docs/RM690B0_DRIVER.md#troubleshooting](docs/RM690B0_DRIVER.md#troubleshooting) and [docs/RM690B0_LVGL.md#troubleshooting](docs/RM690B0_LVGL.md#troubleshooting) for detailed solutions.**

---

## Contributing

Contributions welcome! Please:

1. Fork the appropriate branch
2. Test on actual hardware
3. Document changes
4. Submit pull request

**Areas for contribution:** LVGL widgets, performance optimizations, bug fixes, documentation, examples.

---

## License

**MIT License**

Based on CircuitPython 10.0.3 (MIT License)  
Built-in fonts use Liberation fonts (SIL OFL 1.1)

See full license in source code.

---

## Links

**Repositories:**

- Main: <https://github.com/ppsx/circuitpython/tree/rm690b0-driver-clean>
- LVGL: <https://github.com/ppsx/circuitpython/tree/lvgl>

**Hardware:**

- Waveshare: <https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-2.41>
- ESP32-S3: <https://www.espressif.com/>

**Documentation:**

- [Complete docs](docs/)
- [Examples](examples/)
- [Font tools](fonts/)

---

## Credits

**Developed by:** Przemyslaw Patrick Socha and AI agents
**Based on:** CircuitPython 10.0.3, LVGL 8.x, ESP-IDF  
**Hardware:** Waveshare ESP32-S3 Touch AMOLED 2.41

---

**Enjoy building with RM690B0 on ESP32-S3!** 🎉

---

## Showcase

### 🎮 ESP32-Doom (PrBoom Port)

A highly optimized port of Doom running natively on this board using ESP-IDF.

- **Performance:** **65 FPS** (stable) at full **600x450** resolution.
- **Optimizations:** QSPI 80MHz, Double Buffered DMA, Internal RAM.
- **Repo:** <https://github.com/ppsx/esp32-doom>
