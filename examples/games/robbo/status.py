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

import sys

import pygame

from . import screen, game, images, quit


class Status(object):
    """
    Status data and display
    """

    DIGITBG = pygame.Surface((16, 32))
    DIGITBG = DIGITBG.convert()
    DIGITBG.fill((0, 0, 0))

    Y = 416
    X_PARTS = 128
    X_KEYS = 256
    X_BULLETS = 384
    X_LEVEL = 512

    def __init__(self, level):
        self.level = level
        self.digits = game.images.get_digits()
        # Wczytujemy obrazki
        self.images = {
            'parts':   game.images.get_icon(images.S_PARTS),
            'keys':    game.images.get_icon(images.S_KEYS),
            'bullets': game.images.get_icon(images.S_BULLETS),
            'level': game.images.get_icon(images.S_LEVEL)
        }
        self.refresh()
        self.clear()

    def refresh(self):
        screen.blit(self.images['parts'], pygame.Rect(self.X_PARTS - 32, self.Y, 32, 32))
        screen.blit(self.images['keys'], pygame.Rect(self.X_KEYS - 32, self.Y, 32, 32))
        screen.blit(self.images['bullets'], pygame.Rect(self.X_BULLETS - 32, self.Y, 32, 32))
        screen.blit(self.images['level'], pygame.Rect(self.X_LEVEL - 36, self.Y, 32, 32))

    def clear(self):
        self.keys = 0
        self.parts = 0
        self.bullets = 0

    def printnum(self, num, pos, dig):
        for i in range(dig-1, -1, -1):
            n = num % 10
            num = num // 10
            rect = pygame.Rect(pos, (16, 32)).move(i*16, 0)
            screen.blit(self.DIGITBG, rect)
            screen.blit(self.digits[n], rect)

    def update(self):
        scrclip = screen.get_clip()
        screen.set_clip(screen.get_rect())
        self.printnum(self.parts, (self.X_PARTS, self.Y), 2)
        self.printnum(self.keys, (self.X_KEYS, self.Y), 2)
        self.printnum(self.bullets, (self.X_BULLETS, self.Y), 2)
        self.printnum(self.level+1, (self.X_LEVEL, self.Y), 2)
        screen.set_clip(scrclip)

    def select_level(self):
        """
        Manually select level.
        """
        screen.set_clip(screen.get_rect())
        rect = pygame.Rect((self.X_LEVEL, self.Y), (16, 32))
        screen.blit(self.DIGITBG, rect)
        screen.blit(self.DIGITBG, rect.move(16, 0))
        pygame.display.flip()

        digits = []

        # Event loop to enter time
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                quit()
            elif event.type == pygame.KEYDOWN:
                if pygame.K_0 <= event.key <= pygame.K_9:
                    n = event.key - pygame.K_0
                    screen.blit(self.digits[n], rect.move(16 * len(digits), 0))
                    pygame.display.flip()
                    digits = [10*i for i in digits]
                    digits.append(n)
            pygame.event.pump()
            if len(digits) == 2:
                break

        return sum(digits) - 1


