# Consolidated Benchmark Suites

Primary entrypoints:
- each `benchmark_*.py` is fully standalone and can be copied directly as `code.py`
- `benchmark_quick.py` - fastest smoke check, only core comparable scenarios
- `benchmark_standard.py` - recommended default for routine comparisons
- `benchmark_full.py` - longest run, adds retained/backend-specific scenarios

Human-readable results are printed to serial and also written as:
- `/fb_<profile>.txt`
- `/fb_<profile>.json`

Groups reported by this directory:
- `FB-SINGLE` - framebuffer, single buffer, core tests with `copy=False`
- `FB-DOUBLE` - framebuffer, double buffer, core tests with `copy=False` plus retained tests with `copy=True`

Core comparable scenarios used across firmware families:
- `full_fill`
- `partial_rect`
- `scene_mixed`
- `text_menu`
- `text_large`
- `blit_band`
- `sprite_opaque`
- `sprite_transparent`

Backend-specific scenarios kept in the consolidated suite:
- `retained_sprite`
- `retained_text`
- `retained_transparent`

Legacy benchmark scripts remain available for deep diagnostics:
- `benchmark_fb_profile.py` - long-run FB profiler and regression tracking
- `benchmark_simple_flush.py` - low-level flush-focused checks
- `benchmark_animation_*.py` - targeted sprite animation experiments
- `benchmark_text.py` / `benchmark_gfx_display.py` - older narrower workloads

Host-side comparison:
- `python ../examples/benchmark_compare.py fb=fb_standard.json dl=../benchmark_gfx_displaylist/dl_standard.json dio=../benchmark_gfx_displayio/displayio_standard.json`
- input files are the `*.json` outputs produced by the consolidated suites
