# Code Removal Audit - Phase 4

## Scope

Faza 4 usuwa stary standalone module `rm690b0` z firmware i zostawia wyłącznie komponenty potrzebne do obecnej architektury (`displayio + qspibus`) oraz przyszłej integracji JPEG.

Data audytu: 2026-02-06

---

## Files Removed

| File | Lines | Role | Decision |
|------|------:|------|----------|
| `shared-bindings/rm690b0/RM690B0.c` | 513 | Python API klasy `RM690B0` | DELETE |
| `shared-bindings/rm690b0/RM690B0.h` | 50 | deklaracje typu/bindings | DELETE |
| `shared-bindings/rm690b0/__init__.c` | 93 | rejestracja modułu `rm690b0` | DELETE |
| `ports/espressif/common-hal/rm690b0/RM690B0.c` | 3762 | główna implementacja standalone drivera | DELETE |
| `ports/espressif/common-hal/rm690b0/RM690B0.h` | 26 | nagłówek HAL dla standalone drivera | DELETE |
| `ports/espressif/common-hal/rm690b0/fonts/*.h` (7 files) | 5449 | wbudowane bitmap fonts | DELETE |

### Totals

- Removed C source/header lines: **9893**
- Removed font binary/header footprint: **~384 KB** (headers in repo)

---

## Files Retained

| File | Lines | Role | Decision |
|------|------:|------|----------|
| `ports/espressif/common-hal/rm690b0/esp_lcd_rm690b0.c` | 342 | vendor panel commands/init helpers | KEEP |
| `ports/espressif/common-hal/rm690b0/esp_lcd_rm690b0.h` | 109 | vendor panel definitions | KEEP |
| `ports/espressif/common-hal/rm690b0/esp_jpeg/esp_jpeg.c` | 295 | ESP JPEG decoder glue | KEEP |
| `ports/espressif/common-hal/rm690b0/esp_jpeg/esp_jpeg.h` | 72 | ESP JPEG decoder API | KEEP |

Rationale:
- `esp_lcd_rm690b0.*` jest nadal potrzebny przez ścieżkę panelową używaną z `displayio`.
- `esp_jpeg/*` jest zachowany jako baza pod dalsze prace wokół `jpegio`.

---

## Build System Changes

- `ports/espressif/boards/waveshare_esp32_s3_amoled_241/mpconfigboard.mk`
  - disabled standalone module flag (`CIRCUITPY_RM690B0` removed)
  - retained `CIRCUITPY_QSPIBUS = 1`
- `py/circuitpy_mpconfig.mk`
  - removed active `CIRCUITPY_RM690B0` make switch
- `py/circuitpy_defns.mk`
  - removed `rm690b0/%` source patterns from build graph
- `ports/espressif/Makefile`
  - removed standalone `common-hal/rm690b0/*.c` compile block

Result:
- `firmware.bin` no longer contains `rm690b0` module strings
- `qspibus` strings are present in firmware

---

## Board/Pin Naming Changes

Board aliases migrated to generic LCD naming for new display path:

- `LCD_CS`, `LCD_CLK`, `LCD_D0`, `LCD_D1`, `LCD_D2`, `LCD_D3`, `LCD_RESET`

Compatibility aliases (`QSPI_*`, `AMOLED_RESET`) are still exposed to avoid breaking existing test scripts.

---

## Functionality Migration Map

### Migrated to displayio/qspibus path

| Legacy capability | New path | Status |
|------------------|----------|--------|
| panel bus init/deinit | `qspibus.QSPIBus` | DONE |
| panel init sequence execution | `BusDisplay` + RM690B0 init sequence | DONE |
| full/partial refresh | `displayio.Display` / `BusDisplay` | DONE |
| color write transactions | qspibus packed command/data flow | DONE |

### Deprecated (replaced by ecosystem APIs)

| Old standalone API | Replacement |
|--------------------|-------------|
| `rm690b0.fill_rect()` | `displayio.Bitmap` + `displayio.TileGrid` |
| `rm690b0.circle()` | `vectorio.Circle` |
| `rm690b0.line()` | `vectorio` or bitmap drawing |
| `rm690b0.text()` | `adafruit_display_text.label.Label` / `terminalio` |
| `rm690b0.blit_bmp()` | `adafruit_imageload` |
| `rm690b0.blit_jpeg()` | `jpegio` + bitmap path |
| `rm690b0.swap_buffers()` | `display.refresh()` / auto-refresh |

---

## Decision

**Proceed with removal: APPROVED**

Faza 3 potwierdziła działający tor `qspibus + displayio` na realnym sprzęcie (rendering kolorów i figur, stabilny cleanup/deinit).
