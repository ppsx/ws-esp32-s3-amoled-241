# RM690B0 Driver — Project Status

## Overall Readiness (2026-03-07)

## Documentation Roles

- `docs/project_status_summary.md` is the human-oriented status document and should carry the current narrative state, decisions, and risks.
- `docs/project_summary.yaml` is the compact bootstrap context for AI/tools and should remain short, factual, and easy to ingest.

- Standalone `rm690b0` backend is active and maintained.
- Rendering backends are dual-path and runtime-switchable: `FRAMEBUFFER` / `DISPLAY_LIST`.
- DISPLAY_LIST hardening is complete for current v1 baseline.
- FRAMEBUFFER tuning is closed for the current baseline; regression gate remains in place for future changes.

## FRAMEBUFFER Path (Current Baseline)

Implemented and validated:

- `BUFFER_SINGLE` deferred flush: draw calls update framebuffer + dirty map, real panel flush happens on `swap_buffers()`.
- `swap_buffers(copy=True)` dirty-copy: after present, copy only flushed dirty regions (not full framebuffer).
- Full-frame copy fallback: DMA-assisted copy with automatic CPU `memcpy` fallback if DMA path is unavailable.
- Safety ordering: post-swap copy starts only after in-flight display DMA transfer completes.

Latest tuning loop (2026-03-07, closed baseline):

- Kept: FB text dirty batching, adaptive dirty flush planning/coalescing, transparent-run BLIT helper, partial flush row-copy fast path, and copy-back rect coalescing for `swap_buffers(copy=True)`.
- Reverted: dirty coalescing policy experiment and narrow-partial chunk heuristic after retained-BLIT regression.
- Fixed benchmark tooling: removed stray EOF token from `benchmark_fb_profile.py`, corrected `scenario_end` aggregation, and refreshed `compare_fb_profile.py` to the canonical FB baseline.

Observed profile snapshot after final baseline refresh:

- `fb_single_rebuild/primitive_stress`: ~35.5 FPS.
- `fb_double_rebuild/full_redraw_control`: ~25.1 FPS.
- `fb_double_retained/retained_blit_transparent`: ~568-574 FPS (gate PASS).

## DISPLAY_LIST Path (Current Baseline)

- DMA overlap improvements and chunk ping-pong are active.
- Runtime policy: `buffer_mode=BUFFER_SINGLE` recommended for DL deployments.
- Driver still attempts second static chunk allocation (best-effort), so DL ping-pong can still be available in single mode.
- Mixed-frame rendering (`FRAMEBUFFER` + `DISPLAY_LIST` draw calls in one frame) remains intentionally blocked.

Final DL defaults in firmware:

- `GLYPH_ATLAS_SLOTS=40`
- `AUTO_COMPACT_EVERY_N_FRAMES=24`
- `AUTO_COMPACT_MIN_COMMANDS=64`
- `AUTO_COMPACT_GUARD_COMMANDS=3400`
- `AUTO_COMPACT_GUARD_PAYLOAD_BYTES=512 KiB`

## Firmware Artifacts (2026-03-07)

- Stable standalone build artifacts:
  - `firmware/firmware-rm690b0.bin` (`1900432` bytes)
  - `firmware/firmware-rm690b0.uf2` (`3670016` bytes)
- LVGL build artifacts:
  - `firmware/firmware-rm690b0-lvgl.bin` (`2124640` bytes)
  - `firmware/firmware-rm690b0-lvgl.uf2` (`4118528` bytes)
- Operational rule: use `.bin` as the canonical artifact for `esptool.py` flashing; keep `.uf2` as the matching packaged image for UF2-aware distribution flows.
- Current state: both variants are present in the repository and the LVGL image fits again after font-storage deduplication in the driver.

## FB Regression Gate

Automated check script:

- `examples/benchmark_gfx/compare_fb_profile.py`

Current gate targets:

- `fb_single_rebuild / primitive_stress`
- `fb_double_rebuild / full_redraw_control`
- `fb_double_retained / retained_blit_transparent`

Run:

```bash
python examples/benchmark_gfx/compare_fb_profile.py \
  --csv examples/benchmark_gfx/fb_profile.csv
```

Exit code contract:

- `0` = PASS
- `1` = FAIL (missing scenario or below threshold)

## Operational Recommendation

- Keep DL internals frozen at current baseline unless new, reproducible regressions appear.
- Keep FB internals frozen at the current baseline as well, unless a concrete regression appears or a rotation-focused workload justifies `rotation != 0` tuning.

## Open Risks

- LVGL integration remains a separate stream with known GC-pressure touch stability caveats.
- Geometry paths for `rotation != 0` remain mostly untuned and would need dedicated benchmarking before optimization.
- `copy=True` retained scenarios still spend notable time in `swap_ms`, but the low-risk copy-phase workstream has been exhausted for now.

## Examples & Input Ecosystem (2026-03-22)

- Global settings system added: `examples/settings.py` stores rotation (0/180), joystick type (I2C/GPIO), and GPIO pin assignments. Persisted on flash, read by all games and benchmarks at startup.
- Touch-based settings UI (`examples/settings_ui.py`) accessible via gear icon button on the main menu.
- Shared joystick module (`examples/joystick.py`) replaces 7 inline PCA9554 drivers across games. Supports two backends:
  - I2C: PCA9554 expander at address 0x21 (SparkFun Qwiic Navigation Switch)
  - GPIO: direct microswitches with internal pull-up, pin-configurable via settings
- All 8 games and ~30 benchmark files apply `display.rotation` from settings after display init.
- Main menu (`examples/code.py`) updated with settings button and rotation-aware touch mapping.

## Reference Files

- `docs/RM690B0_DRIVER.md`
- `docs/TECHNICAL_NOTES.md`
- `examples/benchmark_gfx/benchmark_fb_profile.py`
- `examples/benchmark_gfx/compare_fb_profile.py`
- `examples/benchmark_gfx/fb_profile.csv`
- `ports/espressif/common-hal/rm690b0/RM690B0.c`
- `ports/espressif/common-hal/rm690b0/rm690b0_draw.c`
- `ports/espressif/common-hal/rm690b0/rm690b0_internal.h`
