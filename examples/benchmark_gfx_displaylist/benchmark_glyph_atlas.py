# SPDX-FileCopyrightText: Copyright (c) 2026 Przemyslaw Patrick Socha
#
# SPDX-License-Identifier: MIT
"""
RM690B0 DISPLAY_LIST glyph-atlas benchmark.

Copy this file to CIRCUITPY as code.py and read serial output.
The script prints CSV rows that can be pasted into a spreadsheet.
"""

import gc
import os
import time

import rm690b0


WARMUP_SECONDS = 3.0
MEASURE_SECONDS = 12.0
SWAP_COPY = False
# Keep this in sync with RM690B0_DL_GLYPH_ATLAS_SLOTS in C driver.
ATLAS_SLOTS_BUILD = 40


def monotonic_ns():
    try:
        return time.monotonic_ns()
    except AttributeError:
        return int(time.monotonic() * 1_000_000_000)


def percentile(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * p)
    return ordered[idx]


def draw_static_ui(display, frame):
    display.fill_color(rm690b0.BLACK)
    display.text(6, 6, "RM690B0 ATLAS BENCH", rm690b0.WHITE)
    display.text(6, 34, "SCENARIO: STATIC_UI", rm690b0.CYAN)
    display.text(6, 62, "FRAME: %06d" % frame, rm690b0.LIME)
    display.text(6, 90, "ALT: 1234m", rm690b0.YELLOW)
    display.text(6, 118, "SPD: 87.6 m/s", rm690b0.YELLOW)
    display.text(6, 146, "TEMP: 21.4 C", rm690b0.YELLOW)
    display.text(6, 174, "MODE: NOMINAL", rm690b0.PINK)


def draw_live_numbers(display, frame):
    display.fill_color(rm690b0.BLACK)
    temp_tenths = 200 + ((frame * 7) % 180)
    press_tenths = 9800 + ((frame * 13) % 700)
    alt = 900 + ((frame * 11) % 2200)
    speed_tenths = 120 + ((frame * 9) % 500)
    display.text(6, 6, "SCENARIO: LIVE_NUMBERS", rm690b0.CYAN)
    display.text(6, 34, "FRAME: %06d" % frame, rm690b0.WHITE)
    display.text(6, 62, "TEMP: %d.%d C" % (temp_tenths // 10, temp_tenths % 10), rm690b0.YELLOW)
    display.text(6, 90, "PRESS: %d.%d hPa" % (press_tenths // 10, press_tenths % 10), rm690b0.YELLOW)
    display.text(6, 118, "ALT: %d m" % alt, rm690b0.YELLOW)
    display.text(6, 146, "SPD: %d.%d m/s" % (speed_tenths // 10, speed_tenths % 10), rm690b0.YELLOW)
    display.text(6, 174, "BAT: %d%%" % (40 + (frame % 60)), rm690b0.LIME)


def draw_ascii_sweep(display, frame):
    display.fill_color(rm690b0.BLACK)
    line_h = display.font_height + 2
    start = frame % 95
    y = 4
    display.text(4, y, "SCENARIO: ASCII_SWEEP", rm690b0.CYAN)
    y += line_h
    width_chars = 24
    for row in range(7):
        base = start + row * width_chars
        chars = []
        for col in range(width_chars):
            code = 32 + ((base + col) % 95)
            chars.append(chr(code))
        display.text(4, y, "".join(chars), rm690b0.WHITE)
        y += line_h


def draw_mixed_fonts(display, frame):
    display.fill_color(rm690b0.BLACK)
    fonts = (
        rm690b0.FONT_8x8,
        rm690b0.FONT_16x16,
        rm690b0.FONT_24x24,
    )
    font = fonts[frame % len(fonts)]
    display.set_font(font)
    line_h = display.font_height + 2
    y = 4
    display.text(4, y, "SCENARIO: MIXED_FONTS", rm690b0.CYAN)
    y += line_h
    display.text(4, y, "FONT=%d FRAME=%06d" % (font, frame), rm690b0.WHITE)
    y += line_h
    display.text(4, y, "0123456789 +-*/= .,:", rm690b0.YELLOW)
    y += line_h
    display.text(4, y, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", rm690b0.LIME)
    y += line_h
    display.text(4, y, "abcdefghijklmnopqrstuvwxyz", rm690b0.PINK)


def run_scenario(display, name, font_id, draw_fn):
    display.set_font(font_id)
    gc.collect()
    display.display_list_stats(reset=True)

    warmup_end = monotonic_ns() + int(WARMUP_SECONDS * 1_000_000_000)
    frame = 0
    while monotonic_ns() < warmup_end:
        draw_fn(display, frame)
        display.swap_buffers(copy=SWAP_COPY)
        frame += 1

    display.display_list_stats(reset=True)
    gc.collect()

    frame_times_ms = []
    start_ns = monotonic_ns()
    end_ns = start_ns + int(MEASURE_SECONDS * 1_000_000_000)
    frame = 0
    while monotonic_ns() < end_ns:
        t0 = monotonic_ns()
        draw_fn(display, frame)
        display.swap_buffers(copy=SWAP_COPY)
        t1 = monotonic_ns()
        frame_times_ms.append((t1 - t0) / 1_000_000.0)
        frame += 1
    total_ns = monotonic_ns() - start_ns

    stats = display.display_list_stats(reset=True)

    frames = len(frame_times_ms)
    total_s = total_ns / 1_000_000_000.0 if total_ns > 0 else 0.0
    fps = (frames / total_s) if total_s > 0 else 0.0
    avg_ms = (sum(frame_times_ms) / frames) if frames else 0.0
    p95_ms = percentile(frame_times_ms, 0.95)
    max_ms = max(frame_times_ms) if frames else 0.0

    hits = int(stats.get("glyph_atlas_hits", 0))
    misses = int(stats.get("glyph_atlas_misses", 0))
    builds = int(stats.get("glyph_atlas_builds", 0))
    evictions = int(stats.get("glyph_atlas_evictions", 0))
    lookups = hits + misses
    hit_rate = (100.0 * hits / lookups) if lookups > 0 else 100.0

    print(
        "CSV,%s,%d,%.3f,%.3f,%.3f,%.2f,%.2f,%d,%d,%d,%d"
        % (
            name,
            frames,
            avg_ms,
            p95_ms,
            max_ms,
            fps,
            hit_rate,
            hits,
            misses,
            builds,
            evictions,
        )
    )


def main():
    try:
        rm690b0.RM690B0.deinit()
    except Exception:
        pass

    display = rm690b0.RM690B0(
        buffer_mode=rm690b0.BUFFER_SINGLE,
        render_mode=rm690b0.RENDER_DISPLAY_LIST,
    )
    display.init_display()
    try:
        import settings
        display.rotation = settings.rotation
    except ImportError:
        pass
    display.set_font(rm690b0.FONT_16x24)

    uname = os.uname()
    print("RM690B0_GLYPH_ATLAS_BENCH_START")
    print(
        "INFO,sysname=%s,release=%s,machine=%s,warmup_s=%.1f,measure_s=%.1f,swap_copy=%s,atlas_slots_build=%d"
        % (uname.sysname, uname.release, uname.machine, WARMUP_SECONDS, MEASURE_SECONDS, SWAP_COPY, ATLAS_SLOTS_BUILD)
    )
    print(
        "CSV_HEADER,scenario,frames,avg_frame_ms,p95_frame_ms,max_frame_ms,fps,hit_rate_percent,hits,misses,builds,evictions"
    )

    run_scenario(display, "static_ui", rm690b0.FONT_16x24, draw_static_ui)
    run_scenario(display, "live_numbers", rm690b0.FONT_16x24, draw_live_numbers)
    run_scenario(display, "ascii_sweep", rm690b0.FONT_16x16, draw_ascii_sweep)
    run_scenario(display, "mixed_fonts", rm690b0.FONT_8x8, draw_mixed_fonts)

    print("RM690B0_GLYPH_ATLAS_BENCH_END")


main()
