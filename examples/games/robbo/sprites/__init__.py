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

from .. import game, screen, screen_rect, images
from ..defs import SIZE


class Sprite(pygame.sprite.Sprite):
    IMAGE = None

    def __init__(self, pos):
        super(Sprite, self).__init__()
        if self.IMAGE is not None:
            self.image = game.images.get_icon(self.IMAGE)
        self.rect = pygame.Rect(SIZE*pos[0], SIZE*pos[1], SIZE, SIZE).move(screen_rect.topleft)


class BlinkingSprite(Sprite):
    """
    Sprite with multiple _images
    """
    GROUPS = 'update',
    IMAGES = None

    UPDATE_TIME = 1  # update frequency

    def __init__(self, pos):
        super(BlinkingSprite, self).__init__(pos)
        if self.IMAGES is not None:
            self._images = tuple(game.images.get_icon(icon) for icon in self.IMAGES)
            self._imageno = 0
            self.image = self._images[0]
            self.update_time = self.UPDATE_TIME

    def update(self):
        """
        Update image state

        Return value can be used by subclasses to do their own update.
        """
        if self.UPDATE_TIME:
            self.update_time -= 1
            if not self.update_time:
                self.update_time = self.UPDATE_TIME
                self._imageno = (self._imageno + 1) % len(self.IMAGES)
                self.image = self._images[self._imageno]
                return True
            return False


class Stars(pygame.sprite.Sprite):
    """
    Teleport and die stars
    """
    GROUPS = 'blast', 'durable'
    UPDATE_TIME = 1

    def __init__(self, rect):
        super(Stars, self).__init__()
        self._images = (
            game.images.get_icon(images.STARS1),
            game.images.get_icon(images.STARS2),
            game.images.get_icon(images.STARS3))
        self.rect = rect
        self._todie = len(self._images) * self.UPDATE_TIME
        self.image = self._images[-1]

    def update(self):
        self._todie -= 1
        if self._todie < 0:
            self._todie = 0
            self.kill()
            return
            
        if self._todie % self.UPDATE_TIME == 0:
            if self._todie:
                # Safe index calculation
                idx = self._todie // self.UPDATE_TIME - 1
                if idx >= 0 and idx < len(self._images):
                     self.image = self._images[idx]
            else:
                self.kill()


def explode(target):
    if not isinstance(target, Stars):
        target.kill()
        game.board.add_sprite(Stars(target.rect))


# Register all sprites
from . import static,  items, mobs, teleport, robbo, guns
