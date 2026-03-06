# RM690B0 Documentation Index

This directory tracks the standalone `rm690b0` driver workstream (branch: `display-list`) for Waveshare ESP32-S3 AMOLED 2.41.

## Current Status (2026-03-06)

- `FRAMEBUFFER` and `DISPLAY_LIST` backends co-exist and are runtime-switchable (`render_mode`).
- DISPLAY_LIST performance hardening is closed for the current v1 baseline.
- Final DL runtime defaults in firmware:
  - `RM690B0_DL_GLYPH_ATLAS_SLOTS = 40`
  - `RM690B0_DL_AUTO_COMPACT_EVERY_N_FRAMES = 24`
  - `RM690B0_DL_AUTO_COMPACT_MIN_COMMANDS = 64`
  - `RM690B0_DL_AUTO_COMPACT_GUARD_COMMANDS = 3400`
  - `RM690B0_DL_AUTO_COMPACT_GUARD_PAYLOAD_BYTES = 512 * 1024`
- `BUFFER_SINGLE` is recommended default for DL. The driver still tries to allocate a second static DMA chunk buffer (best-effort), so ping-pong can still be used when memory allows.
- Mixed `FRAMEBUFFER` + `DISPLAY_LIST` drawing in one frame remains intentionally blocked.
- Latest FB tuning loop outcome:
  - kept: unswapped BLIT span helper optimization (`blit_buffer`, transparent run-copy path),
  - reverted: aggressive dirty coalescing policy variant (measured regression in retained BLIT workload).
- `benchmark_fb_profile.py` runtime `NameError` (stray token at EOF) was fixed.

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
  - Machine-readable project snapshot.
- [snapshot.txt](snapshot.txt)
  - Compact status dump for tooling/automation.
- [RM690B0_LVGL.md](RM690B0_LVGL.md)
  - LVGL integration reference (maintained separately).
- `examples/benchmark_gfx/benchmark_fb_profile.py`
  - Full FB profile benchmark (CSV generator).
- `examples/benchmark_gfx/compare_fb_profile.py`
  - FB profile regression gate (PASS/FAIL for key scenarios).

Last updated: `2026-03-06`
