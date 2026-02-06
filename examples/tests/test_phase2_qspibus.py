"""
Test Phase 2: QSPIBus Module

INSTRUKCJA DLA UZYTKOWNIKA:
1. Flash firmware: cd repos/circuitpython-rm690b0 && ./build_waveshare.sh flash
2. Skopiuj test: cp examples/tests/test_phase2_qspibus.py /media/CIRCUITPY/code.py
3. Otworz monitor: ./build_waveshare.sh monitor
4. Zresetuj board (RST)

SPODZIEWANY OUTPUT:
  ==================================================
  Testing QSPIBus Module
  ==================================================
  [1/3] Creating QSPIBus...
      [OK] QSPIBus created successfully
  [2/3] Testing deinitialization...
      [OK] QSPIBus deinitialized
  [3/3] Testing context manager...
      [OK] Context manager works
  ==================================================
  [OK] ALL TESTS PASSED
  ==================================================

MOZLIWE BLEDY:
  - "GPIO X in use" -> Pin conflict, sprawdz czy inne moduly nie uzywaja LCD pins
  - "SPI bus init failed" -> SPI2 problem, sprawdz ESP-IDF config
  - "Semaphore timeout" -> DMA callback nie dziala
"""

import board
import displayio
import qspibus


def resolve_pin(*candidates):
    for name in candidates:
        if hasattr(board, name):
            return getattr(board, name), name
    raise AttributeError("No compatible pin alias found: {}".format(", ".join(candidates)))


print("=" * 50)
print("Testing QSPIBus Module")
print("=" * 50)

try:
    # Ensure previous display bus owners are released first.
    displayio.release_displays()

    clock, clock_name = resolve_pin("LCD_CLK", "QSPI_CLK", "DISPLAY_SCK")
    data0, data0_name = resolve_pin("LCD_D0", "QSPI_D0", "DISPLAY_D0")
    data1, data1_name = resolve_pin("LCD_D1", "QSPI_D1", "DISPLAY_D1")
    data2, data2_name = resolve_pin("LCD_D2", "QSPI_D2", "DISPLAY_D2")
    data3, data3_name = resolve_pin("LCD_D3", "QSPI_D3", "DISPLAY_D3")
    cs, cs_name = resolve_pin("LCD_CS", "QSPI_CS", "DISPLAY_CS")

    reset = None
    reset_name = None
    for candidate in ("LCD_RESET", "AMOLED_RESET", "DISPLAY_RST"):
        if hasattr(board, candidate):
            reset = getattr(board, candidate)
            reset_name = candidate
            break

    print(
        "Using pins: clock={}, data0={}, data1={}, data2={}, data3={}, cs={}, reset={}".format(
            clock_name,
            data0_name,
            data1_name,
            data2_name,
            data3_name,
            cs_name,
            reset_name if reset_name else "None",
        )
    )

    print("\n[1/3] Creating QSPIBus...")
    bus = qspibus.QSPIBus(
        clock=clock,
        data0=data0,
        data1=data1,
        data2=data2,
        data3=data3,
        cs=cs,
        reset=reset,
        frequency=80_000_000,
    )
    print("    [OK] QSPIBus created successfully")

    print("\n[2/3] Testing deinitialization...")
    bus.deinit()
    print("    [OK] QSPIBus deinitialized")

    print("\n[3/3] Testing context manager...")
    with qspibus.QSPIBus(
        clock=clock,
        data0=data0,
        data1=data1,
        data2=data2,
        data3=data3,
        cs=cs,
        frequency=80_000_000,
    ) as _test_bus:
        pass
    print("    [OK] Context manager works")

    print("\n" + "=" * 50)
    print("[OK] ALL TESTS PASSED")
    print("=" * 50)
    print("\nNote: send() method is not exposed to Python.")
    print("It will be tested in Phase 3 with display driver.")

except Exception as e:
    print("\n" + "=" * 50)
    print("[FAIL] TEST FAILED:", e)
    print("=" * 50)
    import traceback

    traceback.print_exception(type(e), e, e.__traceback__)
