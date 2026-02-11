# Copyright (c) 2026 Przemyslaw Patrick Socha

import os
import sys
from PIL import Image

def rgba_to_rgb(img, bg_color=(0, 0, 0)):
    """Composite RGBA image onto solid background color, return RGB."""
    if img.mode != 'RGBA':
        return img.convert('RGB')
    bg = Image.new('RGB', img.size, bg_color)
    bg.paste(img, mask=img.split()[3])
    return bg

def convert_and_split(src_path, dest_dir, prefix, width, height, transparent_color=None):
    try:
        img = Image.open(src_path)
    except Exception as e:
        print(f"Failed to open {src_path}: {e}")
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    bg = transparent_color if transparent_color else (0, 0, 0)
    img = rgba_to_rgb(img, bg)

    # icons.png layout: 34px stride, 2px offset, 32x32 tiles
    # Rect(34*(n%10)+2, 34*(n//10)+2, 32, 32)
    count = 0
    for r in range(10):
        for c in range(10):
            x = 34 * c + 2
            y = 34 * r + 2

            if x + width > img.width or y + height > img.height:
                continue

            crop = img.crop((x, y, x + width, y + height))
            idx = r * 10 + c
            fn = f"{prefix}{idx}.bmp"
            crop.save(os.path.join(dest_dir, fn))
            print(f"Saved {fn}")
            count += 1

    print(f"Total: {count} icons")

def split_digits(src_path, dest_dir, transparent_color=None):
    try:
        img = Image.open(src_path)
    except:
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # digits.png layout: 18px stride, 16x32 tiles
    bg = transparent_color if transparent_color else (0, 0, 0)
    img = rgba_to_rgb(img, bg)

    for n in range(10):
        x = 18 * n
        crop = img.crop((x, 0, x + 16, 32))
        crop.save(os.path.join(dest_dir, f"digit_{n}.bmp"))
        print(f"Saved digit_{n}.bmp")

if __name__ == "__main__":
    src_icons = "../skins/default/icons.png"
    src_digits = "../skins/default/digits.png"
    dest = "../skins/default/bmp"

    # --transparent RGB hex, e.g.: python tools_split.py --transparent 947658
    # NOTE: quote '#' in shell:  --transparent '#947658'  or omit it
    transparent_color = None
    if "--transparent" in sys.argv:
        idx = sys.argv.index("--transparent")
        if idx + 1 < len(sys.argv):
            h = sys.argv[idx + 1].lstrip('#')
            transparent_color = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
            print(f"Transparency marker: RGB{transparent_color}")
        else:
            print("WARNING: --transparent requires a hex color value, e.g.: --transparent 947658")
            sys.exit(1)

    convert_and_split(src_icons, dest, "icon_", 32, 32, transparent_color)
    split_digits(src_digits, dest, transparent_color)
