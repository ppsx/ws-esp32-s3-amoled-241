# RM690B0 Driver — Project Status

> **⚠️ ARCHITECTURE NOTE (v2.0):**
> Standalone `rm690b0` module was removed in Phase 4.
> Current path is `qspibus + displayio` with panel helper driver.
> See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) and [CODE_REMOVAL_AUDIT.md](CODE_REMOVAL_AUDIT.md).

## Overall Readiness

- **Phase 2 (QSPIBus) Complete and Hardware-Validated**: `qspibus` module is integrated in firmware and passed hardware tests (construct/deinit/context-manager) on 2026-02-06.
- **Phase 3 (DisplayIO Integration) Complete**: panel path renders correctly on hardware (color cycle + geometry tests) with stable cleanup/deinit sequence.
- **Phase 4 (Standalone Removal) Complete**: legacy `rm690b0` module and built-in font payload were removed from firmware build; vendor panel/JPEG files retained for current and future integration.
- **Phase 5 (LVGL) Status**: feature work progressed, but stability under GC pressure still requires validation.
- **Phase 6 (Final Documentation) Complete**: `CHANGES.md` and `TESTING_GUIDE.md` are published and linked from the documentation index.
- Driver stack now targets maintainable upstream architecture first; performance tuning remains a follow-up track.
- LVGL rendering clean at 100+ FPS with zero tearing in typical usage; touch input is functional with coordinate transformation, but frequent `gc.collect()` or large allocations can cause loss of responsiveness
- **AMOLED Optimized**: LVGL Dark Theme background is now pure black (0x000000) for maximum power efficiency and contrast.
- **Dynamic Themes**: Added `set_theme_color()` API for switching between Light and Dark modes in real-time.
- Native text API provides lightweight, fast text rendering with 7 embedded fonts (8×8 to 32×48 pixels), independent from LVGL, with TTF-to-bitmap conversion toolchain
- Alignment corrections, dynamic span allocation, and property-only APIs eliminate earlier crashes, stack pressure, and duplicate entry points
- Validation passes confirm expected frame timings (~25 ms full-screen fill, ~14 ms 10-circle burst) on the Waveshare ESP32-S3 AMOLED board; long‑running stability with GC and LVGL+touch is an open issue

## Delivered Outcomes

### Phase 1-4: Migration to DisplayIO Stack (COMPLETE)

- Phase 2 bus layer delivered: new `qspibus` module (analog to `fourwire`) for QSPI display communication on ESP32-S3
- Phase 2 hardware test status: PASS via `examples/tests/test_phase2_qspibus.py` (create/deinit/context manager)
- Phase 4 cleanup completed: standalone `rm690b0` module removed from build, with retained vendor files only (`esp_lcd_rm690b0.*`, `esp_jpeg/*`)
- Rendering core refactored around framebuffer batching, lazy allocations, and clip helpers verified in `CODE_VERIFICATION_COMPLETE.md`
- Image support refactored: Dedicated `image_converter` module removed in favor of `jpegio` with hardware acceleration and optimized C-level `convert_bmp` for 24-bit bitmap loading. Both paths now support direct RGB565 byte-swapped output for zero-copy DMA.
- Redundant RAW conversion function was removed to cut a 56 ms overhead.
- **Conditional double-buffering** (`#6`): `RM690B0(buffer_mode=)` constructor kwarg selects `BUFFER_SINGLE` (one framebuffer, 540 KB, dirty-tracked flush) or `BUFFER_DOUBLE` (two framebuffers, 1080 KB, tear-free swap, default). Module constants `rm690b0.BUFFER_SINGLE` / `rm690b0.BUFFER_DOUBLE` exposed. Single-buffer `swap_buffers()` path now uses dirty tracking instead of unconditional full-screen flush. Verified on hardware: ~512 KB savings in BUFFER_SINGLE mode (`test_gfx/test_buffer_mode.py`).
- Double-buffering with `swap_buffers()` API enables flicker-free updates and smooth animations
- Native text rendering API with 7 built-in bitmap fonts (8×8, 16×16, 16×24, 24×24, 24×32, 32×32, 32×48 pixels)
- Text rendering features: `set_font(id)` for font selection, `text(x,y,str,color,bg)` for rendering, transparent or solid backgrounds, UTF-8 support, ASCII 0x20-0x7E (95 chars)
- TTF-to-bitmap conversion toolchain: `ttf_to_rm690b0.py` (457 lines) converts any TrueType font, `test_converted_font.py` (377 lines) validates/previews fonts
- Total font size: ~538 KB in flash for all 7 fonts; rendering performance: 0.3-7.7 ms for "Hello World" (10-500× faster than DisplayIO)
- Unified benchmarking and diagnostics scripts consolidate prior tooling, ship quick/diagnostic/memory-efficient modes, and document runbooks in the README and benchmark guides.
- JPEG support leverages `jpegio` and ESP-IDF's hardware-accelerated `esp_jpeg` decoder for fast loads (10-50x faster) directly to swap-ready buffers.
- All pin definitions properly configured through board config files (`mpconfigboard.h`) with no hardcoded GPIO numbers in driver code
- Streaming JPEG path now writes decoded blocks directly into the framebuffer, eliminating the previous ~540 KB PSRAM allocation and making image blits resilient to memory fragmentation.
- `examples/benchmark_simple_flush.py` benchmarks both buffering modes plus partial-width/full-width rectangles and circle paths, guarding the new fill/circle optimizations against regressions.

### Phase 5: LVGL Integration (FUNCTIONALLY COMPLETE, STABILITY OPEN)

- **LVGL Library**: v8.x compiled and integrated into CircuitPython firmware
- **Display Driver**: Flush callback implemented using existing RM690B0 DMA paths, rendering at 100+ FPS with zero artifacts in standard scenarios
- **Touch Input**: FT6336U driver integrated with automatic portrait→landscape coordinate transformation; known issue: frequent `gc.collect()` and large heap activity (e.g. TTF font loading) can break touch responsiveness
- **Python Widget API**: CircuitPython-native widget classes (Widget, Label, Button) with property support
- **Event System**: Python callbacks for button clicks and widget interactions working in normal operation
- **Memory Architecture**: ~72 KB PSRAM for LVGL display buffers (2×30-row), ~150-600 bytes per widget
- **Interactive GUIs**: Counter app, multi-button controls, and settings panels tested on hardware
- **Build System**: Widget files (Widget.c, Label.c, Button.c) integrated into build system
- **Property System**: MP_TYPE_FLAG_HAS_SPECIAL_ACCESSORS enables read/write properties on all widgets
- **Inheritance**: Label and Button inherit Widget properties (x, y, width, height)

### Documentation

- Documentation sweep replaced scattered notes with focused guides (e.g. autosplit, double-buffering, image pipeline, board configuration)
- **New**: Consolidated all LVGL documentation into comprehensive `RM690B0_LVGL.md` guide
- **New**: Updated TECHNICAL_NOTES.md Section 11 with complete native text rendering documentation (architecture, API, font format, TTF conversion toolchain)
- **New**: Font conversion documentation: `TTF_CONVERTER_README.md`, `QUICK_START_TTF.md`, `TTF_CONVERTER_SUMMARY.md` in `fonts/` directory
- Removed obsolete stub notices and outdated LVGL docs
- Synced final status briefs for downstream agents including updated `snapshot.txt` with native text API details

## Quality & Release Confidence

- Compilation issues (e.g. stray XML fragment) resolved; builds succeed without warnings after enforcing safe pointer usage and const correctness.
- Memory pressure regressions uncovered during stress tests were partially addressed by reordering allocations and surfacing PSRAM telemetry; a **known critical issue remains** where LVGL + touch can become unresponsive under heavy GC pressure or repeated `gc.collect()` calls.
- Callback-only refresh experiment was reverted after benchmarks exposed 50–5000 % slowdowns; delay-based flow retained for predictable performance.
- Current recommendation: treat LVGL integration as **beta** on this board, avoid explicit `gc.collect()` in the main UI loop, and minimize large heap allocations during interactive use (e.g. load TTF fonts early, once).

## Confirmed Constraints & Decisions

- 30-line DMA ceiling on the RM690B0/ESP32-S3 path is hard hardware limit; attempts at 60+ line chunks fail and are intentionally avoided.
- SD card pipelines use standard `sdioio` (1-bit mode) with 40 MHz clocking and VFS block-device mounting. Custom `espsdcard`/`sdcardio` implementations removed in favor of CircuitPython standard (Feb 2026).
- Image format support limited to BMP and JPEG only; PNG was intentionally not implemented due to high PSRAM memory requirements. BMP acceleration and JPEG performance optimization remain potential enhancement targets.
- Board-specific configuration (pins, timing, offsets) fully externalized to `mpconfigboard.h` files for easy porting to new hardware.

## Remaining Opportunities

### Phase 6: Final Documentation (COMPLETE)

- Added `../../circuitpython-rm690b0/CHANGES.md` with v2.0 changelog, breaking changes, migration links, and performance context.
- Added `TESTING_GUIDE.md` with complete hardware validation flow for Phase 1-4 plus optional benchmarks.
- Updated documentation index links and phase status references for release readiness.

### Next Track: Stability & Widget Expansion

- Document known LVGL+GC touch issue with clear workarounds and constraints
- Expand widget library: add Slider, Checkbox, Switch, Arc, Bar, Image, Textarea, Dropdown, Roller
- Build widget gallery examples for regression coverage

### Performance & Testing

- Create comprehensive test suite for BMP and JPEG image conversion (different bit depths, orientations, compression levels)
- Tune the JPEG (`esp_jpeg`) and BMP conversion pipelines further (profile caching strategies, DMA-assisted copies) to push frame prep below 200 ms
- Add targeted stress tests for LVGL + touch under GC pressure (large allocations, explicit `gc.collect()` in loops) and capture failure modes
- Revisit asynchronous flush strategies only if FreeRTOS semaphore costs can be amortised

### Future Enhancements

- Board auto-initialization: `board.DISPLAY`, `board.LVGL`, `board.TOUCH` objects (optional convenience feature)
- Power management: Sleep modes, auto-sleep, power consumption optimization
- Additional specialized widgets and bindings:
  - LVGL: Calendar widget, Bitmap-style image widget (bindings for existing LVGL types)
  - Native RM690B0 driver: simple text rendering API with a small set of built-in fonts for common UI/debug text

## Document Quick Reference

- `docs/project_summary.yaml`: machine-readable board snapshot for automation pipelines
- `docs/project_status_summary.md`: executive status (this file) summarizing readiness, risks, and next actions
- `docs/RM690B0_LVGL.md`: Comprehensive LVGL integration guide with Python API reference and examples
- `docs/TECHNICAL_NOTES.md`: deep technical reference covering RM690B0 driver, touch integration, storage and performance
