# RM690B0 Display Driver - Complete Guide

> **Status (2026-03-06, branch `display-list`):**
> This document is current for the standalone `rm690b0` driver.
> Driver supports both `FRAMEBUFFER` and `DISPLAY_LIST` render backends with runtime switching (`render_mode`).

### DISPLAY_LIST Backend Status (2026-03-06)

- DL hardening is closed for the current v1 baseline.
- Final defaults: `GLYPH_ATLAS_SLOTS=40`, `AUTO_COMPACT_EVERY_N_FRAMES=24`, `MIN_COMMANDS=64`, `GUARD_COMMANDS=3400`, `GUARD_PAYLOAD_BYTES=512 KiB`.
- `BUFFER_SINGLE` is the recommended default for DL.
- The driver still tries to allocate a second static DMA chunk buffer in single mode (best-effort), enabling ping-pong overlap when memory allows.
- Mixed drawing (`FRAMEBUFFER` + `DISPLAY_LIST` in one frame) remains intentionally unsupported.
- LVGL uses a dedicated path (`rm690b0_lvgl`), not rm690b0 DISPLAY_LIST replay.

### FRAMEBUFFER Backend Status (2026-03-06)

- `swap_buffers(copy=True)` dirty-copy baseline is stable and remains enabled.
- Accepted in latest tuning loop: unswapped BLIT span helper optimization in `blit_buffer` (FB path).
- Reverted after measured regression: aggressive dirty coalescing policy variant in `RM690B0.c` (drop in retained BLIT scenario).
- Current benchmark script `benchmark_fb_profile.py` no longer raises EOF `NameError` (stray token removed).

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
11. [DMA Memory Management](#dma-memory-management)
12. [Examples](#examples)
13. [Implementation Details](#implementation-details)
14. [Troubleshooting](#troubleshooting)

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

| Component              | Specification                     |
| ---------------------- | --------------------------------- |
| **Display Controller** | RM690B0 AMOLED                    |
| **Resolution**         | 600×450 pixels (landscape)        |
| **Interface**          | QSPI (Quad SPI)                   |
| **Color Format**       | RGB565 (16-bit)                   |
| **Clock Speed**        | 80 MHz                            |
| **Framebuffer**        | 540 KB in PSRAM (double buffered) |
| **DMA Limit**          | 30 lines per transfer             |
| **MCU**                | ESP32-S3                          |

---

## Architecture

### System Overview

```text
┌────────────────────────────────────────────────────┐
│             Python Application                     │
├────────────────────────────────────────────────────┤
│              rm690b0 Module (CircuitPython)        │
│  • init_display()     • fill_rect()                │
│  • set_font()         • line()                     │
│  • text()             • circle()                   │
│  • swap_buffers()     • rect()                     │
├────────────────────────────────────────────────────┤
│           C Driver (common-hal/rm690b0/)           │
│  RM690B0.c       — Core, DMA, flush, properties    │
│  rm690b0_draw.c  — Primitives (rect, line, circle) │
│  rm690b0_text.c  — Font rendering (7 fonts)        │
│  rm690b0_image.c — BMP/JPEG decoders               │
│  rm690b0_internal.h — Shared header & inline helpers│
├────────────────────────────────────────────────────┤
│              ESP-IDF LCD Component                 │
│  • esp_lcd_rm690b0.c (panel driver)                │
│  • QSPI Communication                              │
│  • Hardware Acceleration                           │
├────────────────────────────────────────────────────┤
│                  ESP32-S3 Hardware                 │
│  • PSRAM (framebuffer storage)                     │
│  • DMA (transfer engine)                           │
│  • JPEG Decoder (hardware accelerated)             │
│  • QSPI Peripheral                                 │
└────────────────────────────────────────────────────┘
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

- **CircuitPython**: 10.1.3
- **Build**: Custom build with RM690B0 support
- **Module**: `rm690b0` (built-in)

### Module Availability

The `rm690b0` module is available on compatible CircuitPython builds:

```python
import rm690b0  # ✅ Available on ESP32-S3 with RM690B0 display
```

---

## Quick Start

### Minimal Example

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
display.text(50, 200, "Hello, World!", color=rm690b0.WHITE)

# Show on screen
display.swap_buffers()
```

### Graphics Example

```python
import rm690b0

display = rm690b0.RM690B0()
display.init_display()

# Blue background
display.fill_color(rm690b0.BLUE)

# White rectangle
display.rect(50, 50, 200, 100, color=rm690b0.WHITE)

# Filled red circle
display.fill_circle(400, 225, 50, color=rm690b0.RED)

# Yellow line
display.line(0, 0, 600, 450, color=rm690b0.YELLOW)

# Update display
display.swap_buffers()
```

---

## Python API Reference

### Class: `RM690B0`

Main display driver class providing graphics, text, and image rendering.

#### Constructor

```python
display = rm690b0.RM690B0(*, buffer_mode=rm690b0.BUFFER_DOUBLE)
```

Creates a new RM690B0 display instance. Only one instance should exist at a time.

**Parameters:**

- `buffer_mode` (int, keyword-only, optional): Selects the framebuffer allocation strategy.
  - `rm690b0.BUFFER_DOUBLE` *(default)* — allocates a second 540 KB front buffer in SPIRAM on the
    first `swap_buffers()` call; provides tear-free animation via pointer swap.
  - `rm690b0.BUFFER_SINGLE` — uses only one framebuffer (540 KB); the front buffer is **never**
    allocated, saving ~540 KB of SPIRAM. `swap_buffers()` flushes dirty regions tracked since the
    last call, or the full screen if no dirty regions are recorded. Drawing calls in this mode
    update only the framebuffer/dirty map; visible refresh happens on `swap_buffers()`.
    Recommended for static UI / dashboard applications.

**Example:**

```python
import rm690b0

# Default: double-buffered (backward compatible)
display = rm690b0.RM690B0()

# Explicit double-buffered
display = rm690b0.RM690B0(buffer_mode=rm690b0.BUFFER_DOUBLE)

# Single-buffered: saves ~540 KB of SPIRAM
display = rm690b0.RM690B0(buffer_mode=rm690b0.BUFFER_SINGLE)
```

---

#### Buffer Mode Constants

| Constant               | Value | Description                                              |
| ---------------------- | ----- | -------------------------------------------------------- |
| `rm690b0.BUFFER_SINGLE` | `0`  | Single framebuffer — dirty-tracked flush, saves 540 KB  |
| `rm690b0.BUFFER_DOUBLE` | `1`  | Double framebuffer — tear-free animation (default)       |

**Choosing the right mode:**

| Use case                         | Recommended mode  |
| -------------------------------- | ----------------- |
| Animations, games, smooth motion | `BUFFER_DOUBLE`   |
| Static UI, dashboards, text      | `BUFFER_SINGLE`   |
| Memory-constrained applications  | `BUFFER_SINGLE`   |

**Memory usage:**

- `BUFFER_DOUBLE`: ~1080 KB SPIRAM (back buffer + front buffer)
- `BUFFER_SINGLE`: ~540 KB SPIRAM (back buffer only)

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

- **BUFFER_DOUBLE + `copy=True`**: Pointer swap + dirty-copy front→back (incremental updates).
- **BUFFER_DOUBLE + `copy=False`**: Pointer swap without copy (best for full redraw loops).
- **BUFFER_SINGLE**: No front/back pointer swap. `swap_buffers()` flushes accumulated dirty regions
  (or full screen when no dirty rects are present). `copy` has no practical effect in this mode.

**Performance:**

- `BUFFER_DOUBLE`: swap path is dominated by display DMA and optional copy cost.
- `BUFFER_SINGLE`: draw calls are cheap (deferred flush), and frame cost moves to `swap_buffers()`.
  Batch drawing work, then call one `swap_buffers()` per frame/tick.

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

##### `rotation`

Get or set display rotation.

```python
rotation = display.rotation  # 0
```

**Type:** `int`  
**Value:** `0`, `90`, `180`, `270`

**Note:** Hardware rotation is set to 0. This property controls software-based rotation for drawing operations (pixels, lines, rects, text, images). Optimized with loop unrolling and pointer arithmetic for high performance.

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
# Example usage:
# Draw a progress bar at 75%
# Background (gray)
display.fill_rect(50, 200, 500, 30, 0x7BEF)
# Progress (green)
width = int(500 * 75 / 100)
display.fill_rect(50, 200, width, 30, 0x07E0)
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
- ✅ **Batch Rendering**: Calculates full bounding box and flushes once per string for maximum performance.

### Built-in Fonts

| ID  | Size  | Style                | Memory | Best For                 |
| --- | ----- | -------------------- | ------ | ------------------------ |
| 0   | 8×8   | Liberation Mono Bold | 760 B  | Tiny text, debug, status |
| 1   | 16×16 | Liberation Mono Bold | 30 KB  | Body text, labels        |
| 2   | 16×24 | Liberation Mono Bold | 45 KB  | Code, monospace text     |
| 3   | 24×24 | Liberation Mono Bold | 68 KB  | Headings, emphasis       |
| 4   | 24×32 | Liberation Mono Bold | 91 KB  | Large headings           |
| 5   | 32×32 | Liberation Mono Bold | 121 KB | Display text             |
| 6   | 32×48 | Liberation Mono Bold | 182 KB | Very large text          |

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
display.text(10, 10, "Hello, World!", color=rm690b0.WHITE)

# Colored text with solid background
display.text(10, 50, "Warning!", color=rm690b0.BLACK, background=rm690b0.YELLOW)

# Status text (small font)
display.set_font(0)
display.text(10, 430, f"FPS: 60  Temp: 25C", color=rm690b0.GREEN)

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

# Initialize display
display = rm690b0.RM690B0()
display.init_display()

display.fill_color(rm690b0.BLACK)  # Black

# Title (large)
display.set_font(3)  # 24×24
display.text(50, 20, "System Status", color=rm690b0.WHITE)

# Body (medium)
display.set_font(1)  # 16×16
display.text(50, 80, "CPU: 45%", color=rm690b0.GREEN)
display.text(50, 110, "Memory: 2.1 MB free", color=rm690b0.GREEN)
display.text(50, 140, "Temperature: 25C", color=rm690b0.GREEN)

# Footer (small)
display.set_font(0)  # 8×8
display.text(10, 430, "v1.0.0 | Uptime: 3h 24m", color=rm690b0.GRAY)

display.swap_buffers()
```

**Colored Labels:**

```python
def show_status(display, msg, status):
    """Show status message with color coding."""
    display.fill_color(rm690b0.BLACK)
    display.set_font(1)

    if status == "error":
        color = rm690b0.RED
        bg = 0x1800     # Dark red
    elif status == "warning":
        color = rm690b0.BLACK
        bg = rm690b0.YELLOW
    elif status == "success":
        color = rm690b0.WHITE
        bg = rm690b0.GREEN
    else:
        color = rm690b0.WHITE
        bg = None       # Transparent

    display.text(50, 200, msg, color=color, background=bg)
    display.swap_buffers()

# Example usage:
# display = rm690b0.RM690B0()
# display.init_display()
# show_status(display, "Connected!", "success")
```

---

## Image Support

### Overview

The RM690B0 driver supports loading and displaying BMP and JPEG images.

**Supported Formats:**

- ✅ BMP: 24-bit RGB (converted to 16-bit RGB565 via `convert_bmp`)
- ✅ JPEG: Hardware-accelerated decoding (via `jpegio`)

### `convert_bmp(bmp_data, destination_bitmap)`

Converts 24-bit BMP data to a 16-bit RGB565 `displayio.Bitmap` in-place, handling necessary byte swapping for optimal display performance.

```python
display.convert_bmp(bmp_data, bitmap)
```

**Parameters:**

- `bmp_data` (bytes): Source BMP file data (header + pixels).
- `destination_bitmap` (displayio.Bitmap): Destination bitmap of correct size (width, height, 65535 colors).

**Performance:**

- optimized C implementation
- Performs 24-bit → 16-bit conversion
- Applies Big-Endian byte swapping directly for DMA readiness

**Example:**

```python
# Load BMP data
with open("/sd/image.bmp", "rb") as f:
    data = f.read()

# Create destination bitmap
bitmap = displayio.Bitmap(width, height, 65535)

# Convert
display.convert_bmp(data, bitmap)

# Display (note dest_is_swapped=True)
display.blit_buffer(x, y, width, height, bitmap, dest_is_swapped=True)
```

### `blit_buffer(x, y, width, height, buffer, dest_is_swapped=False, transparent_color=-1, src_x1=0, src_y1=0, src_x2=-1, src_y2=-1)`

Enhanced blit function supporting pre-swapped data, transparency, and source region selection.

**Parameters:**

- `x, y` (int): Destination coordinates on screen
- `width, height` (int): Dimensions of source bitmap
- `buffer` (bytes/bytearray): Source bitmap data (RGB565 format)
- `dest_is_swapped` (bool, optional): If `True`, data is assumed to be Big-Endian (display native) and will NOT be swapped. Use this for `convert_bmp` results and JPEG decoded data. Default: `False`
- `transparent_color` (int, optional): RGB565 color value to skip (treat as transparent). Range: 0x0000-0xFFFF. Use -1 for no transparency. Default: `-1`
- `src_x1, src_y1` (int, optional): Top-left corner of source region. Default: `0, 0`
- `src_x2, src_y2` (int, optional): Bottom-right corner of source region (exclusive). Use -1 for full width/height. Default: `-1, -1`

**Sprite Blitting with Transparency:**

The `transparent_color` parameter enables efficient sprite rendering:

```python
# Pre-render ball sprite once (44×44 with black background)
sprite_w = 44
sprite_h = 44
sprite_data = bytearray(sprite_w * sprite_h * 2)  # RGB565

# Render sprite primitives into sprite_data
# (black background = 0x0000)
# ... draw_circle, fill_circle, etc ...

# Blit sprite with transparency in animation loop
while True:
    # Update position
    x += vx
    y += vy

    # Blit sprite, skipping black (0x0000) pixels
    display.blit_buffer(x, y, sprite_w, sprite_h, sprite_data,
                        transparent_color=0x0000)
    display.swap_buffers()
```

**Source Region Selection:**

Copy only a portion of the source bitmap:

```python
# Large sprite sheet: 100×100
sprite_sheet = bytearray(100 * 100 * 2)

# Blit only 20×20 region from (40, 60) to (60, 80)
display.blit_buffer(x, y, 100, 100, sprite_sheet,
                    src_x1=40, src_y1=60,
                    src_x2=60, src_y2=80)
```

**Performance:**

- **Without transparency**: Same speed as before (memcpy fast path when `dest_is_swapped=True`)
- **With transparency**: ~10-20% slower per pixel (still 100-1000× faster than Python)
- **Pre-rendered sprites**: One-time cost at startup, then fast blit every frame

---

### JPEG Support

JPEG decoding is handled via the separate `jpegio` module, which utilizes the ESP32-S3 hardware decoder.

**Example:**

```python
import jpegio
import displayio

decoder = jpegio.JpegDecoder()
width, height = decoder.open("/sd/image.jpg")
bitmap = displayio.Bitmap(width, height, 65535)
decoder.decode(bitmap)

# Display (JPEG decoder outputs Big-Endian on ESP32-S3)
display.blit_buffer(x, y, width, height, bitmap, dest_is_swapped=True)
```

---

### Pre-rendered Sprites for Games

Pre-rendering sprites once and blitting with transparency provides optimal performance for game animations.

**Benefits:**

- ✅ Render complex graphics (gradients, anti-aliasing, effects) once at startup
- ✅ Fast per-frame blitting with transparency (~0.1-0.2 ms per sprite)
- ✅ No need to redraw primitives every frame
- ✅ Smooth animations at 500-1000 FPS

**Example: Ball Sprite with Shine and Shadow**

```python
import rm690b0
import math

display = rm690b0.RM690B0()
display.init_display()

def pre_render_ball_sprite(radius, color):
    """Pre-render a ball sprite with shine effect."""
    size = radius * 2 + 4  # +4 for 2px padding
    sprite_data = bytearray(size * size * 2)  # RGB565

    # Create temporary buffer view (16-bit little-endian)
    import struct

    def set_pixel(x, y, rgb565):
        """Set pixel in sprite buffer."""
        if 0 <= x < size and 0 <= y < size:
            idx = (y * size + x) * 2
            # Store as little-endian (Python native)
            sprite_data[idx] = rgb565 & 0xFF
            sprite_data[idx + 1] = (rgb565 >> 8) & 0xFF

    # Fill background with black (transparent color)
    for y in range(size):
        for x in range(size):
            set_pixel(x, y, 0x0000)

    # Draw filled circle (main ball)
    cx, cy = size // 2, size // 2
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            if dx*dx + dy*dy <= radius*radius:
                set_pixel(x, y, color)

    # Add shine effect (white highlight)
    shine_x = cx - radius // 3
    shine_y = cy - radius // 3
    shine_radius = radius // 4
    for y in range(size):
        for x in range(size):
            dx = x - shine_x
            dy = y - shine_y
            if dx*dx + dy*dy <= shine_radius*shine_radius:
                set_pixel(x, y, 0xFFFF)  # White

    # Add shadow effect (darker edge)
    shadow_color = darken_color(color, 0.5)
    for angle_deg in range(0, 360, 5):
        angle = math.radians(angle_deg)
        for r in range(radius - 2, radius + 1):
            x = int(cx + r * math.cos(angle))
            y = int(cy + r * math.sin(angle))
            if 0 <= x < size and 0 <= y < size:
                set_pixel(x, y, shadow_color)

    return sprite_data, size, size

def darken_color(rgb565, factor):
    """Darken RGB565 color by factor (0.0-1.0)."""
    r = int(((rgb565 >> 11) & 0x1F) * factor)
    g = int(((rgb565 >> 5) & 0x3F) * factor)
    b = int((rgb565 & 0x1F) * factor)
    return (r << 11) | (g << 5) | b

# Pre-render ball sprite ONCE
ball_radius = 20
ball_color = 0xF800  # Red
sprite_data, sprite_w, sprite_h = pre_render_ball_sprite(ball_radius, ball_color)

# Animation loop - high FPS
x, y = 100, 100
vx, vy = 2, 3
BLACK = 0x0000

while True:
    # Clear screen
    display.fill_color(BLACK)

    # Update position
    x += vx
    y += vy

    # Bounce off walls
    if x < 0 or x > 600 - sprite_w:
        vx = -vx
    if y < 0 or y > 450 - sprite_h:
        vy = -vy

    # Blit sprite with transparency (skip black background)
    display.blit_buffer(x, y, sprite_w, sprite_h, sprite_data,
                        transparent_color=0x0000)

    display.swap_buffers(copy=False)
```

**Expected Performance:** 500-1000 FPS with smooth animation.

---

### Sprite Sheets for Multiple Sprites

For games with multiple sprites, use a sprite sheet:

```python
# Create sprite sheet: 4 sprites, 32×32 each, arranged in 2×2 grid
SPRITE_SIZE = 32
SHEET_W = 64
SHEET_H = 64
sprite_sheet = bytearray(SHEET_W * SHEET_H * 2)

# Pre-render all sprites into sheet
# ... render sprite 0 at (0, 0)
# ... render sprite 1 at (32, 0)
# ... render sprite 2 at (0, 32)
# ... render sprite 3 at (32, 32)

# Blit individual sprite from sheet
sprite_id = 2  # Third sprite
sprite_x = (sprite_id % 2) * SPRITE_SIZE
sprite_y = (sprite_id // 2) * SPRITE_SIZE

display.blit_buffer(x, y, SHEET_W, SHEET_H, sprite_sheet,
                    transparent_color=0x0000,
                    src_x1=sprite_x, src_y1=sprite_y,
                    src_x2=sprite_x + SPRITE_SIZE, src_y2=sprite_y + SPRITE_SIZE)
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
import board
import sdioio
import storage

# Mount SD card
sd = sdioio.SDCard(
    clock=board.SDIO_CLK,
    command=board.SDIO_CMD,
    data=[board.SDIO_D0],
    frequency=40_000_000
)
vfs = storage.VfsFat(sd)
storage.mount(vfs, "/sd")

# Load image
with open("/sd/images/logo.bmp", "rb") as f:
    data = f.read()

display.blit_bmp(100, 100, data)
display.swap_buffers()

# Note: Unmounting is not typically needed in main loop
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
    """Convert RGB888 (0-255) to RGB565 format."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

# Example usage
red = rgb565(255, 0, 0)      # 0xF800
green = rgb565(0, 255, 0)    # 0x07E0
blue = rgb565(0, 0, 255)     # 0x001F
white = rgb565(255, 255, 255) # 0xFFFF
black = rgb565(0, 0, 0)       # 0x0000
```

### Common Colors

| Color      | RGB565     | Hex Value |
| ---------- | ---------- | --------- |
| Black      | 0, 0, 0    | 0x0000    |
| White      | 31, 63, 31 | 0xFFFF    |
| Red        | 31, 0, 0   | 0xF800    |
| Green      | 0, 63, 0   | 0x07E0    |
| Blue       | 0, 0, 31   | 0x001F    |
| Yellow     | 31, 63, 0  | 0xFFE0    |
| Cyan       | 0, 63, 31  | 0x07FF    |
| Magenta    | 31, 0, 31  | 0xF81F    |
| Gray (50%) | 15, 31, 15 | 0x7BEF    |
| Orange     | 31, 32, 0  | 0xFC00    |
| Purple     | 16, 0, 16  | 0x8010    |

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

| Operation          | Time      | Notes                                                      |
| ------------------ | --------- | ---------------------------------------------------------- |
| Full screen fill   | ~25–34 ms | Hardware limited by DMA, both single/double buffer tracked |
| Full-width fill    | ~5 ms     | Exercises partial-height DMA path                          |
| 64 px column fill  | ~6 ms     | Stresses narrow-span cache/fill loop                       |
| Circle (r=50)      | ~2 ms     | Optimized Bresenham (with span cache)                      |
| Text "Hello World" | ~1.2 ms   | Native font rendering                                      |
| 100×100 rectangle  | ~0.5 ms   | DMA accelerated                                            |
| Single pixel       | ~0.001 ms | Direct framebuffer write                                   |

**Targeted benchmarks (`examples/benchmark_simple_flush.py`):**

- Runs in both single- and double-buffer modes so regressions in swap/buffer sync are obvious.
- Adds two extra rectangle tests (full width × 64 rows, narrow 64‑px column) to cover the optimized fill loops.
- Includes circle/fill_circle runs to monitor the new span cache and clipping paths.

**Automated FB regression gate (`examples/benchmark_gfx/compare_fb_profile.py`):**

- Checks 3 key scenarios against fixed thresholds:
  - `fb_single_rebuild / primitive_stress`
  - `fb_double_rebuild / full_redraw_control`
  - `fb_double_retained / retained_blit_transparent`
- Handles incomplete `scenario_end` windows by falling back to the last `sample` row.
- Returns non-zero exit code on regression (`FAIL`), so it can be used in CI/hooks.

```bash
python examples/benchmark_gfx/compare_fb_profile.py \
  --csv examples/benchmark_gfx/fb_profile.csv
```

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

## DMA Memory Management

To prevent heap fragmentation and ensure stability:

- **Dynamic Buffer Allocation**: The driver attempts to allocate static DMA buffers (`chunk_buffers`) at initialization. It prioritizes internal memory, then PSRAM, and adaptively reduces buffer size if allocation fails.
- **Adaptive Flushing**: Rendering operations respect the actual size of the allocated static buffers, avoiding fallback to slow and fragmentation-prone `heap_caps_malloc` for every frame.

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

def draw_progress(x, y, width, height, percent, color=rm690b0.GREEN):
    """Draw a progress bar."""
    # Border
    display.rect(x, y, width, height, rm690b0.WHITE)

    # Background
    display.fill_rect(x+2, y+2, width-4, height-4, 0x2104)  # Dark gray

    # Progress
    prog_width = int((width-4) * percent / 100)
    if prog_width > 0:
        display.fill_rect(x+2, y+2, prog_width, height-4, color)

    # Percentage text
    display.set_font(1)
    text = f"{percent}%"
    text_x = x + width//2 - len(text)*8
    display.text(text_x, y + height//2 - 8, text, rm690b0.WHITE)

# Demo
display.fill_color(rm690b0.BLACK)
display.set_font(3)
display.text(150, 50, "Loading...", rm690b0.WHITE)

for i in range(0, 101, 5):
    draw_progress(100, 200, 400, 40, i)
    display.swap_buffers(copy=True)
    time.sleep(0.1)

display.set_font(3)
display.text(200, 300, "Complete!", rm690b0.GREEN)
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
    display.fill_circle(cx, cy, radius, rm690b0.BLACK)
    display.circle(cx, cy, radius, rm690b0.WHITE)

    # Hour marks
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = int(cx + (radius - 10) * math.cos(angle))
        y1 = int(cy + (radius - 10) * math.sin(angle))
        x2 = int(cx + (radius - 5) * math.cos(angle))
        y2 = int(cy + (radius - 5) * math.sin(angle))
        display.line(x1, y1, x2, y2, rm690b0.WHITE)

    # Hour hand
    angle = math.radians((hour % 12) * 30 + minute * 0.5 - 90)
    x = int(cx + radius * 0.5 * math.cos(angle))
    y = int(cy + radius * 0.5 * math.sin(angle))
    display.line(cx, cy, x, y, rm690b0.WHITE)

    # Minute hand
    angle = math.radians(minute * 6 - 90)
    x = int(cx + radius * 0.7 * math.cos(angle))
    y = int(cy + radius * 0.7 * math.sin(angle))
    display.line(cx, cy, x, y, rm690b0.GREEN)

    # Second hand
    angle = math.radians(second * 6 - 90)
    x = int(cx + radius * 0.8 * math.cos(angle))
    y = int(cy + radius * 0.8 * math.sin(angle))
    display.line(cx, cy, x, y, rm690b0.RED)

    # Center dot
    display.fill_circle(cx, cy, 5, rm690b0.WHITE)

# Main loop
while True:
    t = time.localtime()

    display.fill_color(rm690b0.BLACK)
    draw_clock(300, 225, 150, t.tm_hour, t.tm_min, t.tm_sec)

    # Digital time
    display.set_font(3)
    time_str = f"{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"
    display.text(220, 400, time_str, rm690b0.WHITE)

    display.swap_buffers(copy=False)
    time.sleep(1)
```

### Example 4: Image Gallery

```python
import rm690b0
import os
import time

import board
import sdioio
import storage

display = rm690b0.RM690B0()
display.init_display()

# Mount SD card
sd = sdioio.SDCard(
    clock=board.SDIO_CLK,
    command=board.SDIO_CMD,
    data=[board.SDIO_D0],
    frequency=40_000_000
)
vfs = storage.VfsFat(sd)
storage.mount(vfs, "/sd")

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
        # For BMP: Read data, convert, and blit
        # (Assuming dimensions are known or parsed - simplified for example)
        # In real usage, parse header or hardcode size
        w, h = 600, 450 
        bitmap = displayio.Bitmap(w, h, 65535)
        display.convert_bmp(data, bitmap)
        display.blit_buffer(50, 50, w, h, bitmap, dest_is_swapped=True)
    else:
        # For JPEG: Use generic jpegio
        import jpegio
        decoder = jpegio.JpegDecoder()
        w, h = decoder.open(f"/sd/images/{filename}")
        bitmap = displayio.Bitmap(w, h, 65535)
        decoder.decode(bitmap)
        display.blit_buffer(50, 50, w, h, bitmap, dest_is_swapped=True)

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

```text
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
# Use the rgb565() helper function defined earlier
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
   def show_image(display, path):
       with open(path, 'rb') as f:
           data = f.read()
       display.blit_jpeg(0, 0, data)
       display.swap_buffers()
       del data
       gc.collect()
   ```

---

### Issue: RuntimeError 0x101 (ESP_ERR_NO_MEM)

**Symptoms:** `RuntimeError: Failed to refresh display: UNKNOWN ERROR (0x101)`

**Root Cause:** DMA memory allocation failure during display transfer

**What's Happening:**
The ESP32-S3 has limited DMA-capable internal RAM (~400 KB). When the display driver needs to flush regions to the screen, it allocates a temporary buffer from DMA memory. If this memory is fragmented or exhausted, the allocation fails with error 0x101.

**Common Triggers:**

- Complex games with many draw operations
- Frequent full-screen updates
- Memory-intensive Python code running alongside display updates
- Multiple large allocations without garbage collection

**Solutions:**

1. **Add garbage collection before display updates:**

   ```python
   import gc

   def game_loop():
       gc.collect()  # Free Python heap
       # ... drawing operations ...
       display.swap_buffers()
       gc.collect()  # Clean up after frame
   ```

2. **Batch drawing operations:**

   ```python
   # Inefficient - many small operations
   for tile in tiles:
       display.fill_rect(tile.x, tile.y, 16, 16, tile.color)

   # Better - minimize Python→C calls
   display.fill_rect(x, y, width, height, color)  # One large call
   ```

3. **Avoid premature buffer activation:**

   ```python
   # Don't do this
   display.init_display()
   display.swap_buffers()  # ← BAD: activates buffers too early

   # Do this
   display.init_display()
   # Let first frame initialize buffers naturally
   ```

4. **Reduce memory pressure:**

   ```python
   # Pre-allocate reusable objects
   class Game:
       def __init__(self):
           self.temp_buffer = bytearray(1000)  # Reuse this

       def update(self):
           # Use self.temp_buffer instead of creating new ones
           pass
   ```

**Driver-Level Fix (Firmware):**
The driver has been optimized to use smaller DMA chunks (23.4 KB instead of 58.6 KB), which significantly reduces the likelihood of this error. If you're building custom firmware, ensure the following setting in `RM690B0.c`:

```c
#define RM690B0_MAX_CHUNK_PIXELS (LCD_H_RES * 20)  // 20 lines
```

**Verification Test:**

```python
import rm690b0
import gc
import time

display = rm690b0.RM690B0()
display.init_display()

# Stress test - 500 frames with alternating patterns
errors = 0
for frame in range(500):
    try:
        gc.collect()
        if frame % 2 == 0:
            display.fill_color(0x0000)
        else:
            for i in range(20):
                x = (frame * 10 + i * 30) % 600
                y = (frame * 5 + i * 20) % 450
                display.fill_rect(x, y, 50, 50, 0xFFFF)
        display.swap_buffers()
    except RuntimeError as e:
        if "0x101" in str(e):
            errors += 1
            print(f"Frame {frame}: 0x101 error!")

print(f"Completed 500 frames, {errors} errors")
# Expected: 0 errors with optimized driver
```

**Performance Impact:**
The driver optimization has minimal performance impact (~0.7ms per full-screen flush), which is negligible for typical applications.

**Further Reading:**
See `TECHNICAL_NOTES.md` for detailed memory architecture analysis and DMA allocation strategies.

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

---

## Glyph Atlas Benchmark (Update 2026-03-05)

Benchmark script was moved to:

- `../examples/benchmark_gfx_displaylist/benchmark_glyph_atlas.py`

Current tuning model:

- glyph atlas size is controlled in C by `RM690B0_DL_GLYPH_ATLAS_SLOTS`
- recommended value from latest measurements: `40`
- runtime constructor override is intentionally removed to keep setup simpler
