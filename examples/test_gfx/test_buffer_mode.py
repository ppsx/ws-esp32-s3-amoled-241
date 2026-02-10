# Copyright (c) 2026 Przemyslaw Patrick Socha

import gc
import rm690b0
import time

# ── 1. Constants ───────────────────────────────────────────────────────────────
print("=== Constants ===")
print(f"BUFFER_SINGLE = {rm690b0.BUFFER_SINGLE}")   # expected: 0
print(f"BUFFER_DOUBLE = {rm690b0.BUFFER_DOUBLE}")   # expected: 1

# ── 2. DOUBLE mode (default — backward compat) ────────────────────────────────
print("\n=== DOUBLE mode ===")
gc.collect()
before = gc.mem_free()
d = rm690b0.RM690B0()
d.init_display()
d.swap_buffers()                # lazy-allocates front buffer (~540 KB)
gc.collect()
after = gc.mem_free()
print(f"Memory before: {before // 1024} KB")
print(f"Memory after:  {after // 1024} KB")
print(f"Used:          {(before - after) // 1024} KB  (expected ~1080 KB)")
d.fill_color(rm690b0.BLACK)
d.text(10, 10, "DOUBLE mode OK", rm690b0.GREEN)
d.swap_buffers()
time.sleep(1)
d.deinit()

# ── 3. SINGLE mode ────────────────────────────────────────────────────────────
print("\n=== SINGLE mode ===")
gc.collect()
before = gc.mem_free()
s = rm690b0.RM690B0(buffer_mode=rm690b0.BUFFER_SINGLE)
s.init_display()
s.swap_buffers()                # does NOT allocate front buffer
gc.collect()
after = gc.mem_free()
print(f"Memory before: {before // 1024} KB")
print(f"Memory after:  {after // 1024} KB")
print(f"Used:          {(before - after) // 1024} KB  (expected ~540 KB)")
s.fill_color(rm690b0.BLACK)
s.text(10, 10, "SINGLE mode OK", rm690b0.CYAN)
s.swap_buffers()
time.sleep(1)
s.deinit()

# ── 4. Dirty tracking in SINGLE mode ─────────────────────────────────────────
print("\n=== Dirty tracking (SINGLE) ===")
s2 = rm690b0.RM690B0(buffer_mode=rm690b0.BUFFER_SINGLE)
s2.init_display()
s2.fill_color(rm690b0.BLACK)
# Draw a few small elements, then flush once
s2.fill_rect(10, 10, 100, 30, rm690b0.RED)
s2.fill_rect(10, 50, 200, 30, rm690b0.YELLOW)
s2.text(10, 90, "Dirty rects flushed", rm690b0.WHITE)
s2.swap_buffers()               # should flush 3 dirty regions, not the full screen
print("OK — visually verify: 2 rectangles and text should be visible")
time.sleep(1)
s2.deinit()

print("\n=== DONE ===")
