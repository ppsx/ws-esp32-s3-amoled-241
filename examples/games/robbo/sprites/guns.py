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

import random
import pygame

from .. import game, screen, screen_rect, images, sounds
from ..board import Board, rectcollide
from ..defs import *

from . import Sprite, Stars


def hit(rect, oldrect=None):
    hits = rectcollide(rect, game.board.sprites)
    if hits:
        for hit in hits:
            if game.board.sprites_fragile in hit.groups():
                if hasattr(hit, 'hit'):
                    hit.hit()
                else:
                    sounds.play(sounds.blaster)
                    hit.kill()
                    game.board.add_sprite(Stars(hit.rect))
            elif oldrect is not None:
                    game.board.add_sprite(Stars(oldrect))
        return True
    else:
        return False


class ShortBlast(pygame.sprite.Sprite):
    """
    Short blast shot by Robbo and guns
    """
    GROUPS = 'blast',
    UPDATE_TIME = 1

    def __init__(self, rect, dir, icon=None, flash=True):
        super(ShortBlast, self).__init__()
        self.dir = dir
        self.flash = flash
        if icon is None:
            if dir == EAST or dir == WEST:
                self._images = game.images.get_icon(images.BLAST_H1), game.images.get_icon(images.BLAST_H2)
            else:
                self._images = game.images.get_icon(images.BLAST_V1), game.images.get_icon(images.BLAST_V2)
            self._ci = 0
            self.image = self._images[0]
        else:
            self._images = None
            self.image = game.images.get_icon(icon)
        self.rect = rect

    def update(self):
        newrect = self.rect.move(STEPS[self.dir])
        if not game.board.rect.contains(newrect) or hit(newrect, self.rect if self.flash else None):
            self.kill()
            return
        self.rect = newrect
        if self._images is not None:
            self._ci = 1 - self._ci
            self.image = self._images[self._ci]


def fire_blast(source, dir, icon=None, flash=True):
    testrect = source.rect.move(STEPS[dir])
    if not hit(testrect):
        blast = ShortBlast(source.rect, dir, icon, flash)
        game.board.add_sprite(blast)


@Board.sprite('Ll')
def place_blast(pos, dir=0):
    rect = pygame.Rect(SIZE*pos[0], SIZE*pos[1], SIZE, SIZE).move(screen_rect.topleft)
    return ShortBlast(rect, dir)


class LongBlast(pygame.sprite.Sprite):
    """
    Short blast shot by Robbo and guns
    """
    GROUPS = 'blast',

    END_IMAGES = images.STARS1, images.STARS3, images.STARS1

    def __init__(self, rect, dir, prev):
        super(LongBlast, self).__init__()
        self.dir = dir
        if dir == EAST or dir == WEST:
            self._images = game.images.get_icon(images.BLAST_H1), game.images.get_icon(images.BLAST_H2)
        else:
            self._images = game.images.get_icon(images.BLAST_V1), game.images.get_icon(images.BLAST_V2)
        if isinstance(prev, LongBlast):
            self.ci = prev.ci
            self._skipframe = False
        else:
            self.ci = 0
            self._skipframe = True  # we need this as this will be updated in the same frame
        self.image = self._images[0]
        self.rect = rect
        self._prev = prev
        self._head = True
        self._end = None

    def update(self):
        if self._skipframe:
            self._skipframe = False
            return
        self.ci = (self.ci + 1) % len(self._images)
        self.image = self._images[self.ci]
        if self._head:
            self._head = False
            newrect = self.rect.move(STEPS[self.dir])
            if not game.board.rect.contains(newrect) or hit(newrect):
                game.board.chain.append(self)
            else:
                next = LongBlast(newrect, self.dir, self)
                game.board.add_sprite(next)
        elif self._end is not None:
            if self._end == 0:
                super(LongBlast, self).kill()
                self._prev.blasting = False
            self._end -= 1

    def chain(self):
        if isinstance(self._prev, LongBlast):
            super(LongBlast, self).kill()
            game.board.chain.append(self._prev)
        elif isinstance(self._prev, Gun):
            self._images = tuple(game.images.get_icon(i) for i in self.END_IMAGES)
            self.ci = -1
            self._end = len(self.END_IMAGES)

    def kill(self):
        super(LongBlast, self).kill()
        if isinstance(self._prev, LongBlast):
            game.board.chain.append(self._prev)
        elif isinstance(self._prev, Gun):
            self._prev.blasting = False


@Board.sprite('}')
class Gun(Sprite):
    GROUPS = 'update',
    IMAGES = images.GUN_E, images.GUN_S, images.GUN_W, images.GUN_N

    SHOOT_FREQUENCY = 12
    ROTATE_FREQUENCY = 12

    MOVE_DELAY = 3

    BIG_BLAST_ICONS = images.STARS1, images.STARS2, images.STARS3, images.STARS2, images.STARS1

    def __init__(self, pos, facing=None, moving=None, shot_type=0, moves=None, rotates=False, rotates_random=False):
        if facing is None:
            facing = random.randrange(4)
            rotates = 1
            rotates_random = 1
            shot_type = 0
        self.IMAGE = self.IMAGES[facing]
        super(Gun, self).__init__(pos)
        self.facing = facing
        self.shot_type = shot_type
        self.rotates_random = rotates_random
        self.rotates = rotates
        self._to_rotate = self.ROTATE_FREQUENCY
        self.moves = moves
        self.moving = moving
        if moves:
            self.GROUPS = Gun.GROUPS + ('push',)
            self._tomove = self.MOVE_DELAY
        else:
            self.GROUPS = Gun.GROUPS + ('static',)
        self.blasting = False

    def update(self):
        if not self.blasting:
            if self.moves:
                self._tomove -= 1
                if self._tomove == 0:
                    step = STEPS[self.moving]
                    newrect = self.rect.move(step)
                    if game.board.can_move(newrect):
                        self.rect = newrect
                    else:
                        self.moving = (self.moving + 2) % 4
                        if game.board.can_move(newrect): self.rect = newrect
                    self._tomove = self.MOVE_DELAY
            if self.rotates:
                if self.rotates_random:
                    self._to_rotate = random.randrange(self.ROTATE_FREQUENCY)
                else:
                    self._to_rotate -= 1
                if self._to_rotate == 0:
                    self._to_rotate = self.ROTATE_FREQUENCY
                    twist = -1
                    if self.rotates_random and random.randrange(2): twist = 1
                    self.facing = (self.facing + twist) % 4
                    self.image = game.images.get_icon(self.IMAGES[self.facing])
        if self.shot_type == 2:
            if self.blasting:
                self.blasting -= 1
                blast = ShortBlast(self.rect, self.facing, self.BIG_BLAST_ICONS[self.blasting], False)
                game.board.add_sprite(blast)
            else:
                if random.randrange(self.SHOOT_FREQUENCY) == 0:
                    fire_blast(self, self.facing, self.BIG_BLAST_ICONS[-1], False)
                    self.blasting = len(self.BIG_BLAST_ICONS) - 1
        elif self.shot_type == 1:
            if not self.blasting and random.randrange(self.SHOOT_FREQUENCY) == 0:
                rect = self.rect.move(STEPS[self.facing])
                if game.board.rect.contains(rect) and not hit(rect):
                    game.board.add_sprite(LongBlast(rect, self.facing, self))
                    self.blasting = True
        elif random.randrange(self.SHOOT_FREQUENCY) == 0:
            fire_blast(self, self.facing)
