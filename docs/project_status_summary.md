# RM690B0 Driver — Project Status

## Overall Readiness (2026-03-06)

- Standalone `rm690b0` backend is active and maintained.
- Rendering backends are dual-path and runtime-switchable: `FRAMEBUFFER` / `DISPLAY_LIST`.
- DISPLAY_LIST hardening is complete for current v1 baseline.
- FRAMEBUFFER optimization loop is active; regression gate is in place and used after each iteration.

## FRAMEBUFFER Path (Current Baseline)

Implemented and validated:

- `BUFFER_SINGLE` deferred flush: draw calls update framebuffer + dirty map, real panel flush happens on `swap_buffers()`.
- `swap_buffers(copy=True)` dirty-copy: after present, copy only flushed dirty regions (not full framebuffer).
- Full-frame copy fallback: DMA-assisted copy with automatic CPU `memcpy` fallback if DMA path is unavailable.
- Safety ordering: post-swap copy starts only after in-flight display DMA transfer completes.

Latest tuning loop (2026-03-06):

- Kept: `blit_buffer` unswapped span helper optimization in FB (`rm690b0_draw.c`) including transparent-run path.
- Reverted: dirty coalescing policy experiment (`RM690B0.c`) due retained BLIT regression.
- Fixed benchmark script runtime issue: removed stray token causing `NameError` in `benchmark_fb_profile.py`.

Observed profile snapshot after revert/fix:

- `fb_single_rebuild/primitive_stress`: ~34.5 FPS.
- `fb_double_rebuild/full_redraw_control`: ~25.0 FPS.
- `fb_double_retained/retained_blit_transparent`: ~1159 FPS (gate PASS).

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
- Continue FB workstream with copy-phase optimization in `swap(copy=True)` as the next priority.

## Open Risks

- LVGL integration remains a separate stream with known GC-pressure touch stability caveats.
- Transparent BLIT optimization ROI depends on workload transparency ratio.
- `copy=True` retained scenarios still spend notable time in `swap_ms`, suggesting room in copy-phase tuning.

## Reference Files

- `docs/RM690B0_DRIVER.md`
- `docs/TECHNICAL_NOTES.md`
- `examples/benchmark_gfx/benchmark_fb_profile.py`
- `examples/benchmark_gfx/compare_fb_profile.py`
- `examples/benchmark_gfx/fb_profile.csv`
- `ports/espressif/common-hal/rm690b0/RM690B0.c`
- `ports/espressif/common-hal/rm690b0/rm690b0_draw.c`
- `ports/espressif/common-hal/rm690b0/rm690b0_internal.h`
