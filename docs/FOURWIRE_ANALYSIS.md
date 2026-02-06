# FourWire Analysis for QSPIBus Implementation

## API Surface

### Constructor
- Signature and args parsing: `shared-bindings/fourwire/FourWire.c:62`
- Parameters:
  - `spi_bus: busio.SPI`
  - `command: Optional[microcontroller.Pin]`
  - `chip_select: Optional[microcontroller.Pin]`
  - `reset: Optional[microcontroller.Pin]`
  - `baudrate: int = 24000000`
  - `polarity: int = 0`
  - `phase: int = 0`
- Pin validation:
  - `validate_obj_is_free_pin_or_none(...)` for `command/chip_select/reset` in `shared-bindings/fourwire/FourWire.c:76`
- SPI object type validation:
  - `mp_arg_validate_type(..., &busio_spi_type, ...)` in `shared-bindings/fourwire/FourWire.c:80`
- Constructor handoff to common-hal:
  - `common_hal_fourwire_fourwire_construct(...)` in `shared-bindings/fourwire/FourWire.c:88`

### send() Method
- Python entrypoint signature and parsing: `shared-bindings/fourwire/FourWire.c:116`
- Command validation: 8-bit (`0..255`) in `shared-bindings/fourwire/FourWire.c:126`
- Data input: `ReadableBuffer` via `mp_get_buffer_raise(...)` in `shared-bindings/fourwire/FourWire.c:130`
- Transaction model:
  - Wait until bus lock available in `shared-bindings/fourwire/FourWire.c:133`
  - Send command then payload in `shared-bindings/fourwire/FourWire.c:141`
  - End transaction and unlock in `shared-bindings/fourwire/FourWire.c:143`
- Common-hal transmit implementation:
  - 9-bit emulation path when no command pin in `shared-module/fourwire/FourWire.c:104`
  - Regular D/C toggle + SPI write path in `shared-module/fourwire/FourWire.c:143`
- Blocking behavior:
  - Blocking at Python level until transaction ends (`begin_transaction` loop + synchronous send).

### deinit() Method
- Common-hal deinit logic: `shared-module/fourwire/FourWire.c:57`
- Cleanup steps:
  1. Deinit inline SPI bus if owned (`shared-module/fourwire/FourWire.c:58`)
  2. Reset command pin (`shared-module/fourwire/FourWire.c:62`)
  3. Reset chip-select pin (`shared-module/fourwire/FourWire.c:63`)
  4. Reset reset pin (`shared-module/fourwire/FourWire.c:64`)

## Integration Points

- Integration with `busio.SPI`:
  - Bus handle stored in object in `shared-module/fourwire/FourWire.c:23`
  - Lock/configure/unlock sequence in:
    - `shared-module/fourwire/FourWire.c:88`
    - `shared-module/fourwire/FourWire.c:93`
    - `shared-module/fourwire/FourWire.c:167`
- Pin management strategy:
  - Validate free pins at binding layer (`shared-bindings/fourwire/FourWire.c:76`)
  - Construct and configure as outputs in common-hal (`shared-module/fourwire/FourWire.c:34`)
  - Mark pins as never-reset for display persistence (`shared-module/fourwire/FourWire.c:36`)
  - Release via `common_hal_reset_pin(...)` on deinit (`shared-module/fourwire/FourWire.c:62`)
- Error handling patterns:
  - Parameter range checks: `mp_arg_validate_int_range` (`shared-bindings/fourwire/FourWire.c:85`)
  - User-facing runtime errors: `mp_raise_RuntimeError_varg` (`shared-bindings/fourwire/FourWire.c:102`)
  - Retry loop for bus availability using `RUN_BACKGROUND_TASKS` (`shared-bindings/fourwire/FourWire.c:135`)

## Code Patterns to Reuse

- Constructor validation and parsing:
  - `shared-bindings/fourwire/FourWire.c:62`
- Structured transaction (`begin -> send cmd -> send data -> end`):
  - `shared-bindings/fourwire/FourWire.c:133`
- Pin setup and reset workflow:
  - Setup: `shared-module/fourwire/FourWire.c:31`
  - Cleanup: `shared-module/fourwire/FourWire.c:57`

## Differences for QSPIBus

- FourWire: 1 data line (`MOSI`) + optional `command` pin.
- QSPIBus: 4 data lines (`D0..D3`) + clock + CS (+ optional reset).
- FourWire transport: standard SPI command/data split.
- QSPIBus transport: QSPI panel IO (`esp_lcd_panel_io_spi`) with quad mode enabled.

## ESP32-S3 Specifics

- `SPI2_HOST` should be used (`SPI1_HOST` reserved for flash/PSRAM).
- QSPI panel IO configuration should enable quad mode (`.flags.quad_mode = 1`).
- DMA completion callback + semaphore synchronization is the preferred transfer completion model.
- In this tree there is no dedicated `ports/espressif/common-hal/fourwire/` implementation; FourWire uses shared common-hal implementation (`shared-module/fourwire/`).
