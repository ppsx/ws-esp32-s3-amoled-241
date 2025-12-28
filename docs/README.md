# Project Documentation

This directory contains the core documentation for the RM690B0 display driver and its LVGL integration on the Waveshare ESP32-S3 Touch AMOLED 2.41 board.

## Documentation Files

### [`RM690B0_DRIVER.md`](RM690B0_DRIVER.md)
Complete API reference for the standalone `rm690b0` display driver: initialization, graphics primitives (pixel, line, circle, rectangle, fill operations), native text rendering with 7 built-in fonts (8×8 to 32×48), image support (BMP/JPEG with hardware acceleration), RGB565 color system, double-buffering, performance optimization, and practical examples including analog clock, progress bars, and image gallery.

### [`RM690B0_LVGL.md`](RM690B0_LVGL.md)
Integration guide for `rm690b0_lvgl` with LVGL 8.x: initialization sequence, touch input with automatic coordinate transformation, Python widget API (Widget, Label, Button), event system with callbacks, usage examples (counter app, multi-button controls, settings panels), complete widget reference for all implemented classes, and detailed troubleshooting including known GC/touch stability issue.

### [`TECHNICAL_NOTES.md`](TECHNICAL_NOTES.md)
Detailed technical notes about the `rm690b0` driver: rendering architecture (30-line DMA limit, framebuffer management), performance benchmarks, storage options (flash/PSRAM/SD card), touch-display integration (FT6336U coordinate mapping), native text rendering system (Section 11), TTF font conversion toolchain, DMA memory management, and comprehensive troubleshooting guide.

### [`project_status_summary.md`](project_status_summary.md)
Project status summary: Phase 5 complete (LVGL integration + native text), readiness assessment (`rm690b0` production-ready, `rm690b0_lvgl` beta due to GC/touch bug), key achievements, current limitations, and Phase 6 roadmap (documentation + 9-13 additional widgets).

### [`project_summary.yaml`](project_summary.yaml)
Machine-readable description of Waveshare ESP32-S3 Touch AMOLED 2.41 board: hardware configuration (GPIO pins, I2C devices), software components (rm690b0, rm690b0_lvgl modules), implementation status, and structured roadmap – designed for automation tools and technical reviews.

### [`snapshot.txt`](snapshot.txt)
Compact technical summary in key=value format: board configuration, module APIs, performance metrics, font system (7 built-in fonts + TTF converter), widget classes, known issues (especially GC/touch bug), practical usage rules, and current project status – optimized for quick reference and automated parsing.

## Quick Links

### Getting Started
- For display driver basics: See **Quick Start** section in [`RM690B0_DRIVER.md`](RM690B0_DRIVER.md#quick-start)
- For LVGL integration: See **Quick Start** section in [`RM690B0_LVGL.md`](RM690B0_LVGL.md#quick-start)
- For technical details: See [`TECHNICAL_NOTES.md`](TECHNICAL_NOTES.md)

### API Reference
- **Display Driver API**: [`RM690B0_DRIVER.md#python-api-reference`](RM690B0_DRIVER.md#python-api-reference)
- **LVGL Widget API**: [`RM690B0_LVGL.md#widget-classes`](RM690B0_LVGL.md#widget-classes)
- **Native Text API**: [`TECHNICAL_NOTES.md#text-api-reference`](TECHNICAL_NOTES.md#text-api-reference)

### Examples
- **Graphics Examples**: [`RM690B0_DRIVER.md#examples`](RM690B0_DRIVER.md#examples)
- **LVGL Examples**: [`RM690B0_LVGL.md#examples`](RM690B0_LVGL.md#examples)
- **Complete Scripts**: See [`../examples/`](../examples/) directory

### Troubleshooting
- **Display Issues**: [`RM690B0_DRIVER.md#troubleshooting`](RM690B0_DRIVER.md#troubleshooting)
- **LVGL Issues**: [`RM690B0_LVGL.md#troubleshooting`](RM690B0_LVGL.md#troubleshooting)
- **Technical Issues**: [`TECHNICAL_NOTES.md#common-issues--solutions`](TECHNICAL_NOTES.md#common-issues--solutions)

## Document Statistics

| Document | Lines | Topics Covered |
|----------|-------|----------------|
| `RM690B0_DRIVER.md` | 1,668 | Display driver API, graphics primitives, text rendering, images |
| `RM690B0_LVGL.md` | 3,234 | LVGL integration, Python widgets, event handling, examples |
| `TECHNICAL_NOTES.md` | 1,655 | Architecture, DMA, performance, touch integration, fonts |
| `project_status_summary.md` | 84 | Project status, roadmap, known issues |
| `project_summary.yaml` | 206 | Machine-readable project configuration |
| `snapshot.txt` | 35 | Compact reference in key=value format |

## Related Resources

- **Main Repository**: [`../README.md`](../README.md)
- **Example Scripts**: [`../examples/`](../examples/)
- **Font Tools**: [`../fonts/`](../fonts/)
- **Build Scripts**: [`../build/`](../build/)

---

Last Updated: 2025-01-04