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

from warnings import warn
from .. import game, images, sounds
from ..board import Board
from ..defs import *
from . import BlinkingSprite, Stars


@Board.sprite('&')
class Teleport(BlinkingSprite):
    """
    Teleport sprite
    """
    IMAGES = images.TELEPORT1, images.TELEPORT2
    GROUPS = 'teleport', 'update'
    UPDATE_TIME = 3

    def __init__(self, pos, group=None, no=None):
        super(Teleport, self).__init__(pos)
        if group is not None:
            self.group = group
            self.no = no
            game.board.teleports[group][no] = self
        else:
            self.group = None

    def teleport(self, step):
        """Move Robbo to the target teleport"""

        # Check possible destination
        direct = STEPS.index(step)
        moved = 0
        next = self.no
        while True:
            if self.group is not None and next is not None:
                next = (next + 1) % len(game.board.teleports[self.group])
                dest = game.board.teleports[self.group][next]
                if dest is None: continue
            else:
                dest = self
            for k in range(4):
                step = STEPS[direct]
                newrect = dest.rect.move(step)
                if game.board.can_move(newrect):
                    moved = 1
                    break
                direct ^= (((k + 1) % 2) + 2)
            if moved or self.group is None or next == self.no:
                break

        # Create disappear stars
        if moved:
            game.board.add_sprite(Stars(game.robbo.rect))
        # Or make Robbo reappear in the same place
        else:
            step = [0,0]
            dest = game.robbo

        # Move Robbo
        game.robbo.rect = dest.rect.move(step)

        # Make appear stars
        game.robbo.spawn()

        # Play sound
        sounds.play(sounds.teleport)


