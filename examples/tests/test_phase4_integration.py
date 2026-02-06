"""
Test Phase 4: Full integration after standalone rm690b0 removal

INSTRUKCJA:
1. Flash firmware:
     cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
     ./build_waveshare.sh flash
2. Copy test:
     cp /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241/examples/tests/test_phase4_integration.py /media/CIRCUITPY/code.py
3. Monitor:
     cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
     ./build_waveshare.sh monitor

EXPECTED SERIAL:
  ==================================================
  Full Integration Test - v2.0
  ==================================================
  [1/4] Testing sdioio (SD card)...
      [OK] SD card works
  [2/4] Testing QSPIBus...
      [OK] QSPI bus works
  [3/4] Testing displayio (RM690B0)...
      [OK] Display shows colors
  [4/4] Testing complex scene...
      [OK] Multi-element rendering works

EXPECTED SCREEN:
  - red -> green -> blue
  - black scene with three colored rectangles
"""

import time

import board
import displayio
import os
import qspibus
import sdioio
import storage
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
        "    Using pins: "
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


def _show_color(display, rgb):
    bitmap = displayio.Bitmap(600, 450, 1)
    palette = displayio.Palette(1)
    palette[0] = rgb
    group = displayio.Group()
    group.append(displayio.TileGrid(bitmap, pixel_shader=palette))
    display.root_group = group
    display.refresh()


def _render_scene(display):
    scene = displayio.Group()

    bg = displayio.Bitmap(600, 450, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0x000000
    scene.append(displayio.TileGrid(bg, pixel_shader=bg_palette))

    rect_specs = [
        (0xFF0000, 50, 50, 120, 90),
        (0x00FF00, 220, 150, 140, 90),
        (0x0000FF, 400, 260, 120, 100),
    ]

    for color, x, y, w, h in rect_specs:
        bmp = displayio.Bitmap(w, h, 1)
        pal = displayio.Palette(1)
        pal[0] = color
        scene.append(displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y))

    display.root_group = scene
    display.refresh()


def _cleanup(display, qspi_bus, sd_mounted):
    print("\n[Cleanup]")

    if display is not None:
        try:
            _show_color(display, 0x000000)
            print("  [OK] Screen cleared")
        except Exception as exc:
            print(f"  [WARN] Screen clear failed: {exc}")

    try:
        displayio.release_displays()
        print("  [OK] displayio released")
    except Exception as exc:
        print(f"  [WARN] release_displays failed: {exc}")

    if qspi_bus is not None:
        try:
            qspi_bus.deinit()
            print("  [OK] QSPI bus deinitialized")
        except Exception as exc:
            print(f"  [WARN] QSPI deinit failed: {exc}")

    if sd_mounted:
        try:
            storage.umount("/sd")
            print("  [OK] SD unmounted")
        except Exception as exc:
            print(f"  [WARN] SD umount failed: {exc}")


print("=" * 50)
print("Full Integration Test - v2.0")
print("=" * 50)

displayio.release_displays()
qspi_bus = None
display = None
sd_mounted = False

try:
    print("\n[1/4] Testing sdioio (SD card)...")
    sd = sdioio.SDCard(
        clock=board.SD_CLK,
        command=board.SD_MOSI,
        data=[board.SD_MISO],
        frequency=20_000_000,
    )
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")
    sd_mounted = True
    entries = len(os.listdir("/sd"))
    print(f"    [OK] SD card works ({entries} entries)")

    print("\n[2/4] Testing QSPIBus...")
    qspi_bus = _build_qspi_bus()
    print("    [OK] QSPI bus works")

    print("\n[3/4] Testing displayio (RM690B0)...")
    display = RM690B0(qspi_bus, width=600, height=450)

    for color, name in ((0xFF0000, "Red"), (0x00FF00, "Green"), (0x0000FF, "Blue")):
        print(f"    -> {name}")
        _show_color(display, color)
        time.sleep(0.6)

    print("    [OK] Display shows colors")

    print("\n[4/4] Testing complex scene...")
    _render_scene(display)
    print("    [OK] Multi-element rendering works")

    print("\n" + "=" * 50)
    print("[OK] ALL INTEGRATION TESTS PASSED!")
    print("v2.0 stack is functional: sdioio + qspibus + displayio")
    print("=" * 50)

except Exception as exc:
    print("\n" + "=" * 50)
    print(f"[FAIL] INTEGRATION TEST FAILED: {exc}")
    print("=" * 50)
    import traceback

    traceback.print_exception(type(exc), exc, exc.__traceback__)

finally:
    _cleanup(display, qspi_bus, sd_mounted)
