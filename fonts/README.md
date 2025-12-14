# TTF to RM690B0 Font Converter

Convert any TrueType Font (TTF) to bitmap fonts in rm690b0 format with configurable sizes.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Features](#features)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Command-Line Options](#command-line-options)
6. [Examples](#examples)
7. [Integration Guide](#integration-guide)
8. [Font Size Guidelines](#font-size-guidelines)
9. [Testing and Validation](#testing-and-validation)
10. [Tips and Best Practices](#tips-and-best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Font Resources](#font-resources)
13. [Technical Details](#technical-details)

---

## Quick Start

Convert any TrueType font to rm690b0 format in 3 easy steps!

### Prerequisites

```bash
pip install Pillow
```

### Basic Workflow

**Step 1: Convert TTF to Header File**

```bash
python ttf_to_rm690b0.py YourFont.ttf -w 16 -t 16 -o my_font.h
```

**Step 2: Test the Generated Font**

```bash
python test_converted_font.py my_font.h --char A
```

**Step 3: Integrate into RM690B0 Driver**

1. Copy `my_font.h` to: `ports/espressif/common-hal/rm690b0/fonts/`
2. Include in `RM690B0.c`: `#include "fonts/my_font.h"`
3. Add font ID: `#define RM690B0_FONT_CUSTOM (2)`
4. Done! Use with `display.set_font(2)`

---

## Features

✅ **Convert any TTF font** to rm690b0 bitmap format  
✅ **Configurable dimensions** (8×8, 16×16, 24×24, 16×12, etc.)  
✅ **Automatic character rendering** and bitmap generation  
✅ **Customizable character range** (ASCII subset or full range)  
✅ **Preview functionality** to verify characters  
✅ **Generates C header files** ready for inclusion  
✅ **Adjustable font size** and baseline offset  
✅ **Validation tool** included

---

## Installation

```bash
pip install Pillow
```

That's it! Only Pillow is required for font rendering.

---

## Basic Usage

```bash
# Convert to 16×16 font
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 -o font_16x16.h

# Convert to 8×8 font
python ttf_to_rm690b0.py font.ttf -w 8 -t 8 -o font_8x8.h

# Convert to 24×24 font
python ttf_to_rm690b0.py font.ttf -w 24 -t 24 -o font_24x24.h

# Convert to non-square size (16×12)
python ttf_to_rm690b0.py font.ttf -w 16 -t 12 -o font_16x12.h
```

---

## Command-Line Options

### Main Converter: `ttf_to_rm690b0.py`

| Option | Description | Default |
|--------|-------------|---------|
| `ttf_file` | Input TTF font file (required) | - |
| `-w, --width` | Character width in pixels (required) | - |
| `-t, --height` | Character height in pixels (required) | - |
| `-o, --output` | Output header file path (required) | - |
| `-n, --name` | Font array name | `rm690b0_font_{W}x{H}` |
| `-s, --size` | TTF font size in points | Same as height |
| `--start` | First character code | `0x20` (space) |
| `--end` | Last character code | `0x7E` (~) |
| `--baseline` | Baseline offset adjustment | `0` |
| `--preview` | Preview specific character | None |

### Font Validator: `test_converted_font.py`

```bash
# Basic validation
python test_converted_font.py font_16x16.h

# Preview specific character
python test_converted_font.py font_16x16.h --char A

# Show all characters
python test_converted_font.py font_16x16.h --all
```

---

## Examples

### Example 1: Basic 16×16 Font

```bash
python ttf_to_rm690b0.py Arial.ttf -w 16 -t 16 -o arial_16x16.h
```

Output: `arial_16x16.h` with 95 characters (space through ~)

### Example 2: Custom Font Name

```bash
python ttf_to_rm690b0.py DejaVuSans.ttf -w 24 -t 24 \
    --name my_large_font \
    -o custom_24x24.h
```

Output: Array named `my_large_font_data` in `custom_24x24.h`

### Example 3: Uppercase Letters Only

```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 \
    --start 0x41 --end 0x5A \
    -o uppercase_only.h
```

Output: Only characters A-Z (0x41 to 0x5A)

### Example 4: Adjust Font Size

```bash
# Use 18-point font rendered to 16×16 pixels
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 18 -o font_16x16.h
```

Useful when the default size doesn't fill the character box properly.

### Example 5: Baseline Adjustment

```bash
# Shift characters down by 2 pixels
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --baseline 2 -o font_16x16.h
```

Useful for fonts that render too high or too low in the character box.

### Example 6: Preview Characters

```bash
# Preview letter 'A' before generating
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 \
    --preview A \
    -o font_16x16.h
```

Output will include ASCII art preview:
```
Preview of character 'A' (0x41):
================
................
.....###........
.....#.#........
.....#.#........
....##.##.......
....#...#.......
...##...##......
...#######......
..##.....##.....
..#.......#.....
.##.......##....
................
```

### Example 7: Digits Only (0-9)

```bash
python ttf_to_rm690b0.py font.ttf -w 20 -t 30 \
    --start 0x30 --end 0x39 \
    -o digits_20x30.h
```

Perfect for digital clocks and counters.

### Example 8: Liberation Sans 20×20

```bash
# 1. Convert
python ttf_to_rm690b0.py \
    /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf \
    -w 20 -t 20 \
    --name rm690b0_font_20x20 \
    -o liberation_20x20.h \
    --preview A

# 2. Test
python test_converted_font.py liberation_20x20.h --char g

# 3. View all characters
python test_converted_font.py liberation_20x20.h --all

# 4. Copy to driver
cp liberation_20x20.h repos/circuitpython/ports/espressif/common-hal/rm690b0/fonts/
```

---

## Integration Guide

### Step 1: Generate the Font

```bash
python ttf_to_rm690b0.py MyFont.ttf -w 20 -t 20 -o my_font_20x20.h
```

### Step 2: Add to Driver

Place the generated header file in:
```
ports/espressif/common-hal/rm690b0/fonts/my_font_20x20.h
```

### Step 3: Include in RM690B0.c

```c
#include "fonts/rm690b0_font_8x8.h"
#include "fonts/rm690b0_font_16x16.h"
#include "fonts/my_font_20x20.h"  // Add this line
```

### Step 4: Add Font ID

```c
#define RM690B0_FONT_8x8_MONO    (0)
#define RM690B0_FONT_16x16_MONO  (1)
#define RM690B0_FONT_20x20_CUSTOM (2)  // Add this line
```

### Step 5: Add Getter Function

```c
static inline const uint8_t *rm690b0_get_20x20_glyph(uint32_t codepoint) {
    if (codepoint < 32 || codepoint > 126) {
        codepoint = '?';
    }
    return my_font_20x20_data[codepoint - 32];
}
```

### Step 6: Add Drawing Function

```c
static void rm690b0_draw_glyph_20x20(rm690b0_rm690b0_obj_t *self,
    mp_int_t x, mp_int_t y,
    const uint8_t *glyph,
    uint16_t fg, bool has_bg, uint16_t bg) {

    for (int row = 0; row < 20; row++) {
        // Each row is 3 bytes (20 pixels needs 3 bytes)
        uint8_t byte0 = glyph[row * 3];
        uint8_t byte1 = glyph[row * 3 + 1];
        uint8_t byte2 = glyph[row * 3 + 2];
        uint32_t bits = (byte0 << 16) | (byte1 << 8) | byte2;
        
        for (int col = 0; col < 20; col++) {
            bool on = (bits & (0x80000 >> col)) != 0;
            if (on) {
                common_hal_rm690b0_rm690b0_pixel(self, x + col, y + row, fg);
            } else if (has_bg) {
                common_hal_rm690b0_rm690b0_pixel(self, x + col, y + row, bg);
            }
        }
    }
}
```

### Step 7: Update set_font() and text()

Update the font selection logic in the driver to handle the new font ID.

---

## Font Size Guidelines

### Common Font Sizes

| Size | Best For | Example Command |
|------|----------|-----------------|
| 8×8 | Debug output, tiny text | `python ttf_to_rm690b0.py font.ttf -w 8 -t 8 -o font_8x8.h` |
| 12×16 | Small UI text | `python ttf_to_rm690b0.py font.ttf -w 12 -t 16 -o font_12x16.h` |
| 16×16 | Standard UI | `python ttf_to_rm690b0.py font.ttf -w 16 -t 16 -o font_16x16.h` |
| 24×24 | Headers | `python ttf_to_rm690b0.py font.ttf -w 24 -t 24 -o font_24x24.h` |
| 32×32 | Large display | `python ttf_to_rm690b0.py font.ttf -w 32 -t 32 -o font_32x32.h` |

### Use Cases by Size

**Small Fonts (6×8, 8×8, 8×12)**
- Debug output
- Serial console
- Status bars
- Dense information display
- Terminal emulation

**Medium Fonts (12×16, 16×16, 16×20)**
- Standard UI text
- Menu items
- Button labels
- User-facing messages
- Form fields

**Large Fonts (20×20, 24×24, 32×32)**
- Screen titles
- Headers
- Important notifications
- Digital clock displays
- Large numeric displays

**Special Purpose**
- **Digits only** (`--start 0x30 --end 0x39`): Clock, counter
- **Uppercase only** (`--start 0x41 --end 0x5A`): Headers
- **Symbols only**: Icons, indicators
- **Custom range**: Language-specific characters

### Memory Usage

```
Memory = num_chars × height × bytes_per_row
       = num_chars × height × ⌈width / 8⌉

Examples:
  8×8   × 95 chars = 7,600 bytes   (~7.4 KB)
  16×16 × 95 chars = 30,400 bytes  (~29.7 KB)
  24×24 × 95 chars = 68,400 bytes  (~66.8 KB)
  32×32 × 95 chars = 121,600 bytes (~118.8 KB)
```

### Performance Impact

```
Rendering time ≈ width × height × pixel_write_time

Relative speed (compared to 8×8):
  8×8:   1.0× (baseline)
  16×16: 4.0× slower
  24×24: 9.0× slower
  32×32: 16.0× slower
```

---

## Testing and Validation

### Validation Tool

The `test_converted_font.py` script validates and displays generated fonts:

```bash
# Basic validation (shows metadata)
python test_converted_font.py font_16x16.h

# Preview specific character
python test_converted_font.py font_16x16.h --char A

# Show all characters
python test_converted_font.py font_16x16.h --all
```

### Validation Checklist

- [ ] Font metadata correctly parsed
- [ ] Character count matches expected range
- [ ] All characters have correct byte count
- [ ] Codepoint sequence is continuous
- [ ] Characters render clearly
- [ ] Ascenders/descenders not clipped
- [ ] Wide characters (W, M) not compressed
- [ ] Similar characters (0, O) distinguishable

### Critical Characters to Test

Always test these characters for proper rendering:

- **g, j, p, q, y** (descenders)
- **b, d, h, k, l** (ascenders)
- **W, M** (wide characters)
- **i, l, I** (narrow characters)
- **0, O** (similar appearance)

```bash
python test_converted_font.py font.h --char g    # Descender
python test_converted_font.py font.h --char h    # Ascender
python test_converted_font.py font.h --char W    # Wide
python test_converted_font.py font.h --char i    # Narrow
python test_converted_font.py font.h --char 0    # Zero
python test_converted_font.py font.h --char O    # Letter O
```

---

## Tips and Best Practices

### 1. Choose the Right Font Size Parameter

If characters look too small in the bitmap:
```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 18 -o font.h
```

If characters are clipped:
```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 14 -o font.h
```

### 2. Adjust Baseline for Vertical Centering

If characters appear too high:
```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --baseline 2 -o font.h
```

If characters appear too low:
```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --baseline -2 -o font.h
```

### 3. Use Preview to Fine-Tune

```bash
# Preview multiple characters to check appearance
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --preview A -o font.h
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --preview g -o font.h
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --preview Q -o font.h
```

### 4. Choose Appropriate Dimensions

- **Square sizes** (8×8, 16×16, 24×24): Good for monospace fonts
- **Tall sizes** (8×12, 12×16): Better for proportional fonts
- **Wide sizes** (12×8, 16×10): Rare, for special displays

### 5. Font Selection Tips

**For UI:**
- Use sans-serif fonts (Liberation Sans, DejaVu Sans)
- 12×16 or 16×16 for readability
- Regular weight (not bold or thin)

**For Code/Terminal:**
- Use monospace fonts (Liberation Mono, DejaVu Sans Mono)
- 8×8 or 8×12 for compact display
- Bold or regular weight

**For Headers:**
- Use bold fonts
- 24×24 or larger
- Sans-serif or serif

**For Digits:**
- Use monospace or tabular fonts
- Custom range (--start 0x30 --end 0x39)
- Slightly larger than body text

---

## Troubleshooting

### Problem: Characters look blurry or unclear

**Solution**: Increase the font size parameter:
```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 20 -o font.h
```

### Problem: Characters are clipped at top/bottom

**Solution**: Reduce font size or adjust baseline:
```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 14 --baseline 1 -o font.h
```

### Problem: "Pillow library is required"

**Solution**: Install Pillow:
```bash
pip install Pillow
```

### Problem: Font file not found

**Solution**: Use absolute path or check current directory:
```bash
python ttf_to_rm690b0.py /full/path/to/font.ttf -w 16 -t 16 -o font.h
```

### Problem: Characters look different than expected

**Solution**: Preview individual characters to verify:
```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --preview A -o test.h
```

### Problem: Characters too small/large in cell

**Solution**: Adjust the `--size` parameter:
```bash
# Try different sizes
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 14 -o font.h  # Smaller
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 18 -o font.h  # Larger
```

### Problem: Vertical alignment issues

**Solution**: Use `--baseline` to shift characters:
```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --baseline 2 -o font.h   # Down
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --baseline -1 -o font.h  # Up
```

---

## Font Resources

### Where to Find TTF Fonts

**Linux:**
```bash
# List available fonts
fc-list

# Common locations
/usr/share/fonts/truetype/liberation/    # Liberation fonts
/usr/share/fonts/truetype/dejavu/        # DejaVu fonts
/usr/share/fonts/truetype/freefont/      # GNU FreeFont
```

**macOS:**
```bash
/System/Library/Fonts/                   # System fonts
~/Library/Fonts/                         # User fonts
```

**Windows:**
```
C:\Windows\Fonts\                        # All fonts
```

### Free Font Sources

- **Liberation fonts**: `/usr/share/fonts/truetype/liberation/` (SIL OFL licensed)
- **DejaVu fonts**: `/usr/share/fonts/truetype/dejavu/` (free, extended characters)
- **Google Fonts**: https://fonts.google.com (free, open source)
- **Font Squirrel**: https://www.fontsquirrel.com (free for commercial use)

### Recommended Open-Source Fonts

| Font | License | Best For |
|------|---------|----------|
| Liberation Sans | SIL OFL | General UI (Arial alternative) |
| Liberation Mono | SIL OFL | Code, monospace (Courier alternative) |
| DejaVu Sans | Free | Extended characters, Unicode |
| DejaVu Sans Mono | Free | Terminal, code editor |
| Noto Sans | SIL OFL | Multi-language support |
| Roboto | Apache 2.0 | Modern UI, Android-style |
| Source Sans Pro | SIL OFL | Clean, readable UI |
| Ubuntu | Ubuntu Font License | Contemporary design |

### Font License Considerations

When using this tool, ensure you have the right to:
1. Use the TTF font file
2. Convert it to bitmap format
3. Embed it in your firmware

**Common Open Licenses:**
- **SIL OFL 1.1**: Free use, requires attribution
- **Apache 2.0**: Free use, permissive
- **GPL**: Free use, derivative works must be GPL
- **Public Domain**: No restrictions

Always check the font license before distribution!

---

## Technical Details

### Output Format

The script generates a C header file with the following structure:

```c
#pragma once

#include <stdint.h>

// Font: Arial.ttf
// Size: 16×16 pixels
// Characters: 0x20..0x7E (' '..'~')
// Each character: 32 bytes (16 rows × 2 bytes per row)
// Each row: 2 byte(s) for 16 pixels, MSB = leftmost pixel
// Indexing: glyph = rm690b0_font_16x16_data[codepoint - 0x20] for 0x20 <= codepoint <= 0x7E
//
// Generated by ttf_to_rm690b0.py

static const uint8_t rm690b0_font_16x16_data[95][32] = {
    // 0x20 ' '
    {
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    },
    // 0x21 '!'
    {
     0x00, 0x00, 0x10, 0x00, 0x10, 0x00, /* ... */
    },
    // ... (more characters) ...
};
```

### Bitmap Format

**Row-based storage (horizontal):**
- Each character: `height × bytes_per_row`
- `bytes_per_row = (width + 7) / 8`
- Bit order: MSB = leftmost pixel
- Value: 1 = foreground, 0 = background

**Example for 16×16 font:**
- 16 rows × 2 bytes per row = 32 bytes per character
- Bit 15 (MSB of high byte) = leftmost pixel
- Bit 0 (LSB of low byte) = rightmost pixel

### Rendering Process

1. **Load TTF**: Use PIL ImageFont to load TrueType file
2. **Render**: Draw each character to bitmap using PIL ImageDraw
3. **Center**: Automatically center character in target dimensions
4. **Threshold**: Convert grayscale to binary (threshold at 128)
5. **Convert**: Transform bitmap to row-based byte array
6. **Generate**: Create C header file with array data

### Character Centering

Characters are automatically centered within the target dimensions:
- **Horizontal**: Center based on character width
- **Vertical**: Center based on character height + baseline offset

### Bit Ordering

```
For 16-pixel row:
Byte 0: [bit7][bit6][bit5][bit4][bit3][bit2][bit1][bit0]
        |<------- pixels 0-7 (left side) ------------>|

Byte 1: [bit7][bit6][bit5][bit4][bit3][bit2][bit1][bit0]
        |<------- pixels 8-15 (right side) ---------->|

MSB (bit 7 of byte 0) = leftmost pixel
LSB (bit 0 of byte 1) = rightmost pixel
```

---

## Comparison with convert_font_16x16.py

| Feature | ttf_to_rm690b0.py | convert_font_16x16.py |
|---------|-------------------|----------------------|
| Input format | Any TTF file | MikroElektronika C files |
| Size flexibility | Any WxH | Fixed 16×16 only |
| Font sources | Unlimited | Liberation Sans only |
| Preview mode | Yes (ASCII art) | No |
| Baseline adjust | Yes | No |
| Size tuning | Yes (--size) | No |
| Character range | Customizable | Fixed 0x20-0x7E |
| Dependencies | Pillow | None |
| Complexity | Moderate | Simple |

Both tools are valid:
- Use `ttf_to_rm690b0.py` for flexibility and any font
- Use `convert_font_16x16.py` for the specific Liberation Sans 16×16 conversion

---

## Quick Reference

### Minimal Command

```bash
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 -o output.h
```

### Full Options Command

```bash
python ttf_to_rm690b0.py font.ttf \
    --width 16 \
    --height 16 \
    --output font_16x16.h \
    --name my_custom_font \
    --size 18 \
    --baseline 1 \
    --start 0x20 \
    --end 0x7E \
    --preview A
```

### Test Commands

```bash
# Basic validation
python test_converted_font.py font_16x16.h

# Preview specific character
python test_converted_font.py font_16x16.h --char A

# View all characters
python test_converted_font.py font_16x16.h --all
```

### Common Recipes

```bash
# 8×8 debug font
python ttf_to_rm690b0.py font.ttf -w 8 -t 8 -o debug.h

# 16×16 UI font
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 -o ui.h

# 24×24 header font (bold)
python ttf_to_rm690b0.py font-bold.ttf -w 24 -t 24 -o header.h

# Digits only for clock
python ttf_to_rm690b0.py font.ttf -w 20 -t 30 --start 0x30 --end 0x39 -o digits.h

# Fine-tuned font
python ttf_to_rm690b0.py font.ttf -w 16 -t 16 --size 18 --baseline 1 -o tuned.h
```

---

## Project Files

```
ttf_to_rm690b0.py           # Main converter script (457 lines)
test_converted_font.py      # Font validation tool (377 lines)
example_ttf_conversion.sh   # Example usage script (167 lines)
README.md                   # This documentation
```

---

## Summary

The TTF to RM690B0 converter provides a flexible, powerful tool for creating custom bitmap fonts from any TrueType font.

**Key Benefits:**
- ✅ Convert any TTF font to rm690b0 format
- ✅ Any size from 4×6 to 64×64 (or larger)
- ✅ Preview before committing
- ✅ Fine-tune size and alignment
- ✅ Validate generated fonts
- ✅ Ready-to-use C headers

**Ready to use!** Install Pillow and start converting fonts. 🎉

---

## License

This tool is part of the RM690B0 driver project. See main project LICENSE for details.

---

## See Also

- `convert_font_16x16.py` - Convert MikroElektronika font files
- `../docs/RM690B0_DRIVER.md` - Display driver documentation
- `../docs/TECHNICAL_NOTES.md` - Technical details on text rendering