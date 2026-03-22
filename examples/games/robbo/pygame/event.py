# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Event Shim
import time
import busio
import board
from .locals import *

# Singleton input managers
_joystick = None
_i2c = None

EVENT_QUEUE = []

class Event:
    def __init__(self, type, **kwargs):
        self.type = type
        for k, v in kwargs.items():
            setattr(self, k, v)

_last_joy_state = {"up": False, "down": False, "left": False, "right": False, "center": False}
_KEY_MAP = {"up": K_UP, "down": K_DOWN, "right": K_RIGHT, "left": K_LEFT, "center": K_RCTRL}

def _init_inputs():
    global _i2c, _joystick
    if _i2c is None:
        try:
            _i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)
        except Exception as e:
            print(f"I2C Init Error: {e}")
            return
    if _joystick is None:
        try:
            from joystick import Joystick
            _joystick = Joystick(i2c=_i2c)
        except Exception as e:
            print(f"Joystick Init Error: {e}")

def get():
    global EVENT_QUEUE, _last_joy_state
    _init_inputs()

    if _joystick:
        state = _joystick.read()
        for key, pygame_key in _KEY_MAP.items():
            was = _last_joy_state[key]
            now = state[key]
            if now and not was:
                EVENT_QUEUE.append(Event(KEYDOWN, key=pygame_key))
            elif was and not now:
                EVENT_QUEUE.append(Event(KEYUP, key=pygame_key))
        _last_joy_state = state

    ret = EVENT_QUEUE[:]
    EVENT_QUEUE = []
    return ret

def pump():
    get()
    
def wait():
    # Blocking wait
    while True:
        evs = get()
        if evs: return evs[0]
        time.sleep(0.05)

# Internal access to driver
def get_hw_driver():
    return _i2c
