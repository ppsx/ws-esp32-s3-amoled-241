# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Joystick Shim

def get_count():
    # Return 0 so game uses keyboard event logic
    # Our event.py maps HW joystick to Keys
    return 0

class Joystick:
    def __init__(self, id):
        pass
    def init(self):
        pass
    def get_axis(self, axis):
        return 0.0
