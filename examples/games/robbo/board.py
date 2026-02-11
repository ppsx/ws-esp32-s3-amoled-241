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

import pygame

from . import game, screen_rect, screen


class Board(object):
    """
    Game board

    Holds all static and moving sprites.
    """

    symbols = {}

    class sprite(object):
        """Sprite decorator for automatic symbol registering"""
        def __init__(self, symbols):
            self.symbols = symbols
        def __call__(self, cls):
            for symbol in self.symbols:
                Board.symbols[symbol] = cls
            return cls

    def __init__(self):
        self.sprites = pygame.sprite.RenderPlain()          # all sprites
        self.sprites_static = pygame.sprite.Group()         # walls
        self.sprites_update = pygame.sprite.RenderPlain()   # elements that move or blink
        self.sprites_push = pygame.sprite.Group()           # elements that can be pushed
        self.sprites_collect = pygame.sprite.Group()        # collectibles
        self.sprites_door = pygame.sprite.Group()           # doors (can be open with keys)
        self.sprites_teleport = pygame.sprite.Group()       # teleports
        self.sprites_mob = pygame.sprite.Group()            # mobs
        self.sprites_durable = pygame.sprite.Group()        # durable sprite
        self.sprites_fragile = pygame.sprite.Group()        # destroyed on hit
        self.sprites_blast = pygame.sprite.Group()          # blast
        self.sprites_capsule = pygame.sprite.Group()        # capsules
        self.teleports = []
        self.scroll_offset = [0, 0]
        self.background = pygame.Surface(screen.get_size())
        self.background = self.background.convert()

    def add_sprite(self, sprite):
        self.sprites.add(sprite)
        for group in sprite.GROUPS:
            try:
                getattr(self, 'sprites_'+group).add(sprite)
            except AttributeError:
                pass

    def init(self, level):
        """
        Load and init level data
        """
        # Clear sprites from previous level (important for death/reinit)
        for s in self.sprites.sprites():
            s.kill()

        try:
            self.background.fill(bytes.fromhex(level.get('colour', '000000')))
        except (TypeError, ValueError):
            self.background.fill(bytes.fromhex('000000'))

        screen.blit(self.background, screen_rect)

        additional = level['additional']

        tgs = {}
        for g, n in additional.get('&', {}).values():
            tgs[g] = max(n+1, tgs.get(g, 0))
        self.teleports = dict((g, [None] * tgs[g]) for g in tgs)

        mx = 0
        y = 0
        for y, row in enumerate(level['data'].splitlines()):
            for x, c in enumerate(row):
                mx = max(mx, x)
                p = x, y
                data = additional.get(c, {}).get(p, ())
                Sprite = self.symbols.get(c)
                if Sprite is not None:
                    self.add_sprite(Sprite(p, *data))

        self.size = mx+1, y+1
        self.rect = pygame.Rect(screen_rect.topleft, (32 * self.size[0], 32 * self.size[1]))

        self.chain = []

        if 'screws' in level:
            game.status.parts = level['screws']

        if game.status.parts == 0:
            show = True
            for capsule in game.board.sprites_capsule:
                capsule.activate(show)
                show = False

    def move_sprite(self, sprite, step):
        """Move sprive by given step"""
        sprite.rect.move_ip(step)
        screen.blit(sprite.image, sprite.rect)

    def can_move(self, rect, *groups):
        """Check if a sprite can be moved to rect and does not collide with any sprite from the group"""

        # Check we we exit the game area
        if not self.rect.contains(rect):
            return False

        # Check if any sprite from the group blocks us
        if groups:
            for group in groups:
                if rectcollide(rect, getattr(self, 'sprites_'+group)):
                    return False
            return True
        else:
            return not rectcollide(rect, self.sprites)


def rectcollide(rect, group):
    """
    Check if specified rectangle collides with a group of sprites

    :param rect: Rect to test
    :param group: sprite group to test
    """
    crashed = []
    spritecollide = rect.colliderect
    try:
        sprites = group.sprites()
    except AttributeError:
        sprites = group
    for s in sprites:
        if spritecollide(s.rect):
            crashed.append(s)
    return crashed
