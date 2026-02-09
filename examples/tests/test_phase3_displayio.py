"""
Test Phase 3: RM690B0 displayio integration over qspibus

INSTRUKCJA:
1. Flash firmware:
     cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
     ./build_waveshare.sh flash
2. Skopiuj test:
     cp /home/pps/Downloads/__ai__/repos/ws-esp32-s3-amoled-241/examples/tests/test_phase3_displayio.py /media/CIRCUITPY/code.py
3. Monitor:
     cd /home/pps/Downloads/__ai__/repos/circuitpython-rm690b0
     ./build_waveshare.sh monitor
4. Zresetuj board i obserwuj ekran.

SPODZIEWANE:
- Serial: "ALL TESTS PASSED"
- Ekran: czerwony, zielony, niebieski, na koncu bialy prostokat na czarnym tle.
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


def _show_color(display, rgb):
    bitmap = displayio.Bitmap(600, 450, 1)
    palette = displayio.Palette(1)
    palette[0] = rgb
    tile = displayio.TileGrid(bitmap, pixel_shader=palette)
    group = displayio.Group()
    group.append(tile)
    display.root_group = group
    display.refresh()


def _cleanup(display, qspi_bus):
    print("\n[5/5] Cleanup...")
    cleanup_ok = True

    if display is not None:
        try:
            _show_color(display, 0x000000)
            time.sleep(0.1)
            print("    [OK] Screen cleared to black")
        except Exception as exc:
            cleanup_ok = False
            print(f"    [WARN] Could not clear screen: {exc}")

    try:
        displayio.release_displays()
        print("    [OK] displayio.release_displays()")
    except Exception as exc:
        cleanup_ok = False
        print(f"    [WARN] release_displays failed: {exc}")

    if not cleanup_ok:
        raise RuntimeError("Cleanup incomplete")


print("=" * 58)
print("Testing RM690B0 with displayio (Phase 3)")
print("=" * 58)

displayio.release_displays()
qspi_bus = None
display = None
cleaned_up = False

try:
    print("\n[1/5] Creating QSPI bus...")
    qspi_bus = _build_qspi_bus()
    print("    [OK] QSPI bus created")

    print("\n[2/5] Creating RM690B0 panel...")
    display = RM690B0(
        qspi_bus,
        width=600,
        height=450,
        colstart=0,
        rowstart=16,
        rotation=0,
    )
    print("    [OK] RM690B0 panel initialized")

    print("\n[3/5] Color cycle...")
    print("    -> Red")
    _show_color(display, 0xFF0000)
    time.sleep(2)
    print("    -> Green")
    _show_color(display, 0x00FF00)
    time.sleep(2)
    print("    -> Blue")
    _show_color(display, 0x0000FF)
    time.sleep(2)
    print("    [OK] RGB colors displayed")

    print("\n[4/5] Rectangle test...")
    bg = displayio.Bitmap(600, 450, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0x000000
    bg_tile = displayio.TileGrid(bg, pixel_shader=bg_palette)

    rect = displayio.Bitmap(240, 120, 1)
    rect_palette = displayio.Palette(1)
    rect_palette[0] = 0xFFFFFF
    rect_tile = displayio.TileGrid(rect, pixel_shader=rect_palette, x=180, y=165)

    group = displayio.Group()
    group.append(bg_tile)
    group.append(rect_tile)
    display.root_group = group
    display.refresh()
    print("    [OK] Rectangle displayed")

    _cleanup(display, qspi_bus)
    cleaned_up = True

    print("\n" + "=" * 58)
    print("[OK] ALL TESTS PASSED")
    print("Screen expectation: red, green, blue, white rectangle on black")
    print("=" * 58)

except Exception as exc:
    print("\n" + "=" * 58)
    print(f"[FAIL] TEST FAILED: {exc}")
    print("=" * 58)
    import traceback

    traceback.print_exception(type(exc), exc, exc.__traceback__)
    if not cleaned_up:
        try:
            _cleanup(display, qspi_bus)
        except Exception as cleanup_exc:
            print(f"\n[WARN] Cleanup after failure raised: {cleanup_exc}")
except KeyboardInterrupt:
    print("\n" + "=" * 58)
    print("[INTERRUPTED] Test interrupted by user")
    print("=" * 58)
    if not cleaned_up:
        try:
            _cleanup(display, qspi_bus)
        except Exception as cleanup_exc:
            print(f"\n[WARN] Cleanup after interrupt raised: {cleanup_exc}")
