#!/usr/bin/env python3
"""
Test script for validating TTF-converted fonts.

This script helps verify that fonts converted with ttf_to_rm690b0.py
are correctly formatted and can be visualized.

Usage:
    python test_converted_font.py font_file.h
    python test_converted_font.py font_file.h --char A
    python test_converted_font.py font_file.h --all
"""

import argparse
import re
import sys
from pathlib import Path


def parse_font_header(header_path):
    """
    Parse a font header file and extract character data.

    Returns:
        dict with 'width', 'height', 'chars' (list of char dicts)
    """
    with open(header_path, "r") as f:
        content = f.read()

    # Extract metadata from comments
    width = None
    height = None
    char_start = None
    char_end = None
    font_name = None

    # Look for size info: "Size: 16x16 pixels"
    size_match = re.search(r"Size:\s*(\d+)x(\d+)\s*pixels", content)
    if size_match:
        width = int(size_match.group(1))
        height = int(size_match.group(2))

    # Look for character range: "Characters: 0x20..0x7E"
    range_match = re.search(
        r"Characters:\s*0x([0-9A-Fa-f]+)\.\.0x([0-9A-Fa-f]+)", content
    )
    if range_match:
        char_start = int(range_match.group(1), 16)
        char_end = int(range_match.group(2), 16)

    # Extract font array name
    array_match = re.search(r"static const uint8_t\s+(\w+)_data\[", content)
    if array_match:
        font_name = array_match.group(1)

    if not all([width, height, char_start, char_end, font_name]):
        raise ValueError("Could not extract all font metadata from header file")

    # Extract character data
    # Find the array definition
    array_pattern = rf"{font_name}_data\[.*?\]\[.*?\]\s*=\s*\{{(.*?)\}};"
    array_match = re.search(array_pattern, content, re.DOTALL)
    if not array_match:
        raise ValueError(f"Could not find {font_name}_data array")

    array_content = array_match.group(1)

    # Parse each character
    characters = []
    char_pattern = r"// 0x([0-9A-Fa-f]+)\s+\'(.*?)\'\s*\n\s*\{(.*?)\}"

    for match in re.finditer(char_pattern, array_content, re.DOTALL):
        codepoint = int(match.group(1), 16)
        char_display = match.group(2)
        byte_data_str = match.group(3)

        # Extract hex values
        hex_values = re.findall(r"0x([0-9A-Fa-f]+)", byte_data_str)
        byte_data = [int(val, 16) for val in hex_values]

        # Determine actual character
        if char_display.startswith("\\"):
            # Escaped character
            if char_display == "\\\\":
                char = "\\"
            elif char_display == "\\'":
                char = "'"
            elif char_display == '\\"':
                char = '"'
            elif char_display == "\\n":
                char = "\n"
            elif char_display == "\\r":
                char = "\r"
            elif char_display == "\\t":
                char = "\t"
            elif char_display.startswith("\\x"):
                char = chr(int(char_display[2:], 16))
            else:
                char = char_display
        else:
            char = char_display

        characters.append({"codepoint": codepoint, "char": char, "bytes": byte_data})

    return {
        "name": font_name,
        "width": width,
        "height": height,
        "char_start": char_start,
        "char_end": char_end,
        "characters": characters,
    }


def visualize_character(char_data, width, height):
    """
    Convert character byte data to ASCII art.

    Args:
        char_data: Character dict with 'bytes' field
        width: Character width in pixels
        height: Character height in pixels

    Returns:
        String with ASCII art representation
    """
    bytes_per_row = (width + 7) // 8
    byte_data = char_data["bytes"]

    lines = []
    for row in range(height):
        row_start = row * bytes_per_row
        row_end = row_start + bytes_per_row
        row_bytes = byte_data[row_start:row_end]

        # Reconstruct row value
        row_value = 0
        for i, byte_val in enumerate(row_bytes):
            shift = (bytes_per_row - 1 - i) * 8
            row_value |= byte_val << shift

        # Convert to ASCII art
        line = ""
        for x in range(width):
            bit_position = width - 1 - x
            if row_value & (1 << bit_position):
                line += "█"  # Full block
            else:
                line += "·"  # Middle dot for empty

        lines.append(line)

    return "\n".join(lines)


def test_font_file(header_path, show_char=None, show_all=False):
    """
    Test and visualize a font file.

    Args:
        header_path: Path to header file
        show_char: Specific character to display (or None)
        show_all: Show all characters
    """
    print("=" * 60)
    print("Font Header Test")
    print("=" * 60)
    print(f"File: {header_path}")
    print()

    try:
        font_data = parse_font_header(header_path)
    except Exception as e:
        print(f"ERROR: Failed to parse font file: {e}")
        return 1

    # Display font info
    print("Font Information:")
    print(f"  Name:       {font_data['name']}")
    print(f"  Size:       {font_data['width']}x{font_data['height']} pixels")
    print(
        f"  Range:      0x{font_data['char_start']:02X}..0x{font_data['char_end']:02X}"
    )
    print(f"  Characters: {len(font_data['characters'])}")

    bytes_per_char = len(font_data["characters"][0]["bytes"])
    bytes_per_row = (font_data["width"] + 7) // 8
    print(
        f"  Bytes/char: {bytes_per_char} ({font_data['height']} rows × {bytes_per_row} bytes/row)"
    )

    total_size = len(font_data["characters"]) * bytes_per_char
    print(f"  Total size: {total_size} bytes ({total_size / 1024:.2f} KB)")
    print()

    # Validate data
    print("Validation:")
    errors = []

    # Check character count
    expected_count = font_data["char_end"] - font_data["char_start"] + 1
    if len(font_data["characters"]) != expected_count:
        errors.append(
            f"  ✗ Character count mismatch: got {len(font_data['characters'])}, expected {expected_count}"
        )
    else:
        print(f"  ✓ Character count correct ({len(font_data['characters'])})")

    # Check byte counts
    expected_bytes = font_data["height"] * bytes_per_row
    for i, char in enumerate(font_data["characters"]):
        if len(char["bytes"]) != expected_bytes:
            errors.append(
                f"  ✗ Character 0x{char['codepoint']:02X} has {len(char['bytes'])} bytes, expected {expected_bytes}"
            )
            break
    else:
        print(f"  ✓ All characters have correct byte count ({expected_bytes})")

    # Check codepoint sequence
    for i, char in enumerate(font_data["characters"]):
        expected_cp = font_data["char_start"] + i
        if char["codepoint"] != expected_cp:
            errors.append(
                f"  ✗ Codepoint sequence broken at index {i}: got 0x{char['codepoint']:02X}, expected 0x{expected_cp:02X}"
            )
            break
    else:
        print(f"  ✓ Codepoint sequence is continuous")

    if errors:
        print()
        for error in errors:
            print(error)
        return 1

    print()

    # Display character(s)
    if show_char:
        # Find specific character
        char_to_show = None
        if show_char.startswith("0x"):
            search_cp = int(show_char, 16)
            for char in font_data["characters"]:
                if char["codepoint"] == search_cp:
                    char_to_show = char
                    break
        elif len(show_char) == 1:
            search_cp = ord(show_char)
            for char in font_data["characters"]:
                if char["codepoint"] == search_cp:
                    char_to_show = char
                    break

        if char_to_show:
            print(
                f"Character Preview: '{char_to_show['char']}' (0x{char_to_show['codepoint']:02X})"
            )
            print("─" * font_data["width"])
            print(
                visualize_character(
                    char_to_show, font_data["width"], font_data["height"]
                )
            )
            print("─" * font_data["width"])
        else:
            print(f"ERROR: Character '{show_char}' not found in font")
            return 1

    elif show_all:
        print("All Characters:")
        print("=" * 60)

        # Show in groups of 16
        for i in range(0, len(font_data["characters"]), 16):
            group = font_data["characters"][i : i + 16]

            # Print header
            codepoints = " ".join([f"0x{c['codepoint']:02X}" for c in group])
            print(f"\n{codepoints}")
            print("─" * min(60, font_data["width"] * len(group) + len(group) - 1))

            # Print characters side by side (if not too wide)
            if font_data["width"] * len(group) < 70:
                for row in range(font_data["height"]):
                    row_str = ""
                    for char in group:
                        bytes_per_row = (font_data["width"] + 7) // 8
                        row_start = row * bytes_per_row
                        row_end = row_start + bytes_per_row
                        row_bytes = char["bytes"][row_start:row_end]

                        row_value = 0
                        for j, byte_val in enumerate(row_bytes):
                            shift = (bytes_per_row - 1 - j) * 8
                            row_value |= byte_val << shift

                        for x in range(font_data["width"]):
                            bit_position = font_data["width"] - 1 - x
                            if row_value & (1 << bit_position):
                                row_str += "█"
                            else:
                                row_str += "·"
                        row_str += " "
                    print(row_str)
            else:
                # Too wide, print vertically
                for char in group:
                    print(f"\n'{char['char']}' (0x{char['codepoint']:02X}):")
                    print(
                        visualize_character(
                            char, font_data["width"], font_data["height"]
                        )
                    )

    else:
        # Show sample characters
        print("Sample Characters:")
        print("=" * 60)

        sample_chars = ["A", "g", "0", "5", "!", "@"]
        for sample in sample_chars:
            sample_cp = ord(sample)
            for char in font_data["characters"]:
                if char["codepoint"] == sample_cp:
                    print(f"\n'{char['char']}' (0x{char['codepoint']:02X}):")
                    print(
                        visualize_character(
                            char, font_data["width"], font_data["height"]
                        )
                    )
                    break

    print()
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Test and validate TTF-converted font files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s font_16x16.h
  %(prog)s font_16x16.h --char A
  %(prog)s font_16x16.h --char 0x41
  %(prog)s font_8x8.h --all
        """,
    )

    parser.add_argument("header_file", help="Font header file to test")
    parser.add_argument(
        "--char", "-c", help='Display specific character (e.g., "A" or "0x41")'
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="Display all characters"
    )

    args = parser.parse_args()

    # Check if file exists
    header_path = Path(args.header_file)
    if not header_path.exists():
        print(f"ERROR: File not found: {header_path}")
        return 1

    # Run test
    return test_font_file(header_path, args.char, args.all)


if __name__ == "__main__":
    sys.exit(main())
