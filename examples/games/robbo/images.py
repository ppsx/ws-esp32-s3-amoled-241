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


MAGNET_R = 0
MAGNET_L = 1
WALL_GRAY = 2
WALL_RED = 3
SCREW = 4
BULLET = 5
BOX = 6
KEY = 7
BOMB = 8
DOOR = 9
QUESTION = 10
BEAR1 = 11
BEAR2 = 12
BIRD1 = 13
BIRD2 = 14
CAPSULE1 = 15
CAPSULE2 = 16
VOID = 17
BOX_SLIDE = 18
LIFE = 20
STARS3 = 21
STARS2 = 22
STARS1 = 23
GRASS = 24
WALL_GREEN = 25
DEVIL1 = 26
DEVIL2 = 27
BUTTERFLY1 = 28
BUTTERFLY2 = 29
BLAST_H1 = 30
BLAST_H2 = 31
BLAST_V1 = 32
BLAST_V2 = 33
S_PARTS = 34
S_LIFES = 35
S_KEYS = 36
S_BULLETS = 37
S_LEVEL = 38
FORCE1 = 39
FORCE2 = 49
TELEPORT1 = 40
TELEPORT2 = 41
GUN_E = 45
GUN_S = 46
GUN_W = 47
GUN_N = 48
ROBBO_E1 = 50
ROBBO_E2 = 51
ROBBO_S1 = 52
ROBBO_S2 = 53
ROBBO_W1 = 54
ROBBO_W2 = 55
ROBBO_N1 = 56
ROBBO_N2 = 57


class Images(object):
    """
    Class responsible for visuals managements

    Unlike sounds this is kept in class, so multiple skin pack can be selected.
    """

    def __init__(self):
        # Simplified loading
        # Manual dirname for CircuitPython where os.path may be missing
        base_path = __file__.rsplit('/', 1)[0]
        self.skin_path = base_path + '/skins/default/'
        self._cache = {}
        self._digits = None

    def _get_icon_rect(self, n):
        """
        Get icon location in the skin image
        """
        return pygame.Rect(34*(n%10)+2, 34*(n//10)+2, 32, 32)

    def get_icon(self, n):
        """Get icon with given number"""
        # Aliasing for black tile duplicates
        if n in [19, 58, 59]:
            n = 17
            
        if n in self._cache:
            return self._cache[n]
            
        try:
             # Load pre-split BMP
             path = f"{self.skin_path}bmp/icon_{n}.bmp"
             img = pygame.image.load(path)
             self._cache[n] = img
             return img
        except Exception as e:
             print(f"Missing icon {n}: {e}")
             fallback = pygame.Surface((32,32))
             fallback.fill((255, 0, 255)) # Magenta for error
             self._cache[n] = fallback
             return fallback

    def get_digits(self):
        """Get table with digit images"""
        if self._digits is not None:
            return self._digits
        self._digits = []
        for n in range(10):
            try:
                path = f"{self.skin_path}bmp/digit_{n}.bmp"
                self._digits.append(pygame.image.load(path))
            except:
                self._digits.append(pygame.Surface((16,32)))
        return self._digits
