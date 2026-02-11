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

from .. import images
from ..board import Board
from . import Sprite


@Board.sprite('oO')
class GreyWall(Sprite):
    """Grey wall"""
    IMAGE = images.WALL_GRAY
    GROUPS = 'static', 'durable'


@Board.sprite('qQpPsS')
class RedWall(Sprite):
    """Red wall"""
    IMAGE = images.WALL_RED
    GROUPS = 'static', 'durable'


@Board.sprite('-')
class Void(Sprite):
    """Black void"""
    IMAGE = images.VOID
    GROUPS = 'static', 'durable'


@Board.sprite('H')
class Grass(Sprite):
    IMAGE = images.GRASS
    GROUPS = 'static', 'fragile'
