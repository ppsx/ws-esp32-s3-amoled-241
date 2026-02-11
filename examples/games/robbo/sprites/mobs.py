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
from . import Sprite, BlinkingSprite

from .guns import fire_blast


class Mob(BlinkingSprite):
    GROUPS = 'mob', 'update', 'fragile'
    UPDATE_TIME = 3

    def __init__(self, pos, dir=0):
        super(Mob, self).__init__(pos)
        self.dir = dir

    def try_step(self, step):
        newrect = self.rect.move(step)
        if rectcollide(newrect, game.board.sprites_blast):
            return True
        if game.board.can_move(newrect):
            self.rect = newrect
            return True
        return False

    def move(self):
        pass

    def update(self):
        super(Mob, self).update()
        self.move()


@Board.sprite('^')
class Bird(Mob):
    IMAGES = images.BIRD1, images.BIRD2
    GROUPS = Mob.GROUPS + ('birds',)

    SHOOT_FREQUENCY = 6

    def __init__(self, pos, dir=0, shooting_dir=None, shooting=None):
        if not hasattr(game.board, 'sprites_birds'):
            game.board.sprites_birds = pygame.sprite.Group()
        super(Bird, self).__init__(pos, dir)
        if shooting is None and shooting_dir is not None:
            shooting = True
        self.shooting = shooting
        self.shooting_dir = shooting_dir

    def move(self):
        step = STEPS[self.dir]
        if not self.try_step(step):
            newrect = self.rect.move(step)
            self.dir = (self.dir + 2) % 4
        if self.shooting:
            if random.randrange(self.SHOOT_FREQUENCY) == 0:
                fire_blast(self, self.shooting_dir)


class Walker(Mob):
    turn = 0

    def move(self):
        dir0 = self.dir
        rect0 = self.rect
        self.dir = (self.dir - self.turn) % 4
        if self.try_step(STEPS[self.dir]):
            # Test if we circle stupidly in an empty space
            if not game.clever_bears or self.rect == rect0:  # turned off waiting for a gun
                return
            dir1 = self.dir
            rect1 = self.rect
            for _ in range(2):
                dir1 = (dir1 - self.turn) % 4
                rect1 = rect1.move(STEPS[dir1])
                if not game.board.can_move(rect1):
                    return
            self.rect = rect0
            self.dir = dir0
        for _ in range(4):
            if self.try_step(STEPS[self.dir]):
                break
            self.dir = (self.dir + self.turn) % 4


@Board.sprite('@')
class Bear(Walker):
    IMAGES = images.BEAR1, images.BEAR2
    turn = +1


@Board.sprite('*')
class Devil(Walker):
    IMAGES = images.DEVIL1, images.DEVIL2
    turn = -1


@Board.sprite('V')
class Eyes(Mob):
    IMAGES = images.BUTTERFLY1, images.BUTTERFLY2

    HUNT_PROBABILITY = 0.8

    def move(self):
        if random.random() < self.HUNT_PROBABILITY:
            # Head for the Robbo
            x0, y0 = self. rect.topleft
            x1, y1 = game.robbo.rect.topleft
            dx, dy = x1 - x0, y1 - y0
            i = 0 if abs(dx) > abs(dy) else 1
            dx = -32 if dx < 0 else 32 if dx > 0 else 0
            dy = -32 if dy < 0 else 32 if dy > 0 else 0
            steps = ((0, dy), (dx, 0)) if i else ((dx, 0), (0, dy))
            if random.randrange(3) == 0:
                steps = reversed(steps)
        else:
            # Random move
            steps = [STEPS[n] for n in (NORTH, SOUTH, EAST, WEST)] + [None]
            for i in range(len(steps) - 1, 0, -1):
                j = random.randrange(i + 1)
                steps[i], steps[j] = steps[j], steps[i]
        for step in steps:
            if step is None or self.try_step(step):
                break


@Board.sprite('=')
class Barrier(BlinkingSprite):
    IMAGES = images.FORCE1, images.FORCE2
    GROUPS = 'blast', 'fragile'
    UPDATE_TIME = 2

    def __init__(self, pos, dir=0):
        super(Barrier, self).__init__(pos)
        self.dir = dir

    def kill(self):
        super(Barrier, self).kill()

    def update(self):
        super(Barrier, self).update()
        newrect = self.rect.move(STEPS[self.dir])
        if game.board.rect.contains(newrect):
            sprites = rectcollide(newrect, game.board.sprites)
            if not sprites:
                self.rect = newrect
                return
            for sprite in sprites:
                if sprite is game.robbo:
                    print(f"DEBUG: Killed by Barrier {self.rect}")
                    game.robbo.die()
                    return
                elif isinstance(sprite, Barrier):
                    self.rect = newrect
                    return
                elif game.board.sprites_static in sprite.groups():
                    width = self.rect.width
                    top = self.rect.top
                    if self.dir == WEST:
                        end = game.board.rect.right - width
                        rect = pygame.Rect(self.rect.right, top,
                                           end - self.rect.left, self.rect.height)
                        select = min
                        dx = - width
                    else:
                        end = game.board.rect.left
                        rect = pygame.Rect(end, top,
                                           self.rect.left - end, self.rect.height)
                        select = max
                        dx = width
                    walls = rectcollide(rect, game.board.sprites_static)
                    if not walls:
                        self.rect = pygame.Rect(end, self.top, width, self.rect.height)
                    else:
                        wall = select(walls, key=lambda s: s.rect.left)
                        self.rect = pygame.Rect(wall.rect.left + dx, top, width, self.rect.height)
                else:
                    sprite.kill()
                    self.rect = newrect


@Board.sprite('M')
class Magnet(Sprite):
    GROUPS = 'static', 'update'

    def __init__(self, pos, dir):
        self.dir = dir
        self.IMAGE = {EAST: images.MAGNET_R, WEST: images.MAGNET_L}[dir]
        super(Magnet, self).__init__(pos)

    def update(self):
        top = self.rect.top
        if game.robbo.rect.top < self.rect.bottom and game.robbo.rect.bottom > top:
            if self.dir == WEST:
                right = game.robbo.rect.right
                left = self.rect.left
            else:
                right = self.rect.right
                left = game.robbo.rect.left
            if left == right:
                print(f"DEBUG: Killed by Magnet {self.rect} (Vertical overlap)")
                game.robbo.die()
            elif left > right:
                rect = pygame.Rect(right, top, left - right, self.rect.height)
                if not rectcollide(rect, game.board.sprites):
                    game.robbo.active = False
                    game.robbo.walking = STOP
                    game.robbo.step = STEPS[2-self.dir]
