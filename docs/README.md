# Project Documentation Index

This directory contains project documentation for the RM690B0 refactor to the standard CircuitPython stack (`displayio + qspibus + sdioio`) on Waveshare ESP32-S3 AMOLED 2.41.

Status summary:

- Phases 1-4: complete and hardware-validated
- Phase 5: optional optimization implemented and benchmarked
- Phase 6: documentation package complete

## Core Release Documents

- [`TESTING_GUIDE.md`](TESTING_GUIDE.md)
  - Full hardware test procedure (Phase 1-4), optional benchmarks, troubleshooting, and reporting templates.
- [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md)
  - API migration from legacy standalone `rm690b0` to `displayio + qspibus`.
- [`../../circuitpython-rm690b0/CHANGES.md`](../../circuitpython-rm690b0/CHANGES.md)
  - Release changelog for v2.0, including breaking changes and architecture notes.

## Technical References

- [`TECHNICAL_NOTES.md`](TECHNICAL_NOTES.md)
  - Consolidated technical notes, benchmark context, and troubleshooting.
- [`CODE_REMOVAL_AUDIT.md`](CODE_REMOVAL_AUDIT.md)
  - Audit of standalone module removal and retained components.
- [`FOURWIRE_ANALYSIS.md`](FOURWIRE_ANALYSIS.md)
  - Reference analysis used while implementing `qspibus`.
- [`DISPLAYIO_PANEL_ANALYSIS.md`](DISPLAYIO_PANEL_ANALYSIS.md)
  - RM690B0 panel integration notes for displayio.

## Planning and Process Docs

- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
  - Full multi-phase execution plan.
- [`IMPLEMENTATION_PLAN_SUMMARY.md`](IMPLEMENTATION_PLAN_SUMMARY.md)
  - Short plan summary for rapid onboarding.
- [`project_status_summary.md`](project_status_summary.md)
  - Current project status and readiness notes.
- [`CIRCUITPYTHON_UPSTREAM_FEEDBACK.md`](CIRCUITPYTHON_UPSTREAM_FEEDBACK.md)
  - Upstream feedback context and design constraints.

## Legacy Documentation (Deprecated)

- [`RM690B0_DRIVER.md`](RM690B0_DRIVER.md)
  - Legacy standalone API documentation. Kept for reference.
- [`RM690B0_LVGL.md`](RM690B0_LVGL.md)
  - LVGL integration documentation from pre-v2 architecture workstream.

## Hardware Test Scripts

Test script directory:

- [`../examples/tests/`](../examples/tests/)

Required phase tests:

- [`../examples/tests/test_phase1_sdioio.py`](../examples/tests/test_phase1_sdioio.py)
- [`../examples/tests/test_phase2_qspibus.py`](../examples/tests/test_phase2_qspibus.py)
- [`../examples/tests/test_phase3_displayio.py`](../examples/tests/test_phase3_displayio.py)
- [`../examples/tests/test_phase4_integration.py`](../examples/tests/test_phase4_integration.py)

Optional benchmarks:

- [`../examples/tests/benchmark_phase1_sdioio_io.py`](../examples/tests/benchmark_phase1_sdioio_io.py)
- [`../examples/tests/benchmark_phase1_sdioio_freq_sweep.py`](../examples/tests/benchmark_phase1_sdioio_freq_sweep.py)
- [`../examples/tests/benchmark_phase5_displayio.py`](../examples/tests/benchmark_phase5_displayio.py)

## Quick Start

1. Read migration notes: [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md)
2. Validate build and hardware: [`TESTING_GUIDE.md`](TESTING_GUIDE.md)
3. Review release-level impact: [`../../circuitpython-rm690b0/CHANGES.md`](../../circuitpython-rm690b0/CHANGES.md)
4. Use deep technical context when needed: [`TECHNICAL_NOTES.md`](TECHNICAL_NOTES.md)

## Related Repositories

- CircuitPython fork root: [`../../circuitpython-rm690b0/`](../../circuitpython-rm690b0/)
- Board support root: [`../`](../)

Last updated: `2026-02-11`
