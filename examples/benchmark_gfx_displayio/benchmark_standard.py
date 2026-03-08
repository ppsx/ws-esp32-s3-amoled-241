# Copyright (c) 2026 Przemyslaw Patrick Socha
"""Consolidated benchmark suite for displayio firmware."""

import gc
import json
import os
import time
import math

import bitmaptools
import board
import displayio
import terminalio
from adafruit_display_text import label as label_mod
from rm690b0 import RM690B0, create_qspi_bus

BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
YELLOW = 0xFFE0
CYAN = 0x07FF
GRAY = 0x7BEF

PROFILE_MATRIX = {
    "quick": {
        "fill_iterations": 4,
        "partial_iterations": 6,
        "scene_iterations": 5,
        "text_iterations": 5,
        "band_iterations": 4,
        "sprite_duration_s": 5.0,
        "tests": ("full_fill", "scene_mixed", "text_menu", "sprite_transparent"),
    },
    "standard": {
        "fill_iterations": 8,
        "partial_iterations": 10,
        "scene_iterations": 8,
        "text_iterations": 8,
        "band_iterations": 6,
        "sprite_duration_s": 8.0,
        "tests": ("full_fill", "partial_rect", "scene_mixed", "text_menu", "blit_band", "sprite_opaque", "sprite_transparent"),
    },
    "full": {
        "fill_iterations": 12,
        "partial_iterations": 14,
        "scene_iterations": 12,
        "text_iterations": 12,
        "band_iterations": 8,
        "sprite_duration_s": 12.0,
        "tests": ("full_fill", "partial_rect", "scene_mixed", "text_menu", "text_large", "blit_band", "sprite_opaque", "sprite_transparent"),
    },
}


def monotonic_ns():
    try:
        return time.monotonic_ns()
    except AttributeError:
        return int(time.monotonic() * 1_000_000_000)


def get_system_info():
    try:
        uname = os.uname()
        return "%s %s | %s" % (uname.sysname, uname.release, uname.machine)
    except Exception:
        return "unknown"


def measure_avg_ms(iterations, fn):
    gc.collect()
    samples = []
    for i in range(iterations):
        start_ns = monotonic_ns()
        fn(i)
        samples.append((monotonic_ns() - start_ns) / 1_000_000.0)
    return sum(samples) / len(samples), max(samples)


def measure_fps(duration_s, fn):
    gc.collect()
    frames = 0
    start_ns = monotonic_ns()
    deadline_ns = start_ns + int(duration_s * 1_000_000_000)
    while monotonic_ns() < deadline_ns:
        fn(frames)
        frames += 1
    elapsed_s = (monotonic_ns() - start_ns) / 1_000_000_000.0
    fps = frames / elapsed_s if elapsed_s > 0 else 0.0
    return fps, frames, elapsed_s


def make_rgb565_buffer(width, height, color_a, color_b=None):
    buf = bytearray(width * height * 2)
    for y in range(height):
        for x in range(width):
            color = color_a
            if color_b is not None and ((x // 4 + y // 4) & 1):
                color = color_b
            idx = (y * width + x) * 2
            buf[idx] = color & 0xFF
            buf[idx + 1] = (color >> 8) & 0xFF
    return buf


def fill_circle_bitmap(bitmap, cx, cy, r, color):
    w = bitmap.width
    h = bitmap.height
    for dy in range(-r, r + 1):
        py = cy + dy
        if py < 0 or py >= h:
            continue
        dx = int(math.sqrt(r * r - dy * dy))
        x1 = max(0, cx - dx) & ~1
        x2 = min(w, (cx + dx + 2) & ~1)
        if x2 <= x1:
            x2 = min(w, x1 + 2)
        if x1 < x2:
            bitmaptools.fill_region(bitmap, x1, py, x2, py + 1, color)


def draw_circle_bitmap(bitmap, cx, cy, r, color):
    w = bitmap.width
    h = bitmap.height
    x = 0
    y = r
    d = 3 - 2 * r
    while x <= y:
        for px, py in (
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x),
            (cx + y, cy - x), (cx - y, cy - x),
        ):
            if 0 <= px < w and 0 <= py < h:
                bitmap[px, py] = color
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1


def pre_render_ball_sprite(radius):
    size = radius * 2 + 4
    sprite = displayio.Bitmap(size, size, 65536)
    sprite.fill(0x0000)
    cx = radius + 2
    cy = radius + 2
    fill_circle_bitmap(sprite, cx, cy, radius, 0xF800)
    draw_circle_bitmap(sprite, cx, cy, radius, 0x8800)
    inner_r = int(radius * 0.7)
    draw_circle_bitmap(sprite, cx - int(radius * 0.15), cy - int(radius * 0.15), inner_r, 0xFD20)
    shine_x = cx - int(radius * 0.4)
    shine_y = cy - int(radius * 0.4)
    fill_circle_bitmap(sprite, shine_x, shine_y, int(radius * 0.25), 0xFFE0)
    fill_circle_bitmap(sprite, shine_x, shine_y, int(radius * 0.15), 0xFFFF)
    fill_circle_bitmap(sprite, cx + int(radius * 0.3), cy + int(radius * 0.2), max(1, int(radius * 0.08)), 0xFDA0)
    fill_circle_bitmap(sprite, cx - int(radius * 0.1), cy + int(radius * 0.4), max(1, int(radius * 0.08)), 0xFC00)
    shadow_y = cy + int(radius * 0.5)
    fill_circle_bitmap(sprite, cx, shadow_y, int(radius * 0.3), 0x4000)
    return sprite


def make_transparent_bitmap(width, height):
    bmp = displayio.Bitmap(width, height, 4)
    palette = displayio.Palette(4)
    palette[0] = 0x000000
    palette[1] = 0xFFE000
    palette[2] = 0xF80000
    palette[3] = 0xFFFFFF
    palette.make_transparent(0)
    cx = width // 2
    cy = height // 2
    rr = max(2, min(width, height) // 2 - 3)
    inner = max(1, rr // 4)
    for y in range(height):
        for x in range(width):
            dx = x - cx
            dy = y - cy
            inside = (dx * dx + dy * dy) <= rr * rr
            if not inside:
                bmp[x, y] = 0
            elif dx * dx + dy * dy < inner * inner:
                bmp[x, y] = 3
            elif ((x + y) & 1) == 0:
                bmp[x, y] = 1
            else:
                bmp[x, y] = 2
    return bmp, palette


def format_metric(result):
    if result["metric"] == "fps":
        return "%.2f FPS" % result["value"]
    if result["metric"] == "mp_s":
        return "%.2f MP/s" % result["value"]
    return "%.2f ms" % result["value"]


def write_reports(output_prefix, report_text, payload):
    try:
        with open(output_prefix + ".txt", "w") as handle:
            handle.write(report_text)
    except OSError:
        pass
    try:
        with open(output_prefix + ".json", "w") as handle:
            json.dump(payload, handle)
    except OSError:
        pass


def render_report(suite_name, results, system_info, note=None):
    lines = []
    lines.append("=" * 72)
    lines.append("DISPLAYIO Benchmark Suite")
    lines.append("Profile: %s" % suite_name.upper())
    lines.append("System: %s" % system_info)
    if note:
        lines.append(note)
    lines.append("Workloads are implemented natively with Bitmap/TileGrid/Label/dirty refresh.")
    lines.append("Core comparable tests: full_fill, partial_rect, scene_mixed, text_menu, text_large, blit_band, sprite_opaque, sprite_transparent")
    lines.append("=" * 72)
    lines.append("")
    lines.append("[DISPLAYIO]")
    for result in results:
        lines.append("  %-22s %12s" % (result["label"], format_metric(result)))
    lines.append("")
    lines.append("Output files: displayio_%s.txt / displayio_%s.json" % (suite_name, suite_name))
    return "\n".join(lines) + "\n"


class DisplayEnv:
    def __init__(self):
        displayio.release_displays()
        bus = create_qspi_bus(board)
        try:
            self.display = RM690B0(bus, auto_refresh=False)
        except TypeError:
            self.display = RM690B0(bus)
        try:
            self.display.auto_refresh = False
        except AttributeError:
            pass

        self.width = self.display.width
        self.height = self.display.height
        self.canvas = displayio.Bitmap(self.width, self.height, 65536)
        self.bg = displayio.Bitmap(self.width, self.height, 65536)
        self.color_converter = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565)
        self.canvas_grid = displayio.TileGrid(self.canvas, pixel_shader=self.color_converter)
        self.overlay = displayio.Group()
        self.root = displayio.Group()
        self.root.append(self.canvas_grid)
        self.root.append(self.overlay)
        self.display.root_group = self.root
        try:
            self.display.brightness = 1.0
        except RuntimeError:
            pass

    def refresh(self):
        self.display.refresh()

    def deinit(self):
        displayio.release_displays()


# bitmap helpers

def fill_screen(env, color):
    env.canvas.fill(color)
    env.canvas.dirty()


def fill_rect(env, x, y, w, h, color):
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(env.width, x + w)
    y2 = min(env.height, y + h)
    if x2 <= x1 or y2 <= y1:
        return
    bitmaptools.fill_region(env.canvas, x1, y1, x2, y2, color)
    env.canvas.dirty(x1=x1, y1=y1, x2=x2, y2=y2)


def hline(env, x, y, length, color):
    x1 = max(0, x)
    x2 = min(env.width, x + length)
    if y < 0 or y >= env.height or x2 <= x1:
        return
    bitmaptools.draw_line(env.canvas, x1, y, x2 - 1, y, color)
    env.canvas.dirty(x1=x1, y1=y, x2=x2, y2=y + 1)


def arrayblit_region(env, buf, x, y, w, h):
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(env.width, x + w)
    y2 = min(env.height, y + h)
    if x2 <= x1 or y2 <= y1:
        return
    bitmaptools.arrayblit(env.canvas, buf, x1=x1, y1=y1, x2=x2, y2=y2)
    env.canvas.dirty(x1=x1, y1=y1, x2=x2, y2=y2)


def restore_background_rect(env, x, y, w, h):
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(env.width, x + w)
    y2 = min(env.height, y + h)
    if x2 <= x1 or y2 <= y1:
        return
    bitmaptools.blit(env.canvas, env.bg, x1, y1, x1=x1, y1=y1, x2=x2, y2=y2)
    env.canvas.dirty(x1=x1, y1=y1, x2=x2, y2=y2)


def normalize_sprite_rect(x, y, w, h, limit_w, limit_h, pad=2):
    x1 = max(0, x - pad) & ~1
    y1 = max(0, y - pad)
    x2 = min(limit_w, (x + w + pad + 1) & ~1)
    y2 = min(limit_h, y + h + pad)
    if x2 <= x1:
        x2 = min(limit_w, x1 + 2)
    if y2 <= y1:
        y2 = min(limit_h, y1 + 1)
    return x1, y1, x2, y2


def mark_moving_rect_dirty(bitmap, prev_x, prev_y, x, y, w, h, limit_w, limit_h, pad=2):
    prev_rect = normalize_sprite_rect(prev_x, prev_y, w, h, limit_w, limit_h, pad=pad)
    cur_rect = normalize_sprite_rect(x, y, w, h, limit_w, limit_h, pad=pad)
    x1 = min(prev_rect[0], cur_rect[0])
    y1 = min(prev_rect[1], cur_rect[1])
    x2 = max(prev_rect[2], cur_rect[2])
    y2 = max(prev_rect[3], cur_rect[3])
    bitmap.dirty(x1=x1, y1=y1, x2=x2, y2=y2)


def reset_overlay(env):
    while len(env.overlay):
        env.overlay.pop()


def create_label(env, text, color, x, y, scale):
    lbl = label_mod.Label(terminalio.FONT, text=text, color=color, x=x, y=y, scale=scale)
    env.overlay.append(lbl)
    return lbl


def setup_static_sprite_background(env):
    env.bg.fill(0x1082)
    for gy in range(60, env.height, 36):
        bitmaptools.draw_line(env.bg, 0, gy, env.width - 1, gy, 0x2104)
    bitmaptools.blit(env.canvas, env.bg, 0, 0)
    env.canvas.dirty()


def load_raw_background(bitmap, path):
    import array
    fb = array.array("H", bytearray(bitmap.width * bitmap.height * 2))
    with open(path, "rb") as handle:
        read = handle.readinto(fb)
    expected = bitmap.width * bitmap.height * 2
    if read != expected:
        raise RuntimeError("background file is the wrong size")
    bitmaptools.arrayblit(bitmap, fb, x1=0, y1=0, x2=bitmap.width, y2=bitmap.height)


def mark_tilegrid_union_dirty(env, old_x, old_y, new_x, new_y, w, h, pad=2):
    x1 = max(0, min(old_x, new_x) - pad) & ~1
    y1 = max(0, min(old_y, new_y) - pad)
    x2 = min(env.width, (max(old_x + w, new_x + w) + pad + 1) & ~1)
    y2 = min(env.height, max(old_y + h, new_y + h) + pad)
    if x2 <= x1:
        x2 = min(env.width, x1 + 2)
    if y2 <= y1:
        y2 = min(env.height, y1 + 1)
    env.canvas.dirty(x1=x1, y1=y1, x2=x2, y2=y2)


def bench_full_fill(env, iterations):
    colors = (RED, GREEN, BLUE, WHITE)
    pixels = env.width * env.height
    avg_ms, max_ms = measure_avg_ms(iterations, lambda i: (fill_screen(env, colors[i % len(colors)]), env.refresh()))
    mp_s = ((pixels * iterations) / 1_000_000.0) / ((avg_ms * iterations) / 1000.0) if avg_ms > 0 else 0.0
    return (
        {"label": "full_fill", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},
        {"label": "full_fill_bw", "metric": "mp_s", "value": mp_s, "detail": {}},
    )


def bench_partial_rect(env, iterations):
    positions = ((20, 20), (120, 20), (220, 40), (320, 80), (420, 40), (220, 160))
    area = 100 * 100
    def frame(i):
        x, y = positions[i % len(positions)]
        fill_screen(env, BLACK)
        fill_rect(env, x, y, 100, 100, GREEN)
        env.refresh()
    avg_ms, max_ms = measure_avg_ms(iterations, frame)
    mp_s = ((area * iterations) / 1_000_000.0) / ((avg_ms * iterations) / 1000.0) if avg_ms > 0 else 0.0
    return (
        {"label": "partial_rect", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},
        {"label": "partial_rect_bw", "metric": "mp_s", "value": mp_s, "detail": {}},
    )


def bench_scene_mixed(env, iterations):
    def frame(i):
        fill_screen(env, 0x0841)
        fill_rect(env, 24, 24, 140, 80, RED)
        fill_rect(env, 220, 90, 160, 120, GREEN)
        fill_rect(env, 420, 260, 140, 120, BLUE)
        fill_rect(env, 100, 280, 120, 100, YELLOW)
        moving_x = 120 + ((i * 37) % 320)
        moving_y = 90 + ((i * 29) % 220)
        fill_rect(env, moving_x, moving_y, 80, 80, WHITE)
        env.refresh()
    avg_ms, max_ms = measure_avg_ms(iterations, frame)
    return ({"label": "scene_mixed", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},)


def bench_text_menu(env, iterations):
    fill_screen(env, BLACK)
    reset_overlay(env)
    y = 24
    for item, color in (("Score", WHITE), ("Level", CYAN), ("Lives", YELLOW), ("Power", GREEN), ("Exit", RED)):
        create_label(env, item, color, 24, y, 2)
        y += 26
    frame_label = create_label(env, "frame=000", WHITE, 220, 24, 2)
    env.canvas.dirty()
    env.refresh()

    def frame(i):
        frame_label.text = "frame=%03d" % i
        env.refresh()

    try:
        avg_ms, max_ms = measure_avg_ms(iterations, frame)
    finally:
        reset_overlay(env)
    return ({"label": "text_menu", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},)


def bench_text_large(env, iterations):
    fill_screen(env, BLACK)
    reset_overlay(env)
    create_label(env, "SCORE", GREEN, 90, 140, 4)
    value_label = create_label(env, "0000", WHITE, 90, 220, 4)
    env.canvas.dirty()
    env.refresh()

    def frame(i):
        value_label.text = "%04d" % (i * 3)
        env.refresh()

    try:
        avg_ms, max_ms = measure_avg_ms(iterations, frame)
    finally:
        reset_overlay(env)
    return ({"label": "text_large", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},)


def bench_blit_band(env, iterations):
    height = 64
    buf = make_rgb565_buffer(env.width, height, BLUE, CYAN)
    area = env.width * height
    def frame(i):
        fill_screen(env, BLACK)
        y = (i * 17) % max(1, (env.height - height))
        arrayblit_region(env, buf, 0, y, env.width, height)
        env.refresh()
    avg_ms, max_ms = measure_avg_ms(iterations, frame)
    mp_s = ((area * iterations) / 1_000_000.0) / ((avg_ms * iterations) / 1000.0) if avg_ms > 0 else 0.0
    return (
        {"label": "blit_band", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},
        {"label": "blit_band_bw", "metric": "mp_s", "value": mp_s, "detail": {}},
    )


def bench_sprite_opaque(env, duration_s):
    radius = 20
    sprite = pre_render_ball_sprite(radius)
    env.bg.fill(0x0000)
    bitmaptools.draw_line(env.bg, 0, 0, env.width - 1, 0, 0x4208)
    bitmaptools.draw_line(env.bg, 0, env.height - 1, env.width - 1, env.height - 1, 0x4208)
    bitmaptools.draw_line(env.bg, 0, 0, 0, env.height - 1, 0x4208)
    bitmaptools.draw_line(env.bg, env.width - 1, 0, env.width - 1, env.height - 1, 0x4208)
    bitmaptools.blit(env.canvas, env.bg, 0, 0)
    env.canvas.dirty()
    env.refresh()

    fx = float(radius + 2)
    fy = float(radius + 2)
    vx = 8.0
    vy = 6.0
    x = int(fx) & ~1
    y = int(fy) & ~1
    prev_x = x
    prev_y = y

    def clear_previous(px, py):
        r = radius + 2
        x1 = max(0, px - r) & ~1
        y1 = max(0, py - r)
        x2 = min(env.width, (px + r + 1) & ~1)
        y2 = min(env.height, py + r)
        if x2 <= x1:
            x2 = min(env.width, x1 + 2)
        if y2 <= y1:
            y2 = min(env.height, y1 + 1)
        bitmaptools.blit(env.canvas, env.bg, x1, y1, x1=x1, y1=y1, x2=x2, y2=y2)

    def mark_dirty(px, py, cx, cy):
        r = radius + 2
        x1 = min(px, cx) - r
        y1 = min(py, cy) - r
        x2 = max(px, cx) + r
        y2 = max(py, cy) + r
        x1 = max(0, x1) & ~1
        y1 = max(0, y1)
        x2 = min(env.width, (x2 + 1) & ~1)
        y2 = min(env.height, y2)
        if x2 <= x1:
            x2 = min(env.width, x1 + 2)
        if y2 <= y1:
            y2 = min(env.height, y1 + 1)
        env.canvas.dirty(x1=x1, y1=y1, x2=x2, y2=y2)

    def frame(_):
        nonlocal fx, fy, vx, vy, x, y, prev_x, prev_y
        fx += vx
        fy += vy
        x = int(fx) & ~1
        y = int(fy) & ~1

        margin = 2
        if x - radius <= 0:
            fx = float(radius + margin)
            x = radius + margin
            vx = abs(vx)
        elif x + radius >= env.width - 1:
            fx = float(env.width - radius - margin)
            x = env.width - radius - margin
            vx = -abs(vx)

        if y - radius <= 0:
            fy = float(radius + margin)
            y = radius + margin
            vy = abs(vy)
        elif y + radius >= env.height - 1:
            fy = float(env.height - radius - margin)
            y = env.height - radius - margin
            vy = -abs(vy)

        clear_previous(prev_x, prev_y)
        bitmaptools.blit(env.canvas, sprite, x - radius - 2, y - radius - 2, skip_source_index=0x0000)
        mark_dirty(prev_x, prev_y, x, y)
        env.refresh()
        prev_x = x
        prev_y = y

    fps, frames, elapsed_s = measure_fps(duration_s, frame)
    return ({"label": "sprite_opaque", "metric": "fps", "value": fps, "detail": {"frames": frames, "elapsed_s": elapsed_s}},)


def bench_sprite_transparent(env, duration_s):
    radius = 20
    sprite = pre_render_ball_sprite(radius)
    try:
        load_raw_background(env.bg, "/gfx/cerber.raw")
    except (OSError, RuntimeError):
        setup_static_sprite_background(env)
    else:
        bitmaptools.blit(env.canvas, env.bg, 0, 0)
        env.canvas.dirty()
    env.refresh()

    fx = float(radius + 2)
    fy = float(radius + 2)
    vx = 8.0
    vy = 6.0
    x = int(fx) & ~1
    y = int(fy) & ~1
    prev_x = x
    prev_y = y

    def clear_previous(px, py):
        r = radius + 2
        x1 = max(0, px - r) & ~1
        y1 = max(0, py - r)
        x2 = min(env.width, (px + r + 1) & ~1)
        y2 = min(env.height, py + r)
        if x2 <= x1:
            x2 = min(env.width, x1 + 2)
        if y2 <= y1:
            y2 = min(env.height, y1 + 1)
        bitmaptools.blit(env.canvas, env.bg, x1, y1, x1=x1, y1=y1, x2=x2, y2=y2)

    def mark_dirty(px, py, cx, cy):
        r = radius + 2
        x1 = min(px, cx) - r
        y1 = min(py, cy) - r
        x2 = max(px, cx) + r
        y2 = max(py, cy) + r
        x1 = max(0, x1) & ~1
        y1 = max(0, y1)
        x2 = min(env.width, (x2 + 1) & ~1)
        y2 = min(env.height, y2)
        if x2 <= x1:
            x2 = min(env.width, x1 + 2)
        if y2 <= y1:
            y2 = min(env.height, y1 + 1)
        env.canvas.dirty(x1=x1, y1=y1, x2=x2, y2=y2)

    def frame(_):
        nonlocal fx, fy, vx, vy, x, y, prev_x, prev_y
        fx += vx
        fy += vy
        x = int(fx) & ~1
        y = int(fy) & ~1

        if x - radius <= 0:
            fx = float(radius + 2)
            x = radius + 2
            vx = abs(vx)
        elif x + radius >= env.width - 1:
            fx = float(env.width - radius - 2)
            x = env.width - radius - 2
            vx = -abs(vx)

        if y - radius <= 0:
            fy = float(radius + 2)
            y = radius + 2
            vy = abs(vy)
        elif y + radius >= env.height - 1:
            fy = float(env.height - radius - 2)
            y = env.height - radius - 2
            vy = -abs(vy)

        clear_previous(prev_x, prev_y)
        bitmaptools.blit(env.canvas, sprite, x - radius - 2, y - radius - 2, skip_source_index=0x0000)
        mark_dirty(prev_x, prev_y, x, y)
        env.refresh()
        prev_x = x
        prev_y = y

    fps, frames, elapsed_s = measure_fps(duration_s, frame)
    return ({"label": "sprite_transparent", "metric": "fps", "value": fps, "detail": {"frames": frames, "elapsed_s": elapsed_s}},)


def collect_results(profile_name):
    cfg = PROFILE_MATRIX[profile_name]
    env = DisplayEnv()
    results = []
    try:
        tests = cfg["tests"]
        if "full_fill" in tests:
            results.extend(bench_full_fill(env, cfg["fill_iterations"]))
        if "partial_rect" in tests:
            results.extend(bench_partial_rect(env, cfg["partial_iterations"]))
        if "scene_mixed" in tests:
            results.extend(bench_scene_mixed(env, cfg["scene_iterations"]))
        if "text_menu" in tests:
            results.extend(bench_text_menu(env, cfg["text_iterations"]))
        if "text_large" in tests:
            results.extend(bench_text_large(env, cfg["text_iterations"]))
        if "blit_band" in tests:
            results.extend(bench_blit_band(env, cfg["band_iterations"]))
        if "sprite_opaque" in tests:
            results.extend(bench_sprite_opaque(env, cfg["sprite_duration_s"]))
        if "sprite_transparent" in tests:
            results.extend(bench_sprite_transparent(env, cfg["sprite_duration_s"]))
    finally:
        fill_screen(env, BLACK)
        env.refresh()
        env.deinit()
    return results


def run_profile(profile_name):
    system_info = get_system_info()
    results = collect_results(profile_name)
    note = "Group: DISPLAYIO. Scenarios use native displayio primitives, labels and dirty-region refresh."
    payload = {"backend": "DISPLAYIO", "profile": profile_name, "system": system_info, "groups": [{"name": "DISPLAYIO"}], "results": results, "note": note}
    report = render_report(profile_name, results, system_info, note=note)
    print(report)
    write_reports("/displayio_" + profile_name, report, payload)

run_profile("standard")
