# Project Documentation

This directory contains the core documentation for the RM690B0 display driver and its LVGL integration on the Waveshare ESP32-S3 Touch AMOLED 2.41 board.

- `RM690B0_DRIVER.md`  
  Complete API reference for the standalone `rm690b0` display driver: initialization, graphics primitives (lines, circles, rectangles), native text rendering with 7 built-in fonts, image support (BMP/JPEG), color system, performance optimization, and practical examples.

- `RM690B0_LVGL.md`  
  Integration guide for `rm690b0_lvgl` with LVGL 8.x: initialization, architecture, Python widget API (Widget, Label, Button), usage examples, and implementation notes.

- `TECHNICAL_NOTES.md`  
  Detailed technical notes about the `rm690b0` driver: rendering architecture, performance, DMA, storage (flash/PSRAM/SD), touch integration (FT6336U), native text rendering with built-in bitmap fonts, and common issues and solutions.

- `project_status_summary.md`  
  Project status summary: readiness level, key achievements, limitations (including known LVGL+touch stability issue under GC pressure), and planned next steps.

- `project_summary.yaml`  
  Machine-readable description of board configuration, key components (display, touch, I2C devices), and project state synthesis – used by automation tools and technical reviews.

- `snapshot.txt`  
  Compact summary of project configuration, functionality, and status in key=value format – contains information about native text API, 7 built-in bitmap fonts, and TTF conversion tools.