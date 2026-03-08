# Consolidated Benchmark Suites

Primary entrypoints:
- each `benchmark_*.py` is fully standalone and can be copied directly as `code.py`
- `benchmark_quick.py` - fastest smoke check, only core comparable scenarios
- `benchmark_standard.py` - recommended default for routine comparisons
- `benchmark_full.py` - longest run, adds retained/backend-specific scenarios

Human-readable results are printed to serial and also written as:
- `/dl_<profile>.txt`
- `/dl_<profile>.json`

Groups reported by this directory:
- `DL` - display-list backend, single consolidated group

Notes:
- `BUFFER_DOUBLE` is intentionally not part of the consolidated DL suite.
- Retained scenarios run with `copy=True` because that is the realistic DL workload.

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
- `benchmark_dl_profile.py` - long-run DL telemetry profiler
- `benchmark_glyph_atlas.py` - glyph atlas-specific performance and hit/miss study
- `benchmark_simple_flush.py` - low-level flush/present checks
- `benchmark_animation_*.py` - targeted sprite animation experiments

Host-side comparison:
- `python ../examples/benchmark_compare.py fb=../benchmark_gfx/fb_standard.json dl=dl_standard.json dio=../benchmark_gfx_displayio/displayio_standard.json`
- input files are the `*.json` outputs produced by the consolidated suites
