# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Key Shim
from .locals import *

def get_mods():
    return 0

def get_pressed():
    # Return a map-like object or list
    # For now just return empty list as we rely on events
    return []
