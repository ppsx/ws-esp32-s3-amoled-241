# coding: utf8
# Copyright (C) 2019 Maciej Dems <maciej.dems@p.lodz.pl>
# CircuitPython port: Copyright (c) 2025 Przemyslaw Patrick Socha
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of GNU General Public License as published by the
# Free Software Foundation; either version 3 of the license, or (at your
# opinion) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import time
import pygame
from pygame.locals import *

from .defs import *

levels = None
images = None
status = None
board = None
robbo = None

from . import screen, screen_rect, clock, clock_speed, skin, sounds, quit
from .board import Board
from .images import Images
from .status import Status

# Register all sprites — do not remove the line below
from .sprites import explode


clever_bears = False

MOVES = {
    K_UP: NORTH,
    K_DOWN: SOUTH,
    K_LEFT: WEST,
    K_RIGHT: EAST,
    K_w: NORTH,
    K_s: SOUTH,
    K_a: WEST,
    K_d: EAST
}

SCROLLS = {
    K_UP: SCROLL_UP,
    K_DOWN: SCROLL_DOWN,
    K_w: SCROLL_UP,
    K_s: SCROLL_DOWN
}

JOYSTICK_MOVES = {
    (0, -1): WEST,
    (0, 1): EAST,
    (1, -1): NORTH,
    (1, 1): SOUTH,
}

JOYSTICK_SCROLLS = {
    -1: SCROLL_UP,
    1: SCROLL_DOWN
}


class EndLevel(Exception):
    """End level exception"""
    pass


class SelectLevel(Exception):
    """Level selected exception"""
    def __init__(self, level):
        self.level = level


class ChangeLevelSet(Exception):
    """Load levels exception"""
    pass


def update_sprites():
    board.sprites_update.update()
    board.sprites_blast.update()


def draw_sprites():
    screen.fill(0)  # black full screen (side strips + status bar)
    bg = board.background.fill_color
    if bg:
        screen.fill(bg, screen_rect)
    board.sprites.draw(screen)
    scrclip = screen.get_clip()
    screen.set_clip(screen.get_rect())
    status.refresh()
    status.update()
    screen.set_clip(scrclip)
    pygame.display.flip()


def play_level(level):
    """The game loop"""
    pygame.mouse.set_visible(False)

    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
    joystick_axes = [0, 0]
    joystick_axis = None

    global clock_speed, clever_bears

    # Init global game objects
    global images, status, board
    images = Images()

    # Center board horizontally
    cols = max(len(row) for row in levels[level]['data'].splitlines())
    board_w = cols * SIZE
    x_off = ((600 - board_w) // 2) & ~1  # 2-pixel aligned for RM690B0
    screen_rect.x = x_off
    screen_rect.width = board_w

    status = Status(level)
    board = Board()

    screen.fill(0)  # black entire screen (side strips)
    screen.set_clip(screen_rect)
    board.init(levels[level])
    # print(f"DEBUG: Board initialized. Robbo at {robbo.rect if robbo else 'None'}")
    status.update()

    scrolling = 0       # are we scrolling?
    scroll_step = 0       # scrolling direction
    fire_button = False   # CENTER button held = fire mode
    reset_tap_count = 0   # triple-tap CENTER = level reset
    reset_tap_deadline = 0

    # Draw static sprites
    board.sprites.draw(screen)

    try:
        while True:
            # Check if robbo died and, if so, recreate board
            if not robbo.alive():
                # Wait
                for _ in range(6):
                    update_sprites()
                    draw_sprites()
                    clock.tick(clock_speed)
                # Cleanup board
                print("DEBUG: Robbo died!")
                sounds.play(sounds.die)
                for sprite in board.sprites.sprites():
                    explode(sprite)
                for _ in range(12):     # timeout
                    if not board.sprites: break
                    update_sprites()
                    draw_sprites()
                    clock.tick(clock_speed)
                # Wait
                for _ in range(6):
                    update_sprites()
                    clock.tick(clock_speed)
                # Recreate board
                offset = board.scroll_offset[1]
                status.clear()
                board.init(levels[level])
                status.update()
                for sprite in board.sprites.sprites():
                    sprite.rect.move_ip(0, offset)
                board.scroll_offset = [0, offset]
                board.rect.move_ip(0, offset)
                board.sprites.draw(screen)

            # Test for chained bombs and trigger them
            chain = board.chain
            board.chain = []
            for item in chain:
                item.chain()

            move = None
            joystick_can_fire = True

            # Process user events
            for event in pygame.event.get():
                if event.type == QUIT:
                    quit()
                elif event.type == KEYDOWN:
                    # Robbo moves
                    mods = pygame.key.get_mods()
                    if event.key == K_RCTRL:
                        fire_button = True
                        robbo.move_key(STOP)
                        # Triple-tap detection for level reset
                        now = time.monotonic()
                        if now < reset_tap_deadline:
                            reset_tap_count += 1
                        else:
                            reset_tap_count = 1
                        reset_tap_deadline = now + 0.6
                        if reset_tap_count >= 3:
                            reset_tap_count = 0
                            fire_button = False
                            scrolling = 0
                            status.clear()
                            board.scroll_offset = [0, 0]
                            board.init(levels[level])
                            status.update()
                            board.sprites.draw(screen)
                    elif event.key in MOVES:
                        move = MOVES[event.key]
                        if fire_button:
                            robbo.fire(move)
                            move = None
                        elif mods & KMOD_CTRL:
                            if event.key in SCROLLS:
                                scrolling = True
                                scroll_step = SCROLLS[event.key]
                        elif mods & KMOD_SHIFT:
                            robbo.fire(move)
                            move = None
                        else:
                            robbo.move_key(move)
                    # system keys
                    elif event.key == K_f:
                        # if not pygame.display.toggle_fullscreen():
                            import robbo as main
                            flags = main.FLAGS_WINDOW if screen.get_flags() & pygame.FULLSCREEN else main.FLAGS_FULLSCREEN
                            main.screen = pygame.display.set_mode((640, 480), flags)
                            status.refresh()
                            status.update()
                            screen.set_clip(screen_rect)
                    elif event.key == K_l and mods & KMOD_CTRL and not mods & (KMOD_ALT | KMOD_META):
                        draw_sprites()
                        if mods & KMOD_SHIFT:
                            raise ChangeLevelSet()
                        else:
                            raise SelectLevel(status.select_level())
                    elif event.key == K_b and mods & KMOD_CTRL and not mods & (KMOD_ALT | KMOD_META | KMOD_SHIFT):
                        clever_bears = not clever_bears
                    elif event.key == K_m and mods & KMOD_CTRL and not mods & (KMOD_ALT | KMOD_META | KMOD_SHIFT):
                        sounds.mute = not sounds.mute
                    elif event.key == K_PLUS or event.key == K_EQUALS:
                        clock_speed *= 1.2
                    elif event.key == K_MINUS:
                        clock_speed /= 1.2
                    elif event.key == K_x and mods & KMOD_CTRL and not mods & (KMOD_SHIFT | KMOD_ALT | KMOD_META):
                        robbo.die()
                    elif event.key == K_q and mods & KMOD_CTRL and not mods & (KMOD_SHIFT | KMOD_ALT | KMOD_META):
                        quit()
                elif event.type == KEYUP:
                    if event.key == K_RCTRL:
                        fire_button = False
                    elif MOVES.get(event.key) == robbo.walking:
                        if move: robbo.update()
                        robbo.move_key(STOP)
                    elif event.key == K_LCTRL:
                        scrolling = 0
                    if scrolling is True and SCROLLS.get(event.key) == scroll_step:
                        if pygame.key.get_mods() & KMOD_CTRL:
                            scrolling = False
                        else:
                            scrolling = 0
                elif event.type == pygame.JOYAXISMOTION and event.axis < 2:
                    prev = joystick_axes[event.axis]
                    if prev == -1:
                        curr = -1 if event.value <= -0.45 else 1 if event.value >= 0.50 else 0
                    elif prev == 1:
                        curr = 1 if event.value >= 0.45 else -1 if event.value <= -0.50 else 0
                    else:
                        curr = -1 if event.value <= -0.55 else 1 if event.value >= 0.55 else 0
                    if curr != prev:
                        joystick_axes[event.axis] = curr
                        if joystick.get_numbuttons() > 1 and joystick.get_button(1):
                            if event.axis == 1:
                                if curr != 0:
                                    scrolling = True
                                    scroll_step = JOYSTICK_SCROLLS[curr]
                                else:
                                    scrolling = False
                        else:
                            if curr != 0:
                                move = JOYSTICK_MOVES[(event.axis, curr)]
                                if joystick.get_button(0):
                                    if joystick_can_fire: robbo.fire(move)
                                    joystick_can_fire = False
                                else:
                                    robbo.move_key(move)
                                    joystick_axis = event.axis
                            elif joystick_axis == event.axis:
                                robbo.move_key(STOP)
                                joystick_axis = event.axis
                elif event.type == pygame.JOYBUTTONUP and event.button == 1:
                    scrolling = 0
            pygame.event.pump()

            # Check if scrolling is needed
            if scrolling and (
                    (board.scroll_offset[1] >= 0 and scroll_step == SCROLL_UP) or
                    (board.rect.bottom <= screen_rect.height + SIZE and scroll_step == SCROLL_DOWN)
            ):
                scrolling = False if scrolling is True else 0
            else:
                if robbo.rect.top < screen_rect.top + 2*SIZE and board.scroll_offset[1] < 0:
                    if not isinstance(scrolling, bool):
                        scrolling = 3; scroll_step = SCROLL_UP
                elif robbo.rect.bottom > screen_rect.bottom - 2*SIZE and board.rect.bottom > screen_rect.height+SIZE:
                    if not isinstance(scrolling, bool):
                        scrolling = 3; scroll_step = SCROLL_DOWN
                elif scrolling and scrolling is not True:
                        scrolling -= 1

            # print(scrolling)

            update_sprites()

            robbo.update()

            if scrolling:
                for _ in range(2):
                    for sprite in board.sprites.sprites():
                        sprite.rect.move_ip(0, scroll_step)
                    board.scroll_offset[1] += scroll_step
                    board.rect.move_ip(0, scroll_step)
                    draw_sprites()
            else:
                # Draw moving sprites
                draw_sprites()
                clock.tick(clock_speed)

    except EndLevel:
        sounds.play(sounds.finish)
        robbo.kill()
        # Show loading screen instead of slow pixel-by-pixel fade
        hw = pygame.display.get_hw_driver()
        if hw:
            hw.fill_color(0)
            hw.set_font(2)  # 16x24 monospace
            hw.text(120, 180, "Landing at next planet.", 0xFFFF)
            hw.text(180, 220, "Please wait...", 0xFFFF)
            hw.swap_buffers()
