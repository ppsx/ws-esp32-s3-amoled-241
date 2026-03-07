# RM690B0 Documentation Index

This directory tracks the standalone `rm690b0` driver documentation for Waveshare ESP32-S3 AMOLED 2.41.

## Start Here

- Human-oriented status and decisions: [project_status_summary.md](project_status_summary.md)
- AI/bootstrap context: [project_summary.yaml](project_summary.yaml)

## Current Status (2026-03-07)

- `FRAMEBUFFER` and `DISPLAY_LIST` backends co-exist and are runtime-switchable (`render_mode`).
- DISPLAY_LIST performance hardening is closed for the current v1 baseline.
- FRAMEBUFFER tuning is also closed for the current baseline; the remaining work is optional (`rotation != 0` specialization) rather than required performance recovery.
- Final DL runtime defaults in firmware:
  - `RM690B0_DL_GLYPH_ATLAS_SLOTS = 40`
  - `RM690B0_DL_AUTO_COMPACT_EVERY_N_FRAMES = 24`
  - `RM690B0_DL_AUTO_COMPACT_MIN_COMMANDS = 64`
  - `RM690B0_DL_AUTO_COMPACT_GUARD_COMMANDS = 3400`
  - `RM690B0_DL_AUTO_COMPACT_GUARD_PAYLOAD_BYTES = 512 * 1024`
- `BUFFER_SINGLE` is recommended default for DL. The driver still tries to allocate a second static DMA chunk buffer (best-effort), so ping-pong can still be used when memory allows.
- Mixed `FRAMEBUFFER` + `DISPLAY_LIST` drawing in one frame remains intentionally blocked.
- Latest FB tuning loop outcome:
  - kept: FB text dirty batching, adaptive dirty flush planning, transparent BLIT run-copy/span helper, partial flush row-copy fast path, and copy-back rect coalescing for `swap_buffers(copy=True)`,
  - reverted: aggressive dirty coalescing policy variant and narrow-partial chunk heuristic after measured retained-BLIT regression.
- `benchmark_fb_profile.py` fixes are in place: stray EOF token removed, `scenario_end` metrics now reflect the whole scenario, and `compare_fb_profile.py` baseline matches the canonical FB profile gate.
- Pre-built firmware artifacts are available in `../firmware/` for both variants (`firmware-rm690b0` and `firmware-rm690b0-lvgl`), each as `.bin` and `.uf2`. Use `.bin` with `esptool.py`; keep `.uf2` as a distribution artifact for UF2-aware tooling.

## Runtime Guidance

- `FRAMEBUFFER + copy=False`: highest FPS for full-redraw animation workloads.
- `FRAMEBUFFER + copy=True`: retained UI with incremental updates (copy only changed regions after swap).
- `FRAMEBUFFER + BUFFER_SINGLE`: deferred flush model (draw now, flush once on `swap_buffers()`).
- `DISPLAY_LIST + copy=False`: command-stream scenes rebuilt every frame.
- `DISPLAY_LIST + copy=True`: retained command lists with partial presents; monitor health via `display_list_stats()`.
- LVGL path (`rm690b0_lvgl`) is separate and should not be treated as DL-backend reuse.

## Key Documents

- [RM690B0_DRIVER.md](RM690B0_DRIVER.md)
  - API reference and architecture for standalone driver.
- [TECHNICAL_NOTES.md](TECHNICAL_NOTES.md)
  - Performance notes, historical context, and troubleshooting.
- [project_status_summary.md](project_status_summary.md)
  - Executive status and immediate priorities.
- [project_summary.yaml](project_summary.yaml)
  - Short machine-readable bootstrap context for AI/tools.
- [RM690B0_LVGL.md](RM690B0_LVGL.md)
  - LVGL integration reference (maintained separately).
- [../firmware/README.md](../firmware/README.md)
  - Pre-built firmware artifact matrix and flashing instructions.
- `examples/benchmark_gfx/benchmark_fb_profile.py`
  - Full FB profile benchmark (CSV generator).
- `examples/benchmark_gfx/compare_fb_profile.py`
  - FB profile regression gate (PASS/FAIL for key scenarios).

Last updated: `2026-03-07`
