# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Shim for CircuitPython
from . import display
from . import time
from . import event
from . import image
from . import mixer
from . import sprite
from . import mouse
from . import joystick

def init():
    pass

def quit():
    disp = display.get_hw_driver()
    if disp:
        disp.fill_color(0x0000)
        disp.swap_buffers()
        if display.is_display_owned():
            disp.deinit()
    try:
        event.get_hw_driver().deinit()
    except:
        pass


from .rect import Rect
from .display import Surface
from .locals import *
from . import key

