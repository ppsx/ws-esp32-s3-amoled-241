#!/usr/bin/env python3
"""
Convert TrueType Font (TTF) to rm690b0 bitmap font format.

This script takes a TTF font file and converts it to the rm690b0 row-based
bitmap format at a specified size (e.g., 8x8, 16x16, 24x24, 16x12).

rm690b0 format:
- Row-based storage (horizontal orientation)
- Each row: N bytes for width pixels (rounded up to nearest byte)
- MSB (bit 7) = leftmost pixel, LSB (bit 0) = rightmost pixel
- 1 bit = foreground, 0 bit = background

Requirements:
    pip install Pillow

Usage:
    python ttf_to_rm690b0.py input.ttf --width 16 --height 16 --output font_16x16.h
    python ttf_to_rm690b0.py input.ttf -w 24 -h 24 -o font_24x24.h
    python ttf_to_rm690b0.py input.ttf -w 8 -h 8 --name my_font -o font_8x8.h
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow library is required. Install with: pip install Pillow")
    sys.exit(1)


def render_character(font, char, width, height, baseline_offset=0):
    """
    Render a single character to a bitmap.

    Args:
        font: PIL ImageFont object
        char: Character to render
        width: Target width in pixels
        height: Target height in pixels
        baseline_offset: Vertical offset for baseline adjustment

    Returns:
        List of integers representing rows (width bits per row)
    """
    # Create image with target size
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    # Get font metrics
    ascent, descent = font.getmetrics()

    # Get bounding box for the character at origin
    bbox = draw.textbbox((0, 0), char, font=font)

    # Calculate baseline position in the target box
    # Standard typography: baseline should be at about 80% from top for mixed text
    # This leaves room for descenders (g, j, p, q, y)
    baseline_y = int(height * 0.8) + baseline_offset

    # Calculate where to draw the character
    # bbox[0], bbox[1] is the offset from origin to top-left of char
    # We want to center horizontally and align baseline
    x_offset = (width - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y_offset = baseline_y - ascent

    # Draw the character
    draw.text((x_offset, y_offset), char, font=font, fill=255)

    # Convert to bitmap rows
    rows = []
    pixels = img.load()

    for y in range(height):
        row_value = 0
        for x in range(width):
            pixel = pixels[x, y]
            # Threshold at 128 (middle gray)
            if pixel > 128:
                # Set bit: MSB = leftmost pixel
                bit_position = width - 1 - x
                row_value |= 1 << bit_position
        rows.append(row_value)

    return rows


def rows_to_bytes(rows, width):
    """
    Convert row values to byte array.

    Args:
        rows: List of row values (integers)
        width: Width in pixels

    Returns:
        List of bytes
    """
    bytes_per_row = (width + 7) // 8  # Round up to nearest byte
    result = []

    for row_value in rows:
        # Split row into bytes (MSB first)
        for byte_idx in range(bytes_per_row):
            shift = (bytes_per_row - 1 - byte_idx) * 8
            byte_val = (row_value >> shift) & 0xFF
            result.append(byte_val)

    return result


def convert_ttf_to_rm690b0(
    ttf_path,
    width,
    height,
    start_char=0x20,
    end_char=0x7E,
    font_size=None,
    baseline_offset=0,
):
    """
    Convert TTF font to rm690b0 format.

    Args:
        ttf_path: Path to TTF file
        width: Character width in pixels
        height: Character height in pixels
        start_char: First character code (default: 0x20 = space)
        end_char: Last character code (default: 0x7E = ~)
        font_size: TTF font size in points (default: height)
        baseline_offset: Vertical offset adjustment

    Returns:
        List of character dictionaries with bitmap data
    """
    if font_size is None:
        font_size = height

    try:
        font = ImageFont.truetype(str(ttf_path), font_size)
    except Exception as e:
        print(f"ERROR: Could not load font '{ttf_path}': {e}")
        sys.exit(1)

    characters = []

    for codepoint in range(start_char, end_char + 1):
        char = chr(codepoint)

        # Render character
        rows = render_character(font, char, width, height, baseline_offset)

        # Convert to bytes
        byte_data = rows_to_bytes(rows, width)

        characters.append({"codepoint": codepoint, "char": char, "bytes": byte_data})

        if codepoint % 16 == 0:
            print(
                f"Processed {codepoint - start_char + 1}/{end_char - start_char + 1} characters..."
            )

    print(f"Processed all {len(characters)} characters")
    return characters


def generate_header_file(
    characters, output_path, font_name, width, height, start_char, ttf_source
):
    """
    Generate C header file with bitmap font data.

    Args:
        characters: List of character dictionaries
        output_path: Output file path
        font_name: Font array name
        width: Character width
        height: Character height
        start_char: First character code
        ttf_source: Source TTF file name
    """
    bytes_per_char = len(characters[0]["bytes"])
    bytes_per_row = (width + 7) // 8

    with open(output_path, "w") as f:
        f.write("#pragma once\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write(f"// Font: {ttf_source}\n")
        f.write(f"// Size: {width}x{height} pixels\n")
        f.write(
            f"// Characters: 0x{start_char:02X}..0x{characters[-1]['codepoint']:02X} "
        )
        f.write(f"('{chr(start_char)}'..'{characters[-1]['char']}')\n")
        f.write(
            f"// Each character: {bytes_per_char} bytes ({height} rows × {bytes_per_row} bytes per row)\n"
        )
        f.write(
            f"// Each row: {bytes_per_row} byte(s) for {width} pixels, MSB = leftmost pixel\n"
        )
        f.write(
            f"// Indexing: glyph = {font_name}_data[codepoint - 0x{start_char:02X}] "
        )
        f.write(
            f"for 0x{start_char:02X} <= codepoint <= 0x{characters[-1]['codepoint']:02X}\n"
        )
        f.write("//\n")
        f.write("// Generated by ttf_to_rm690b0.py\n\n")

        f.write(
            f"static const uint8_t {font_name}_data[{len(characters)}][{bytes_per_char}] = {{\n"
        )

        for char_info in characters:
            cp = char_info["codepoint"]
            ch = char_info["char"]

            # Escape special characters in comments
            if ch == "\\":
                ch_display = "\\\\"
            elif ch == "'":
                ch_display = "\\'"
            elif ch == '"':
                ch_display = '\\"'
            elif ch == "\n":
                ch_display = "\\n"
            elif ch == "\r":
                ch_display = "\\r"
            elif ch == "\t":
                ch_display = "\\t"
            elif ord(ch) < 32 or ord(ch) > 126:
                ch_display = f"\\x{ord(ch):02X}"
            else:
                ch_display = ch

            f.write(f"    // 0x{cp:02X} '{ch_display}'\n")
            f.write("    {")

            bytes_data = char_info["bytes"]
            for i, byte_val in enumerate(bytes_data):
                if i > 0:
                    f.write(",")
                if i % 16 == 0:
                    f.write("\n     ")
                else:
                    f.write(" ")
                f.write(f"0x{byte_val:02X}")

            f.write("\n    },\n")

        f.write("};\n")


def visualize_character(char_data, width, height):
    """
    Visualize a character as ASCII art for debugging.

    Args:
        char_data: Character dictionary with 'bytes' field
        width: Character width
        height: Character height

    Returns:
        String representation
    """
    bytes_per_row = (width + 7) // 8
    byte_data = char_data["bytes"]

    lines = []
    for row in range(height):
        line = ""
        row_bytes = byte_data[row * bytes_per_row : (row + 1) * bytes_per_row]

        # Reconstruct row value
        row_value = 0
        for i, byte_val in enumerate(row_bytes):
            row_value |= byte_val << ((bytes_per_row - 1 - i) * 8)

        # Convert to ASCII art
        for x in range(width):
            bit_position = width - 1 - x
            if row_value & (1 << bit_position):
                line += "#"
            else:
                line += "."

        lines.append(line)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Convert TrueType Font (TTF) to rm690b0 bitmap font format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s font.ttf -w 16 -t 16 -o font_16x16.h
  %(prog)s font.ttf -w 24 -t 24 -o font_24x24.h --name my_font_24x24
  %(prog)s font.ttf -w 8 -t 12 -o font_8x12.h --size 10
  %(prog)s font.ttf -w 16 -t 16 --start 0x41 --end 0x5A -o uppercase.h
        """,
    )

    parser.add_argument("ttf_file", type=str, help="Input TTF font file")
    parser.add_argument(
        "-w", "--width", type=int, required=True, help="Character width in pixels"
    )
    parser.add_argument(
        "-t", "--height", type=int, required=True, help="Character height in pixels"
    )
    parser.add_argument(
        "-o", "--output", type=str, required=True, help="Output header file path"
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default=None,
        help="Font array name (default: auto-generated from size)",
    )
    parser.add_argument(
        "-s",
        "--size",
        type=int,
        default=None,
        help="TTF font size in points (default: same as height)",
    )
    parser.add_argument(
        "--start",
        type=lambda x: int(x, 0),
        default=0x20,
        help="First character code (default: 0x20)",
    )
    parser.add_argument(
        "--end",
        type=lambda x: int(x, 0),
        default=0x7E,
        help="Last character code (default: 0x7E)",
    )
    parser.add_argument(
        "--baseline",
        type=int,
        default=0,
        help="Baseline offset adjustment (default: 0)",
    )
    parser.add_argument(
        "--preview",
        type=str,
        default=None,
        help='Preview specific character (e.g., "A" or "0x41")',
    )

    args = parser.parse_args()

    # Validate inputs
    if args.width < 1 or args.width > 64:
        print("ERROR: Width must be between 1 and 64 pixels")
        sys.exit(1)

    if args.height < 1 or args.height > 64:
        print("ERROR: Height must be between 1 and 64 pixels")
        sys.exit(1)

    if args.start < 0 or args.start > 0x10FFFF:
        print("ERROR: Start character code out of range")
        sys.exit(1)

    if args.end < args.start or args.end > 0x10FFFF:
        print("ERROR: End character code must be >= start code")
        sys.exit(1)

    # Generate font name if not specified
    if args.name is None:
        args.name = f"rm690b0_font_{args.width}x{args.height}"

    # Check if TTF file exists
    ttf_path = Path(args.ttf_file)
    if not ttf_path.exists():
        print(f"ERROR: TTF file not found: {ttf_path}")
        sys.exit(1)

    print("=" * 60)
    print("TTF to rm690b0 Font Converter")
    print("=" * 60)
    print(f"Input:  {ttf_path}")
    print(f"Output: {args.output}")
    print(f"Size:   {args.width}x{args.height} pixels")
    print(
        f"Range:  0x{args.start:02X}..0x{args.end:02X} ({chr(args.start)}..{chr(args.end)})"
    )
    print(f"Name:   {args.name}")
    if args.size:
        print(f"TTF size: {args.size} points")
    if args.baseline != 0:
        print(f"Baseline offset: {args.baseline}")
    print("=" * 60)

    # Convert font
    print("\nConverting font...")
    characters = convert_ttf_to_rm690b0(
        ttf_path,
        args.width,
        args.height,
        args.start,
        args.end,
        args.size,
        args.baseline,
    )

    # Preview character if requested
    if args.preview:
        # Parse preview character
        if args.preview.startswith("0x"):
            preview_code = int(args.preview, 16)
        elif len(args.preview) == 1:
            preview_code = ord(args.preview)
        else:
            print(f"ERROR: Invalid preview character: {args.preview}")
            sys.exit(1)

        # Find character in converted data
        preview_char = None
        for char_data in characters:
            if char_data["codepoint"] == preview_code:
                preview_char = char_data
                break

        if preview_char:
            print(
                f"\nPreview of character '{chr(preview_code)}' (0x{preview_code:02X}):"
            )
            print("=" * args.width)
            print(visualize_character(preview_char, args.width, args.height))
            print("=" * args.width)
        else:
            print(f"WARNING: Character 0x{preview_code:02X} not in converted range")

    # Generate header file
    print(f"\nGenerating header file: {args.output}")
    generate_header_file(
        characters,
        args.output,
        args.name,
        args.width,
        args.height,
        args.start,
        ttf_path.name,
    )

    print("\nDone!")
    print(f"Generated {len(characters)} characters")
    print(f"Bytes per character: {len(characters[0]['bytes'])}")
    print(f"Total size: {len(characters) * len(characters[0]['bytes'])} bytes")
    print(f"\nTo use in your code:")
    print(f'  #include "{Path(args.output).name}"')
    print(f"  const uint8_t *glyph = {args.name}_data[codepoint - 0x{args.start:02X}];")


if __name__ == "__main__":
    main()
