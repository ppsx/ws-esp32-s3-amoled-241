# Hardware Tests - Waveshare ESP32-S3 AMOLED 2.41

## Przeglad

Ten katalog zawiera testy hardware dla migracji SD card na `sdioio`.

**Nowa lokalizacja testow:** `examples/tests/`

## Dostepne skrypty

```text
examples/tests/
├── README.md
├── test_phase1_sdioio.py
├── test_phase2_qspibus.py
├── benchmark_phase1_sdioio_io.py
└── benchmark_phase1_sdioio_freq_sweep.py
```

## Przygotowanie

1. Zbuduj firmware:
```bash
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh build
```

2. Flash firmware:
```bash
./build_waveshare.sh flash
```

3. Sprawdz montowanie CIRCUITPY:
```bash
ls /media/CIRCUITPY
```

## Uruchamianie

### 1) Test funkcjonalny SD (`test_phase1_sdioio.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase1_sdioio.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# reset RST na boardzie
```

### 1b) Test QSPIBus (`test_phase2_qspibus.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/test_phase2_qspibus.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# reset RST na boardzie
```

### 2) Benchmark I/O dla jednej czestotliwosci (`benchmark_phase1_sdioio_io.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/benchmark_phase1_sdioio_io.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# reset RST na boardzie
```

### 3) Benchmark sweep czestotliwosci (`benchmark_phase1_sdioio_freq_sweep.py`)

```bash
cd /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241
cp examples/tests/benchmark_phase1_sdioio_freq_sweep.py /media/CIRCUITPY/code.py
cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
./build_waveshare.sh monitor
# reset RST na boardzie
```

## Optional helper script

Mozesz uzyc helpera z roota repo `circuitpython-rm690b0`:

```bash
./run_test.sh ../ws-esp32-s3-amoled-241/examples/tests/test_phase1_sdioio.py
```

Jesli trzymasz lokalnego helpera, ustaw:

```bash
TEST_FILE="examples/tests/$1"
```

## Uwagi

- Testy wymagaja fizycznego hardware.
- Preferowany odczyt do wydajnosci: `readinto()`.
- Dla benchmarkow SD card reset boarda przed kazdym przebiegiem daje bardziej powtarzalne wyniki.
