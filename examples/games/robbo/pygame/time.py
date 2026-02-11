# Copyright (c) 2025 Przemyslaw Patrick Socha

# Pygame Time Shim
import time

class Clock:
    def __init__(self):
        self.last_tick = time.monotonic()
        
    def tick(self, fps=60):
        now = time.monotonic()
        dt = now - self.last_tick
        
        target_dt = 1.0 / fps
        sleep_time = target_dt - dt
        
        if sleep_time > 0:
            time.sleep(sleep_time)
            
        self.last_tick = time.monotonic()
        return (self.last_tick - now) * 1000 # Return ms elapsed since last call

    def get_fps(self):
        return 60.0 # Stub

def get_ticks():
    return int(time.monotonic() * 1000)

def wait(ms):
    time.sleep(ms / 1000.0)
    return ms
