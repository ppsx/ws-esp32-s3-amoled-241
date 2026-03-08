# Copyright (c) 2026 Przemyslaw Patrick Socha
"""
Consolidated benchmark suite for rm690b0 backends.

This file is intentionally standalone so benchmark_quick.py / benchmark_standard.py /
benchmark_full.py are the only entrypoints the user needs.
"""

import gc
import json
import os
import time

import rm690b0

BLACK = getattr(rm690b0, "BLACK", 0x0000)
WHITE = getattr(rm690b0, "WHITE", 0xFFFF)
RED = getattr(rm690b0, "RED", 0xF800)
GREEN = getattr(rm690b0, "GREEN", 0x07E0)
BLUE = getattr(rm690b0, "BLUE", 0x001F)
YELLOW = getattr(rm690b0, "YELLOW", 0xFFE0)
CYAN = getattr(rm690b0, "CYAN", 0x07FF)
GRAY = getattr(rm690b0, "GRAY", 0x7BEF)

PROFILE_MATRIX = {
    "quick": {
        "fill_iterations": 4,
        "partial_iterations": 6,
        "scene_iterations": 5,
        "text_iterations": 5,
        "band_iterations": 4,
        "sprite_duration_s": 5.0,
        "tests": (
            "full_fill",
            "scene_mixed",
            "text_menu",
            "sprite_transparent",
        ),
    },
    "standard": {
        "fill_iterations": 8,
        "partial_iterations": 10,
        "scene_iterations": 8,
        "text_iterations": 8,
        "band_iterations": 6,
        "sprite_duration_s": 8.0,
        "tests": (
            "full_fill",
            "partial_rect",
            "scene_mixed",
            "text_menu",
            "blit_band",
            "sprite_opaque",
            "sprite_transparent",
            "retained_sprite",
        ),
    },
    "full": {
        "fill_iterations": 12,
        "partial_iterations": 14,
        "scene_iterations": 12,
        "text_iterations": 12,
        "band_iterations": 8,
        "sprite_duration_s": 12.0,
        "tests": (
            "full_fill",
            "partial_rect",
            "scene_mixed",
            "text_menu",
            "text_large",
            "blit_band",
            "sprite_opaque",
            "sprite_transparent",
            "retained_sprite",
            "retained_text",
            "retained_transparent",
        ),
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


def make_rgb565_buffer(width, height, color_a, color_b=None):
    data = bytearray(width * height * 2)
    for y in range(height):
        for x in range(width):
            color = color_a
            if color_b is not None and ((x // 4 + y // 4) & 1):
                color = color_b
            idx = (y * width + x) * 2
            data[idx] = color & 0xFF
            data[idx + 1] = (color >> 8) & 0xFF
    return data


def make_transparent_rgb565_sprite(width, height, transparent_color=0x0000):
    data = bytearray(width * height * 2)
    cx = width // 2
    cy = height // 2
    rx = max(2, width // 2 - 3)
    ry = max(2, height // 2 - 3)
    for y in range(height):
        for x in range(width):
            dx = x - cx
            dy = y - cy
            idx = (y * width + x) * 2
            inside = (dx * dx * 100) // max(1, rx * rx) + (dy * dy * 100) // max(1, ry * ry) <= 100
            if inside:
                color = YELLOW if ((x + y) & 1) == 0 else RED
                if abs(dx) < width // 8 and abs(dy) < height // 8:
                    color = WHITE
            else:
                color = transparent_color
            data[idx] = color & 0xFF
            data[idx + 1] = (color >> 8) & 0xFF
    return data


def measure_avg_ms(iterations, fn):
    gc.collect()
    samples = []
    for i in range(iterations):
        start_ns = monotonic_ns()
        fn(i)
        elapsed_ms = (monotonic_ns() - start_ns) / 1_000_000.0
        samples.append(elapsed_ms)
    avg_ms = sum(samples) / len(samples)
    max_ms = max(samples)
    return avg_ms, max_ms


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


def render_report(suite_name, backend_name, groups_meta, results, system_info, note=None):
    lines = []
    lines.append("=" * 72)
    lines.append("%s Benchmark Suite" % backend_name)
    lines.append("Profile: %s" % suite_name.upper())
    lines.append("System: %s" % system_info)
    if note:
        lines.append(note)
    lines.append("Core comparable tests: full_fill, partial_rect, scene_mixed, text_menu, text_large, blit_band, sprite_opaque, sprite_transparent")
    lines.append("Backend-specific tests: retained_sprite, retained_text, retained_transparent")
    lines.append("=" * 72)
    for meta in groups_meta:
        group = meta["name"]
        lines.append("")
        lines.append("[%s]" % group)
        for result in results:
            if result["group"] != group:
                continue
            lines.append("  %-22s %12s" % (result["label"], format_metric(result)))
    lines.append("")
    lines.append("Output files: %s.txt / %s.json" % (backend_name.lower() + "_" + suite_name, backend_name.lower() + "_" + suite_name))
    return "\n".join(lines) + "\n"


def bench_full_fill(display, copy_mode, iterations):
    colors = (RED, GREEN, BLUE, WHITE)
    pixels = display.width * display.height
    avg_ms, max_ms = measure_avg_ms(
        iterations,
        lambda i: (display.fill_color(colors[i % len(colors)]), display.swap_buffers(copy=copy_mode)),
    )
    mp_s = ((pixels * iterations) / 1_000_000.0) / ((avg_ms * iterations) / 1000.0) if avg_ms > 0 else 0.0
    return (
        {"label": "full_fill", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},
        {"label": "full_fill_bw", "metric": "mp_s", "value": mp_s, "detail": {}},
    )


def bench_partial_rect(display, copy_mode, iterations):
    positions = ((20, 20), (120, 20), (220, 40), (320, 80), (420, 40), (220, 160))
    area = 100 * 100
    def frame(i):
        x, y = positions[i % len(positions)]
        display.fill_color(BLACK)
        display.fill_rect(x, y, 100, 100, GREEN)
        display.swap_buffers(copy=copy_mode)
    avg_ms, max_ms = measure_avg_ms(iterations, frame)
    mp_s = ((area * iterations) / 1_000_000.0) / ((avg_ms * iterations) / 1000.0) if avg_ms > 0 else 0.0
    return (
        {"label": "partial_rect", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},
        {"label": "partial_rect_bw", "metric": "mp_s", "value": mp_s, "detail": {}},
    )


def bench_scene_mixed(display, copy_mode, iterations):
    def frame(i):
        display.fill_color(0x0841)
        display.fill_rect(24, 24, 140, 80, RED)
        display.fill_rect(220, 90, 160, 120, GREEN)
        display.fill_rect(420, 260, 140, 120, BLUE)
        display.fill_rect(100, 280, 120, 100, YELLOW)
        moving_x = 120 + ((i * 37) % 320)
        moving_y = 90 + ((i * 29) % 220)
        display.fill_rect(moving_x, moving_y, 80, 80, WHITE)
        display.swap_buffers(copy=copy_mode)
    avg_ms, max_ms = measure_avg_ms(iterations, frame)
    return ({"label": "scene_mixed", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},)


def bench_text_menu(display, copy_mode, iterations):
    display.set_font(rm690b0.FONT_16x16)
    items = ("Score", "Level", "Lives", "Power", "Exit")
    colors = (WHITE, CYAN, YELLOW, GREEN, RED)
    def frame(i):
        display.fill_color(BLACK)
        y = 24
        for idx, item in enumerate(items):
            display.text(24, y, item, colors[idx])
            y += 28
        display.text(220, 24, "frame=%03d" % i, WHITE)
        display.swap_buffers(copy=copy_mode)
    avg_ms, max_ms = measure_avg_ms(iterations, frame)
    return ({"label": "text_menu", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},)


def bench_text_large(display, copy_mode, iterations):
    display.set_font(rm690b0.FONT_24x32)
    def frame(i):
        display.fill_color(BLACK)
        display.text(90, 130, "SCORE", GREEN)
        display.text(90, 190, "%04d" % (i * 3), WHITE)
        display.swap_buffers(copy=copy_mode)
    avg_ms, max_ms = measure_avg_ms(iterations, frame)
    return ({"label": "text_large", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},)


def bench_blit_band(display, copy_mode, iterations):
    height = 64
    buf = make_rgb565_buffer(display.width, height, BLUE, CYAN)
    area = display.width * height
    def frame(i):
        display.fill_color(BLACK)
        display.blit_buffer(0, (i * 17) % max(1, (display.height - height)), display.width, height, buf)
        display.swap_buffers(copy=copy_mode)
    avg_ms, max_ms = measure_avg_ms(iterations, frame)
    mp_s = ((area * iterations) / 1_000_000.0) / ((avg_ms * iterations) / 1000.0) if avg_ms > 0 else 0.0
    return (
        {"label": "blit_band", "metric": "ms", "value": avg_ms, "detail": {"max_ms": max_ms}},
        {"label": "blit_band_bw", "metric": "mp_s", "value": mp_s, "detail": {}},
    )


def bench_sprite_opaque(display, copy_mode, duration_s, background=False):
    sw = 40
    sh = 40
    sprite = make_rgb565_buffer(sw, sh, YELLOW, GREEN)
    width_limit = max(1, display.width - sw)
    height_limit = max(1, display.height - sh - 80)
    def frame(i):
        x = (i * 7) % width_limit
        y = 60 + ((i * 5) % height_limit)
        if background:
            display.fill_color(0x1082)
            for gy in range(60, display.height, 40):
                display.hline(0, gy, display.width, 0x2104)
        else:
            display.fill_color(BLACK)
        display.blit_buffer(x, y, sw, sh, sprite)
        display.swap_buffers(copy=copy_mode)
    fps, frames, elapsed_s = measure_fps(duration_s, frame)
    return ({"label": "sprite_opaque", "metric": "fps", "value": fps, "detail": {"frames": frames, "elapsed_s": elapsed_s}},)


def bench_sprite_transparent(display, copy_mode, duration_s):
    sw = 44
    sh = 44
    sprite = make_transparent_rgb565_sprite(sw, sh)
    width_limit = max(1, display.width - sw)
    height_limit = max(1, display.height - sh - 80)
    def frame(i):
        x = (i * 7) % width_limit
        y = 60 + ((i * 5) % height_limit)
        display.fill_color(0x1082)
        for gy in range(60, display.height, 36):
            display.hline(0, gy, display.width, 0x2104)
        display.blit_buffer(x, y, sw, sh, sprite, transparent_color=0x0000)
        display.swap_buffers(copy=copy_mode)
    fps, frames, elapsed_s = measure_fps(duration_s, frame)
    return ({"label": "sprite_transparent", "metric": "fps", "value": fps, "detail": {"frames": frames, "elapsed_s": elapsed_s}},)


def bench_retained_sprite(display, duration_s):
    sw = 40
    sh = 40
    sprite = make_rgb565_buffer(sw, sh, YELLOW, GREEN)
    width_limit = max(1, display.width - sw)
    height_limit = max(1, display.height - sh - 80)
    display.fill_color(BLACK)
    display.swap_buffers(copy=True)
    prev = None
    def frame(i):
        nonlocal prev
        x = (i * 9) % width_limit
        y = 60 + ((i * 7) % height_limit)
        if prev is not None:
            display.fill_rect(prev[0], prev[1], sw, sh, BLACK)
        display.blit_buffer(x, y, sw, sh, sprite)
        display.swap_buffers(copy=True)
        prev = (x, y)
    fps, frames, elapsed_s = measure_fps(duration_s, frame)
    return ({"label": "retained_sprite", "metric": "fps", "value": fps, "detail": {"frames": frames, "elapsed_s": elapsed_s}},)


def bench_retained_text(display, duration_s):
    display.fill_color(BLACK)
    display.set_font(rm690b0.FONT_16x24)
    display.swap_buffers(copy=True)
    def frame(i):
        display.fill_rect(24, 120, 300, 32, BLACK)
        display.text(24, 120, "frame=%05d" % i, WHITE)
        display.fill_rect(24, 170, 320, 18, 0x0841)
        display.fill_rect(24, 170, 20 + ((i * 9) % 280), 18, GREEN)
        display.swap_buffers(copy=True)
    fps, frames, elapsed_s = measure_fps(duration_s, frame)
    return ({"label": "retained_text", "metric": "fps", "value": fps, "detail": {"frames": frames, "elapsed_s": elapsed_s}},)


def bench_retained_transparent(display, duration_s):
    sw = 44
    sh = 44
    sprite = make_transparent_rgb565_sprite(sw, sh)
    width_limit = max(1, display.width - sw)
    height_limit = max(1, display.height - sh - 80)
    display.fill_color(0x1082)
    for gy in range(60, display.height, 36):
        display.hline(0, gy, display.width, 0x2104)
    display.swap_buffers(copy=True)
    prev = None
    def frame(i):
        nonlocal prev
        x = (i * 9) % width_limit
        y = 60 + ((i * 7) % height_limit)
        if prev is not None:
            px, py = prev
            display.fill_rect(px, py, sw, sh, 0x1082)
            for gy in range(py, py + sh, 36):
                if 60 <= gy < display.height:
                    display.hline(px, gy, sw, 0x2104)
        display.blit_buffer(x, y, sw, sh, sprite, transparent_color=0x0000)
        display.swap_buffers(copy=True)
        prev = (x, y)
    fps, frames, elapsed_s = measure_fps(duration_s, frame)
    return ({"label": "retained_transparent", "metric": "fps", "value": fps, "detail": {"frames": frames, "elapsed_s": elapsed_s}},)


def open_display(group):
    display = rm690b0.RM690B0(buffer_mode=group["buffer_mode"], render_mode=group["render_mode"])
    display.init_display()
    display.brightness = 1.0
    if group.get("prime_double", False):
        try:
            display.swap_buffers(copy=True)
        except Exception:
            pass
    return display


def collect_results(profile_name, mode_groups):
    cfg = PROFILE_MATRIX[profile_name]
    results = []
    groups_meta = []
    for group in mode_groups:
        groups_meta.append({"name": group["name"]})
        display = open_display(group)
        try:
            tests = cfg["tests"]
            if "full_fill" in tests:
                for row in bench_full_fill(display, group["copy_scene"], cfg["fill_iterations"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "partial_rect" in tests:
                for row in bench_partial_rect(display, group["copy_scene"], cfg["partial_iterations"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "scene_mixed" in tests:
                for row in bench_scene_mixed(display, group["copy_scene"], cfg["scene_iterations"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "text_menu" in tests:
                for row in bench_text_menu(display, group["copy_scene"], cfg["text_iterations"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "text_large" in tests:
                for row in bench_text_large(display, group["copy_scene"], cfg["text_iterations"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "blit_band" in tests:
                for row in bench_blit_band(display, group["copy_scene"], cfg["band_iterations"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "sprite_opaque" in tests:
                for row in bench_sprite_opaque(display, group["copy_scene"], cfg["sprite_duration_s"], background=False):
                    row["group"] = group["name"]
                    results.append(row)
            if "sprite_transparent" in tests:
                for row in bench_sprite_transparent(display, group["copy_scene"], cfg["sprite_duration_s"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "retained_sprite" in tests and group.get("copy_retained"):
                for row in bench_retained_sprite(display, cfg["sprite_duration_s"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "retained_text" in tests and group.get("copy_retained"):
                for row in bench_retained_text(display, cfg["sprite_duration_s"]):
                    row["group"] = group["name"]
                    results.append(row)
            if "retained_transparent" in tests and group.get("copy_retained"):
                for row in bench_retained_transparent(display, cfg["sprite_duration_s"]):
                    row["group"] = group["name"]
                    results.append(row)
        finally:
            display.fill_color(BLACK)
            try:
                display.swap_buffers(copy=False)
            except Exception:
                pass
            display.deinit()
    return groups_meta, results


def run_profile(profile_name, backend_name, note, mode_groups):
    system_info = get_system_info()
    groups_meta, results = collect_results(profile_name, mode_groups)
    prefix = "/%s_%s" % (backend_name.lower(), profile_name)
    payload = {
        "backend": backend_name,
        "profile": profile_name,
        "system": system_info,
        "groups": groups_meta,
        "results": results,
        "note": note,
    }
    report = render_report(profile_name, backend_name, groups_meta, results, system_info, note=note)
    print(report)
    write_reports(prefix, report, payload)

BACKEND_NAME = "FB"
NOTE = "FB-SINGLE and FB-DOUBLE both run core tests with copy=False. Retained tests run only on FB-DOUBLE with copy=True."
MODE_GROUPS = (
    {"name": "FB-SINGLE", "buffer_mode": rm690b0.BUFFER_SINGLE, "render_mode": rm690b0.RENDER_FRAMEBUFFER, "copy_scene": False, "copy_retained": False, "prime_double": False},
    {"name": "FB-DOUBLE", "buffer_mode": rm690b0.BUFFER_DOUBLE, "render_mode": rm690b0.RENDER_FRAMEBUFFER, "copy_scene": False, "copy_retained": True, "prime_double": True},
)

run_profile("quick", BACKEND_NAME, NOTE, MODE_GROUPS)
