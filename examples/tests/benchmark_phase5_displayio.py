"""
Benchmark Phase 5: displayio performance on RM690B0 over qspibus.

INSTRUKCJA:
1. Flash firmware:
     cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
     ./build_waveshare.sh flash
2. Copy benchmark:
     cp /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241/examples/tests/benchmark_phase5_displayio.py /media/CIRCUITPY/code.py
3. Monitor:
     cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
     ./build_waveshare.sh monitor

OUTPUT:
  - Full screen fill (600x450)
  - Partial update (100x100)
  - Multi-element scene
"""

import time

import board
import displayio
import qspibus
from busdisplay import BusDisplay


# Command format expected by busdisplay:
# [cmd][num_args | delay_flag][args...][delay_ms if delay_flag]
_INIT_SEQUENCE = (
    b"\xFE\x01\x20"
    b"\x26\x01\x0A"
    b"\x24\x01\x80"
    b"\xFE\x01\x13"
    b"\xEB\x01\x0E"
    b"\xFE\x01\x00"
    b"\x3A\x01\x55"
    b"\xC2\x81\x00\x0A"
    b"\x35\x00"
    b"\x51\x81\x00\x0A"
    b"\x11\x80\x50"
    b"\x2A\x04\x00\x10\x01\xD1"
    b"\x2B\x04\x00\x00\x02\x57"
    b"\x29\x80\x0A"
    b"\x36\x81\x30\x0A"
    b"\x51\x01\xFF"
)


class RM690B0(BusDisplay):
    def __init__(
        self,
        bus,
        *,
        width=600,
        height=450,
        colstart=0,
        rowstart=16,
        rotation=0,
        **kwargs,
    ):
        kwargs.setdefault("auto_refresh", False)
        super().__init__(
            bus,
            _INIT_SEQUENCE,
            width=width,
            height=height,
            colstart=colstart,
            rowstart=rowstart,
            rotation=rotation,
            color_depth=16,
            **kwargs,
        )


def _first_pin(*names):
    for name in names:
        if hasattr(board, name):
            return getattr(board, name), name
    raise AttributeError("Missing board pin alias: " + ", ".join(names))


def _build_qspi_bus():
    clock, clock_name = _first_pin("LCD_CLK", "QSPI_CLK", "DISPLAY_SCK")
    data0, data0_name = _first_pin("LCD_D0", "QSPI_D0", "DISPLAY_D0")
    data1, data1_name = _first_pin("LCD_D1", "QSPI_D1", "DISPLAY_D1")
    data2, data2_name = _first_pin("LCD_D2", "QSPI_D2", "DISPLAY_D2")
    data3, data3_name = _first_pin("LCD_D3", "QSPI_D3", "DISPLAY_D3")
    cs, cs_name = _first_pin("LCD_CS", "QSPI_CS", "DISPLAY_CS")
    reset, reset_name = _first_pin("LCD_RESET", "AMOLED_RESET", "DISPLAY_RST")

    print(
        "Using pins: "
        f"clock={clock_name}, data0={data0_name}, data1={data1_name}, "
        f"data2={data2_name}, data3={data3_name}, cs={cs_name}, reset={reset_name}"
    )

    return qspibus.QSPIBus(
        clock=clock,
        data0=data0,
        data1=data1,
        data2=data2,
        data3=data3,
        cs=cs,
        reset=reset,
        frequency=40_000_000,
    )


def _average_ms(samples):
    return (sum(samples) / len(samples)) * 1000.0


def _bench_full_screen(display, iterations=8):
    bitmap = displayio.Bitmap(600, 450, 1)
    palette = displayio.Palette(1)
    tile = displayio.TileGrid(bitmap, pixel_shader=palette)
    group = displayio.Group()
    group.append(tile)
    display.root_group = group

    samples = []
    for i in range(iterations):
        palette[0] = 0xFF0000 if (i & 1) == 0 else 0x0010FF
        start = time.monotonic()
        display.refresh()
        samples.append(time.monotonic() - start)
    return _average_ms(samples)


def _bench_partial_update(display, iterations=12):
    bg = displayio.Bitmap(600, 450, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0x000000

    sprite = displayio.Bitmap(100, 100, 1)
    sprite_palette = displayio.Palette(1)
    sprite_palette[0] = 0x00FF00
    sprite_tile = displayio.TileGrid(sprite, pixel_shader=sprite_palette, x=20, y=20)

    group = displayio.Group()
    group.append(displayio.TileGrid(bg, pixel_shader=bg_palette))
    group.append(sprite_tile)
    display.root_group = group

    positions = (
        (20, 20),
        (120, 20),
        (220, 20),
        (320, 20),
        (420, 20),
        (420, 160),
        (320, 260),
        (220, 260),
        (120, 260),
        (20, 260),
        (20, 140),
        (220, 140),
    )

    samples = []
    for i in range(iterations):
        x, y = positions[i % len(positions)]
        sprite_tile.x = x
        sprite_tile.y = y
        start = time.monotonic()
        display.refresh()
        samples.append(time.monotonic() - start)
    return _average_ms(samples)


def _bench_multi_element(display, iterations=10):
    group = displayio.Group()

    bg = displayio.Bitmap(600, 450, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0x050505
    group.append(displayio.TileGrid(bg, pixel_shader=bg_palette))

    for color, x, y, w, h in (
        (0xFF0000, 24, 24, 140, 80),
        (0x00FF00, 220, 90, 160, 120),
        (0x0000FF, 420, 260, 140, 120),
        (0xFFFF00, 100, 280, 120, 100),
    ):
        bmp = displayio.Bitmap(w, h, 1)
        pal = displayio.Palette(1)
        pal[0] = color
        group.append(displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y))

    moving = displayio.Bitmap(80, 80, 1)
    moving_palette = displayio.Palette(1)
    moving_palette[0] = 0xFFFFFF
    moving_tile = displayio.TileGrid(moving, pixel_shader=moving_palette, x=260, y=180)
    group.append(moving_tile)

    display.root_group = group
    samples = []
    for i in range(iterations):
        moving_tile.x = 120 + ((i * 37) % 320)
        moving_tile.y = 90 + ((i * 29) % 220)
        start = time.monotonic()
        display.refresh()
        samples.append(time.monotonic() - start)
    return _average_ms(samples)


def _show_black(display):
    bitmap = displayio.Bitmap(600, 450, 1)
    palette = displayio.Palette(1)
    palette[0] = 0x000000
    group = displayio.Group()
    group.append(displayio.TileGrid(bitmap, pixel_shader=palette))
    display.root_group = group
    display.refresh()


def _cleanup(display, qspi_bus):
    if display is not None:
        try:
            _show_black(display)
        except Exception as exc:
            print(f"[WARN] Screen clear failed: {exc}")

    try:
        displayio.release_displays()
        print("Cleanup: displayio released")
    except Exception as exc:
        print(f"[WARN] release_displays failed: {exc}")

    if qspi_bus is not None:
        try:
            qspi_bus.deinit()
            print("Cleanup: QSPI bus deinitialized")
        except Exception as exc:
            print(f"[WARN] qspi deinit failed: {exc}")


print("=" * 60)
print("DisplayIO Benchmark - Phase 5 (RM690B0 over qspibus)")
print("=" * 60)

displayio.release_displays()
qspi_bus = None
display = None

try:
    qspi_bus = _build_qspi_bus()
    display = RM690B0(qspi_bus, width=600, height=450)

    # Warm-up refresh to settle timings.
    _show_black(display)
    time.sleep(0.1)

    print("\nRunning benchmarks...")
    full_ms = _bench_full_screen(display)
    partial_ms = _bench_partial_update(display)
    scene_ms = _bench_multi_element(display)

    print("\n" + "=" * 60)
    print("Baseline Performance (v2.0)")
    print("=" * 60)
    print(f"Full screen fill (600x450): {full_ms:.3f} ms")
    print(f"Partial update (100x100):   {partial_ms:.3f} ms")
    print(f"Multi-element scene:        {scene_ms:.3f} ms")
    print("=" * 60)
    print("Target reference: <100 ms for full screen refresh")

except Exception as exc:
    print("\n" + "=" * 60)
    print(f"[FAIL] BENCHMARK FAILED: {exc}")
    print("=" * 60)
    import traceback

    traceback.print_exception(type(exc), exc, exc.__traceback__)

finally:
    _cleanup(display, qspi_bus)
