# Copyright (c) 2025 Przemyslaw Patrick Socha

class Rect:
    def __init__(self, *args):
        if len(args) == 1:
            if isinstance(args[0], Rect):
                self.x = args[0].x
                self.y = args[0].y
                self.w = args[0].w
                self.h = args[0].h
            elif isinstance(args[0], (tuple, list)):
                self.x, self.y, self.w, self.h = args[0]
            else:
                 raise ValueError("Invalid args for Rect")
        elif len(args) == 4:
            self.x, self.y, self.w, self.h = args
        elif len(args) == 2:
             self.x, self.y = args[0]
             self.w, self.h = args[1]
        else:
            self.x, self.y, self.w, self.h = 0, 0, 0, 0

    def __getitem__(self, i):
        if i == 0: return self.x
        elif i == 1: return self.y
        elif i == 2: return self.w
        elif i == 3: return self.h
        raise IndexError("Rect index out of range")

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.w
        yield self.h

    @property
    def left(self): return self.x
    @left.setter
    def left(self, v): self.x = v

    @property
    def top(self): return self.y
    @top.setter
    def top(self, v): self.y = v

    @property
    def right(self): return self.x + self.w
    @right.setter
    def right(self, v): self.x = v - self.w

    @property
    def bottom(self): return self.y + self.h
    @bottom.setter
    def bottom(self, v): self.y = v - self.h
    
    @property
    def width(self): return self.w
    @width.setter
    def width(self, v): self.w = v

    @property
    def height(self): return self.h
    @height.setter
    def height(self, v): self.h = v

    @property
    def size(self): return (self.w, self.h)
    @size.setter
    def size(self, v): self.w, self.h = v
    
    @property
    def topleft(self): return (self.x, self.y)
    @topleft.setter
    def topleft(self, v): self.x, self.y = v

    @property
    def center(self): return (self.x + self.w // 2, self.y + self.h // 2)
    @center.setter
    def center(self, v): 
        self.x = v[0] - self.w // 2
        self.y = v[1] - self.h // 2

    def move(self, x, y=None):
        if isinstance(x, (tuple, list)):
             return Rect(self.x + x[0], self.y + x[1], self.w, self.h)
        return Rect(self.x + x, self.y + y, self.w, self.h)

    def move_ip(self, x, y=None):
        if isinstance(x, (tuple, list)):
            self.x += x[0]
            self.y += x[1]
        else:
            self.x += x
            self.y += y

    def colliderect(self, other):
        return (self.x < other.x + other.w and
                self.x + self.w > other.x and
                self.y < other.y + other.h and
                self.y + self.h > other.y)

    def contains(self, other):
        return (self.x <= other.x and
                self.x + self.w >= other.x + other.w and
                self.y <= other.y and
                self.y + self.h >= other.y + other.h)

    def copy(self):
        return Rect(self.x, self.y, self.w, self.h)

    def inflate(self, x, y):
        return Rect(self.x - x//2, self.y - y//2, self.w + x, self.h + y)

    def __repr__(self):
        return f"<Rect({self.x}, {self.y}, {self.w}, {self.h})>"
