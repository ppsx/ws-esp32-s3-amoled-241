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

from . import Sprite, BlinkingSprite, Stars, explode
from .guns import Gun, hit
from .static import Grass
from .mobs import Eyes


@Board.sprite('#')
class Box(Sprite):
    IMAGE = images.BOX
    GROUPS = 'push',


@Board.sprite('~')
class SlideBox(Sprite):
    IMAGE = images.BOX_SLIDE
    GROUPS = 'push', 'update'

    def __init__(self, pos):
        super(SlideBox, self).__init__(pos)
        self._step = None

    def push(self, step):
        self._step = step
        game.board.sprites_blast.add(self)
        game.board.sprites_update.remove(self)

    def update(self):
        if self._step is not None:
            newrect = self.rect.move(self._step)
            if hit(newrect) or not game.board.rect.contains(newrect):
                self._step = None
                game.board.sprites_blast.remove(self)
                game.board.sprites_update.add(self)
            else:
                self.rect = newrect


@Board.sprite('b')
class Bomb(Sprite):
    IMAGE = images.BOMB
    GROUPS = 'push', 'fragile'

    _chain = []

    def hit(self):
        sounds.play(sounds.bomb)
        rects = [self.rect.move((x, y)) for x in (-SIZE, 0, SIZE) for y in (-SIZE, 0, SIZE) if x != 0 or y != 0]
        rect = self.rect.inflate(64, 64)
        explode(self)
        hits = rectcollide(rect, game.board.sprites)
        for hit in hits:
            try: rects.remove(hit.rect)
            except ValueError: pass
            if hit is game.robbo:
                print(f"DEBUG: Killed by Bomb {self.rect}")
                game.robbo.die()
            elif isinstance(hit, Bomb):
                game.board.chain.append(hit)
            elif game.board.sprites_durable not in hit.groups():
                explode(hit)
        for rect in rects:
            game.board.add_sprite(Stars(rect))

    def chain(self):
        self.hit()


@Board.sprite('!')
class Capsule(BlinkingSprite):
    IMAGES = images.CAPSULE1, images.CAPSULE2
    UPDATE_TIME = 0
    GROUPS = 'push', 'update', 'durable', 'capsule'

    def __init__(self, pos):
        super(Capsule, self).__init__(pos)
        self.active = False

    def activate(self, yuppie=True):
        if yuppie:
            sounds.play(sounds.lastscrew)
            original = screen.copy()
            screen.fill((255, 255, 255))
            pygame.display.flip()
            screen.blit(original, (0,0))
            game.clock.tick(24)     # cinematic frame ;)
            pygame.display.flip()
        self.active = True
        self.UPDATE_TIME = self.update_time = 3


@Board.sprite('T')
class Screw(Sprite):
    IMAGE = images.SCREW
    GROUPS = 'collect',

    def __init__(self, pos):
        super(Screw, self).__init__(pos)
        game.status.parts += 1

    def collect(self):
        if game.status.parts > 0:
            game.status.parts -= 1
        game.status.update()
        # Play sound
        sounds.play(sounds.screw)
        if game.status.parts == 0 and any(not capsule.active for capsule in game.board.sprites_capsule):
            show = True
            for capsule in game.board.sprites_capsule:
                capsule.activate(show)
                show = False


@Board.sprite("'")
class Bullet(Sprite):
    IMAGE = images.BULLET
    GROUPS = 'collect',

    def collect(self):
        game.status.bullets += 9
        game.status.update()
        sounds.play(sounds.bullet)


@Board.sprite('%')
class Key(Sprite):
    IMAGE = images.KEY
    GROUPS = 'collect',

    def collect(self):
        game.status.keys += 1
        game.status.update()
        sounds.play(sounds.key)


@Board.sprite('D')
class Door(Sprite):
    IMAGE = images.DOOR
    GROUPS = 'door',

    def open(self):
        game.status.keys -= 1
        game.status.update()
        sounds.play(sounds.door)


@Board.sprite('?')
class Surprise(Sprite):
    IMAGE = images.QUESTION
    GROUPS = 'push', 'fragile'

    class Spawn(Stars):
        def update(self):
            self._todie -= 1
            if self._todie % self.UPDATE_TIME == 0:
                if self._todie:
                    self.image = self._images[self._todie // self.UPDATE_TIME - 1]
                else:
                    choice = random.choice((
                        None,
                        SlideBox,
                        Screw,
                        Bullet,
                        Key,
                        Bomb,
                        Grass,
                        Gun,
                        Surprise,
                        Eyes,
                        Capsule,
                        # Life,
                    ))
                    self.kill()
                    if choice is not None:
                        pos = (self.rect.left - screen_rect.x) // SIZE, (self.rect.top - screen_rect.y) // SIZE
                        sprite = choice(pos)
                        game.board.add_sprite(sprite)
                        if isinstance(sprite, Screw):
                            game.status.parts -= 1  # screw constructor increased this
                        elif isinstance(sprite, Capsule):
                            sprite.activate(False)
                        game.board.sprites.draw(screen)

    def hit(self):
        self.kill()
        game.board.add_sprite(self.Spawn(self.rect))
