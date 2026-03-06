# SPDX-FileCopyrightText: Copyright (c) 2026 Przemyslaw Patrick Socha
#
# SPDX-License-Identifier: MIT
"""
RM690B0 FRAMEBUFFER profiler (CSV, no serial dependency).

How to use:
1. Copy this file to CIRCUITPY as code.py.
2. Wait until the run finishes.
3. Read /fb_profile.csv from CIRCUITPY.

Purpose:
- Track FRAMEBUFFER backend performance during optimization iterations.
- Compare rebuild workflows (copy=False) and retained workflows (copy=True).
"""

import gc
import os
import time

import rm690b0


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_PATH = "/fb_profile.csv"
OVERWRITE_OUTPUT = True

SAMPLE_INTERVAL_S = 2.0
WARMUP_S = 1.0
PERCENTILE_BIN_MS = 0.25
PERCENTILE_MAX_MS = 128.0

# Scenario durations (seconds)
DURATION_FULL_REDRAW_S = 12
DURATION_PRIMITIVE_STRESS_S = 12
DURATION_TEXT_FULL_REDRAW_S = 12
DURATION_RETAINED_UI_S = 20
DURATION_RETAINED_BLIT_S = 20
DURATION_RETAINED_TEXT_S = 20


# ---------------------------------------------------------------------------
# Colors / constants with safe fallbacks
# ---------------------------------------------------------------------------

BLACK = getattr(rm690b0, "BLACK", 0x0000)
WHITE = getattr(rm690b0, "WHITE", 0xFFFF)
RED = getattr(rm690b0, "RED", 0xF800)
GREEN = getattr(rm690b0, "GREEN", 0x07E0)
BLUE = getattr(rm690b0, "BLUE", 0x001F)
YELLOW = getattr(rm690b0, "YELLOW", 0xFFE0)
CYAN = getattr(rm690b0, "CYAN", 0x07FF)
MAGENTA = getattr(rm690b0, "MAGENTA", 0xF81F)
ORANGE = getattr(rm690b0, "ORANGE", 0xFC00)
GRAY = getattr(rm690b0, "GRAY", 0x7BEF)
PINK = getattr(rm690b0, "PINK", MAGENTA)


MODE_CONFIGS = (
    {
        "name": "fb_single_rebuild",
        "buffer_mode": rm690b0.BUFFER_SINGLE,
        "copy": False,
    },
    {
        "name": "fb_double_rebuild",
        "buffer_mode": rm690b0.BUFFER_DOUBLE,
        "copy": False,
    },
    {
        "name": "fb_double_retained",
        "buffer_mode": rm690b0.BUFFER_DOUBLE,
        "copy": True,
    },
)


def monotonic_ns():
    try:
        return time.monotonic_ns()
    except AttributeError:
        return int(time.monotonic() * 1_000_000_000)


def percentile(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    idx = int((len(ordered) - 1) * p)
    if idx < 0:
        idx = 0
    if idx >= len(ordered):
        idx = len(ordered) - 1
    return float(ordered[idx])


def make_sprite_rgb565_with_transparency(size):
    # Transparent background (0x0000), colored circle + highlight inside.
    data = bytearray(size * size * 2)
    cx = size // 2
    cy = size // 2
    r = max(2, size // 2 - 2)

    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            idx = (y * size + x) * 2

            if dx * dx + dy * dy <= r * r:
                # simple radial color variation
                rr = (31 - min(31, abs(dx))) & 0x1F
                gg = (63 - min(63, abs(dy) * 2)) & 0x3F
                bb = ((abs(dx) + abs(dy)) & 0x1F)
                color = (rr << 11) | (gg << 5) | bb

                # bright highlight
                if (dx + r // 3) * (dx + r // 3) + (dy + r // 3) * (dy + r // 3) < (r // 4) * (r // 4):
                    color = WHITE

                data[idx] = color & 0xFF
                data[idx + 1] = (color >> 8) & 0xFF
            else:
                # transparent key
                data[idx] = 0
                data[idx + 1] = 0

    return data


def write_csv_header(f):
    f.write(
        "mode,buffer_mode,copy,scenario,elapsed_s,frames_total,window_frames,window_fps,"
        "avg_frame_ms,p95_frame_ms,max_frame_ms,avg_draw_ms,avg_swap_ms,"
        "slow_gt25ms,slow_gt40ms,mem_free,mem_alloc,mem_free_post_gc,mem_alloc_post_gc,event,error\n"
    )


def compute_window_metrics(window_frames, frame_ms_values, draw_ms_values, swap_ms_values):
    if window_frames > 0 and frame_ms_values:
        window_time_s = sum(frame_ms_values) / 1000.0
        window_fps = window_frames / window_time_s if window_time_s > 0 else 0.0
        avg_frame_ms = sum(frame_ms_values) / window_frames
        p95_frame_ms = percentile(frame_ms_values, 0.95)
        max_frame_ms = max(frame_ms_values)
        avg_draw_ms = sum(draw_ms_values) / window_frames
        avg_swap_ms = sum(swap_ms_values) / window_frames
    else:
        window_fps = 0.0
        avg_frame_ms = 0.0
        p95_frame_ms = 0.0
        max_frame_ms = 0.0
        avg_draw_ms = 0.0
        avg_swap_ms = 0.0

    return (
        window_fps,
        avg_frame_ms,
        p95_frame_ms,
        max_frame_ms,
        avg_draw_ms,
        avg_swap_ms,
    )


def make_frame_histogram():
    bins = int(PERCENTILE_MAX_MS / PERCENTILE_BIN_MS) + 1
    return [0] * bins


def add_frame_histogram_sample(histogram, frame_ms):
    idx = int(frame_ms / PERCENTILE_BIN_MS)
    if idx < 0:
        idx = 0
    elif idx >= len(histogram):
        idx = len(histogram) - 1
    histogram[idx] += 1


def histogram_percentile(histogram, total_count, p):
    if total_count <= 0:
        return 0.0

    threshold = int(total_count * p)
    if threshold <= 0:
        threshold = 1

    seen = 0
    for idx, count in enumerate(histogram):
        seen += count
        if seen >= threshold:
            return idx * PERCENTILE_BIN_MS

    return (len(histogram) - 1) * PERCENTILE_BIN_MS


def write_sample_row(
    f,
    mode_name,
    buffer_mode,
    copy_mode,
    scenario_name,
    elapsed_s,
    frames_total,
    window_frames,
    frame_ms_values,
    draw_ms_values,
    swap_ms_values,
    slow_25,
    slow_40,
    event,
    error,
    metrics_override=None,
):
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    gc.collect()
    mem_free_post_gc = gc.mem_free()
    mem_alloc_post_gc = gc.mem_alloc()

    if metrics_override is not None:
        window_fps = metrics_override["window_fps"]
        avg_frame_ms = metrics_override["avg_frame_ms"]
        p95_frame_ms = metrics_override["p95_frame_ms"]
        max_frame_ms = metrics_override["max_frame_ms"]
        avg_draw_ms = metrics_override["avg_draw_ms"]
        avg_swap_ms = metrics_override["avg_swap_ms"]
    else:
        (
            window_fps,
            avg_frame_ms,
            p95_frame_ms,
            max_frame_ms,
            avg_draw_ms,
            avg_swap_ms,
        ) = compute_window_metrics(window_frames, frame_ms_values, draw_ms_values, swap_ms_values)

    row = [
        mode_name,
        str(buffer_mode),
        "1" if copy_mode else "0",
        scenario_name,
        "%.3f" % elapsed_s,
        str(frames_total),
        str(window_frames),
        "%.3f" % window_fps,
        "%.3f" % avg_frame_ms,
        "%.3f" % p95_frame_ms,
        "%.3f" % max_frame_ms,
        "%.3f" % avg_draw_ms,
        "%.3f" % avg_swap_ms,
        str(slow_25),
        str(slow_40),
        str(mem_free),
        str(mem_alloc),
        str(mem_free_post_gc),
        str(mem_alloc_post_gc),
        event,
        error,
    ]
    f.write(",".join(row) + "\n")
    f.flush()


def reset_display(display):
    display.fill_color(BLACK)
    display.swap_buffers(copy=False)
    gc.collect()


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def setup_full_redraw(display, state):
    display.set_font(rm690b0.FONT_16x16)


def frame_full_redraw(display, frame, state):
    colors = (BLACK, 0x0821, 0x1082, 0x18C3)
    display.fill_color(colors[frame & 0x03])

    x = (frame * 9) % 560
    y = 80 + ((frame * 5) % 260)
    display.fill_rect(x, y, 40, 30, ORANGE)
    display.line(0, y, 599, 449 - y, CYAN)
    display.fill_circle(300, 225, 32 + (frame % 24), RED)

    display.text(8, 8, "FB FULL REDRAW", WHITE)
    display.text(8, 30, "frame=%06d" % frame, YELLOW)


def setup_primitive_stress(display, state):
    display.set_font(rm690b0.FONT_8x8)
    display.fill_color(BLACK)


def frame_primitive_stress(display, frame, state):
    # Partial region clear to keep workload dirty-heavy, not full redraw.
    display.fill_rect(20, 70, 560, 320, 0x0000)

    for i in range(18):
        x0 = 20 + ((i * 31 + frame * 7) % 560)
        y0 = 70 + ((i * 23 + frame * 5) % 320)
        x1 = 20 + ((i * 11 + frame * 13) % 560)
        y1 = 70 + ((i * 17 + frame * 3) % 320)
        color = (RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW)[(i + frame) % 6]
        display.line(x0, y0, x1, y1, color)

    for i in range(6):
        cx = 60 + ((frame * (5 + i)) % 480)
        cy = 110 + ((frame * (3 + i)) % 220)
        r = 8 + ((frame + i * 7) % 26)
        display.circle(cx, cy, r, WHITE)

    display.text(8, 8, "FB PRIMITIVE STRESS", GRAY)


def setup_text_full_redraw(display, state):
    display.set_font(rm690b0.FONT_16x16)


def frame_text_full_redraw(display, frame, state):
    display.fill_color(BLACK)
    display.text(8, 8, "FB TEXT FULL REDRAW", WHITE)
    for i in range(12):
        y = 34 + i * 18
        value = (frame * (i + 3) * 97) & 0xFFFF
        display.text(8, y, "row=%02d val=%05d" % (i, value), (CYAN, YELLOW, GREEN, PINK)[i & 0x03])


def setup_retained_ui(display, state):
    display.set_font(rm690b0.FONT_16x16)
    display.fill_color(BLACK)
    display.text(8, 8, "FB RETAINED UI", WHITE)
    display.text(8, 30, "copy=True", CYAN)
    display.fill_rect(8, 80, 584, 24, 0x0841)
    display.fill_rect(8, 120, 584, 24, 0x0841)
    display.fill_rect(8, 160, 584, 24, 0x0841)


def frame_retained_ui(display, frame, state):
    display.fill_rect(8, 80, 584, 24, 0x0841)
    display.fill_rect(8, 120, 584, 24, 0x0841)
    display.fill_rect(8, 160, 584, 24, 0x0841)

    progress = (frame * 11) % 560
    display.fill_rect(8, 80, progress, 24, GREEN)

    level = (frame * 7) % 560
    display.fill_rect(8, 120, level, 24, BLUE)

    x = 8 + ((frame * 9) % 560)
    display.fill_rect(x, 160, 16, 24, ORANGE)

    display.fill_rect(8, 200, 350, 24, BLACK)
    display.text(8, 200, "frame=%06d prog=%03d lvl=%03d" % (frame, progress, level), WHITE)


def setup_retained_blit(display, state):
    display.set_font(rm690b0.FONT_16x16)
    display.fill_color(BLACK)
    display.text(8, 8, "FB RETAINED BLIT", WHITE)
    display.text(8, 30, "transparent blit", CYAN)

    state["bg_color"] = 0x1082
    display.fill_rect(0, 90, 600, 330, state["bg_color"])

    sprite_size = 44
    state["sprite_w"] = sprite_size
    state["sprite_h"] = sprite_size
    state["sprite"] = make_sprite_rgb565_with_transparency(sprite_size)

    state["x"] = 100
    state["y"] = 160
    state["vx"] = 7
    state["vy"] = 5
    state["prev_x"] = state["x"]
    state["prev_y"] = state["y"]


def frame_retained_blit(display, frame, state):
    sw = state["sprite_w"]
    sh = state["sprite_h"]

    # Clear previous sprite position.
    display.fill_rect(state["prev_x"], state["prev_y"], sw, sh, state["bg_color"])

    # Update position.
    nx = state["x"] + state["vx"]
    ny = state["y"] + state["vy"]

    if nx <= 0 or nx + sw >= 600:
        state["vx"] = -state["vx"]
        nx = state["x"] + state["vx"]
    if ny <= 90 or ny + sh >= 420:
        state["vy"] = -state["vy"]
        ny = state["y"] + state["vy"]

    state["x"] = nx
    state["y"] = ny

    display.blit_buffer(nx, ny, sw, sh, state["sprite"], transparent_color=0x0000)

    state["prev_x"] = nx
    state["prev_y"] = ny


def setup_retained_text(display, state):
    display.set_font(rm690b0.FONT_16x24)
    display.fill_color(BLACK)
    display.text(8, 8, "FB RETAINED TEXT", WHITE)
    display.text(8, 36, "copy=True", CYAN)


def frame_retained_text(display, frame, state):
    # Update only text rows; this stresses text + dirty tracking in retained mode.
    display.fill_rect(8, 80, 584, 32, BLACK)
    display.fill_rect(8, 118, 584, 32, BLACK)
    display.fill_rect(8, 156, 584, 32, BLACK)

    v0 = (frame * 97) & 0xFFFF
    v1 = (frame * 193) & 0xFFFF
    v2 = (frame * 389) & 0xFFFF

    display.text(8, 80, "A=%05d" % v0, YELLOW)
    display.text(8, 118, "B=%05d" % v1, GREEN)
    display.text(8, 156, "C=%05d" % v2, PINK)


SCENARIOS = (
    {
        "name": "full_redraw_control",
        "duration_s": DURATION_FULL_REDRAW_S,
        "modes": ("fb_single_rebuild", "fb_double_rebuild", "fb_double_retained"),
        "setup": setup_full_redraw,
        "frame": frame_full_redraw,
    },
    {
        "name": "primitive_stress",
        "duration_s": DURATION_PRIMITIVE_STRESS_S,
        "modes": ("fb_single_rebuild", "fb_double_rebuild"),
        "setup": setup_primitive_stress,
        "frame": frame_primitive_stress,
    },
    {
        "name": "text_full_redraw",
        "duration_s": DURATION_TEXT_FULL_REDRAW_S,
        "modes": ("fb_single_rebuild", "fb_double_rebuild"),
        "setup": setup_text_full_redraw,
        "frame": frame_text_full_redraw,
    },
    {
        "name": "retained_ui",
        "duration_s": DURATION_RETAINED_UI_S,
        "modes": ("fb_double_retained",),
        "setup": setup_retained_ui,
        "frame": frame_retained_ui,
    },
    {
        "name": "retained_blit_transparent",
        "duration_s": DURATION_RETAINED_BLIT_S,
        "modes": ("fb_double_retained",),
        "setup": setup_retained_blit,
        "frame": frame_retained_blit,
    },
    {
        "name": "retained_text",
        "duration_s": DURATION_RETAINED_TEXT_S,
        "modes": ("fb_double_retained",),
        "setup": setup_retained_text,
        "frame": frame_retained_text,
    },
)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_scenario(display, f, mode_cfg, scenario):
    mode_name = mode_cfg["name"]
    buffer_mode = int(mode_cfg["buffer_mode"])
    copy_mode = bool(mode_cfg["copy"])
    scenario_name = scenario["name"]
    duration_s = float(scenario["duration_s"])

    reset_display(display)

    state = {}
    try:
        scenario["setup"](display, state)
    except MemoryError as exc:
        write_sample_row(
            f,
            mode_name,
            buffer_mode,
            copy_mode,
            scenario_name,
            0.0,
            0,
            0,
            [],
            [],
            [],
            0,
            0,
            "setup_memory_error",
            str(exc),
        )
        return False

    # Warmup
    warmup_end = monotonic_ns() + int(WARMUP_S * 1_000_000_000)
    warmup_frame = 0
    while monotonic_ns() < warmup_end:
        scenario["frame"](display, warmup_frame, state)
        display.swap_buffers(copy=copy_mode)
        warmup_frame += 1

    gc.collect()

    start_ns = monotonic_ns()
    end_ns = start_ns + int(duration_s * 1_000_000_000)
    window_start_ns = start_ns

    frames_total = 0
    window_frames = 0
    frame_ms_values = []
    draw_ms_values = []
    swap_ms_values = []
    slow_25 = 0
    slow_40 = 0
    scenario_frame_sum_ms = 0.0
    scenario_draw_sum_ms = 0.0
    scenario_swap_sum_ms = 0.0
    scenario_max_frame_ms = 0.0
    scenario_slow_25 = 0
    scenario_slow_40 = 0
    scenario_histogram = make_frame_histogram()

    while monotonic_ns() < end_ns:
        frame_start_ns = monotonic_ns()
        try:
            scenario["frame"](display, frames_total, state)
            draw_end_ns = monotonic_ns()
            display.swap_buffers(copy=copy_mode)
            frame_end_ns = monotonic_ns()
        except MemoryError as exc:
            elapsed_s = (monotonic_ns() - start_ns) / 1_000_000_000.0
            write_sample_row(
                f,
                mode_name,
                buffer_mode,
                copy_mode,
                scenario_name,
                elapsed_s,
                frames_total,
                window_frames,
                frame_ms_values,
                draw_ms_values,
                swap_ms_values,
                slow_25,
                slow_40,
                "memory_error",
                str(exc),
            )
            return False
        except Exception as exc:  # pylint: disable=broad-except
            elapsed_s = (monotonic_ns() - start_ns) / 1_000_000_000.0
            write_sample_row(
                f,
                mode_name,
                buffer_mode,
                copy_mode,
                scenario_name,
                elapsed_s,
                frames_total,
                window_frames,
                frame_ms_values,
                draw_ms_values,
                swap_ms_values,
                slow_25,
                slow_40,
                "runtime_error",
                str(exc),
            )
            return False

        draw_ms = (draw_end_ns - frame_start_ns) / 1_000_000.0
        swap_ms = (frame_end_ns - draw_end_ns) / 1_000_000.0
        frame_ms = (frame_end_ns - frame_start_ns) / 1_000_000.0

        frame_ms_values.append(frame_ms)
        draw_ms_values.append(draw_ms)
        swap_ms_values.append(swap_ms)
        scenario_frame_sum_ms += frame_ms
        scenario_draw_sum_ms += draw_ms
        scenario_swap_sum_ms += swap_ms
        if frame_ms > scenario_max_frame_ms:
            scenario_max_frame_ms = frame_ms
        add_frame_histogram_sample(scenario_histogram, frame_ms)
        if frame_ms > 25.0:
            slow_25 += 1
            scenario_slow_25 += 1
        if frame_ms > 40.0:
            slow_40 += 1
            scenario_slow_40 += 1

        frames_total += 1
        window_frames += 1

        now_ns = monotonic_ns()
        if now_ns - window_start_ns >= int(SAMPLE_INTERVAL_S * 1_000_000_000):
            elapsed_s = (now_ns - start_ns) / 1_000_000_000.0
            write_sample_row(
                f,
                mode_name,
                buffer_mode,
                copy_mode,
                scenario_name,
                elapsed_s,
                frames_total,
                window_frames,
                frame_ms_values,
                draw_ms_values,
                swap_ms_values,
                slow_25,
                slow_40,
                "sample",
                "",
            )

            window_start_ns = now_ns
            window_frames = 0
            frame_ms_values = []
            draw_ms_values = []
            swap_ms_values = []
            slow_25 = 0
            slow_40 = 0

    final_ns = monotonic_ns()
    elapsed_s = (final_ns - start_ns) / 1_000_000_000.0
    if frames_total > 0:
        scenario_time_s = scenario_frame_sum_ms / 1000.0
        scenario_metrics = {
            "window_fps": (frames_total / scenario_time_s) if scenario_time_s > 0 else 0.0,
            "avg_frame_ms": scenario_frame_sum_ms / frames_total,
            "p95_frame_ms": histogram_percentile(scenario_histogram, frames_total, 0.95),
            "max_frame_ms": scenario_max_frame_ms,
            "avg_draw_ms": scenario_draw_sum_ms / frames_total,
            "avg_swap_ms": scenario_swap_sum_ms / frames_total,
        }
    else:
        scenario_metrics = {
            "window_fps": 0.0,
            "avg_frame_ms": 0.0,
            "p95_frame_ms": 0.0,
            "max_frame_ms": 0.0,
            "avg_draw_ms": 0.0,
            "avg_swap_ms": 0.0,
        }
    write_sample_row(
        f,
        mode_name,
        buffer_mode,
        copy_mode,
        scenario_name,
        elapsed_s,
        frames_total,
        frames_total,
        frame_ms_values,
        draw_ms_values,
        swap_ms_values,
        scenario_slow_25,
        scenario_slow_40,
        "scenario_end",
        "",
        metrics_override=scenario_metrics,
    )

    return True


def run_mode(f, mode_cfg):
    mode_name = mode_cfg["name"]
    print("MODE_START", mode_name)

    try:
        rm690b0.RM690B0.deinit()
    except Exception:
        pass

    display = rm690b0.RM690B0(
        buffer_mode=mode_cfg["buffer_mode"],
        render_mode=rm690b0.RENDER_FRAMEBUFFER,
    )
    display.init_display()
    display.set_font(rm690b0.FONT_16x16)

    # Trigger optional front-buffer allocation early for BUFFER_DOUBLE.
    if mode_cfg["buffer_mode"] == rm690b0.BUFFER_DOUBLE:
        try:
            display.swap_buffers(copy=False)
            display.swap_buffers(copy=False)
        except Exception:
            pass

    ok = True
    for scenario in SCENARIOS:
        if mode_name not in scenario["modes"]:
            continue
        print("SCENARIO_START", mode_name, scenario["name"])
        if not run_scenario(display, f, mode_cfg, scenario):
            ok = False
            break

    try:
        display.fill_color(BLACK)
        display.swap_buffers(copy=False)
    except Exception:
        pass

    display.deinit()
    print("MODE_END", mode_name, 1 if ok else 0)
    return ok


def main():
    print("RM690B0_FB_PROFILE_START")

    mode = "w" if OVERWRITE_OUTPUT else "a"
    with open(OUTPUT_PATH, mode) as f:
        uname = os.uname()
        f.write("# RM690B0_FB_PROFILE\n")
        f.write(
            "# sysname=%s release=%s machine=%s\n"
            % (uname.sysname, uname.release, uname.machine)
        )
        f.write(
            "# warmup_s=%.2f sample_interval_s=%.2f\n"
            % (WARMUP_S, SAMPLE_INTERVAL_S)
        )
        f.write(
            "# durations_s full_redraw=%d primitive_stress=%d text_full_redraw=%d retained_ui=%d retained_blit=%d retained_text=%d\n"
            % (
                DURATION_FULL_REDRAW_S,
                DURATION_PRIMITIVE_STRESS_S,
                DURATION_TEXT_FULL_REDRAW_S,
                DURATION_RETAINED_UI_S,
                DURATION_RETAINED_BLIT_S,
                DURATION_RETAINED_TEXT_S,
            )
        )
        write_csv_header(f)

        for mode_cfg in MODE_CONFIGS:
            if not run_mode(f, mode_cfg):
                break

    print("RM690B0_FB_PROFILE_END")


main()
