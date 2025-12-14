# RM690B0 Driver - Technical Notes

> **Consolidated:** December 2025  
> **Purpose:** Technical findings, optimizations, and development notes  
> **Audience:** Developers and maintainers

---

## Overview

This document consolidates technical notes and findings from the RM690B0 driver development. Topics include performance benchmarking, rendering optimizations, documentation tooling, storage I/O considerations, and touch-display integration.

---

## 1. Performance Benchmarking Insights

### Adaptive Delay Implementation

The driver uses an adaptive delay formula to ensure hardware has time to process transfers:

```
delay_us = pixels_transferred / 36
minimum: 50µs
maximum: 500µs
```

### Performance Characteristics

| Operation Type | Pixels | Old Delay | New Delay | Improvement |
|---------------|--------|-----------|-----------|-------------|
| Single line | ~600 | 500µs | 50µs | 10x faster |
| Small rect | ~5,000 | 500µs | ~139µs | 3.6x faster |
| Large bitmap | ~270,000 | 500µs | 500µs | Same (hardware limited) |

### Key Findings

1. **Small operations benefit most** from adaptive delays (10x improvement)
2. **Large operations** are hardware-limited regardless of delay
3. **50µs minimum** prevents artifacts while maintaining performance
4. **Scaling formula** ensures hardware never gets overrun

### Benchmarking Recommendations

- Test with real-world mixed workloads (text + graphics + images)
- Profile memory allocation overhead separately from rendering
- Consider PSRAM access patterns when measuring performance
- Use `time.monotonic_ns()` for accurate sub-millisecond timing

---

## 2. Rendering Optimizations

### Circle Rendering Performance

Original implementation was 39× slower due to:
- Pixel-by-pixel rendering
- Repeated function call overhead
- No batching of operations

**Solution:** Span-based rendering with framebuffer batching
- Collect horizontal spans per scanline
- Batch writes to framebuffer
- Result: 39× performance improvement

### Rectangle Edge Handling

**Issue:** Double-drawing of edges caused visual artifacts

**Solution:** Careful coordinate management
- Horizontal lines: y coordinate boundary handling
- Vertical lines: x coordinate boundary handling
- Fill operations: proper inclusive/exclusive bounds

### DMA Alignment Requirements

**Hardware Constraint:** RM690B0/ESP32-S3 requires even-pixel alignment for DMA

**Solution:** PSRAM framebuffer + staging buffer
1. Maintain full framebuffer in PSRAM (no alignment restrictions)
2. Allow odd-pixel drawing at any coordinate
3. Copy dirty regions to DMA-safe staging buffer
4. Flush staged data to display hardware

### 30-Line DMA Limit

**Hard Limit:** ESP32-S3 LCD peripheral limited to 30 lines per DMA transfer

**Impact:**
- Full screen (450 lines) requires 15 DMA operations
- Attempted 60+ line chunks fail consistently
- This is a hardware limitation, not a driver bug

**Optimization:** Pre-calculate transfer chunks, minimize overhead between DMAs

### Framebuffer Padding Strategy

**Original Issue:** Edge replication caused artifacts

**Solution:** Read from framebuffer at expanded coordinates with bounds checking
- Prevents out-of-bounds access
- Maintains proper color values at edges
- Eliminates visual artifacts from duplicate pixels

---

## 3. Documentation Tooling

### Automated Documentation Generation

The project uses AI-assisted documentation.

### Documentation Standards

**Status Markers:**
- ✅ Complete/Working
- ❌ Not supported/Not implemented
- 🚧 In progress
- ⚠️ Needs attention

**Code Examples:**
- Must be tested and working
- Include expected output when relevant
- Note CircuitPython version requirements

### Maintenance Workflow

1. Make code changes
2. Test thoroughly
3. Update relevant documentation
4. Update `project_summary.yaml`
5. Update navigation in `README.md`

---

## 4. Storage & I/O Considerations

### SD Card - espsdcard Module

**Status:** ✅ **FULLY WORKING** - The native `espsdcard` module using ESP-IDF drivers provides reliable SD card access.

**Solution:** Custom `espsdcard` module replaces the unreliable `sdcardio` module with native ESP-IDF SDMMC drivers, solving all stability issues.

#### Quick Start

```python
import board
import espsdcard
import storage

# Initialize SD card
sd = espsdcard.SDCard(
    cs=board.SD_CS,
    miso=board.SD_MISO,
    mosi=board.SD_MOSI,
    clk=board.SD_CLK
)

# Mount filesystem
vfs = storage.VfsFat(sd)
storage.mount(vfs, "/sd")

# Use files normally
with open("/sd/image.bmp", "rb") as f:
    data = f.read()

# Always cleanup when done
storage.umount("/sd")
sd.deinit()
```

#### Best Practices

**Reading Files:**
- **Optimal chunk size:** 64KB for `read()`, 256KB-1MB for `readinto()` with pre-allocated buffers
- **Performance:** ~645 KB/s with pre-allocated buffers, ~610 KB/s with standard reads
- **For images:** Pre-allocate buffer of exact file size, use `readinto()` for best performance

```python
# Fast method: Pre-allocated buffer (645 KB/s)
size = os.stat("/sd/image.bmp")[6]
buffer = bytearray(size)
with open("/sd/image.bmp", "rb") as f:
    offset = 0
    while offset < size:
        bytes_read = f.readinto(memoryview(buffer)[offset:offset + 1048576])
        if bytes_read is None or bytes_read == 0:
            break
        offset += bytes_read

# Standard method: Chunked reading (610 KB/s)
chunks = []
with open("/sd/image.bmp", "rb") as f:
    while True:
        chunk = f.read(65536)  # 64KB chunks
        if not chunk:
            break
        chunks.append(chunk)
data = b"".join(chunks)
```

**Writing Files:**
- Write speed: ~134-199 KB/s
- Always explicitly `deinit()` the SD card object after unmounting

**Context Manager:**
```python
# Automatic cleanup
with espsdcard.SDCard(cs=board.SD_CS, miso=board.SD_MISO, 
                       mosi=board.SD_MOSI, clk=board.SD_CLK) as sd:
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")
    # Use SD card
    storage.umount("/sd")
# sd.deinit() called automatically
```

**Key Features:**
- ✅ Reliable reads/writes (no random I/O errors)
- ✅ File reopening works correctly
- ✅ Seek operations fully supported
- ✅ Multiple file access patterns
- ✅ Proper resource cleanup
- ✅ 100% API compatible with `sdcardio`

**Migration from sdcardio:**
```python
# Just change the import - code stays the same!
import espsdcard as sdcardio  # Drop-in replacement
```

### Flash vs PSRAM vs SD Card Storage

| Storage | Read Speed | Write Speed | Size | Best Use |
|---------|-----------|-------------|------|----------|
| Internal Flash | Fast, reliable | Slow (wear) | ~3-4 MB usable | Small images, fonts, critical assets |
| PSRAM | Very fast | Very fast | ~6-8 MB usable | Runtime buffers, image cache, framebuffer |
| SD Card (espsdcard) | 645 KB/s (readinto)<br>610 KB/s (read) | ~134-199 KB/s | Limited by card | Large assets, user files, logs |

### Image Loading Pipeline

**Optimal Strategy:**
1. **Small images (<100KB):** Load from flash directly
2. **Medium images (<1MB):** Load from SD card to PSRAM cache using pre-allocated buffer
3. **Large images (>1MB):** Stream from SD card in chunks or pre-load to PSRAM

**SD Card Loading (espsdcard):**
```python
# For display: load entire image to buffer
size = os.stat("/sd/image.bmp")[6]
buffer = bytearray(size)
with open("/sd/image.bmp", "rb") as f:
    offset = 0
    while offset < size:
        bytes_read = f.readinto(memoryview(buffer)[offset:offset + 1048576])
        if not bytes_read:
            break
        offset += bytes_read
# buffer now contains entire image at ~645 KB/s
```

### File Format Recommendations

**For Speed:**
- RAW RGB565 (no decode overhead, direct DMA to display)
- Pre-converted and stored in flash, PSRAM, or SD card

**For Size:**
- JPEG (10-20× compression, hardware decoder on ESP32-S3, ideal for SD card)
- BMP (simple format, works well with SD card streaming)

**Storage Strategy:**
- **Flash:** Critical UI elements, small icons (<100KB)
- **PSRAM:** Active framebuffers, frequently used images
- **SD Card:** Large image library, user content, logs

### Memory Management Tips

1. **Pre-allocate:** Allocate image buffers during startup
2. **Pool Management:** Reuse buffers to prevent fragmentation
3. **PSRAM First:** Use PSRAM for large allocations (framebuffers, images)
4. **GC Hygiene:** Explicit `gc.collect()` after large operations
5. **Monitor:** Track `gc.mem_free()` to detect leaks

---

## 5. Hardware-Specific Notes

### ESP32-S3 Considerations

**PSRAM:**
- Available: ~8 MB
- Access: Slightly slower than internal RAM but acceptable
- Best for: Framebuffers, image caches, large allocations

**DMA:**
- Requires internal RAM for DMA operations
- Cannot DMA directly from PSRAM
- Solution: Staging buffer in DMA-capable memory

**LCD Peripheral:**
- 30-line transfer limit (hardware constraint)
- 80 MHz QSPI clock maximum (tested stable)
- 32-bit command mode for RM690B0

### RM690B0 Display Specifics

**Resolution:** 600×450 (landscape) or 450×600 (portrait)

**Pixel Format:** RGB565 only
- 2 bytes per pixel
- Full framebuffer: 600×450×2 = 540,000 bytes (~527 KB)

**Command Mode:** QSPI with 32-bit commands
- Quad mode flag must be set
- Commands are 32-bit, parameters are 8-bit
- DC pin not used in QSPI mode

**Timing Requirements:**
- Minimum 50µs between small operations
- Scale up to 500µs for large transfers
- Hardware processing time is non-negotiable

**Y-Gap:** 16-pixel offset for Waveshare board
- Manufacturer calibration quirk
- Must be applied to all Y coordinates
- Configurable via `CIRCUITPY_RM690B0_Y_GAP`

---

## 6. Common Issues & Solutions

### Issue: Color Mixing/Artifacts

**Cause:** Insufficient delay between transfers

**Solution:** Adaptive delay formula ensures hardware has time to process

### Issue: Slow Small Operations

**Cause:** Fixed 500µs delay was overkill for small operations

**Solution:** Scale delay based on pixels transferred (minimum 50µs)

### Issue: SD Card Access

**Solution:** Use the `espsdcard` module (native ESP-IDF drivers) instead of `sdcardio`

**Common Issues:**
- **File not found:** Check filepath includes `/sd/` prefix
- **Slow performance:** Use pre-allocated buffers with `readinto()` (645 KB/s vs 610 KB/s)
- **Memory errors:** Use chunked reading for files >1MB
- **Reinitialization fails:** Always call `sd.deinit()` before creating new SD card object

**Best Practices:**
- Use 64KB chunks for `read()`, 256KB-1MB for `readinto()`
- Pre-allocate buffers for best performance
- Always cleanup with `deinit()` or use context manager

### Issue: DMA Alignment Errors

**Cause:** Attempting to DMA from odd addresses or PSRAM

**Solution:**
- Maintain framebuffer in PSRAM (no restrictions)
- Use staging buffer in DMA-capable memory
- Copy dirty regions before flush

---

## 7. Future Optimization Opportunities

### Short Term
- [ ] Profile BMP decoder for optimization opportunities
- [ ] Implement zero-copy paths where possible
- [ ] Tune JPEG decoder parameters for speed/quality tradeoff
- [ ] Add performance counters for profiling

### Medium Term
- [ ] Investigate DMA chaining to reduce overhead
- [ ] Test higher SPI clock frequencies (>80 MHz)
- [ ] Implement image format detection/auto-conversion
- [ ] Add streaming decode for large images

### Long Term
- [ ] Video playback feasibility study
- [ ] Multi-buffer strategies for animation

---

## 8. Testing & Validation

### Performance Testing

**Tools:**
- `time.monotonic_ns()` for microsecond precision
- Custom benchmark scripts in `test_scripts/`
- Memory profiling with `gc.mem_free()`

**Test Cases:**
- Single pixel rendering
- Line drawing (horizontal, vertical, diagonal)
- Rectangles (filled and outlined)
- Circles (filled and outlined)
- Large bitmap transfers
- Mixed workloads

### Memory Testing

**Stress Tests:**
- Repeated large allocations
- Fragmentation scenarios
- PSRAM limit testing
- GC behavior under load

**Monitoring:**
- Track free memory before/after operations
- Detect memory leaks (baseline comparison)
- Measure peak memory usage

### Visual Validation

**Artifact Checks:**
- Edge cases (0,0 and max coordinates)
- Odd/even pixel boundaries
- Color accuracy (known test patterns)
- Rotation correctness (all 4 modes)

---

## 9. Development Tips

### Debugging Display Issues

1. **Check initialization:** Verify command sequence executed
2. **Verify power:** Ensure display power GPIO is set correctly
3. **Test with simple pattern:** Fill screen with solid color first
4. **Check rotation:** Verify MADCTL settings
5. **Monitor timing:** Add logging around DMA operations

### Profiling Performance

```python
import time

start = time.monotonic_ns()
# ... operation ...
elapsed = (time.monotonic_ns() - start) / 1_000_000
print(f"Operation took {elapsed:.2f} ms")
```

### Memory Debugging

```python
import gc

gc.collect()
before = gc.mem_free()
# ... operation ...
gc.collect()
after = gc.mem_free()
print(f"Memory used: {before - after} bytes")
```

---

## 10. Touch-Display Integration

### Architecture Overview

The Waveshare ESP32-S3-Touch-AMOLED-2.41 integrates two independent controllers:
- **RM690B0 Display Controller:** QSPI-connected AMOLED (600×450 landscape)
- **FT6336U Touch Controller:** I2C-connected capacitive touch (450×600 portrait)

These controllers operate independently with separate communication buses and no hardware conflicts.

### Hardware Configuration

#### Display Pins (RM690B0 via QSPI)

```c
#define CIRCUITPY_RM690B0_QSPI_CS        (&pin_GPIO9)
#define CIRCUITPY_RM690B0_QSPI_CLK       (&pin_GPIO10)
#define CIRCUITPY_RM690B0_QSPI_D0        (&pin_GPIO11)
#define CIRCUITPY_RM690B0_QSPI_D1        (&pin_GPIO12)
#define CIRCUITPY_RM690B0_QSPI_D2        (&pin_GPIO13)
#define CIRCUITPY_RM690B0_QSPI_D3        (&pin_GPIO14)
#define CIRCUITPY_RM690B0_RESET          (&pin_GPIO21)
#define CIRCUITPY_RM690B0_POWER          (&pin_GPIO16)
#define CIRCUITPY_RM690B0_WIDTH          (600)
#define CIRCUITPY_RM690B0_HEIGHT         (450)
#define CIRCUITPY_RM690B0_PIXEL_CLOCK_HZ (80 * 1000 * 1000)
```

#### Touch Pins (FT6336U via I2C)

Touch controller shares the board's main I2C bus:
- **I2C Address:** 0x38
- **SCL:** GPIO48 (shared with RTC, IMU, I/O expander)
- **SDA:** GPIO47 (shared with RTC, IMU, I/O expander)
- **Reset:** GPIO3 (dedicated to touch)

#### Bus Independence

| Bus | Controller | Pins | Shared? | Conflicts? |
|-----|------------|------|---------|------------|
| QSPI | RM690B0 Display | GPIO9-14, 21, 16 | ❌ No | ❌ None |
| I2C | FT6336U Touch | GPIO47-48 | ✅ Yes (4+ devices) | ❌ None |

**Key Point:** Display and touch use completely separate buses—no hardware conflicts exist.

### Coordinate System Challenge

#### The Problem

The touch controller and display have **different native orientations**:

| Component | Orientation | Resolution | Coordinate Space |
|-----------|-------------|------------|------------------|
| **FT6336U Touch** | Portrait | 450×600 | X: 0-450, Y: 0-600 |
| **RM690B0 Display** | Landscape | 600×450 | X: 0-600, Y: 0-450 |

```
Touch Controller (Portrait):      Display (Landscape - Default):
┌──────────────┐                 ┌─────────────────────────┐
│ (0,0)        │                 │ (0,0)                   │
│              │                 │                         │
│              │                 │                         │
│     450      │                 │                         │
│      ×       │                 │           600×450       │
│     600      │                 │                         │
│   (450,600)  │                 │                (600,450)│
└──────────────┘                 └─────────────────────────┘
```

**Symptom:** Touch coordinates don't align with display coordinates without transformation.

#### The Solution: Coordinate Transformation

To align portrait touch (450×600) with landscape display (600×450), apply a **270° clockwise rotation**:

```python
def map_touch_to_display(touch_x, touch_y):
    """
    Transform touch coordinates from portrait to landscape.
    
    Rotation: 270° clockwise (90° counter-clockwise)
    
    Args:
        touch_x: 0-450 (portrait width)
        touch_y: 0-600 (portrait height)
    
    Returns:
        (display_x, display_y): 0-600, 0-450 (landscape)
    """
    display_x = 600 - touch_y
    display_y = touch_x
    return display_x, display_y
```

#### Mathematical Explanation

For a 270° clockwise rotation of point (x, y) from portrait (450×600) to landscape (600×450):

```
Given: Portrait coordinate (x, y) where x ∈ [0, 450], y ∈ [0, 600]
Want: Landscape coordinate (x', y') where x' ∈ [0, 600], y' ∈ [0, 450]

Rotation matrix (270° CW = -90° or 90° CCW):
┌ x' ┐   ┌  0  1 ┐ ┌ x ┐   ┌ W-1-y ┐
│ y' │ = │ -1  0 │ │ y │ = │   x   │
└    ┘   └       ┘ └   ┘   └       ┘

Simplified with portrait width W=600:
x' = W - y = 600 - y
y' = x

Therefore:
display_x = 600 - touch_y
display_y = touch_x
```

#### Corner Mapping

```
Touch Portrait               Display Landscape (after 270° CW)
┌──────────────┐            ┌─────────────────────────┐
│ TL (0,0)     │──────────→ │               TR (600,0)│
│              │            │                         │
│   TR (450,0) │──────────→ │ BR (600,450)            │
├──────────────┤            ├─────────────────────────┤
│ BR (450,600) │──────────→ │ BL (0,450)              │
│              │            │                         │
│ BL (0,600)   │──────────→ │ TL (0,0)                │
└──────────────┘            └─────────────────────────┘
```

### Supporting Multiple Rotations

For applications that need display rotation support:

```python
def map_touch_to_display(touch_x, touch_y, display_rotation=0):
    """
    Transform touch coordinates for any display rotation.
    
    Args:
        touch_x: 0-450 (touch always reports portrait)
        touch_y: 0-600 (touch always reports portrait)
        display_rotation: 0, 90, 180, or 270 degrees
    
    Returns:
        (display_x, display_y): Transformed coordinates
    """
    if display_rotation == 0:
        # Landscape (default): Need 270° rotation
        return 600 - touch_y, touch_x
    
    elif display_rotation == 90:
        # Portrait upright: Perfect match, no transformation!
        return touch_x, touch_y
    
    elif display_rotation == 180:
        # Landscape inverted: Need 90° rotation
        return touch_y, 450 - touch_x
    
    elif display_rotation == 270:
        # Portrait inverted: Need 180° rotation
        return 450 - touch_x, 600 - touch_y
    
    else:
        raise ValueError(f"Invalid rotation: {display_rotation}")
```

#### Rotation Summary

| Display Rotation | Display Size | Transformation | Touch Match |
|-----------------|--------------|----------------|-------------|
| **0° (Default)** | 600×450 (landscape) | `(600-ty, tx)` | ❌ Needs 270° rotation |
| **90°** | 450×600 (portrait) | `(tx, ty)` | ✅ Perfect match! |
| **180°** | 600×450 (landscape) | `(ty, 450-tx)` | ❌ Needs 90° rotation |
| **270°** | 450×600 (portrait) | `(450-tx, 600-ty)` | ❌ Needs 180° rotation |

### Basic Integration Example

```python
import board
import busio
import adafruit_focaltouch
import rm690b0

# Initialize display
display = rm690b0.RM690B0()
display.init_display()

# Initialize touch controller
i2c = busio.I2C(board.TP_SCL, board.TP_SDA)
touch = adafruit_focaltouch.Adafruit_FocalTouch(i2c, address=0x38)

def map_touch_to_display(touch_x, touch_y):
    """Transform portrait touch to landscape display."""
    return 600 - touch_y, touch_x

# Main loop
while True:
    if touch.touched:
        for point in touch.touches:
            touch_x, touch_y = point['x'], point['y']
            x, y = map_touch_to_display(touch_x, touch_y)
            # Draw white dot at touch location
            display.fill_rect(x-5, y-5, 10, 10, 0xFFFF)
            display.swap_buffers()
```

### Timing and Synchronization

#### Independent Operation

Display and touch controllers operate independently:

```python
# Touch polling (fast, ~1ms)
if touch.touched:
    for point in touch.touches:
        process_touch(point)

# Display updates (slower, ~16ms for full frame)
display.swap_buffers()
```

#### Recommended Polling Strategy

**Option 1: Continuous Polling (Best for Drawing)**
```python
while True:
    if touch.touched:
        for point in touch.touches:
            x, y = map_touch_to_display(point['x'], point['y'])
            draw_at_position(x, y)
    display.swap_buffers(copy=False)  # Flush changes
```

**Option 2: Event-Based (Best for UI)**
```python
while True:
    if touch.touched:
        touches = touch.touches
        if touches:
            handle_touch_event(touches)
            display.swap_buffers()  # Update after event
    time.sleep(0.01)  # Reduce CPU usage
```

### Performance Considerations

#### Touch Responsiveness

- **Touch Sampling Rate:** ~100 Hz (FT6336U typical)
- **I2C Transaction Time:** ~1-2 ms per read
- **Coordinate Transformation:** Negligible (<0.1 ms)

**Best Practice:** Poll touch at 50-100 Hz for smooth tracking.

#### Bus Conflicts

**I2C Bus Sharing (Touch + RTC + IMU + I/O Expander):**
- No conflicts—I2C handles multi-device arbitration
- Each device has unique address (Touch: 0x38)
- Sequential access is automatically managed

**Display QSPI:**
- Completely independent from I2C
- No interference with touch operations

### Application Patterns

#### Pattern 1: Simple Drawing App

```python
while True:
    if touch.touched:
        for point in touch.touches:
            x, y = map_touch_to_display(point['x'], point['y'])
            display.fill_circle(x, y, 3, 0xFFFF)
    display.swap_buffers(copy=False)
```

#### Pattern 2: Button Interface

```python
class Button:
    def __init__(self, x, y, width, height, label, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.color = color
    
    def draw(self, display):
        display.fill_rect(self.x, self.y, self.width, self.height, self.color)
    
    def contains(self, x, y):
        return (self.x <= x < self.x + self.width and 
                self.y <= y < self.y + self.height)
    
    def on_press(self):
        print(f"Button '{self.label}' pressed")

buttons = [
    Button(50, 50, 150, 60, "Button 1", 0xF800),
    Button(50, 150, 150, 60, "Button 2", 0x07E0),
    Button(50, 250, 150, 60, "Button 3", 0x001F),
]

# Draw buttons
for btn in buttons:
    btn.draw(display)
display.swap_buffers()

# Handle touches
while True:
    if touch.touched:
        for point in touch.touches:
            x, y = map_touch_to_display(point['x'], point['y'])
            for btn in buttons:
                if btn.contains(x, y):
                    btn.on_press()
        time.sleep(0.1)  # Debounce
```

#### Pattern 3: Multi-Touch Tracking

```python
last_positions = {}

while True:
    if touch.touched:
        current = {}
        for i, point in enumerate(touch.touches):
            x, y = map_touch_to_display(point['x'], point['y'])
            current[i] = (x, y)
            
            # Draw line from last position if exists
            if i in last_positions:
                last_x, last_y = last_positions[i]
                display.line(last_x, last_y, x, y, 0xFFFF)
            
        last_positions = current
        display.swap_buffers()
    else:
        last_positions.clear()
```

---

## 11. Text Rendering System

### Status: ✅ IMPLEMENTED

### Architecture

**Built-in Bitmap Font System:**

The RM690B0 driver includes a native text rendering system with 7 built-in bitmap fonts, providing fast, lightweight text display without LVGL or TTF dependencies.

**Key Features:**
- 7 embedded fonts: 8×8, 16×16, 16×24, 24×24, 24×32, 32×32, 32×48 pixels
- Row-based bitmap format (MSB-first horizontal rendering)
- ASCII character set (0x20-0x7E, 95 characters)
- Transparent or solid background rendering
- Independent from LVGL (works standalone)
- Total size: ~538 KB in flash memory
- TTF-to-bitmap conversion toolchain included

### Design Goals

1. **Fast Performance**: Native C rendering directly to framebuffer
2. **Flexibility**: Support external fonts for custom typography
3. **Compatibility**: Use same BDF fonts as adafruit_display_text
4. **Simplicity**: Clean, intuitive API
5. **No LVGL Dependency**: Works independently for simple text needs

### API Design

**Basic Usage:**
```python
import rm690b0

display = rm690b0.RM690B0()
display.init_display()

# Select font (0=8x8, 1=16x16, 2=16x24, 3=24x24, 4=24x32, 5=32x32, 6=32x48)
display.set_font(1)  # 16×16 font

# Draw text with transparent background
display.text(10, 10, "Hello World", color=0xFFFF)

# Draw text with solid background
display.text(10, 50, "Highlighted", color=0x0000, background=0xFFE0)

# Switch to larger font
display.set_font(3)  # 24×24 font
display.text(10, 100, "Bigger!", color=0xF800)

# Smallest font for debug/status text
display.set_font(0)  # 8×8 font
display.text(10, 420, "Status: OK", color=0x07E0)
```

**Available Font IDs:**
- `0` = 8×8 pixels (smallest, ~760 bytes)
- `1` = 16×16 pixels (Liberation Sans, ~30 KB)
- `2` = 16×24 pixels (Liberation Mono Bold, ~45 KB)
- `3` = 24×24 pixels (~68 KB)
- `4` = 24×32 pixels (~91 KB)
- `5` = 32×32 pixels (~121 KB)
- `6` = 32×48 pixels (largest, ~182 KB)
```

### Bitmap Font Format

**Row-Based Format:**
- Horizontal orientation (rows of pixels)
- Each row: N bytes for width pixels (rounded up to nearest byte)
- Bit order: MSB (bit 7) = leftmost pixel, LSB (bit 0) = rightmost pixel
- Bit value: 1 = foreground, 0 = background
- Character data stored as contiguous byte array

**Example: 16×16 Character**
```
Width: 16 pixels → 2 bytes per row
Height: 16 rows
Total: 32 bytes per character

Row storage:
[byte0][byte1] = Row 0 (16 pixels)
[byte2][byte3] = Row 1 (16 pixels)
...
[byte30][byte31] = Row 15 (16 pixels)

Bit layout per row:
byte0: [7][6][5][4][3][2][1][0] = pixels 0-7 (left)
byte1: [7][6][5][4][3][2][1][0] = pixels 8-15 (right)
```

**C Array Format:**
```c
static const uint8_t rm690b0_font_16x16_data[95][32] = {
    // ASCII 0x20 (space)
    {0x00, 0x00, 0x00, 0x00, ...},
    // ASCII 0x21 (!)
    {0x18, 0x18, 0x18, 0x18, ...},
    // ... 93 more characters ...
};
```

### Implementation Details

**Font Selection Flow:**
```
1. User: display.set_font(1)  # Select 16×16 font
   ↓
2. Python: Validate font_id (0-6)
   ↓
3. C: Store font_id in static variable
   ↓
4. User: display.text(10, 10, "Hi", 0xFFFF)
   ↓
5. C: Determine font dimensions from font_id
   ↓
6. C: For each character:
      - Get codepoint (UTF-8 decoded)
      - Fetch glyph data from font array
      - Call font-specific render function
   ↓
7. C: Render glyph to framebuffer
   ↓
8. Display updates on next swap_buffers()
```

**C Rendering Functions:**
```c
// Font selection
void common_hal_rm690b0_rm690b0_set_font(
    rm690b0_rm690b0_obj_t *self,
    mp_int_t font_id  // 0-6
);

// Text rendering
void common_hal_rm690b0_rm690b0_text(
    rm690b0_rm690b0_obj_t *self,
    mp_int_t x, mp_int_t y,
    const char *text,           // UTF-8 string
    uint16_t color,             // RGB565 foreground
    bool has_background,        // true if background set
    uint16_t background_color   // RGB565 background
);

// Font-specific glyph renderers (one per font size)
static void rm690b0_draw_glyph_8x8(...);
static void rm690b0_draw_glyph_16x16(...);
static void rm690b0_draw_glyph_16x24(...);
static void rm690b0_draw_glyph_24x24(...);
static void rm690b0_draw_glyph_24x32(...);
static void rm690b0_draw_glyph_32x32(...);
static void rm690b0_draw_glyph_32x48(...);
```

### Quick Start Examples

**Basic Text Rendering:**
```python
import rm690b0

# Initialize display
display = rm690b0.RM690B0()
display.init_display()

# Select a font (0=8x8, 1=16x16, ..., 6=32x48)
display.set_font(1)  # 16×16 Liberation Sans

# Draw text with transparent background
display.text(10, 10, "Hello World", color=0xFFFF)

# Draw text with solid background
display.text(10, 50, "Status: OK", color=0x0000, background=0x07E0)

# Update display
display.swap_buffers()
```

**Complete Example:**
```python
import rm690b0
import gc

display = rm690b0.RM690B0()
display.init_display()

# Clear screen
display.fill_color(0x0000)  # Black

# Title with large font
display.set_font(3)  # 24×24
display.text(50, 20, "RM690B0 Demo", color=0xFFFF)

# Body text with medium font
display.set_font(1)  # 16×16
display.text(50, 80, "Native text rendering", color=0x07E0)
display.text(50, 110, "7 built-in fonts", color=0x07E0)
display.text(50, 140, "Fast and lightweight", color=0x07E0)

# Status bar with small font
display.set_font(0)  # 8×8
display.text(10, 430, f"FPS: 60  Free: {gc.mem_free()}", color=0xF800)

# Show on display
display.swap_buffers()
```

### Text API Reference

**`set_font(font_id)`**

Select the active font for subsequent text rendering.

- **Parameters:** `font_id` (int) — Font identifier (0-6)
  - `0` = 8×8 monospace
  - `1` = 16×16 Liberation Sans
  - `2` = 16×24 Liberation Mono Bold
  - `3` = 24×24 monospace
  - `4` = 24×32 monospace
  - `5` = 32×32 monospace
  - `6` = 32×48 monospace
- **Returns:** None
- **Notes:** Font selection is global; invalid font_id clamps to 0

**`text(x, y, text, color=0xFFFF, background=None)`**

Render UTF-8 text string at specified coordinates.

- **Parameters:**
  - `x` (int) — Left coordinate in pixels (0-599 for 600×450 display)
  - `y` (int) — Top coordinate in pixels (0-449 for 600×450 display)
  - `text` (str) — UTF-8 encoded string to render
  - `color` (int, optional) — RGB565 foreground color (default: 0xFFFF white)
  - `background` (int or None, optional) — RGB565 background color, or None for transparent
- **Returns:** None
- **Behavior:**
  - Characters rendered left-to-right with fixed width
  - Unsupported characters (outside ASCII 0x20-0x7E) replaced with '?'
  - No automatic word wrap at screen edge
  - Clipping occurs at display boundaries
- **Performance:** 0.3-7.7 ms for "Hello World" depending on font size

**Examples:**
```python
# Transparent white text
display.text(10, 10, "Hello", color=0xFFFF)

# Black text on yellow background
display.text(10, 50, "Warning", color=0x0000, background=0xFFE0)

# Red text (transparent)
display.text(10, 90, "Error!", color=0xF800)

# Custom RGB565 colors
display.text(10, 130, "Custom", color=0x07E0, background=0x001F)
```

### Built-in Fonts

**Font 0: 8×8 Monospace (ID=0)**
- Size: 8×8 pixels, ~760 bytes
- Source: Basic fixed-width bitmap font
- Use: Debug output, status bars, dense information

**Font 1: 16×16 Liberation Sans (ID=1)**
- Size: 16×16 pixels, ~30 KB
- Source: Liberation Sans (converted from TTF)
- Use: Standard UI text, readable content, menus

**Font 2: 16×24 Liberation Mono Bold (ID=2)**
- Size: 16×24 pixels, ~45 KB
- Source: Liberation Mono Bold (converted from TTF)
- Use: Code display, terminal text, monospace needs

**Font 3: 24×24 Monospace (ID=3)**
- Size: 24×24 pixels, ~68 KB
- Source: Liberation Sans 24pt (converted from TTF)
- Use: Headers, prominent labels

**Font 4: 24×32 Monospace (ID=4)**
- Size: 24×32 pixels, ~91 KB
- Source: Custom tall font
- Use: Tall text displays

**Font 5: 32×32 Monospace (ID=5)**
- Size: 32×32 pixels, ~121 KB
- Source: Large display font
- Use: Digital displays, large headers

**Font 6: 32×48 Monospace (ID=6)**
- Size: 32×48 pixels, ~182 KB
- Source: Largest display font
- Use: Maximum readability, clock displays

**Total Flash Usage: ~538 KB for all 7 fonts**

### Features

**Implemented (Phase 5 Complete):**
- ✅ 7 built-in fonts (8×8 to 32×48)
- ✅ `set_font(id)` method for font selection
- ✅ `text(x, y, str, color, bg)` method
- ✅ UTF-8 string support
- ✅ Transparent background (bg=None)
- ✅ Solid background (bg=color)
- ✅ TTF-to-bitmap conversion tool (`ttf_to_rm690b0.py`)
- ✅ Font validation tool (`test_converted_font.py`)
- ✅ ASCII characters 0x20-0x7E (95 chars)
- ✅ Direct framebuffer rendering (fast)
- ✅ Independent from LVGL

**Future Enhancements:**
- Extended character sets (Latin-1, Unicode blocks)
- Variable-width fonts (proportional spacing)
- Anti-aliased fonts (grayscale rendering)
- Text measurement API (`text_width()`, `text_height()`)
- Multi-line text with word wrap
- Vertical text orientation

### Performance Characteristics

**Rendering Speed (per character):**
- 8×8 font: ~20-40 μs/char (64 pixels)
- 16×16 font: ~80-120 μs/char (256 pixels)
- 24×24 font: ~180-250 μs/char (576 pixels)
- 32×32 font: ~320-450 μs/char (1024 pixels)
- 32×48 font: ~480-700 μs/char (1536 pixels)

**Typical String Performance:**
- "Hello World" (11 chars):
  - 8×8: ~0.3-0.4 ms
  - 16×16: ~1.0-1.3 ms
  - 24×24: ~2.0-2.8 ms
  - 32×48: ~5.3-7.7 ms

**Memory Usage:**
- Runtime: Minimal (static font arrays in flash)
- No heap allocations during rendering
- No font caching overhead
- Stack usage: <200 bytes per text() call

**Comparison:**
- Native text: 0.3-7.7 ms for "Hello World"
- LVGL text: 5-20 ms (with full UI overhead)
- DisplayIO text: 50-200 ms (full layer composition)
- **10-500× faster than DisplayIO**

### TTF Font Conversion Toolchain

**Converter Script: `ttf_to_rm690b0.py`**

Converts any TrueType font to RM690B0 bitmap format.

**Features:**
- Any TTF font file as input
- Configurable character dimensions (WxH pixels)
- Supports non-square sizes (e.g., 16×12, 24×32)
- Customizable character range (default: ASCII 0x20-0x7E)
- Adjustable TTF size for optimal rendering
- Baseline offset adjustment
- Character preview mode
- Generates C header files

**Usage Examples:**
```bash
# Basic conversion
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 -o font_16x16.h

# Large font with preview
python ttf_to_rm690b0.py font.ttf -w 32 -t 32 --preview A -o font_32x32.h

# Custom size with adjustments
python ttf_to_rm690b0.py font.ttf -w 24 -t 32 --size 28 --baseline 2 -o font.h

# Digits only (0-9)
python ttf_to_rm690b0.py font.ttf -w 16 -t 24 --start 0x30 --end 0x39 -o digits.h
```

**Conversion Options:**
- `-w WIDTH` or `--width WIDTH` — Character width in pixels (required)
- `-t HEIGHT` or `--height HEIGHT` — Character height in pixels (required)
- `-o OUTPUT` or `--output OUTPUT` — Output header file path (required)
- `--size SIZE` — TTF rendering size (default: height value)
- `--baseline OFFSET` — Vertical baseline adjustment (default: 0)
- `--start CODEPOINT` — First character codepoint (default: 0x20)
- `--end CODEPOINT` — Last character codepoint (default: 0x7E)
- `--name NAME` — Array name in header file (default: auto-generated)
- `--preview CHAR` — Preview character as ASCII art

**Advanced Examples:**
```bash
# Large font (32×32)
python ttf_to_rm690b0.py font.ttf -w 32 -t 32 -o font_32x32.h

# Non-square font (16×24)
python ttf_to_rm690b0.py font.ttf -w 16 -t 24 -o font_16x24.h

# Digits only (0-9)
python ttf_to_rm690b0.py font.ttf -w 20 -t 30 --start 0x30 --end 0x39 -o digits.h

# Fine-tune rendering
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 14 --baseline 2 -o font.h

# Preview before saving
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --preview A -o font.h
```

**Validation Tool: `test_converted_font.py`**

Validates and previews generated font files.

```bash
# Validate font
python test_converted_font.py font_16x16.h

# Preview specific character
python test_converted_font.py font_16x16.h --char A

# Show all characters
python test_converted_font.py font_16x16.h --all
```

**Integration Workflow:**
1. Convert TTF: `python ttf_to_rm690b0.py font.ttf -w 20 -t 20 -o font_20x20.h`
2. Validate: `python test_converted_font.py font_20x20.h --char A`
3. Copy to driver: `cp font_20x20.h .../common-hal/rm690b0/fonts/`
4. Include in RM690B0.c: `#include "fonts/font_20x20.h"`
5. Add font ID constant and getter/drawer functions
6. Update font selection logic in `set_font()` and `text()`

### Font Resources

**Where to Find TTF Fonts:**
- Google Fonts: https://fonts.google.com (free, open source)
- Font Squirrel: https://www.fontsquirrel.com (free for commercial)
- System fonts: `/usr/share/fonts/truetype/` (Linux)
- Liberation Fonts: SIL OFL licensed (used in built-in fonts)
- DejaVu Fonts: Free, extended character support

**Recommended Open-Source Fonts:**
- Liberation Sans/Serif/Mono (Arial/Times/Courier alternatives)
- DejaVu Sans/Serif/Mono (extended Unicode)
- Noto Sans (multi-language support)
- Roboto (modern Android UI font)
- Source Sans/Code Pro (Adobe open source)
- Ubuntu Font Family (contemporary design)

**Font Licensing:**
- Ensure TTF font license allows embedding/distribution
- Common open licenses: SIL OFL 1.1, Apache 2.0, GPL
- Liberation Fonts: SIL OFL (free use, attribution required)
- Always check font license before distribution

### Font Format Specification

RM690B0 fonts use a **row-based bitmap format** optimized for horizontal rendering:

**Key Characteristics:**
- Horizontal orientation (scan rows left-to-right)
- 1 bit per pixel (monochrome)
- Byte-aligned rows (padded to whole bytes)
- ASCII printable characters (0x20-0x7E, 95 chars)
- Fixed-width fonts (each character same width)

**Storage Layout:**
```c
static const uint8_t rm690b0_font_16x16_data[95][32] = {
    // Character 0x20 (space)
    {0x00, 0x00, 0x00, 0x00, ...}, // 32 bytes = 16 rows × 2 bytes/row
    
    // Character 0x21 (!)
    {0x18, 0x00, 0x18, 0x00, ...},
    
    // ... 93 more characters ...
};
```

**Bit Ordering:**
- MSB = leftmost pixel in row
- LSB = rightmost pixel
- Example: `0xC3` = `11000011` = `██    ██` (2 pixels on, 4 off, 2 on)

**Character Indexing:**
- Array index = `codepoint - 0x20`
- Example: 'A' (0x41) → array index 0x41 - 0x20 = 33

### Native Text vs LVGL Text

**Native Text (rm690b0.text()):**
- ✅ Lightweight (no framework overhead)
- ✅ Fast rendering (microseconds per character)
- ✅ 7 built-in fonts (no file loading)
- ✅ Simple API (one function call)
- ✅ Independent from LVGL
- ❌ Fixed-width fonts only
- ❌ No word wrap or layout
- ❌ No text measurement
- **Use for:** Debug output, status text, simple labels, performance-critical text

**LVGL Text (rm690b0_lvgl.Label):**
- ✅ Rich text features (alignment, wrapping)
- ✅ TTF font support (any size, style)
- ✅ Dynamic layout and styling
- ✅ Interactive widgets
- ✅ Text measurement built-in
- ❌ Heavier framework overhead
- ❌ TTF fonts require file loading
- ❌ More memory usage
- **Use for:** Complex UIs, rich text, interactive applications, TTF fonts

**Both Can Coexist:**
```python
import rm690b0
import rm690b0_lvgl

# Initialize both
display = rm690b0.RM690B0()
display.init_display()

lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()
lvgl.init_rendering()

# Native text for status bar (fast)
display.set_font(0)  # 8×8
display.text(10, 10, "FPS: 60", 0x07E0)

# LVGL for main UI (rich features)
label = rm690b0_lvgl.Label("Hello World", x=50, y=50)
button = rm690b0_lvgl.Button("Click Me", x=100, y=100)

# Swap buffers to show native text
display.swap_buffers()

# Handle LVGL events
lvgl.task_handler()
```

**Choose Based On Needs:**
- Simple status/debug text → Native text API
- Complex interactive UI → LVGL
- Mix both for optimal performance + features
