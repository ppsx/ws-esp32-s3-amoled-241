# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Sprite Shim
from . import Rect

class Sprite:
    def __init__(self, *groups):
        self._groups = []
        for g in groups:
            self.add(g)
        self.rect = None
        self.image = None

    def add(self, *groups):
        for g in groups:
            g.add(self)

    def remove(self, *groups):
        for g in groups:
            if g.has(self):
                g.remove(self)
                if g in self._groups:
                    self._groups.remove(g)

    def kill(self):
        for g in list(self._groups):
            g.remove(self)
        self._groups = []

    def alive(self):
        return len(self._groups) > 0

    def groups(self):
        return list(self._groups)
        
    def update(self, *args):
        pass

class Group:
    def __init__(self, *sprites):
        self._sprites = list(sprites)

    def sprites(self):
        return list(self._sprites)

    def add(self, *sprites):
        for s in sprites:
            if s not in self._sprites:
                self._sprites.append(s)
                if self not in s._groups:
                    s._groups.append(self)

    def remove(self, *sprites):
        for s in sprites:
            if s in self._sprites:
                self._sprites.remove(s)

    def has(self, sprite):
        return sprite in self._sprites

    def update(self, *args):
        for s in list(self._sprites):
            s.update(*args)

    def draw(self, surface):
        for s in self._sprites:
            if s.image and s.rect:
                 surface.blit(s.image, s.rect)

    def empty(self):
        self._sprites = []
    
    def __len__(self):
        return len(self._sprites)

    def __iter__(self):
        return iter(self._sprites)

class RenderPlain(Group):
    pass
