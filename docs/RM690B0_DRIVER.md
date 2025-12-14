# RM690B0 Display Driver - Complete Guide

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Requirements](#installation--requirements)
4. [Quick Start](#quick-start)
5. [Python API Reference](#python-api-reference)
6. [Graphics Primitives](#graphics-primitives)
7. [Text Rendering](#text-rendering)
8. [Image Support](#image-support)
9. [Color System](#color-system)
10. [Performance Optimization](#performance-optimization)
11. [Examples](#examples)
12. [Implementation Details](#implementation-details)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The **RM690B0 driver** is a high-performance, standalone display driver for the Waveshare ESP32-S3 Touch AMOLED 2.41 board. It provides direct framebuffer access with hardware-accelerated rendering through DMA transfers.

### What's Included

- **Hardware-Accelerated Graphics**: DMA-backed rendering with double buffering
- **Complete Graphics API**: Lines, circles, rectangles, filled shapes, polygons
- **Native Text Rendering**: 7 built-in bitmap fonts (8×8 to 32×48 pixels)
- **Image Support**: BMP and JPEG loading with hardware JPEG decoder
- **Color Management**: RGB565 format with automatic byte swapping
- **Display Control**: Brightness, rotation, dimensions
- **Zero Dependencies**: Works independently without LVGL or other frameworks

### Key Features

✅ **600×450 AMOLED Display** at 80 MHz QSPI  
✅ **Double Buffering** in PSRAM (zero tearing)  
✅ **DMA Transfers** for maximum performance  
✅ **Native Text API** with 7 embedded fonts (~538 KB total)  
✅ **Fast Rendering**: 10-500× faster than DisplayIO for text  
✅ **Hardware JPEG Decoder** (ESP32-S3 accelerated)  
✅ **BMP Support** (24-bit RGB)  
✅ **Brightness Control** (0.0-1.0)  
✅ **Simple API** (~15 core methods)  
✅ **Production Ready** with proven stability

### Hardware Specifications

| Component | Specification |
|-----------|---------------|
| **Display Controller** | RM690B0 AMOLED |
| **Resolution** | 600×450 pixels (landscape) |
| **Interface** | QSPI (Quad SPI) |
| **Color Format** | RGB565 (16-bit) |
| **Clock Speed** | 80 MHz |
| **Framebuffer** | 540 KB in PSRAM (double buffered) |
| **DMA Limit** | 30 lines per transfer |
| **MCU** | ESP32-S3 |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Python Application                     │
├─────────────────────────────────────────────────────────┤
│              rm690b0 Module (CircuitPython)             │
│  • init_display()     • fill_rect()                     │
│  • set_font()         • line()                          │
│  • text()             • circle()                        │
│  • swap_buffers()     • rect()                          │
├─────────────────────────────────────────────────────────┤
│           C Driver (common-hal/rm690b0/)                │
│  • Framebuffer Management                               │
│  • DMA Transfer Engine                                  │
│  • Text Rendering Engine                                │
│  • Image Decoders (BMP/JPEG)                            │
├─────────────────────────────────────────────────────────┤
│              ESP-IDF LCD Component                       │
│  • esp_lcd_rm690b0.c (panel driver)                     │
│  • QSPI Communication                                   │
│  • Hardware Acceleration                                │
├─────────────────────────────────────────────────────────┤
│                  ESP32-S3 Hardware                       │
│  • PSRAM (framebuffer storage)                          │
│  • DMA (transfer engine)                                │
│  • JPEG Decoder (hardware accelerated)                  │
│  • QSPI Peripheral                                      │
└─────────────────────────────────────────────────────────┘
```

### Memory Architecture

**Double Buffering:**
- **Front Buffer**: Currently displayed (PSRAM)
- **Back Buffer**: Being drawn to (PSRAM)
- **Swap**: `swap_buffers()` flips front/back instantly
- **Result**: Zero tearing, smooth animations

**DMA Staging:**
- DMA requires SRAM buffers (MALLOC_CAP_DMA)
- Driver manages staging buffers automatically
- Transfers up to 30 lines per DMA operation
- Full screen refresh in ~17 chunks

---

## Installation & Requirements

### Hardware Requirements

- **Board**: Waveshare ESP32-S3 Touch AMOLED 2.41
- **Display**: RM690B0 AMOLED (integrated)
- **MCU**: ESP32-S3 with PSRAM

### Software Requirements

- **CircuitPython**: 9.0.0 or later
- **Build**: Custom build with RM690B0 support
- **Module**: `rm690b0` (built-in)

### Module Availability

The `rm690b0` module is available on compatible CircuitPython builds:

```python
import rm690b0  # ✅ Available on ESP32-S3 with RM690B0 display
```

---

## Quick Start

### Minimal Example (3 Lines)

```python
import rm690b0

# Initialize display
display = rm690b0.RM690B0()
display.init_display()

# Draw something
display.fill_color(0xF800)  # Red screen
display.swap_buffers()
```

### Hello World Example

```python
import rm690b0

# Initialize
display = rm690b0.RM690B0()
display.init_display()

# Clear screen (black)
display.fill_color(0x0000)

# Draw text
display.set_font(1)  # 16×16 font
display.text(50, 200, "Hello, World!", color=0xFFFF)

# Show on screen
display.swap_buffers()
```

### Graphics Example

```python
import rm690b0

display = rm690b0.RM690B0()
display.init_display()

# Blue background
display.fill_color(0x001F)

# White rectangle
display.rect(50, 50, 200, 100, color=0xFFFF)

# Filled red circle
display.fill_circle(400, 225, 50, color=0xF800)

# Yellow line
display.line(0, 0, 600, 450, color=0xFFE0)

# Update display
display.swap_buffers()
```

---

## Python API Reference

### Class: `RM690B0`

Main display driver class providing graphics, text, and image rendering.

#### Constructor

```python
display = rm690b0.RM690B0()
```

Creates a new RM690B0 display instance. Only one instance should exist at a time.

**Parameters:** None

**Example:**
```python
import rm690b0
display = rm690b0.RM690B0()
```

---

#### Methods

##### `init_display()`

Initialize the display hardware and framebuffers.

```python
display.init_display()
```

**Parameters:** None  
**Returns:** None  
**Raises:** `RuntimeError` if initialization fails

**What it does:**
- Allocates double-buffered framebuffers in PSRAM
- Configures QSPI interface at 80 MHz
- Initializes RM690B0 controller registers
- Sets up DMA staging buffers
- Clears both buffers to black
- Turns on display power and backlight

**Example:**
```python
display = rm690b0.RM690B0()
display.init_display()  # Must call before any drawing
```

**Note:** Must be called before any other drawing operations.

---

##### `deinit()`

Deinitialize the display and free resources.

```python
display.deinit()
```

**Parameters:** None  
**Returns:** None

**What it does:**
- Frees framebuffer memory
- Releases DMA buffers
- Powers down display
- Resets QSPI interface

**Example:**
```python
display.deinit()
# Display is now off and resources freed
```

---

##### `swap_buffers(copy=True)`

Swap front and back framebuffers, making drawn content visible.

```python
display.swap_buffers(copy=True)
```

**Parameters:**
- `copy` (bool, optional): If `True`, copy front buffer to back buffer after swap. Default: `True`

**Returns:** None

**Behavior:**
- **With `copy=True`**: New back buffer contains previous frame (for incremental updates)
- **With `copy=False`**: New back buffer is undefined (for full redraws)

**Performance:**
- Buffer swap itself is instant (pointer swap)
- Copy operation takes ~3-5 ms if enabled

**Example:**
```python
# Incremental updates (preserve previous frame)
display.fill_circle(x, y, 10, 0xFFFF)
display.swap_buffers(copy=True)  # Old content preserved

# Full redraw (no copy needed)
display.fill_color(0x0000)
display.text(10, 10, "New Frame", 0xFFFF)
display.swap_buffers(copy=False)  # Faster, no copy
```

---

#### Properties

##### `width` (read-only)

Get display width in pixels.

```python
width = display.width  # 600
```

**Type:** `int`  
**Value:** `600` (landscape orientation)

---

##### `height` (read-only)

Get display height in pixels.

```python
height = display.height  # 450
```

**Type:** `int`  
**Value:** `450` (landscape orientation)

---

##### `rotation` (read-only)

Get current display rotation.

```python
rotation = display.rotation  # 0
```

**Type:** `int`  
**Value:** `0` (landscape orientation, fixed)

**Note:** Rotation is currently fixed at 0° (landscape). Software rotation can be implemented in application layer if needed.

---

##### `brightness`

Get or set display brightness.

```python
# Get brightness
level = display.brightness  # 0.0-1.0

# Set brightness
display.brightness = 0.5  # 50%
```

**Type:** `float`  
**Range:** `0.0` (off) to `1.0` (full brightness)

**Example:**
```python
# Dim display
display.brightness = 0.3

# Full brightness
display.brightness = 1.0

# Fade in effect
import time
for i in range(0, 11):
    display.brightness = i / 10
    time.sleep(0.05)
```

---

## Graphics Primitives

### `fill_color(color)`

Fill entire screen with solid color.

```python
display.fill_color(color)
```

**Parameters:**
- `color` (int): RGB565 color value (0x0000-0xFFFF)

**Returns:** None

**Performance:** ~25 ms for full screen

**Example:**
```python
display.fill_color(0x0000)  # Black
display.fill_color(0xFFFF)  # White
display.fill_color(0xF800)  # Red
display.fill_color(0x07E0)  # Green
display.fill_color(0x001F)  # Blue
```

---

### `pixel(x, y, color)`

Draw a single pixel.

```python
display.pixel(x, y, color)
```

**Parameters:**
- `x` (int): X coordinate (0-599)
- `y` (int): Y coordinate (0-449)
- `color` (int): RGB565 color value

**Returns:** None

**Example:**
```python
# Draw red pixel at (100, 100)
display.pixel(100, 100, 0xF800)

# Draw pattern
for i in range(100):
    display.pixel(i, i, 0xFFFF)
```

---

### `line(x0, y0, x1, y1, color)`

Draw a line between two points.

```python
display.line(x0, y0, x1, y1, color)
```

**Parameters:**
- `x0, y0` (int): Start point coordinates
- `x1, y1` (int): End point coordinates
- `color` (int): RGB565 color value

**Returns:** None

**Algorithm:** Bresenham's line algorithm (single-pixel accurate)

**Example:**
```python
# Diagonal line
display.line(0, 0, 600, 450, 0xFFFF)

# Horizontal line
display.line(0, 225, 600, 225, 0xF800)

# Vertical line
display.line(300, 0, 300, 450, 0x07E0)

# Draw X pattern
display.line(0, 0, 600, 450, 0xFFE0)
display.line(600, 0, 0, 450, 0xFFE0)
```

---

### `rect(x, y, width, height, color)`

Draw rectangle outline.

```python
display.rect(x, y, width, height, color)
```

**Parameters:**
- `x, y` (int): Top-left corner coordinates
- `width` (int): Rectangle width in pixels
- `height` (int): Rectangle height in pixels
- `color` (int): RGB565 color value

**Returns:** None

**Note:** Draws 1-pixel border, no corner overlap

**Example:**
```python
# White border rectangle
display.rect(50, 50, 200, 100, 0xFFFF)

# Nested rectangles
display.rect(100, 100, 400, 250, 0xF800)
display.rect(110, 110, 380, 230, 0x07E0)
display.rect(120, 120, 360, 210, 0x001F)
```

---

### `fill_rect(x, y, width, height, color)`

Draw filled rectangle.

```python
display.fill_rect(x, y, width, height, color)
```

**Parameters:**
- `x, y` (int): Top-left corner coordinates
- `width` (int): Rectangle width in pixels
- `height` (int): Rectangle height in pixels
- `color` (int): RGB565 color value

**Returns:** None

**Performance:** Hardware accelerated, very fast

**Example:**
```python
# Red filled rectangle
display.fill_rect(50, 50, 200, 100, 0xF800)

# Progress bar
def draw_progress(percent):
    # Background (gray)
    display.fill_rect(50, 200, 500, 30, 0x7BEF)
    # Progress (green)
    width = int(500 * percent / 100)
    display.fill_rect(50, 200, width, 30, 0x07E0)

draw_progress(75)  # 75%
```

---

### `circle(x, y, radius, color)`

Draw circle outline.

```python
display.circle(x, y, radius, color)
```

**Parameters:**
- `x, y` (int): Center coordinates
- `radius` (int): Circle radius in pixels
- `color` (int): RGB565 color value

**Returns:** None

**Algorithm:** Bresenham's circle algorithm (optimized, 39× faster than naive)

**Example:**
```python
# White circle
display.circle(300, 225, 100, 0xFFFF)

# Concentric circles
for r in range(10, 101, 10):
    display.circle(300, 225, r, 0x07E0)
```

---

### `fill_circle(x, y, radius, color)`

Draw filled circle.

```python
display.fill_circle(x, y, radius, color)
```

**Parameters:**
- `x, y` (int): Center coordinates
- `radius` (int): Circle radius in pixels
- `color` (int): RGB565 color value

**Returns:** None

**Performance:** Optimized scanline filling

**Example:**
```python
# Red filled circle
display.fill_circle(300, 225, 100, 0xF800)

# Traffic light
display.fill_circle(100, 100, 40, 0xF800)  # Red
display.fill_circle(100, 200, 40, 0xFFE0)  # Yellow
display.fill_circle(100, 300, 40, 0x07E0)  # Green
```

---

### `hline(x, y, width, color)`

Draw horizontal line (optimized).

```python
display.hline(x, y, width, color)
```

**Parameters:**
- `x, y` (int): Starting coordinates
- `width` (int): Line length in pixels
- `color` (int): RGB565 color value

**Returns:** None

**Performance:** Faster than `line()` for horizontal lines

**Example:**
```python
# Horizontal separator
display.hline(0, 225, 600, 0xFFFF)

# Stripes
for i in range(0, 450, 20):
    display.hline(0, i, 600, 0x001F if i % 40 else 0xFFFF)
```

---

### `vline(x, y, height, color)`

Draw vertical line (optimized).

```python
display.vline(x, y, height, color)
```

**Parameters:**
- `x, y` (int): Starting coordinates
- `height` (int): Line length in pixels
- `color` (int): RGB565 color value

**Returns:** None

**Performance:** Faster than `line()` for vertical lines

**Example:**
```python
# Vertical separator
display.vline(300, 0, 450, 0xFFFF)

# Grid
for x in range(0, 600, 50):
    display.vline(x, 0, 450, 0x7BEF)
for y in range(0, 450, 50):
    display.hline(0, y, 600, 0x7BEF)
```

---

## Text Rendering

### Overview

The RM690B0 driver includes native text rendering with 7 built-in bitmap fonts. This system is lightweight, fast, and completely independent from LVGL.

**Key Features:**
- ✅ 7 embedded fonts (8×8 to 32×48 pixels)
- ✅ Simple API: `set_font()` + `text()`
- ✅ Transparent or solid backgrounds
- ✅ UTF-8 string support
- ✅ ASCII printable characters (0x20-0x7E)
- ✅ 10-500× faster than DisplayIO text
- ✅ Zero heap allocations during rendering

### Built-in Fonts

| ID | Size | Style | Memory | Best For |
|----|------|-------|--------|----------|
| 0 | 8×8 | Monospace | 760 B | Tiny text, debug, status |
| 1 | 16×16 | Liberation Sans | 30 KB | Body text, labels |
| 2 | 16×24 | Liberation Mono Bold | 45 KB | Code, monospace text |
| 3 | 24×24 | Monospace | 68 KB | Headings, emphasis |
| 4 | 24×32 | Monospace | 91 KB | Large headings |
| 5 | 32×32 | Monospace | 121 KB | Display text |
| 6 | 32×48 | Monospace | 182 KB | Very large text |

**Total:** ~538 KB in flash

### `set_font(font_id)`

Select active font for text rendering.

```python
display.set_font(font_id)
```

**Parameters:**
- `font_id` (int): Font identifier (0-6)

**Returns:** None

**Note:** Invalid font IDs automatically clamp to 0 (no exception)

**Example:**
```python
display.set_font(0)  # 8×8 tiny
display.set_font(1)  # 16×16 normal
display.set_font(3)  # 24×24 large
display.set_font(6)  # 32×48 huge
```

---

### `text(x, y, text, color=0xFFFF, background=None)`

Render text string at specified position.

```python
display.text(x, y, text, color=0xFFFF, background=None)
```

**Parameters:**
- `x, y` (int): Top-left position of text
- `text` (str): UTF-8 string to render
- `color` (int, optional): RGB565 foreground color (default: white)
- `background` (int or None, optional): RGB565 background color or None for transparent

**Returns:** None

**Behavior:**
- Characters rendered left-to-right
- Fixed-width fonts (each character same width)
- Unsupported characters replaced with '?'
- No automatic word wrap
- Clipping at screen boundaries

**Performance:** 0.3-7.7 ms for "Hello World" (depends on font size)

**Example:**
```python
# Simple white text (transparent background)
display.set_font(1)
display.text(10, 10, "Hello, World!", color=0xFFFF)

# Colored text with solid background
display.text(10, 50, "Warning!", color=0x0000, background=0xFFE0)

# Status text (small font)
display.set_font(0)
display.text(10, 430, f"FPS: 60  Temp: 25C", color=0x07E0)

# Multi-line text (manual positioning)
display.set_font(1)
display.text(50, 100, "Line 1", 0xFFFF)
display.text(50, 120, "Line 2", 0xFFFF)
display.text(50, 140, "Line 3", 0xFFFF)
```

### Text Rendering Examples

**Multi-Font UI:**
```python
import rm690b0

display = rm690b0.RM690B0()
display.init_display()

display.fill_color(0x0000)  # Black

# Title (large)
display.set_font(3)  # 24×24
display.text(50, 20, "System Status", color=0xFFFF)

# Body (medium)
display.set_font(1)  # 16×16
display.text(50, 80, "CPU: 45%", color=0x07E0)
display.text(50, 110, "Memory: 2.1 MB free", color=0x07E0)
display.text(50, 140, "Temperature: 25C", color=0x07E0)

# Footer (small)
display.set_font(0)  # 8×8
display.text(10, 430, "v1.0.0 | Uptime: 3h 24m", color=0x7BEF)

display.swap_buffers()
```

**Colored Labels:**
```python
def show_status(msg, status):
    """Show status message with color coding."""
    display.fill_color(0x0000)
    display.set_font(1)
    
    if status == "error":
        color = 0xF800  # Red
        bg = 0x1800     # Dark red
    elif status == "warning":
        color = 0x0000  # Black
        bg = 0xFFE0     # Yellow
    elif status == "success":
        color = 0xFFFF  # White
        bg = 0x07E0     # Green
    else:
        color = 0xFFFF  # White
        bg = None       # Transparent
    
    display.text(50, 200, msg, color=color, background=bg)
    display.swap_buffers()

show_status("Connected!", "success")
```

---

## Image Support

### Overview

The RM690B0 driver supports loading and displaying BMP and JPEG images.

**Supported Formats:**
- ✅ BMP: 24-bit RGB (uncompressed)
- ✅ JPEG: Hardware-accelerated decoding (ESP32-S3 JPEG engine)

### `blit_bmp(x, y, bmp_data)`

Display BMP image from memory.

```python
display.blit_bmp(x, y, bmp_data)
```

**Parameters:**
- `x, y` (int): Top-left position for image
- `bmp_data` (bytes): BMP file data (header + pixels)

**Returns:** None

**Requirements:**
- BMP must be 24-bit RGB format
- Uncompressed only
- Any reasonable size supported

**Example:**
```python
# Load BMP from file
with open("/sd/logo.bmp", "rb") as f:
    bmp_data = f.read()

# Display at position (100, 100)
display.blit_bmp(100, 100, bmp_data)
display.swap_buffers()
```

---

### `blit_jpeg(x, y, jpeg_data)`

Display JPEG image from memory (hardware accelerated).

```python
display.blit_jpeg(x, y, jpeg_data)
```

**Parameters:**
- `x, y` (int): Top-left position for image
- `jpeg_data` (bytes): JPEG file data

**Returns:** None

**Performance:** Hardware JPEG decoder (ESP32-S3), very fast

**Requirements:**
- Standard JPEG format
- Any reasonable size supported
- Hardware decoding handles most JPEG variants

**Example:**
```python
# Load JPEG from file
with open("/sd/photo.jpg", "rb") as f:
    jpeg_data = f.read()

# Display at position (50, 50)
display.blit_jpeg(50, 50, jpeg_data)
display.swap_buffers()
```

---

### Image Loading Best Practices

**Memory Management:**
```python
import gc

# Load and display image
with open("/sd/image.jpg", "rb") as f:
    img_data = f.read()

display.blit_jpeg(0, 0, img_data)
display.swap_buffers()

# Free memory
del img_data
gc.collect()
```

**SD Card Access:**
```python
import espsdcard

# Mount SD card
sd = espsdcard.SDCard("/sd")

# Load image
with open("/sd/images/logo.bmp", "rb") as f:
    data = f.read()

display.blit_bmp(100, 100, data)
display.swap_buffers()

# Unmount
sd.deinit()
```

---

## Color System

### RGB565 Format

The RM690B0 display uses **RGB565** color format:
- **Red**: 5 bits (0-31)
- **Green**: 6 bits (0-63)
- **Blue**: 5 bits (0-31)
- **Total**: 16 bits (0x0000-0xFFFF)

### Color Conversion Helper

```python
def rgb565(r, g, b):
    """Convert RGB888 (0-255 each) to RGB565."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

# Example usage
red = rgb565(255, 0, 0)      # 0xF800
green = rgb565(0, 255, 0)    # 0x07E0
blue = rgb565(0, 0, 255)     # 0x001F
white = rgb565(255, 255, 255) # 0xFFFF
black = rgb565(0, 0, 0)       # 0x0000
```

### Common Colors

| Color | RGB565 | Hex Value |
|-------|--------|-----------|
| Black | 0, 0, 0 | 0x0000 |
| White | 31, 63, 31 | 0xFFFF |
| Red | 31, 0, 0 | 0xF800 |
| Green | 0, 63, 0 | 0x07E0 |
| Blue | 0, 0, 31 | 0x001F |
| Yellow | 31, 63, 0 | 0xFFE0 |
| Cyan | 0, 63, 31 | 0x07FF |
| Magenta | 31, 0, 31 | 0xF81F |
| Gray (50%) | 15, 31, 15 | 0x7BEF |
| Orange | 31, 32, 0 | 0xFC00 |
| Purple | 16, 0, 16 | 0x8010 |

### Color Utilities

```python
# Color constants (define once)
BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
YELLOW = 0xFFE0
CYAN = 0x07FF
MAGENTA = 0xF81F
GRAY = 0x7BEF

# Darken color (50%)
def darken(color):
    r = (color >> 11) & 0x1F
    g = (color >> 5) & 0x3F
    b = color & 0x1F
    return ((r >> 1) << 11) | ((g >> 1) << 5) | (b >> 1)

# Lighten color (add 50% white)
def lighten(color):
    r = min(31, ((color >> 11) & 0x1F) + 8)
    g = min(63, ((color >> 5) & 0x3F) + 16)
    b = min(31, (color & 0x1F) + 8)
    return (r << 11) | (g << 5) | b
```

---

## Performance Optimization

### Rendering Performance

**Benchmark Results:**
| Operation | Time | Notes |
|-----------|------|-------|
| Full screen fill | ~25 ms | Hardware limited by DMA |
| Circle (r=50) | ~2 ms | Optimized Bresenham |
| Text "Hello World" (16×16) | ~1.2 ms | Native font rendering |
| 100×100 rectangle | ~0.5 ms | DMA accelerated |
| Single pixel | ~0.001 ms | Direct framebuffer write |

### Optimization Tips

**1. Use `swap_buffers(copy=False)` for Full Redraws:**
```python
# Slower (unnecessary copy)
display.fill_color(0x0000)
display.text(10, 10, "Frame", 0xFFFF)
display.swap_buffers(copy=True)  # Wastes 3-5 ms

# Faster (no copy needed)
display.fill_color(0x0000)
display.text(10, 10, "Frame", 0xFFFF)
display.swap_buffers(copy=False)  # Saves 3-5 ms
```

**2. Batch Operations:**
```python
# Slower (multiple swap_buffers calls)
for i in range(10):
    display.fill_circle(i*50, 225, 20, 0xFFFF)
    display.swap_buffers()  # 10 swaps

# Faster (single swap)
for i in range(10):
    display.fill_circle(i*50, 225, 20, 0xFFFF)
display.swap_buffers()  # 1 swap
```

**3. Use Appropriate Primitives:**
```python
# Slower (generic line)
for x in range(100, 200):
    display.pixel(x, 100, 0xFFFF)

# Faster (optimized horizontal line)
display.hline(100, 100, 100, 0xFFFF)
```

**4. Pre-calculate Colors:**
```python
# Slower (calculate each frame)
for frame in range(1000):
    color = rgb565(255, frame % 256, 0)
    display.fill_circle(300, 225, 50, color)
    display.swap_buffers()

# Faster (pre-calculate palette)
colors = [rgb565(255, i, 0) for i in range(256)]
for frame in range(1000):
    display.fill_circle(300, 225, 50, colors[frame % 256])
    display.swap_buffers()
```

**5. Minimize Framebuffer Writes:**
```python
# Slower (redraw everything)
while True:
    display.fill_color(0x0000)
    display.fill_rect(0, 0, 600, 50, 0x001F)  # Header
    display.text(10, 15, "App Title", 0xFFFF)
    display.text(300, 200, f"Value: {value}", 0xFFFF)
    display.swap_buffers()

# Faster (only update changing parts with copy=True)
# Draw static elements once
display.fill_color(0x0000)
display.fill_rect(0, 0, 600, 50, 0x001F)
display.text(10, 15, "App Title", 0xFFFF)
display.swap_buffers()

# Update only dynamic parts
while True:
    display.text(300, 200, f"Value: {value}", 0xFFFF)
    display.swap_buffers(copy=True)  # Preserves static content
```

---

## Examples

### Example 1: Simple Status Display

```python
import rm690b0
import time

display = rm690b0.RM690B0()
display.init_display()

# Define colors
BG = 0x0000
HEADER_BG = 0x001F
TEXT = 0xFFFF
GOOD = 0x07E0
WARNING = 0xFFE0

# Draw static UI
display.fill_color(BG)
display.fill_rect(0, 0, 600, 60, HEADER_BG)
display.set_font(3)
display.text(20, 18, "System Monitor", TEXT)

# Draw status labels
display.set_font(1)
display.text(50, 100, "CPU Temperature:", TEXT)
display.text(50, 140, "Memory Free:", TEXT)
display.text(50, 180, "Uptime:", TEXT)

display.swap_buffers()

# Update dynamic values
while True:
    temp = 45  # Get actual temperature
    mem = 2048  # Get actual memory
    uptime = time.monotonic()
    
    # Update values (preserving static UI)
    display.set_font(1)
    
    # Clear old values
    display.fill_rect(300, 100, 250, 20, BG)
    display.fill_rect(300, 140, 250, 20, BG)
    display.fill_rect(300, 180, 250, 20, BG)
    
    # Draw new values
    color = GOOD if temp < 60 else WARNING
    display.text(300, 100, f"{temp}C", color)
    display.text(300, 140, f"{mem} KB", GOOD)
    
    hours = int(uptime // 3600)
    mins = int((uptime % 3600) // 60)
    display.text(300, 180, f"{hours}h {mins}m", TEXT)
    
    display.swap_buffers(copy=True)
    time.sleep(1)
```

### Example 2: Progress Bar

```python
import rm690b0
import time

display = rm690b0.RM690B0()
display.init_display()

def draw_progress(x, y, width, height, percent, color=0x07E0):
    """Draw a progress bar."""
    # Border
    display.rect(x, y, width, height, 0xFFFF)
    
    # Background
    display.fill_rect(x+2, y+2, width-4, height-4, 0x2104)
    
    # Progress
    prog_width = int((width-4) * percent / 100)
    if prog_width > 0:
        display.fill_rect(x+2, y+2, prog_width, height-4, color)
    
    # Percentage text
    display.set_font(1)
    text = f"{percent}%"
    text_x = x + width//2 - len(text)*8
    display.text(text_x, y + height//2 - 8, text, 0xFFFF)

# Demo
display.fill_color(0x0000)
display.set_font(3)
display.text(150, 50, "Loading...", 0xFFFF)

for i in range(0, 101, 5):
    draw_progress(100, 200, 400, 40, i)
    display.swap_buffers(copy=True)
    time.sleep(0.1)

display.set_font(3)
display.text(200, 300, "Complete!", 0x07E0)
display.swap_buffers(copy=True)
```

### Example 3: Analog Clock

```python
import rm690b0
import time
import math

display = rm690b0.RM690B0()
display.init_display()

def draw_clock(cx, cy, radius, hour, minute, second):
    """Draw an analog clock face."""
    # Clock face
    display.fill_circle(cx, cy, radius, 0x0000)
    display.circle(cx, cy, radius, 0xFFFF)
    
    # Hour marks
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = int(cx + (radius - 10) * math.cos(angle))
        y1 = int(cy + (radius - 10) * math.sin(angle))
        x2 = int(cx + (radius - 5) * math.cos(angle))
        y2 = int(cy + (radius - 5) * math.sin(angle))
        display.line(x1, y1, x2, y2, 0xFFFF)
    
    # Hour hand
    angle = math.radians((hour % 12) * 30 + minute * 0.5 - 90)
    x = int(cx + radius * 0.5 * math.cos(angle))
    y = int(cy + radius * 0.5 * math.sin(angle))
    display.line(cx, cy, x, y, 0xFFFF)
    
    # Minute hand
    angle = math.radians(minute * 6 - 90)
    x = int(cx + radius * 0.7 * math.cos(angle))
    y = int(cy + radius * 0.7 * math.sin(angle))
    display.line(cx, cy, x, y, 0x07E0)
    
    # Second hand
    angle = math.radians(second * 6 - 90)
    x = int(cx + radius * 0.8 * math.cos(angle))
    y = int(cy + radius * 0.8 * math.sin(angle))
    display.line(cx, cy, x, y, 0xF800)
    
    # Center dot
    display.fill_circle(cx, cy, 5, 0xFFFF)

# Main loop
while True:
    t = time.localtime()
    
    display.fill_color(0x0000)
    draw_clock(300, 225, 150, t.tm_hour, t.tm_min, t.tm_sec)
    
    # Digital time
    display.set_font(3)
    time_str = f"{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"
    display.text(220, 400, time_str, 0xFFFF)
    
    display.swap_buffers(copy=False)
    time.sleep(1)
```

### Example 4: Image Gallery

```python
import rm690b0
import espsdcard
import os

display = rm690b0.RM690B0()
display.init_display()

# Mount SD card
sd = espsdcard.SDCard("/sd")

# Get list of images
images = [f for f in os.listdir("/sd/images") 
          if f.endswith(('.jpg', '.jpeg', '.bmp'))]

current = 0

def show_image(filename):
    """Load and display an image."""
    display.fill_color(0x0000)
    
    with open(f"/sd/images/{filename}", "rb") as f:
        data = f.read()
    
    if filename.endswith('.bmp'):
        display.blit_bmp(50, 50, data)
    else:
        display.blit_jpeg(50, 50, data)
    
    # Show filename
    display.set_font(1)
    display.text(10, 10, filename, 0xFFFF, 0x0000)
    
    display.swap_buffers()
    del data

# Show first image
if images:
    show_image(images[current])
    print("Touch screen to advance (simulated with time delay)")
    
    # Auto-advance for demo
    import time
    while True:
        time.sleep(3)
        current = (current + 1) % len(images)
        show_image(images[current])
```

---

## Implementation Details

### DMA Architecture

**30-Line Limit:**
- Hardware DMA supports maximum 30 lines per transfer
- Full screen (450 lines) requires 15 DMA operations
- Driver automatically chunks large operations

**Alignment Requirements:**
- DMA buffers must be even-pixel aligned
- Driver adds internal padding automatically
- No user action required

**Color Format:**
- RGB565 with automatic GB byte swapping
- Hardware quirk handled by driver
- Users work with standard RGB565 values

### Framebuffer Management

**Double Buffering:**
```
PSRAM Layout:
┌──────────────────────────────┐
│  Front Buffer (540 KB)       │  ← Currently displayed
├──────────────────────────────┤
│  Back Buffer (540 KB)        │  ← Being drawn to
└──────────────────────────────┘
```

**swap_buffers() Operation:**
1. Pointer swap (instant)
2. Optional copy front→back (~3-5 ms if copy=True)
3. New frame ready for drawing

### Text Rendering Engine

**Font Format:**
- Row-based bitmap (horizontal scan)
- MSB = leftmost pixel
- 1 bit per pixel (monochrome)
- Byte-aligned rows

**Rendering Process:**
1. UTF-8 decode → codepoint
2. Map codepoint → font glyph
3. Blit glyph to framebuffer
4. Advance cursor by character width

---

## Troubleshooting

### Issue: Display Shows Nothing

**Symptoms:** Black screen after initialization

**Causes & Solutions:**
1. **Forgot `init_display()`:**
   ```python
   display = rm690b0.RM690B0()
   display.init_display()  # ← Must call this!
   ```

2. **Forgot `swap_buffers()`:**
   ```python
   display.fill_color(0xFFFF)
   display.swap_buffers()  # ← Must swap to see changes!
   ```

3. **Brightness set to 0:**
   ```python
   display.brightness = 1.0  # Full brightness
   ```

---

### Issue: Colors Look Wrong

**Symptoms:** Colors appear swapped or incorrect

**Cause:** RGB565 format confusion

**Solution:** Use RGB565 format correctly
```python
# Wrong (RGB888)
display.fill_color(255, 0, 0)  # ERROR

# Correct (RGB565)
def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

RED = rgb565(255, 0, 0)  # 0xF800
display.fill_color(RED)  # Correct
```

---

### Issue: Text Not Visible

**Symptoms:** `text()` called but nothing appears

**Causes & Solutions:**
1. **Forgot `set_font()`:**
   ```python
   display.set_font(1)  # ← Select font first
   display.text(10, 10, "Hello", 0xFFFF)
   ```

2. **Color matches background:**
   ```python
   # Won't see white text on white background
   display.fill_color(0xFFFF)
   display.text(10, 10, "Hello", 0xFFFF)  # Invisible!
   
   # Solution: use contrasting color
   display.text(10, 10, "Hello", 0x0000)  # Black on white
   ```

3. **Text rendered off-screen:**
   ```python
   # Check coordinates are within bounds
   display.text(700, 10, "Hello", 0xFFFF)  # x=700 is off-screen!
   ```

---

### Issue: Slow Performance

**Symptoms:** Low frame rate, laggy updates

**Solutions:**

1. **Use `copy=False` for full redraws:**
   ```python
   display.fill_color(0x0000)
   display.swap_buffers(copy=False)  # Faster
   ```

2. **Batch drawing operations:**
   ```python
   # Draw everything, then swap once
   for i in range(10):
       display.circle(i*50, 225, 20, 0xFFFF)
   display.swap_buffers()  # Single swap
   ```

3. **Profile your code:**
   ```python
   import time
   start = time.monotonic()
   # ... drawing operations ...
   elapsed = time.monotonic() - start
   print(f"Frame time: {elapsed*1000:.1f} ms")
   ```

---

### Issue: Memory Errors

**Symptoms:** `MemoryError` when loading images

**Causes & Solutions:**
1. **Image too large:**
   ```python
   import gc
   
   # Load image
   with open("image.jpg", "rb") as f:
       data = f.read()
   
   display.blit_jpeg(0, 0, data)
   
   # Free memory immediately
   del data
   gc.collect()
   ```

2. **Multiple images in memory:**
   ```python
   # Don't do this
   img1 = open("a.jpg", "rb").read()
   img2 = open("b.jpg", "rb").read()
   img3 = open("c.jpg", "rb").read()
   
   # Do this instead
   def show_image(path):
       with open(path, "rb") as f:
           data = f.read()
       display.blit_jpeg(0, 0, data)
       del data
       gc.collect()
   ```

---

### Getting Help

**Documentation:**
- `TECHNICAL_NOTES.md` - Detailed technical information
- `RM690B0_LVGL.md` - LVGL integration guide
- `project_status_summary.md` - Project status and known issues

**Test Scripts:**
- `test_scripts/` directory contains examples
- Try running included test scripts for verification

**Common Patterns:**
- Check examples in this document
- Reference `flappy_bird_clone.py` and `snake_game.py` for real-world usage

---

## Summary

The **RM690B0 driver** provides:

✅ **Production-ready** standalone display driver  
✅ **High performance** with DMA acceleration  
✅ **Simple API** (~15 core methods)  
✅ **Native text** with 7 built-in fonts  
✅ **Image support** (BMP + hardware JPEG)  
✅ **Complete graphics** primitives  
✅ **Zero dependencies** (works without LVGL)

**Perfect for:**
- Games (see `flappy_bird_clone.py`, `snake_game.py`)
- Dashboards and status displays
- Data visualization
- Simple UIs without heavy frameworks
- Performance-critical applications

**Choose RM690B0 driver when you need:**
- Fast, lightweight rendering
- Direct framebuffer control
- Simple graphics and text
- No LVGL complexity

**Choose RM690B0_LVGL when you need:**
- Rich UI widgets
- TTF font support
- Complex layouts
- Interactive elements
