# Consolidated Benchmark Suites

Primary entrypoints:
- each `benchmark_*.py` is fully standalone and can be copied directly as `code.py`
- `benchmark_quick.py` - fastest smoke check, only core comparable scenarios
- `benchmark_standard.py` - recommended default for routine comparisons
- `benchmark_full.py` - longest run for cross-backend comparison

Human-readable results are printed to serial and also written as:
- `/displayio_<profile>.txt`
- `/displayio_<profile>.json`

Groups reported by this directory:
- `DISPLAYIO`

Core comparable scenarios used across firmware families:
- `full_fill`
- `partial_rect`
- `scene_mixed`
- `text_menu`
- `text_large`
- `blit_band`
- `sprite_opaque`
- `sprite_transparent`

Notes:
- There is no `FB-SINGLE/FB-DOUBLE` split here.
- This suite uses native displayio primitives, TileGrid/Bitmap, Label and dirty-region refresh. It does not use `DisplayCompat`.
- Older scripts remain available for lower-level or narrower diagnostics.

Host-side comparison:
- `python ../examples/benchmark_compare.py fb=../benchmark_gfx/fb_standard.json dl=../benchmark_gfx_displaylist/dl_standard.json dio=displayio_standard.json`
- input files are the `*.json` outputs produced by the consolidated suites
