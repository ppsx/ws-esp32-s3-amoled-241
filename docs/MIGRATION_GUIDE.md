# Migration Guide: v1.x (standalone `rm690b0`) -> v2.0 (`displayio + qspibus`)

## Executive Summary

- **OLD (v1.x):** standalone module `rm690b0`
- **NEW (v2.0):** standard CircuitPython stack: `qspibus` + `displayio` + panel driver (`BusDisplay`)
- **Impact:** 100% API breaking change for apps using `import rm690b0`
- **Effort:** zwykle 1-3h na aplikację (proste UI), więcej przy niestandardowym renderingu

---

## Why This Change

Zmiana była wymagana dla upstream acceptance w CircuitPython: panel musi działać przez `displayio`, a nie przez oddzielny, board-specific standalone API.

### Benefits

- zgodność ze standardowym API CircuitPython
- kompatybilność z bibliotekami ekosystemu (`adafruit_display_text`, `vectorio`, `adafruit_imageload`)
- prostsze utrzymanie długoterminowe
- mniejsze ryzyko regresji przy aktualizacjach core

### Trade-offs

- pełne breaking changes dla starego kodu
- inny model renderowania (scene graph zamiast imperative draw+swap)
- potencjalnie inny profil wydajności

---

## API Mapping

| Old API (`rm690b0`) | New API (`displayio`) |
|---------------------|-----------------------|
| `rm690b0.init_display()` | `panel = RM690B0(bus, ...)` + `display = displayio.Display(panel, ...)` |
| `rm690b0.fill_color(color)` | `Bitmap` + `Palette` + `display.root_group = ...` |
| `rm690b0.fill_rect(...)` | `Bitmap`/`TileGrid` dla obszaru |
| `rm690b0.circle(...)` | `vectorio.Circle` |
| `rm690b0.line(...)` | `vectorio` lub drawing into `Bitmap` |
| `rm690b0.text(...)` | `adafruit_display_text.label.Label` lub `terminalio` |
| `rm690b0.blit_bmp(...)` | `adafruit_imageload.load(...)` |
| `rm690b0.blit_jpeg(...)` | `jpegio` + mapowanie do bitmapy |
| `rm690b0.swap_buffers()` | `display.refresh()` albo auto-refresh |
| `rm690b0.set_rotation(...)` | `display.rotation = ...` (zależnie od drivera) |

---

## New Initialization Template

```python
import board
import displayio
import qspibus
from busdisplay import BusDisplay

# Local/packaged RM690B0 wrapper for BusDisplay init sequence
from adafruit_rm690b0 import RM690B0

displayio.release_displays()

bus = qspibus.QSPIBus(
    clock=board.LCD_CLK,
    data0=board.LCD_D0,
    data1=board.LCD_D1,
    data2=board.LCD_D2,
    data3=board.LCD_D3,
    cs=board.LCD_CS,
    reset=board.LCD_RESET,
    frequency=40_000_000,
)

panel = RM690B0(bus, width=600, height=450)
display = displayio.Display(panel, width=600, height=450)
```

Uwaga: na tej płytce stabilny cleanup zwykle wymaga: ekran->czarny, `displayio.release_displays()`, potem `bus.deinit()`.

---

## Migration Examples

Poniższe przykłady bazują na Appendix A (A.1/A.2) z `docs/CIRCUITPYTHON_UPSTREAM_FEEDBACK.md` i są dostosowane do aktualnego flow.

### Example 1: Simple Graphics

**Before (v1.x):**

```python
import rm690b0

rm690b0.init_display()
rm690b0.fill_color(rm690b0.BLACK)
rm690b0.fill_rect(50, 50, 200, 100, rm690b0.RED)
rm690b0.swap_buffers()
```

**After (v2.0):**

```python
import displayio

bg = displayio.Bitmap(600, 450, 1)
bg_pal = displayio.Palette(1)
bg_pal[0] = 0x000000

rect = displayio.Bitmap(200, 100, 1)
rect_pal = displayio.Palette(1)
rect_pal[0] = 0xFF0000

group = displayio.Group()
group.append(displayio.TileGrid(bg, pixel_shader=bg_pal))
group.append(displayio.TileGrid(rect, pixel_shader=rect_pal, x=50, y=50))

display.root_group = group
display.refresh()
```

### Example 2: Text/Clock (Appendix A.1)

**Before (v1.x):**

```python
import rm690b0
import time

rm690b0.init_display()
while True:
    rm690b0.fill_color(rm690b0.BLACK)
    rm690b0.circle(300, 225, 100, rm690b0.WHITE)
    rm690b0.text(250, 300, "12:34", rm690b0.WHITE, rm690b0.BLACK)
    rm690b0.swap_buffers()
    time.sleep(1)
```

**After (v2.0):**

```python
import time
import vectorio
import terminalio
from adafruit_display_text import label

scene = displayio.Group()
clock_face = vectorio.Circle(radius=100, pixel_shader=0xFFFFFF, x=300, y=225)
time_label = label.Label(terminalio.FONT, text="00:00", color=0xFFFFFF, x=250, y=300)
scene.append(clock_face)
scene.append(time_label)
display.root_group = scene

while True:
    t = time.localtime()
    time_label.text = f"{t.tm_hour % 12:02d}:{t.tm_min:02d}"
    time.sleep(1)
```

### Example 3: JPEG Gallery (Appendix A.2)

**Before (v1.x):**

```python
import rm690b0

rm690b0.init_display()
rm690b0.blit_jpeg("/sd/photos/a.jpg", 0, 0)
rm690b0.swap_buffers()
```

**After (v2.0):**

```python
import displayio
import jpegio

with open("/sd/photos/a.jpg", "rb") as f:
    raw = f.read()

decoder = jpegio.JpegDecoder()
img = decoder.decode(raw)

bitmap = displayio.Bitmap(img.width, img.height, 65536)
# map pixels from decoder output into bitmap (project-specific helper)

palette = displayio.Palette(65536)
# init palette to RGB565 identity or converted mapping

tile = displayio.TileGrid(bitmap, pixel_shader=palette)
group = displayio.Group()
group.append(tile)
display.root_group = group
display.refresh()
```

---

## Step-by-Step Migration Checklist

1. Usuń `import rm690b0` i dodaj init `displayio + qspibus`.
2. Zamień imperative drawing calls na budowanie `displayio.Group()`.
3. Zastąp `swap_buffers()` przez `display.refresh()` albo auto-refresh.
4. Zamień text API na `adafruit_display_text`/`terminalio`.
5. Przetestuj cleanup (black frame + `release_displays()` + `bus.deinit()`).

---

## Common Issues

### `ImportError: No module named rm690b0`

Oczekiwane po fazie 4. Moduł standalone został usunięty.

### Czarne tło mimo braku błędów

- sprawdź poprawne aliasy pinów (`LCD_*` preferowane)
- upewnij się, że używasz poprawnego init sequence panelu
- sprawdź kolejność cleanup/init przy ponownym uruchomieniu testu

### `.show(x) removed. Use .root_group = x`

W nowszym API użyj `display.root_group = group` zamiast `display.show(group)`.

---

## Quick Validation Script

Referencja: `examples/tests/test_phase4_integration.py`

Skrypt sprawdza jednocześnie:
- `sdioio` (mount/read/write)
- `qspibus`
- `displayio` rendering
- cleanup i deinit

---

## Related Docs

- `docs/CODE_REMOVAL_AUDIT.md`
- `docs/TECHNICAL_NOTES.md`
- `docs/CIRCUITPYTHON_UPSTREAM_FEEDBACK.md`
