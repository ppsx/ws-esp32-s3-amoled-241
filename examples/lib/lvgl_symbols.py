# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
LVGL Symbol Constants for CircuitPython
========================================

This module provides Python constants for LVGL FontAwesome symbols.
These symbols are UTF-8 encoded Unicode characters that are included
in the Montserrat fonts used by LVGL.

The symbols appear as icons when used in Label or Button text.

Usage:
    import rm690b0_lvgl
    from lvgl_symbols import *

    # Button with icon
    btn = rm690b0_lvgl.Button(text=f"{SYMBOL_HOME} Home")

    # Label with multiple icons
    status = rm690b0_lvgl.Label(text=f"{SYMBOL_WIFI} {SYMBOL_BATTERY_FULL}")

Note: These are TEXT characters, not images. They must be rendered
      using an LVGL font that includes FontAwesome glyphs.

Author: CircuitPython Community
License: MIT
"""

# Audio/Video
SYMBOL_AUDIO = "\uf001"  # 🔊 Speaker icon
SYMBOL_VIDEO = "\uf008"  # 📹 Video camera
SYMBOL_PLAY = "\uf04b"  # ▶ Play button
SYMBOL_PAUSE = "\uf04c"  # ⏸ Pause button
SYMBOL_STOP = "\uf04d"  # ⏹ Stop button
SYMBOL_PREV = "\uf048"  # ⏮ Previous track
SYMBOL_NEXT = "\uf051"  # ⏭ Next track
SYMBOL_EJECT = "\uf052"  # ⏏ Eject
SYMBOL_MUTE = "\uf026"  # 🔇 Muted speaker
SYMBOL_VOLUME_MID = "\uf027"  # 🔉 Medium volume
SYMBOL_VOLUME_MAX = "\uf028"  # 🔊 Maximum volume
SYMBOL_SHUFFLE = "\uf074"  # 🔀 Shuffle
SYMBOL_LOOP = "\uf079"  # 🔁 Loop/repeat

# UI Controls
SYMBOL_OK = "\uf00c"  # ✓ Checkmark
SYMBOL_CLOSE = "\uf00d"  # ✗ Close/X
SYMBOL_PLUS = "\uf067"  # + Plus sign
SYMBOL_MINUS = "\uf068"  # - Minus sign
SYMBOL_LEFT = "\uf053"  # ◀ Left arrow
SYMBOL_RIGHT = "\uf054"  # ▶ Right arrow
SYMBOL_UP = "\uf077"  # ▲ Up arrow
SYMBOL_DOWN = "\uf078"  # ▼ Down arrow
SYMBOL_LIST = "\uf00b"  # ☰ List/menu bars
SYMBOL_BARS = "\uf0c9"  # ☰ Hamburger menu (same as list)
SYMBOL_BULLET = "\u2022"  # • Bullet point

# Navigation
SYMBOL_HOME = "\uf015"  # 🏠 Home
SYMBOL_SETTINGS = "\uf013"  # ⚙ Settings/gear
SYMBOL_POWER = "\uf011"  # ⏻ Power button
SYMBOL_REFRESH = "\uf021"  # ↻ Refresh/reload
SYMBOL_DOWNLOAD = "\uf019"  # ⬇ Download
SYMBOL_UPLOAD = "\uf093"  # ⬆ Upload
SYMBOL_DRIVE = "\uf01c"  # 💾 Hard drive
SYMBOL_DIRECTORY = "\uf07b"  # 📁 Folder
SYMBOL_FILE = "\uf158"  # 📄 File

# Communication
SYMBOL_CALL = "\uf095"  # 📞 Phone
SYMBOL_BELL = "\uf0f3"  # 🔔 Notification bell
SYMBOL_ENVELOPE = "\uf0e0"  # ✉ Email/message
SYMBOL_WIFI = "\uf1eb"  # 📶 WiFi signal
SYMBOL_BLUETOOTH = "\uf293"  # Bluetooth
SYMBOL_GPS = "\uf124"  # 📍 GPS/location

# Media/Content
SYMBOL_IMAGE = "\uf03e"  # 🖼 Picture/image
SYMBOL_EDIT = "\uf303"  # ✎ Edit/pencil
SYMBOL_COPY = "\uf0c5"  # 📋 Copy
SYMBOL_SAVE = "\uf0c7"  # 💾 Save/floppy disk
SYMBOL_TRASH = "\uf2ed"  # 🗑 Delete/trash
SYMBOL_CUT = "\uf0c4"  # ✂ Cut/scissors
SYMBOL_PASTE = "\uf0ea"  # 📋 Paste

# System
SYMBOL_CHARGE = "\uf0e7"  # ⚡ Lightning/charging
SYMBOL_USB = "\uf287"  # USB connector
SYMBOL_SD_CARD = "\uf7c2"  # 💳 SD card
SYMBOL_KEYBOARD = "\uf11c"  # ⌨ Keyboard
SYMBOL_BACKSPACE = "\uf55a"  # ⌫ Backspace
SYMBOL_WARNING = "\uf071"  # ⚠ Warning triangle
SYMBOL_EYE_OPEN = "\uf06e"  # 👁 Eye open (visible)
SYMBOL_EYE_CLOSE = "\uf070"  # Eye closed (hidden)
SYMBOL_TINT = "\uf043"  # 💧 Water droplet

# Battery States
SYMBOL_BATTERY_FULL = "\uf240"  # 🔋 Battery full
SYMBOL_BATTERY_3 = "\uf241"  # 🔋 Battery 75%
SYMBOL_BATTERY_2 = "\uf242"  # 🔋 Battery 50%
SYMBOL_BATTERY_1 = "\uf243"  # 🔋 Battery 25%
SYMBOL_BATTERY_EMPTY = "\uf244"  # 🔋 Battery empty

# Special
SYMBOL_DUMMY = "\uf8ff"  # Placeholder symbol
SYMBOL_NEW_LINE = "\uf8a2"  # ↵ New line


# Helper function to list all symbols
def list_all_symbols():
    """Print all available symbols with their names and icons."""
    print("=" * 60)
    print("LVGL Symbol Constants")
    print("=" * 60)

    categories = {
        "Audio/Video": [
            ("AUDIO", SYMBOL_AUDIO),
            ("VIDEO", SYMBOL_VIDEO),
            ("PLAY", SYMBOL_PLAY),
            ("PAUSE", SYMBOL_PAUSE),
            ("STOP", SYMBOL_STOP),
            ("PREV", SYMBOL_PREV),
            ("NEXT", SYMBOL_NEXT),
            ("EJECT", SYMBOL_EJECT),
            ("MUTE", SYMBOL_MUTE),
            ("VOLUME_MID", SYMBOL_VOLUME_MID),
            ("VOLUME_MAX", SYMBOL_VOLUME_MAX),
            ("SHUFFLE", SYMBOL_SHUFFLE),
            ("LOOP", SYMBOL_LOOP),
        ],
        "UI Controls": [
            ("OK", SYMBOL_OK),
            ("CLOSE", SYMBOL_CLOSE),
            ("PLUS", SYMBOL_PLUS),
            ("MINUS", SYMBOL_MINUS),
            ("LEFT", SYMBOL_LEFT),
            ("RIGHT", SYMBOL_RIGHT),
            ("UP", SYMBOL_UP),
            ("DOWN", SYMBOL_DOWN),
            ("LIST", SYMBOL_LIST),
            ("BARS", SYMBOL_BARS),
            ("BULLET", SYMBOL_BULLET),
        ],
        "Navigation": [
            ("HOME", SYMBOL_HOME),
            ("SETTINGS", SYMBOL_SETTINGS),
            ("POWER", SYMBOL_POWER),
            ("REFRESH", SYMBOL_REFRESH),
            ("DOWNLOAD", SYMBOL_DOWNLOAD),
            ("UPLOAD", SYMBOL_UPLOAD),
            ("DRIVE", SYMBOL_DRIVE),
            ("DIRECTORY", SYMBOL_DIRECTORY),
            ("FILE", SYMBOL_FILE),
        ],
        "Communication": [
            ("CALL", SYMBOL_CALL),
            ("BELL", SYMBOL_BELL),
            ("ENVELOPE", SYMBOL_ENVELOPE),
            ("WIFI", SYMBOL_WIFI),
            ("BLUETOOTH", SYMBOL_BLUETOOTH),
            ("GPS", SYMBOL_GPS),
        ],
        "Media/Content": [
            ("IMAGE", SYMBOL_IMAGE),
            ("EDIT", SYMBOL_EDIT),
            ("COPY", SYMBOL_COPY),
            ("SAVE", SYMBOL_SAVE),
            ("TRASH", SYMBOL_TRASH),
            ("CUT", SYMBOL_CUT),
            ("PASTE", SYMBOL_PASTE),
        ],
        "System": [
            ("CHARGE", SYMBOL_CHARGE),
            ("USB", SYMBOL_USB),
            ("SD_CARD", SYMBOL_SD_CARD),
            ("KEYBOARD", SYMBOL_KEYBOARD),
            ("BACKSPACE", SYMBOL_BACKSPACE),
            ("WARNING", SYMBOL_WARNING),
            ("EYE_OPEN", SYMBOL_EYE_OPEN),
            ("EYE_CLOSE", SYMBOL_EYE_CLOSE),
            ("TINT", SYMBOL_TINT),
        ],
        "Battery": [
            ("BATTERY_FULL", SYMBOL_BATTERY_FULL),
            ("BATTERY_3", SYMBOL_BATTERY_3),
            ("BATTERY_2", SYMBOL_BATTERY_2),
            ("BATTERY_1", SYMBOL_BATTERY_1),
            ("BATTERY_EMPTY", SYMBOL_BATTERY_EMPTY),
        ],
    }

    for category, symbols in categories.items():
        print(f"\n{category}:")
        print("-" * 60)
        for sym_name, sym_char in symbols:
            full_name = f"SYMBOL_{sym_name}"
            print(f"  {full_name:30s} {sym_char}")


# Example usage
if __name__ == "__main__":
    print("LVGL Symbol Constants Module")
    print("=" * 60)
    print("\nThis module provides FontAwesome symbol constants for LVGL.")
    print("\nExample usage:")
    print("  from lvgl_symbols import *")
    print('  button = rm690b0_lvgl.Button(text=f"{SYMBOL_HOME} Home")')
    print('  label = rm690b0_lvgl.Label(text=f"{SYMBOL_WIFI} Connected")')
    print("\n")

    list_all_symbols()
