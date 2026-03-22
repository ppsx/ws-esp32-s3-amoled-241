# SPDX-FileCopyrightText: Copyright (c) 2026 Przemyslaw Patrick Socha
#
# SPDX-License-Identifier: MIT
"""
RM690B0 DISPLAY_LIST long-run profiler without serial output dependency.

How to use:
1. Copy this file to CIRCUITPY as code.py.
2. Wait for the run to finish (or stop it manually).
3. Read /dl_profile.csv from CIRCUITPY.

The CSV is append-free by default (overwrite each run) and contains periodic
samples with FPS + heap + display-list telemetry.
"""

import gc
import os
import time

import rm690b0


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_PATH = "/dl_profile.csv"
OVERWRITE_OUTPUT = True

SAMPLE_INTERVAL_S = 2.0
WARMUP_S = 1.0

# Keep defaults moderate; increase to 1800+ for deep long-run checks.
DURATION_RETAINED_TEXT_S = 60
DURATION_RETAINED_BLIT_S = 60
DURATION_PAYLOAD_STRESS_S = 45
DURATION_COMMAND_STRESS_S = 45
DURATION_REBUILD_CONTROL_S = 45

BUFFER_MODE = rm690b0.BUFFER_SINGLE

# High enough to cross command guard before periodic compact kicks in.
COMMAND_STRESS_RECTS_PER_FRAME = 180

# Prevent command-list explosion in retained copy=True scenarios.
ENABLE_PERIODIC_COMPACT = False
COMPACT_EVERY_N_FRAMES_COPY_TRUE = 24
COMPACT_GUARD_COMMAND_COUNT = 0


def monotonic_ns():
    try:
        return time.monotonic_ns()
    except AttributeError:
        return int(time.monotonic() * 1_000_000_000)


def stat_get(stats, key):
    return int(stats.get(key, 0))


def make_sprite_rgb565(w, h):
    # Simple gradient sprite, RGB565 little-endian byte order.
    data = bytearray(w * h * 2)
    for y in range(h):
        for x in range(w):
            r = (x * 31) // (w - 1) if w > 1 else 31
            g = (y * 63) // (h - 1) if h > 1 else 63
            b = ((x + y) * 31) // max(1, (w + h - 2))
            c = (r << 11) | (g << 5) | b
            idx = (y * w + x) * 2
            data[idx] = c & 0xFF
            data[idx + 1] = (c >> 8) & 0xFF
    return data


def write_csv_header(f):
    f.write(
        "scenario,copy,elapsed_s,frames_total,window_frames,window_fps,"
        "mem_free,mem_alloc,mem_free_post_gc,mem_alloc_post_gc,"
        "command_count,payload_bytes,max_command_count,max_payload_bytes,"
        "rejected_command_limit,rejected_payload_limit,allocation_failures,"
        "present_count,present_full,present_partial,"
        "compact_count,compact_trimmed_commands,"
        "auto_compact_trigger_periodic,auto_compact_trigger_command_guard,auto_compact_trigger_payload_guard,"
        "glyph_atlas_hits,glyph_atlas_misses,glyph_atlas_builds,glyph_atlas_evictions,"
        "event\n"
    )


def write_sample_row(
    f,
    scenario,
    copy_mode,
    elapsed_s,
    frames_total,
    window_frames,
    window_fps,
    stats,
    event,
):
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    gc.collect()
    mem_free_post_gc = gc.mem_free()
    mem_alloc_post_gc = gc.mem_alloc()

    row = [
        scenario,
        "1" if copy_mode else "0",
        "%.3f" % elapsed_s,
        str(frames_total),
        str(window_frames),
        "%.3f" % window_fps,
        str(mem_free),
        str(mem_alloc),
        str(mem_free_post_gc),
        str(mem_alloc_post_gc),
        str(stat_get(stats, "command_count")),
        str(stat_get(stats, "payload_bytes")),
        str(stat_get(stats, "max_command_count")),
        str(stat_get(stats, "max_payload_bytes")),
        str(stat_get(stats, "rejected_command_limit")),
        str(stat_get(stats, "rejected_payload_limit")),
        str(stat_get(stats, "allocation_failures")),
        str(stat_get(stats, "present_count")),
        str(stat_get(stats, "present_full")),
        str(stat_get(stats, "present_partial")),
        str(stat_get(stats, "compact_count")),
        str(stat_get(stats, "compact_trimmed_commands")),
        str(stat_get(stats, "auto_compact_trigger_periodic")),
        str(stat_get(stats, "auto_compact_trigger_command_guard")),
        str(stat_get(stats, "auto_compact_trigger_payload_guard")),
        str(stat_get(stats, "glyph_atlas_hits")),
        str(stat_get(stats, "glyph_atlas_misses")),
        str(stat_get(stats, "glyph_atlas_builds")),
        str(stat_get(stats, "glyph_atlas_evictions")),
        event,
    ]
    f.write(",".join(row) + "\n")
    f.flush()


def reset_to_clean_frame(display):
    # Ensure the panel and DL state are clean before each scenario.
    display.fill_color(rm690b0.BLACK)
    display.swap_buffers(copy=False)
    display.display_list_stats(reset=True)
    gc.collect()


def setup_retained_text(display, state):
    display.set_font(rm690b0.FONT_16x24)
    display.fill_color(rm690b0.BLACK)
    display.text(8, 8, "DL PROFILE", rm690b0.WHITE)
    display.text(8, 40, "SCENARIO: RETAINED_TEXT", rm690b0.CYAN)
    display.text(8, 72, "copy=True", rm690b0.YELLOW)
    display.swap_buffers(copy=True)


def frame_retained_text(display, frame, state):
    # Opaque clear + redraw on the same region to stress retained-list churn.
    display.fill_rect(8, 120, 584, 32, rm690b0.BLACK)
    display.text(8, 120, "frame=%06d" % frame, rm690b0.WHITE)

    bar_w = 20 + ((frame * 7) % 560)
    display.fill_rect(8, 170, 584, 18, 0x0841)
    display.fill_rect(8, 170, bar_w, 18, rm690b0.GREEN)

    dot_x = 8 + ((frame * 9) % 568)
    display.fill_rect(8, 206, 584, 20, rm690b0.BLACK)
    display.fill_rect(dot_x, 208, 16, 16, rm690b0.YELLOW)


def setup_retained_blit(display, state):
    state["sprite_w"] = 48
    state["sprite_h"] = 48
    state["sprite"] = make_sprite_rgb565(state["sprite_w"], state["sprite_h"])

    display.set_font(rm690b0.FONT_16x16)
    display.fill_color(rm690b0.BLACK)
    display.text(8, 8, "DL PROFILE", rm690b0.WHITE)
    display.text(8, 30, "SCENARIO: RETAINED_BLIT_CHURN", rm690b0.CYAN)
    display.text(8, 52, "copy=True", rm690b0.YELLOW)
    display.fill_rect(0, 300, 600, 80, 0x1082)
    display.swap_buffers(copy=True)


def frame_retained_blit(display, frame, state):
    sw = state["sprite_w"]
    sh = state["sprite_h"]
    sprite = state["sprite"]

    # Clear full strip each frame so older BLIT commands become obsolete.
    display.fill_rect(0, 300, 600, 80, 0x1082)

    x1 = (frame * 5) % (600 - sw)
    x2 = (600 - sw) - x1
    y = 316

    display.blit_buffer(x1, y, sw, sh, sprite)
    display.blit_buffer(x2, y, sw, sh, sprite)


def setup_payload_stress(display, state):
    # Force payload guard activity by enqueueing several opaque BLITs per frame
    # at fixed slots. New BLITs fully cover older commands in each slot.
    sw = 96
    sh = 96
    state["sprite_w"] = sw
    state["sprite_h"] = sh
    state["sprite_a"] = make_sprite_rgb565(sw, sh)

    sprite_b = bytearray(sw * sh * 2)
    src = state["sprite_a"]
    for i in range(0, len(src), 2):
        c = src[i] | (src[i + 1] << 8)
        inv = (~c) & 0xFFFF
        sprite_b[i] = inv & 0xFF
        sprite_b[i + 1] = (inv >> 8) & 0xFF
    state["sprite_b"] = sprite_b

    state["slots"] = (
        (8, 220),
        (204, 220),
        (400, 220),
        (8, 338),
        (204, 338),
        (400, 338),
    )

    display.set_font(rm690b0.FONT_16x16)
    display.fill_color(rm690b0.BLACK)
    display.text(8, 8, "DL PROFILE", rm690b0.WHITE)
    display.text(8, 30, "SCENARIO: PAYLOAD_STRESS", rm690b0.CYAN)
    display.text(8, 52, "copy=True", rm690b0.YELLOW)
    display.swap_buffers(copy=True)


def frame_payload_stress(display, frame, state):
    sw = state["sprite_w"]
    sh = state["sprite_h"]
    sprite_a = state["sprite_a"]
    sprite_b = state["sprite_b"]

    # Keep command coverage deterministic (same slots each frame), while pixel
    # payload changes to prevent trivial no-op style behavior.
    for idx, (x, y) in enumerate(state["slots"]):
        sprite = sprite_a if ((frame + idx) & 1) == 0 else sprite_b
        display.blit_buffer(x, y, sw, sh, sprite)


def setup_command_stress(display, state):
    # Stress command-count guard: many retained fill_rect commands per frame,
    # with a per-frame opaque clear that can compact old history.
    state["rects_per_frame"] = COMMAND_STRESS_RECTS_PER_FRAME
    state["colors"] = (
        0xF800,  # red
        0x07E0,  # green
        0x001F,  # blue
        0xFFE0,  # yellow
    )

    display.set_font(rm690b0.FONT_16x16)
    display.fill_color(rm690b0.BLACK)
    display.text(8, 8, "DL PROFILE", rm690b0.WHITE)
    display.text(8, 30, "SCENARIO: COMMAND_STRESS", rm690b0.CYAN)
    display.text(8, 52, "copy=True", rm690b0.YELLOW)
    display.swap_buffers(copy=True)


def frame_command_stress(display, frame, state):
    rects = state["rects_per_frame"]
    colors = state["colors"]

    # Opaque clear of the stress area lets compaction trim old frame commands.
    display.fill_rect(8, 120, 584, 320, 0x0000)

    for i in range(rects):
        x = 8 + ((i * 13 + frame * 7) % 576)
        y = 120 + ((i * 9 + frame * 5) % 312)
        w = 4 + (i % 5)
        h = 3 + ((i // 5) % 4)
        c = colors[(i + frame) & 0x03]
        display.fill_rect(x, y, w, h, c)


def setup_rebuild_control(display, state):
    display.set_font(rm690b0.FONT_16x16)


def frame_rebuild_control(display, frame, state):
    # copy=False control path: command list rebuilt every frame.
    display.fill_color(rm690b0.BLACK)
    display.text(8, 8, "DL PROFILE", rm690b0.WHITE)
    display.text(8, 30, "SCENARIO: REBUILD_CONTROL", rm690b0.CYAN)
    display.text(8, 52, "copy=False", rm690b0.YELLOW)
    display.text(8, 74, "frame=%06d" % frame, rm690b0.WHITE)

    x = (frame * 11) % 540
    display.fill_rect(8, 120, 584, 24, 0x0841)
    display.fill_rect(8 + x, 120, 44, 24, rm690b0.PINK)


SCENARIOS = (
    {
        "name": "retained_text",
        "duration_s": DURATION_RETAINED_TEXT_S,
        "copy": True,
        "setup": setup_retained_text,
        "frame": frame_retained_text,
    },
    {
        "name": "retained_blit_churn",
        "duration_s": DURATION_RETAINED_BLIT_S,
        "copy": True,
        "setup": setup_retained_blit,
        "frame": frame_retained_blit,
    },
    {
        "name": "retained_payload_stress",
        "duration_s": DURATION_PAYLOAD_STRESS_S,
        "copy": True,
        "setup": setup_payload_stress,
        "frame": frame_payload_stress,
    },
    {
        "name": "retained_command_stress",
        "duration_s": DURATION_COMMAND_STRESS_S,
        "copy": True,
        "setup": setup_command_stress,
        "frame": frame_command_stress,
    },
    {
        "name": "rebuild_control",
        "duration_s": DURATION_REBUILD_CONTROL_S,
        "copy": False,
        "setup": setup_rebuild_control,
        "frame": frame_rebuild_control,
    },
)


def maybe_periodic_compact(display, copy_mode, frames_total):
    if not copy_mode or not ENABLE_PERIODIC_COMPACT:
        return False
    if COMPACT_EVERY_N_FRAMES_COPY_TRUE <= 0:
        return False
    if frames_total <= 0:
        return False
    if (frames_total % COMPACT_EVERY_N_FRAMES_COPY_TRUE) != 0:
        return False

    display.compact_display_list()
    return True


def run_scenario(display, f, scenario):
    name = scenario["name"]
    duration_s = float(scenario["duration_s"])
    copy_mode = bool(scenario["copy"])
    setup_fn = scenario["setup"]
    frame_fn = scenario["frame"]

    reset_to_clean_frame(display)

    state = {}
    try:
        setup_fn(display, state)
    except MemoryError:
        stats = display.display_list_stats(reset=True)
        write_sample_row(
            f,
            name,
            copy_mode,
            0.0,
            0,
            0,
            0.0,
            stats,
            "setup_memory_error",
        )
        return False

    warmup_end = monotonic_ns() + int(WARMUP_S * 1_000_000_000)
    warmup_frame = 0
    while monotonic_ns() < warmup_end:
        try:
            frame_fn(display, warmup_frame, state)
            maybe_periodic_compact(display, copy_mode, warmup_frame)
            display.swap_buffers(copy=copy_mode)
        except MemoryError:
            stats = display.display_list_stats(reset=True)
            write_sample_row(
                f,
                name,
                copy_mode,
                0.0,
                warmup_frame,
                warmup_frame,
                0.0,
                stats,
                "warmup_memory_error",
            )
            return False
        warmup_frame += 1

    display.display_list_stats(reset=True)
    gc.collect()

    start_ns = monotonic_ns()
    end_ns = start_ns + int(duration_s * 1_000_000_000)
    window_start_ns = start_ns

    frames_total = 0
    window_frames = 0
    compacted_in_window = False

    while monotonic_ns() < end_ns:
        try:
            frame_fn(display, frames_total, state)
            if maybe_periodic_compact(display, copy_mode, frames_total):
                compacted_in_window = True
            display.swap_buffers(copy=copy_mode)
        except MemoryError:
            now_ns = monotonic_ns()
            stats = display.display_list_stats(reset=True)
            elapsed_s = (now_ns - start_ns) / 1_000_000_000.0
            window_s = max(1e-9, (now_ns - window_start_ns) / 1_000_000_000.0)
            window_fps = window_frames / window_s
            write_sample_row(
                f,
                name,
                copy_mode,
                elapsed_s,
                frames_total,
                window_frames,
                window_fps,
                stats,
                "memory_error",
            )
            return False

        frames_total += 1
        window_frames += 1

        now_ns = monotonic_ns()
        if (now_ns - window_start_ns) >= int(SAMPLE_INTERVAL_S * 1_000_000_000):
            stats = display.display_list_stats(reset=True)
            event = "sample"

            # Adaptive guard: compact if command count gets too close to DL limit.
            if copy_mode and COMPACT_GUARD_COMMAND_COUNT > 0:
                if stat_get(stats, "command_count") >= COMPACT_GUARD_COMMAND_COUNT:
                    try:
                        display.compact_display_list()
                        event = "sample_compact_guard"
                        compacted_in_window = True
                    except MemoryError:
                        elapsed_s = (now_ns - start_ns) / 1_000_000_000.0
                        window_s = max(1e-9, (now_ns - window_start_ns) / 1_000_000_000.0)
                        window_fps = window_frames / window_s
                        write_sample_row(
                            f,
                            name,
                            copy_mode,
                            elapsed_s,
                            frames_total,
                            window_frames,
                            window_fps,
                            stats,
                            "compact_guard_memory_error",
                        )
                        return False

            if compacted_in_window and event == "sample":
                event = "sample_compact_periodic"

            elapsed_s = (now_ns - start_ns) / 1_000_000_000.0
            window_s = max(1e-9, (now_ns - window_start_ns) / 1_000_000_000.0)
            window_fps = window_frames / window_s
            write_sample_row(
                f,
                name,
                copy_mode,
                elapsed_s,
                frames_total,
                window_frames,
                window_fps,
                stats,
                event,
            )
            window_start_ns = now_ns
            window_frames = 0
            compacted_in_window = False

    final_ns = monotonic_ns()
    stats = display.display_list_stats(reset=True)
    elapsed_s = (final_ns - start_ns) / 1_000_000_000.0
    window_s = max(1e-9, (final_ns - window_start_ns) / 1_000_000_000.0)
    window_fps = window_frames / window_s if window_frames > 0 else 0.0
    end_event = "scenario_end_compact" if compacted_in_window else "scenario_end"
    write_sample_row(
        f,
        name,
        copy_mode,
        elapsed_s,
        frames_total,
        window_frames,
        window_fps,
        stats,
        end_event,
    )

    return True


def main():
    try:
        rm690b0.RM690B0.deinit()
    except Exception:
        pass

    display = rm690b0.RM690B0(
        buffer_mode=BUFFER_MODE,
        render_mode=rm690b0.RENDER_DISPLAY_LIST,
    )
    display.init_display()
    try:
        import settings
        display.rotation = settings.rotation
    except ImportError:
        pass
    display.set_font(rm690b0.FONT_16x16)

    mode = "w" if OVERWRITE_OUTPUT else "a"
    with open(OUTPUT_PATH, mode) as f:
        uname = os.uname()
        f.write("# RM690B0_DL_PROFILE\n")
        f.write(
            "# sysname=%s release=%s machine=%s\n"
            % (uname.sysname, uname.release, uname.machine)
        )
        f.write(
            "# warmup_s=%.2f sample_interval_s=%.2f buffer_mode=%d\n"
            % (WARMUP_S, SAMPLE_INTERVAL_S, BUFFER_MODE)
        )
        f.write(
            "# durations_s retained_text=%d retained_blit_churn=%d retained_payload_stress=%d retained_command_stress=%d rebuild_control=%d\n"
            % (
                DURATION_RETAINED_TEXT_S,
                DURATION_RETAINED_BLIT_S,
                DURATION_PAYLOAD_STRESS_S,
                DURATION_COMMAND_STRESS_S,
                DURATION_REBUILD_CONTROL_S,
            )
        )
        f.write(
            "# compact periodic=%d every_n_frames=%d guard_command_count=%d\n"
            % (
                1 if ENABLE_PERIODIC_COMPACT else 0,
                COMPACT_EVERY_N_FRAMES_COPY_TRUE,
                COMPACT_GUARD_COMMAND_COUNT,
            )
        )
        write_csv_header(f)

        for scenario in SCENARIOS:
            ok = run_scenario(display, f, scenario)
            if not ok:
                break

    display.fill_color(rm690b0.BLACK)
    display.swap_buffers(copy=False)


main()
