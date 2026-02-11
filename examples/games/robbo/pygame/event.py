# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Event Shim
import time
import busio
import board
from .locals import *

# Singleton input managers
_joystick = None
_touch = None
_i2c = None

EVENT_QUEUE = []

class Event:
    def __init__(self, type, **kwargs):
        self.type = type
        for k, v in kwargs.items():
            setattr(self, k, v)

def _init_inputs():
    global _i2c, _joystick, _touch
    if _i2c is None:
        try:
             _i2c = busio.I2C(board.TP_SCL, board.TP_SDA, frequency=400000)
        except Exception as e:
             print(f"I2C Init Error: {e}")
             return

    # Try Joystick
    if _joystick is None:
        try:
            # We implement a simple PCA9554 driver here inline or import it?
            # Let's import the one we will create in lib/ or just inline a simple one
            # For robustness, let's assume we can map to the one in examples if we copy it,
            # but better to have it here.
            _joystick = JoystickHandler(_i2c)
        except Exception as e:
            print(f"Joystick Init Error: {e}")

# Simple Joystick Wrapper
class JoystickHandler:
    def __init__(self, i2c, addr=0x21):
        self.i2c = i2c
        self.addr = addr
        self.last_state = 0
        self.init_pca()

    def init_pca(self):
         # Config inputs
         self.write_reg(3, 0x1F) 
         self.write_reg(1, 0xE0)

    def write_reg(self, reg, val):
        while not self.i2c.try_lock(): pass
        try: self.i2c.writeto(self.addr, bytes([reg, val]))
        except: pass
        finally: self.i2c.unlock()

    def read_buttons(self):
        while not self.i2c.try_lock(): pass
        val = 0xFF
        try:
            buf = bytearray(1)
            self.i2c.writeto_then_readfrom(self.addr, bytes([0]), buf)
            val = buf[0]
        except: pass
        finally: self.i2c.unlock()
        return val

    def get_events(self):
        events = []
        val = self.read_buttons()
        
        # Bits: 0=UP, 1=DOWN, 2=RIGHT, 3=LEFT, 4=CENTER
        # Active LOW
        
        # Mapping to Keyboard keys for pyrobbo
        MAPPING = {
            0: K_UP,
            1: K_DOWN,
            2: K_RIGHT,
            3: K_LEFT,
            4: K_RCTRL # Fire/Action
        }
        
        if val == self.last_state: return []
        
        changes = val ^ self.last_state
        for bit in range(5):
             if changes & (1 << bit):
                 key = MAPPING.get(bit, 0)
                 is_press = not (val & (1 << bit))
                 
                 evt_type = KEYDOWN if is_press else KEYUP
                 events.append(Event(evt_type, key=key))
                 
        self.last_state = val
        return events

def get():
    global EVENT_QUEUE
    _init_inputs()
    
    # Poll hardware
    if _joystick:
        hw_events = _joystick.get_events()
        EVENT_QUEUE.extend(hw_events)
        
    # Return and clear
    ret = EVENT_QUEUE[:]
    EVENT_QUEUE = []
    return ret

def pump():
    _init_inputs()
    if _joystick:
        hw_events = _joystick.get_events()
        # In a real queue we would append, but get() does the clearing.
        # If pump is called, it should just ensure hardware is polled.
        # Our get() calls poll anyway.
        # But if the user calls pump() then checks key.get_pressed(), we need state.
        # For now, just pass.
        pass
    
def wait():
    # Blocking wait
    while True:
        evs = get()
        if evs: return evs[0]
        time.sleep(0.05)

# Internal access to driver
def get_hw_driver():
    return _i2c
