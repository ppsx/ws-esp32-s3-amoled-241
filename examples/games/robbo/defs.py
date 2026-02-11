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

import os

# Directions
NORTH = 3
EAST = 0
SOUTH = 1
WEST = 2

# Cell size
SIZE = 32

# Robbo steps
STEPS = (SIZE, 0), (0, SIZE), (-SIZE, 0), (0, -SIZE)
STOP = -1

# Scroll steps
SCROLL_UP = SIZE // 2
SCROLL_DOWN = -SCROLL_UP


# Directories - Simplified for CircuitPython
DATA_DIRS = ['/games/robbo']  # robbo folder is in /games/
