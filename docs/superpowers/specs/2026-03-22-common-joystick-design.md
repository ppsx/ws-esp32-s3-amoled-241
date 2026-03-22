# Common Joystick Library

## Overview

Replace duplicated inline PCA9554 I2C joystick drivers across 7 games with a shared `joystick.py` module that supports both I2C and GPIO backends, selected via `settings.py`.

## Module: `examples/joystick.py`

Single file, ~80-100 lines. One class `Joystick`.

### Interface

```python
from joystick import Joystick

js = Joystick()        # reads settings.joystick_type and settings.gpio_pins
state = js.read()      # {"up": bool, "down": bool, "left": bool, "right": bool, "center": bool}
js.deinit()            # cleanup I2C bus or GPIO pins
```

### Constructor

Reads `settings.joystick_type` (fallback: `"i2c"` if no settings).

**I2C backend:**
- Bus: `board.TP_SCL` / `board.TP_SDA`
- Device: PCA9554 at address `0x21`
- Config: pins 0-4 input (0b00011111), pins 5-7 output
- Pin mapping: 0=UP, 1=DOWN, 2=RIGHT, 3=LEFT, 4=CENTER

**GPIO backend:**
- Reads pin numbers from `settings.gpio_pins` dict
- Initializes `digitalio.DigitalInOut` for each non-None pin
- Sets `direction = Direction.INPUT`, `pull = Pull.UP`
- Pins set to `None` in settings → always read as `False`

### read()

Returns dict with 5 boolean keys. Both backends use active-LOW logic (pressed = pin reads 0).

### deinit()

- I2C: deinits I2C bus
- GPIO: deinits each DigitalInOut pin

## Game Refactoring

7 games have inline PCA9554 drivers to replace:

| Game | Current class | Lines removed | Adaptation |
|------|--------------|---------------|------------|
| game_snake.py | NavigationSwitch | ~40 | `js.read()` directly maps to snake direction |
| game_pacman.py | JoystickInput | ~35 | Convert dict → DIR_* constants |
| game_frogger.py | JoystickInput | ~35 | Convert dict → direction constant |
| game_minesweeper.py | JoystickInput | ~35 | Convert dict → direction/action |
| game_sokoban.py | (inline driver) | ~35 | Convert dict → direction |
| game_galaxian.py | (inline driver) | ~35 | Convert dict → direction |
| robbo/pygame/event.py | JoystickHandler | ~40 | Convert dict → pygame key events |

**Not modified:** game_flappy_bird.py (touch only)

### Refactor pattern

Each game:
1. Remove inline PCA9554 constants and joystick class
2. Add `from joystick import Joystick`
3. Replace `JoystickInput()` / `NavigationSwitch()` with `Joystick()`
4. Adapt call site: `js.read()` → game-specific conversion (1-5 lines)
5. Replace `joystick.deinit()` call

## Scope

### In scope
- `examples/joystick.py` — shared module
- 7 game files — refactor to use shared module

### Out of scope
- Benchmarks (don't use joystick)
- settings_ui.py changes (settings format unchanged)
- LED control on PCA9554 (pins 5-7, currently only in test files)
