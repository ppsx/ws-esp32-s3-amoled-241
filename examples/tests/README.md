# Hardware Tests - Waveshare ESP32-S3 AMOLED 2.41

## Overview

This directory contains hardware tests for SD card migration to `sdioio`.

**New test location:** `examples/tests/`

## Available Scripts

```text
examples/tests/
├── README.md
├── adafruit_rm690b0.py
├── test_phase1_sdioio.py
├── test_phase2_qspibus.py
├── test_phase3_displayio.py
├── test_phase4_integration.py
├── benchmark_phase1_sdioio_io.py
├── benchmark_phase1_sdioio_freq_sweep.py
└── benchmark_phase5_displayio.py
```

## Preparation

1. Build firmware:
```bash
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh build
```

2. Flash firmware:
```bash
./build_waveshare.sh flash
```

3. Check CIRCUITPY mounting:
```bash
ls /media/CIRCUITPY
```

## Running Tests

### 1) SD Functional Test (`test_phase1_sdioio.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase1_sdioio.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# Press RST button on board
```

### 1b) QSPIBus Test (`test_phase2_qspibus.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase2_qspibus.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# Press RST button on board
```

### 2) I/O Benchmark for Single Frequency (`benchmark_phase1_sdioio_io.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/benchmark_phase1_sdioio_io.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# Press RST button on board
```

### 3) Frequency Sweep Benchmark (`benchmark_phase1_sdioio_freq_sweep.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/benchmark_phase1_sdioio_freq_sweep.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# Press RST button on board
```

### 4) displayio + RM690B0 Test (`test_phase3_displayio.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase3_displayio.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# Press RST button on board
```

Expected result:

- Screen: red -> green -> blue -> white rectangle on black background.
- Cleanup: screen returns to black, `displayio.release_displays()` and `qspi_bus.deinit()` pass successfully.
- Script can be run again without hard reset of the board.

## Optional Helper Script

You can use the helper from the root of `circuitpython-rm690b0` repo:

```bash
./run_test.sh ../ws-esp32-s3-amoled-241/examples/tests/test_phase1_sdioio.py
```

If you keep a local helper, set:

```bash
TEST_FILE="examples/tests/$1"
```

## Notes

- Tests require physical hardware.
- Preferred method for read performance: `readinto()`.
- For SD card benchmarks, board reset before each run gives more repeatable results.
- For Phase 3 test, check colored screens and rectangle, so you need to watch the display.
- In Phase 3, proper cleanup is part of the test (required for repeatable rerun without reset).

### 5) v2.0 Stack Integration Test (`test_phase4_integration.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase4_integration.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# Press RST button on board
```

Expected result:

- Serial: `ALL INTEGRATION TESTS PASSED`
- Tests simultaneously: `sdioio` + `qspibus` + `displayio`
- Screen: red -> green -> blue, then scene with three rectangles

### 6) displayio Benchmark (`benchmark_phase5_displayio.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/benchmark_phase5_displayio.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# Press RST button on board
```

Expected result:

- Serial: timing table for `full screen`, `partial update`, `multi-element scene`
- Benchmark serves as baseline/comparison before and after Phase 5 optimizations
