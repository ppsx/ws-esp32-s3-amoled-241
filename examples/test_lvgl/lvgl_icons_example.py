"""
LVGL Icons and Symbols Example for RM690B0 Display
===================================================

This example demonstrates how to use LVGL FontAwesome icons/symbols
with the rm690b0_lvgl module on the Waveshare ESP32-S3 Touch AMOLED board.

Key Points:
- LVGL symbols are UTF-8 encoded Unicode characters (NOT images)
- They are part of the FontAwesome font embedded in Montserrat fonts
- Use Unicode escape sequences like "\uf015" for HOME icon
- Symbols work in both Labels and Buttons

Hardware: Waveshare ESP32-S3-Touch-AMOLED-2.41
- Display: RM690B0 (600×450 AMOLED)
- Touch: FT6336U (I2C)

Author: CircuitPython Community
License: MIT
"""

import time

import board
import busio
import rm690b0
import rm690b0_lvgl
from lvgl_symbols import *

# ============================================================================
# INITIALIZATION
# ============================================================================

print("=" * 60)
print("LVGL Icons Example")
print("=" * 60)

display = rm690b0.RM690B0()
display.init_display()

print("\nInitializing LVGL display...")
lvgl = rm690b0_lvgl.RM690B0_LVGL()
lvgl.init_display()

print("Initializing touch controller...")
i2c = busio.I2C(board.TP_SCL, board.TP_SDA)
lvgl.init_touch(i2c)

print("Display and touch initialized successfully!")

# ============================================================================
# STATUS BAR WITH ICONS
# ============================================================================

print("\nCreating status bar with icons...")

# WiFi icon (top-left)
wifi_label = rm690b0_lvgl.Label(text=SYMBOL_WIFI)
wifi_label.x = 10
wifi_label.y = 10
wifi_label.set_text_color(0x00FF00)  # Green = connected

# Battery icon (top-right)
battery_label = rm690b0_lvgl.Label(text=SYMBOL_BATTERY_3)
battery_label.x = 520
battery_label.y = 10
battery_label.set_text_color(0x00FF00)  # Green = good charge

# Battery percentage text
battery_text = rm690b0_lvgl.Label(text="75%")
battery_text.x = 560
battery_text.y = 10
battery_text.set_text_color(0xFFFFFF)

# ============================================================================
# NAVIGATION BUTTONS WITH ICONS
# ============================================================================

print("Creating navigation buttons...")

# Home button
home_btn = rm690b0_lvgl.Button(text=f"{SYMBOL_HOME} Home")
home_btn.x = 50
home_btn.y = 80
home_btn.width = 150
home_btn.height = 70

# Settings button
settings_btn = rm690b0_lvgl.Button(text=f"{SYMBOL_SETTINGS} Settings")
settings_btn.x = 225
settings_btn.y = 80
settings_btn.width = 150
settings_btn.height = 70

# Power button
power_btn = rm690b0_lvgl.Button(text=f"{SYMBOL_POWER} Power")
power_btn.x = 400
power_btn.y = 80
power_btn.width = 150
power_btn.height = 70
power_btn.set_style_bg_color(0xFF0000)  # Red background

# ============================================================================
# MEDIA CONTROLS WITH ICON-ONLY BUTTONS
# ============================================================================

print("Creating media control buttons...")

# Previous button
prev_btn = rm690b0_lvgl.Button(text=SYMBOL_PREV)
prev_btn.x = 100
prev_btn.y = 180
prev_btn.width = 80
prev_btn.height = 80

# Play/Pause button
play_pause_btn = rm690b0_lvgl.Button(text=SYMBOL_PLAY)
play_pause_btn.x = 200
play_pause_btn.y = 180
play_pause_btn.width = 80
play_pause_btn.height = 80
play_pause_btn.set_style_bg_color(0x00AA00)  # Green

# Stop button
stop_btn = rm690b0_lvgl.Button(text=SYMBOL_STOP)
stop_btn.x = 300
stop_btn.y = 180
stop_btn.width = 80
stop_btn.height = 80
stop_btn.set_style_bg_color(0xAA0000)  # Dark red

# Next button
next_btn = rm690b0_lvgl.Button(text=SYMBOL_NEXT)
next_btn.x = 400
next_btn.y = 180
next_btn.width = 80
next_btn.height = 80

# Volume label
volume_label = rm690b0_lvgl.Label(text=f"{SYMBOL_VOLUME_MAX} Volume")
volume_label.x = 220
volume_label.y = 280

# ============================================================================
# FILE OPERATIONS WITH ICONS
# ============================================================================

print("Creating file operation buttons...")

# Save button
save_btn = rm690b0_lvgl.Button(text=f"{SYMBOL_SAVE} Save")
save_btn.x = 50
save_btn.y = 320
save_btn.width = 120
save_btn.height = 60

# Edit button
edit_btn = rm690b0_lvgl.Button(text=f"{SYMBOL_EDIT} Edit")
edit_btn.x = 190
edit_btn.y = 320
edit_btn.width = 120
edit_btn.height = 60

# Trash button
trash_btn = rm690b0_lvgl.Button(text=f"{SYMBOL_TRASH} Delete")
trash_btn.x = 330
trash_btn.y = 320
trash_btn.width = 120
trash_btn.height = 60
trash_btn.set_style_bg_color(0xCC0000)  # Red

# Download button
download_btn = rm690b0_lvgl.Button(text=f"{SYMBOL_DOWNLOAD} Download")
download_btn.x = 470
download_btn.y = 320
download_btn.width = 120
download_btn.height = 60

# ============================================================================
# STATUS LABEL
# ============================================================================

# Status message at bottom
status_label = rm690b0_lvgl.Label(text="Touch any button to test")
status_label.x = 150
status_label.y = 410
status_label.set_text_color(0xFFFF00)  # Yellow

# ============================================================================
# EVENT HANDLERS
# ============================================================================

# State variables
is_playing = False
volume_level = 3  # 0-3 (mute to max)


def on_home_click(btn):
    status_label.text = f"{SYMBOL_HOME} Home button clicked!"
    print("Home clicked")


def on_settings_click(btn):
    status_label.text = f"{SYMBOL_SETTINGS} Settings opened"
    print("Settings clicked")


def on_power_click(btn):
    status_label.text = f"{SYMBOL_WARNING} Power button pressed!"
    print("Power clicked")


def on_play_pause_click(btn):
    global is_playing
    is_playing = not is_playing
    if is_playing:
        play_pause_btn.text = SYMBOL_PAUSE
        status_label.text = f"{SYMBOL_PLAY} Now playing..."
    else:
        play_pause_btn.text = SYMBOL_PLAY
        status_label.text = f"{SYMBOL_PAUSE} Paused"
    print(f"Play/Pause - is_playing={is_playing}")


def on_stop_click(btn):
    global is_playing
    is_playing = False
    play_pause_btn.text = SYMBOL_PLAY
    status_label.text = f"{SYMBOL_STOP} Stopped"
    print("Stop clicked")


def on_prev_click(btn):
    status_label.text = f"{SYMBOL_PREV} Previous track"
    print("Previous clicked")


def on_next_click(btn):
    status_label.text = f"{SYMBOL_NEXT} Next track"
    print("Next clicked")


def on_save_click(btn):
    status_label.text = f"{SYMBOL_OK} File saved!"
    print("Save clicked")


def on_edit_click(btn):
    status_label.text = f"{SYMBOL_EDIT} Editing..."
    print("Edit clicked")


def on_trash_click(btn):
    status_label.text = f"{SYMBOL_TRASH} Deleted!"
    print("Trash clicked")


def on_download_click(btn):
    status_label.text = f"{SYMBOL_DOWNLOAD} Downloading..."
    print("Download clicked")


# Register callbacks
home_btn.on_click = on_home_click
settings_btn.on_click = on_settings_click
power_btn.on_click = on_power_click
play_pause_btn.on_click = on_play_pause_click
stop_btn.on_click = on_stop_click
prev_btn.on_click = on_prev_click
next_btn.on_click = on_next_click
save_btn.on_click = on_save_click
edit_btn.on_click = on_edit_click
trash_btn.on_click = on_trash_click
download_btn.on_click = on_download_click

# ============================================================================
# MAIN LOOP
# ============================================================================

print("\n" + "=" * 60)
print("UI Ready! Touch buttons to interact")
print("Icons should display correctly (not as rectangles)")
print("If you see rectangles, check:")
print("  1. Font includes FontAwesome symbols")
print("  2. UTF-8 encoding is correct")
print("  3. Firmware is up to date")
print("=" * 60 + "\n")

# Simulate battery drain
battery_level = 3
battery_counter = 0

while True:
    lvgl.task_handler()

    # Update battery icon every ~5 seconds (simulated)
    battery_counter += 1
    if battery_counter > 500:  # Adjust based on your task_handler delay
        battery_counter = 0
        battery_level = (battery_level - 1) % 5  # Cycle through 0-4

        battery_icons = [
            SYMBOL_BATTERY_EMPTY,
            SYMBOL_BATTERY_1,
            SYMBOL_BATTERY_2,
            SYMBOL_BATTERY_3,
            SYMBOL_BATTERY_FULL,
        ]

        battery_colors = [
            0xFF0000,  # Red - empty
            0xFF6600,  # Orange - low
            0xFFCC00,  # Yellow - medium
            0x66FF00,  # Yellow-green - good
            0x00FF00,  # Green - full
        ]

        battery_label.text = battery_icons[battery_level]
        battery_label.set_text_color(battery_colors[battery_level])
        battery_text.text = f"{battery_level * 25}%"

    time.sleep(0.01)
