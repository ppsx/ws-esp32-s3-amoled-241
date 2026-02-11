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


BASE_DIR = "/games"

import sys

try:
    import robbo
except ImportError:
    if __file__ == "<stdin>":
        path = BASE_DIR
    else:
        path = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."
    sys.path.insert(0, path)
    import robbo

def main():
    """Entry point for menu launcher"""
    robbo.main()

if __name__ == "__main__":
    main()
