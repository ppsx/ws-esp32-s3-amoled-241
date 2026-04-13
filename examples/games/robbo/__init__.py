# Copyright (c) 2025 Przemyslaw Patrick Socha

BASE_DIR = "/games/robbo"

# coding: utf8
import sys

# Ensure local pygame shim is found
try:
    shim_path = __file__.rsplit('/', 1)[0]
except:
    shim_path = "."
sys.path.append(shim_path)
sys.path.append(BASE_DIR)

import pygame
from pygame.locals import *

from .defs import *
from .level_loader import load_levels

# Constants
FLAGS_FULLSCREEN = 0
FLAGS_WINDOW = 0

# Globals
clock = None
clock_speed = None
screen = None
screen_rect = None
skin = 'default'
levelset = 'original'
levels = {}

def quit():
    pygame.quit()
    sys.exit()

def main(display=None):
    global skin, levelset, clock, clock_speed, screen, screen_rect

    # Initialize Shim
    pygame.init()

    # Inject external display before set_mode if provided
    if display is not None:
        pygame.display.inject_display(display)

    # Setup Display
    # Hardware specific size usually, but game expects 640x480 logic sometimes
    # Shim set_mode ignores size arguments usually and gives HW surface
    screen = pygame.display.set_mode((600, 450))
    
    # Define game area rect (used for clipping in original game)
    # Original was (64, 32), (512, 384) for 640x480
    # Our screen is 600x450.
    # Let's use almost full screen or center it.
    # 512x384 fits in 600x450.
    # Limit screen_rect for board to leave room for status bar
    # 600x450, status Y=416, leaves 34px
    screen_rect = pygame.Rect(0, 0, 600, 416)
    
    clock = pygame.time.Clock()
    clock_speed = 8
    
    # Load Levels directly
    from . import game, sounds
    
    # Hardcoded config
    game.clever_bears = False
    sounds.mute = False

    try:
        # Main Game Loop
        while True:
            try:
                print(f"Loading level set: {levelset}")
                game.levels = load_levels(levelset)
                if not game.levels:
                     print("No levels found!")
                     return
            except Exception as e:
                print(f"Error loading levels: {e}")
                return

            level = 0
            while level < len(game.levels):
                try:
                    # Run level
                    game.play_level(level)

                except game.SelectLevel as selected:
                    if 0 <= selected.level < len(game.levels):
                        level = selected.level
                except game.ChangeLevelSet:
                    pass # Not implemented yet
                else:
                    level += 1

                if level >= len(game.levels):
                    level = 0

    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"\nGame crashed: {e}")
    finally:
        print("Cleaning up...")
        pygame.quit()
        print("Robbo exited")
