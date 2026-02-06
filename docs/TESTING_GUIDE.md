# Testing Guide - CircuitPython RM690B0 v2.0

- Version: `2.0.0`
- Board: `waveshare_esp32_s3_amoled_241`
- Last updated: `2026-02-06`
- Plan reference: [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) (Phase 6)

## 1. Overview

This guide describes how to validate the refactored RM690B0 stack based on:

- `sdioio`
- `qspibus`
- `displayio` + `BusDisplay`
- RM690B0 panel init sequence used in phase test scripts

Goal of this guide:

1. Confirm hardware correctness for phases 1-4.
2. Provide reproducible run order and expected outputs.
3. Provide troubleshooting for common hardware and API issues.
4. Provide a consistent report format for success and failure.

Scope:

- Required tests: `test_phase1_sdioio.py` to `test_phase4_integration.py`
- Optional benchmarks: Phase 1 SD benchmarks + Phase 5 display benchmark
- This guide is for real hardware, not host-only simulation.

Test suite location:

- `../examples/tests/`

Main scripts:

- `../examples/tests/test_phase1_sdioio.py`
- `../examples/tests/test_phase2_qspibus.py`
- `../examples/tests/test_phase3_displayio.py`
- `../examples/tests/test_phase4_integration.py`

Optional scripts:

- `../examples/tests/benchmark_phase1_sdioio_io.py`
- `../examples/tests/benchmark_phase1_sdioio_freq_sweep.py`
- `../examples/tests/benchmark_phase5_displayio.py`

## 2. Requirements

### 2.1 Hardware requirements

- Waveshare ESP32-S3 Touch AMOLED 2.41
- USB data cable (stable)
- FAT32 SD card (recommended for Phase 1 and Phase 4)
- Host PC (Linux/macOS/Windows)

Recommended:

- Fresh board reset before each phase test
- Stable USB port (avoid weak hubs)
- SD card with known good health

### 2.2 Software requirements

- Built firmware from `repos/circuitpython-rm690b0`
- Serial monitor workflow via `./build_waveshare.sh monitor`
- Access to CIRCUITPY mount point

Paths used in commands below:

- CircuitPython repo:
  - `/home/pps/Downloads/__ai__/repos/circuitpython-rm690b0`
- Board support/docs repo:
  - `/home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241`

### 2.3 Required module availability

The firmware should include:

- `qspibus`
- `sdioio`
- `displayio`
- `busdisplay`

The standalone module should be removed:

- `rm690b0` should not import in v2.0

## 3. Preparation

### 3.1 Build and flash firmware

Run from CircuitPython repo:

```bash
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh rebuild
./build_waveshare.sh flash
```

Expected:

- build finishes with exit code 0
- board reboots into new firmware
- CIRCUITPY appears as mount point

### 3.2 Verify board connection and monitor

```bash
ls /media/CIRCUITPY
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
```

If mount point differs on your system, adapt commands accordingly.

### 3.3 Module sanity check

Copy this snippet as `code.py` once before phase tests:

```python
import sys
import board

print("CircuitPython:", sys.version)
print("Board:", board.board_id)

try:
    import qspibus
    print("[OK] qspibus available")
except ImportError:
    print("[FAIL] qspibus missing")

try:
    import sdioio
    print("[OK] sdioio available")
except ImportError:
    print("[FAIL] sdioio missing")

try:
    import rm690b0
    print("[FAIL] rm690b0 unexpectedly present")
except ImportError:
    print("[OK] rm690b0 removed as expected")
```

Pass criteria:

- `qspibus` import OK
- `sdioio` import OK
- `rm690b0` import fails

### 3.4 General run pattern

For each test phase:

1. Copy selected script to CIRCUITPY as `code.py`.
2. Open serial monitor.
3. Press board reset.
4. Capture full serial output.
5. For display tests, observe screen output.

Copy example:

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase1_sdioio.py /media/CIRCUITPY/code.py
```

## 4. Hardware Tests (Required Order)

Run phases in order. Do not skip a failed phase.

---

## 4.1 Phase 1 - `sdioio` SD card validation

- Script: `../examples/tests/test_phase1_sdioio.py`

### Preparation

1. Insert SD card (FAT32).
2. Copy script to CIRCUITPY.
3. Open serial monitor.
4. Reset board.

### Run commands

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase1_sdioio.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
```

### Expected serial output

```text
==================================================
Testing sdioio with Waveshare ESP32-S3 AMOLED 2.41
==================================================

[1/5] Creating SDCard object...
    ✓ SDCard object created

[2/5] Mounting SD card...
    ✓ SD card mounted to /sd

[3/5] Listing files...
    Files on SD card (X items): [...]
    ✓ Directory listing works

[4/5] Write test...
    ✓ Write test passed

[5/5] Read test...
    ✓ Read test passed

[Cleanup] Removing test file...
    ✓ Cleanup complete

==================================================
✓ ALL TESTS PASSED - sdioio works!
==================================================
```

### Expected screen output

- No specific display validation in this phase.

### Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `No SD card found` or mount fails | card missing/unreadable | reinsert card, test card, format FAT32 |
| write/read error | filesystem issue | reformat FAT32 and rerun |
| `GPIO conflict` | wrong pin ownership | verify no other script currently holds SD pins |
| test hangs at mount | unstable power/USB | use stable USB port, avoid hub |

### PASS/FAIL criteria

PASS:

- all 5 steps complete
- cleanup succeeds

FAIL:

- any exception
- mount/read/write failure

---

## 4.2 Phase 2 - `qspibus` module validation

- Script: `../examples/tests/test_phase2_qspibus.py`

### Preparation

1. Copy script to CIRCUITPY.
2. Ensure no previous display owner remains (`displayio.release_displays()` is in script).
3. Reset board.

### Run commands

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase2_qspibus.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
```

### Expected serial output

```text
==================================================
Testing QSPIBus Module
==================================================
Using pins: clock=..., data0=..., data1=..., data2=..., data3=..., cs=..., reset=...

[1/3] Creating QSPIBus...
    [OK] QSPIBus created successfully

[2/3] Testing deinitialization...
    [OK] QSPIBus deinitialized

[3/3] Testing context manager...
    [OK] Context manager works

==================================================
[OK] ALL TESTS PASSED
==================================================
```

### Expected screen output

- No mandatory visual changes in this phase.

### Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `module 'board' has no attribute ...` | pin alias mismatch | script uses fallback aliases, verify `pins.c` exports |
| `GPIO ... in use` | bus owner not released | power cycle or ensure `displayio.release_displays()` called first |
| deinit causes reset | unstable cleanup sequence | verify latest firmware with deinit fixes from Phase 3/4 work |
| bus creation fails | invalid frequency/timing | try lower frequency and retest |

### PASS/FAIL criteria

PASS:

- create/deinit/context-manager checks pass

FAIL:

- any exception during bus lifecycle

---

## 4.3 Phase 3 - RM690B0 with `displayio`

- Script: `../examples/tests/test_phase3_displayio.py`
- This phase requires screen observation.

### Preparation

1. Copy script to CIRCUITPY.
2. Open monitor.
3. Reset board.
4. Keep screen visible for color cycle.

### Run commands

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase3_displayio.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
```

### Expected serial output

```text
==========================================================
Testing RM690B0 with displayio (Phase 3)
==========================================================

[1/5] Creating QSPI bus...
    [OK] QSPI bus created

[2/5] Creating RM690B0 panel...
    [OK] RM690B0 panel initialized

[3/5] Color cycle...
    -> Red
    -> Green
    -> Blue
    [OK] RGB colors displayed

[4/5] Rectangle test...
    [OK] Rectangle displayed

[5/5] Cleanup...
    [OK] Screen cleared to black
    [OK] displayio.release_displays()
    [OK] QSPI bus deinitialized

==========================================================
[OK] ALL TESTS PASSED
Screen expectation: red, green, blue, white rectangle on black
==========================================================
```

### Expected screen output

Sequence:

1. Red full-screen fill
2. Green full-screen fill
3. Blue full-screen fill
4. White rectangle on black background
5. Cleanup black screen

### Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| serial passes but screen stays black | panel init/transport mismatch | verify latest RM690B0 init sequence and qspibus transport build |
| hangs on first color | refresh path stalled | retest after hard reset, verify firmware includes latest qspibus changes |
| wrong colors (BGR/RGB swapped) | color order mismatch | verify MADCTL sequence in panel init |
| rerun causes board reset | incomplete cleanup | keep cleanup order: black frame -> `release_displays()` -> `bus.deinit()` |
| `.show(x) removed` error | old display API usage | use `display.root_group = group` |

### PASS/FAIL criteria

PASS:

- serial reports success
- screen visibly shows RGB sequence and rectangle
- cleanup succeeds without forced reboot

FAIL:

- black screen without expected transitions
- wrong colors/geometry
- cleanup triggers unstable reset loop

---

## 4.4 Phase 4 - Full stack integration

- Script: `../examples/tests/test_phase4_integration.py`
- Validates `sdioio + qspibus + displayio` in one run.

### Preparation

1. Insert SD card.
2. Copy integration script.
3. Open monitor.
4. Reset board.

### Run commands

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase4_integration.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
```

### Expected serial output

```text
==================================================
Full Integration Test - v2.0
==================================================

[1/4] Testing sdioio (SD card)...
    [OK] SD card works (... entries)

[2/4] Testing QSPIBus...
    [OK] QSPI bus works

[3/4] Testing displayio (RM690B0)...
    -> Red
    -> Green
    -> Blue
    [OK] Display shows colors

[4/4] Testing complex scene...
    [OK] Multi-element rendering works

==================================================
[OK] ALL INTEGRATION TESTS PASSED!
v2.0 stack is functional: sdioio + qspibus + displayio
==================================================

[Cleanup]
  [OK] Screen cleared
  [OK] displayio released
  [OK] QSPI bus deinitialized
  [OK] SD unmounted
```

### Expected screen output

1. Red, green, blue sequence
2. Black background with multiple colored rectangles
3. Cleanup back to black

### Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `module 'os' has no attribute 'listdir'` | wrong module import shadowing | ensure script imports built-in `os`, not replaced module |
| `module 'displayio' has no attribute 'Display'` | API mismatch in script | use panel object pattern used in current phase scripts |
| SD test fails, display part never runs | SD card issue | resolve Phase 1 first, then rerun integration |
| integration passes but cleanup unstable | deinit ordering | keep cleanup order used by script and retest |

### PASS/FAIL criteria

PASS:

- all four sections pass
- display visuals appear as expected
- cleanup completes

FAIL:

- any component fails (`sdioio`, `qspibus`, or display path)

## 5. Optional Tests and Benchmarks

Optional tests are recommended after all required phases pass.

---

## 5.1 SD benchmark (single frequency)

- Script: `../examples/tests/benchmark_phase1_sdioio_io.py`

Purpose:

- measure SD write/read throughput at selected frequency and chunk size

Run:

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/benchmark_phase1_sdioio_io.py /media/CIRCUITPY/code.py
```

Example observed result (4 MB, 20 MHz, 64 KB chunk):

- write: `222.09 KB/s`
- read alloc: `838.65 KB/s`
- readinto: `930.70 KB/s`

---

## 5.2 SD frequency sweep benchmark

- Script: `../examples/tests/benchmark_phase1_sdioio_freq_sweep.py`

Purpose:

- compare throughput across requested frequencies

Run:

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/benchmark_phase1_sdioio_freq_sweep.py /media/CIRCUITPY/code.py
```

Observed best read throughput:

- `readinto`: `~1.13 MB/s` at requested `40 MHz`

Notes:

- write throughput changed little across tested frequencies
- read throughput improved with higher frequency and `readinto`

---

## 5.3 Display benchmark (Phase 5)

- Script: `../examples/tests/benchmark_phase5_displayio.py`

Purpose:

- baseline display refresh timings for v2.0 and post-optimization checks

Run:

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/benchmark_phase5_displayio.py /media/CIRCUITPY/code.py
```

Observed baseline and optimized values:

| Metric | Baseline | Optimized |
|---|---:|---:|
| Full screen fill (600x450) | 360.499 ms | 341.250 ms |
| Partial update (100x100) | 62.584 ms | 52.916 ms |
| Multi-element scene | 59.700 ms | 51.500 ms |

Interpretation:

- full-screen improved but remains above `<100 ms` target
- partial and scene updates improved noticeably

## 6. Reporting Results

### 6.1 Success report template

Use this format when all required phases pass:

```markdown
## Test Success Report

- Date: YYYY-MM-DD
- Board: waveshare_esp32_s3_amoled_241
- Firmware build: [build id/date]
- Required phases: PASS (1/2/3/4)
- Optional benchmarks: [yes/no]

### Display validation
- RGB sequence visible: yes/no
- Rectangle/scene visible: yes/no
- Cleanup black screen visible: yes/no

### Notes
- [extra observations]
```

### 6.2 Failure report template

Use this format when any phase fails:

~~~markdown
## Test Failure Report

- Date: YYYY-MM-DD
- Board: waveshare_esp32_s3_amoled_241
- Firmware build: [build id/date]
- Failed phase: [1/2/3/4/optional]
- Script: [file path]

### Exact error
```text
[paste exact traceback or error line]
```

### Full serial output
```text
[paste complete serial log]
```

### Screen behavior
- expected: [what should happen]
- actual: [what was observed]

### Reproduction steps
1. [step]
2. [step]
3. [step]

### Additional context
- SD card model/capacity:
- USB cable/port details:
- whether hard reset/power cycle changes behavior:
~~~

### 6.3 What to attach

For failures, attach:

- exact script used
- complete monitor log
- short video or photos for display mismatch
- note if issue reproduces after power cycle
- note if issue reproduces after running another phase first

## 7. Final Checklist (Ready for PR)

Use this checklist before marking release docs as complete.

### 7.1 Build

- [ ] `./build_waveshare.sh build` returns success
- [ ] firmware image generated
- [ ] required modules available (`qspibus`, `sdioio`, `displayio`)

### 7.2 Required hardware tests

- [ ] `test_phase1_sdioio.py` PASS
- [ ] `test_phase2_qspibus.py` PASS
- [ ] `test_phase3_displayio.py` PASS
- [ ] `test_phase4_integration.py` PASS

### 7.3 Display behavior

- [ ] red/green/blue sequence visible
- [ ] white rectangle visible in Phase 3
- [ ] integration scene visible in Phase 4
- [ ] cleanup returns screen to black

### 7.4 Stability

- [ ] scripts can rerun without forced board reset
- [ ] deinit does not produce uncontrolled restart
- [ ] no persistent resource lock between phases

### 7.5 Documentation

- [ ] `CHANGES.md` exists and reflects current architecture
- [ ] `MIGRATION_GUIDE.md` updated and linked
- [ ] `TECHNICAL_NOTES.md` includes benchmark context
- [ ] this guide (`TESTING_GUIDE.md`) stays aligned with script output

## 8. Contacts and Escalation

If a blocker appears:

1. Open issue with full failure template.
2. Include exact firmware and script references.
3. Include hardware observation details for display-related failures.

Suggested channels:

- Project issue tracker
- Maintainer review thread for RM690B0 refactor
- CircuitPython discussion thread (if upstream-facing issue)

## 9. Cross References

- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
- [`IMPLEMENTATION_PLAN_SUMMARY.md`](IMPLEMENTATION_PLAN_SUMMARY.md)
- [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md)
- [`TECHNICAL_NOTES.md`](TECHNICAL_NOTES.md)
- [`CODE_REMOVAL_AUDIT.md`](CODE_REMOVAL_AUDIT.md)
- [`../README.md`](../README.md)

## 10. Revision Log

- `2026-02-06`: Initial Phase 6 release version of testing guide.
- `2026-02-06`: Added required phase outputs, troubleshooting, and report templates.
- `2026-02-06`: Added optional benchmark references with observed baseline metrics.
