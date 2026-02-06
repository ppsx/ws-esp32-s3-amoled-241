# DisplayIO Panel Analysis (Phase 3)

## Scope

Goal of phase 3 is to run RM690B0 through CircuitPython `displayio` flow instead
of the standalone `rm690b0` API.

In this fork, there is no standalone `displayio_panel_protocol_t` driver layer.
The active architecture is:

`displayio` scene graph -> `busdisplay.BusDisplay` -> display bus backend.

Because of that, phase 3 implementation maps RM690B0 to:

1. `qspibus` as a `displayio`-compatible bus backend.
1. Python wrapper `RM690B0(BusDisplay)` with RM690B0 init sequence.

## Required Display Operations

`BusDisplay` internally requires bus-level primitives:

1. `begin_transaction()`
1. `send(DISPLAY_COMMAND, ...)`
1. `send(DISPLAY_DATA, ...)`
1. `end_transaction()`
1. `reset()` and `bus_free()`

These were added to `qspibus` in firmware (phase 3 C changes).

## QSPI Command/Data Mapping

RM690B0 over ESP-IDF panel IO uses packed QSPI command transactions.
`BusDisplay` sends command and data in separate calls, so `qspibus` now keeps:

1. `pending_command` (last command byte)
1. `has_pending_command` flag
1. `in_transaction` state

Mapping used:

1. `DISPLAY_COMMAND`: store command byte (or flush no-data command).
1. `DISPLAY_DATA`: send payload under pending command.
1. `end_transaction`: flush command without payload if still pending.

## RM690B0 Init Sequence Source

Init bytes are taken from:

`ports/espressif/common-hal/rm690b0/RM690B0.c` -> `lcd_init_cmds[]`

Key commands kept:

1. Panel page setup (`FE`, `26`, `24`, `EB`)
1. Pixel format `3A=0x55` (RGB565)
1. Sleep out (`11`) + delay
1. Display on (`29`) + delay
1. MADCTL (`36=0x30`)
1. Brightness (`51=0xFF`)

## Geometry / Offsets

Phase 3 test uses logical geometry from current project assumptions:

1. `width=600`
1. `height=450`
1. `colstart=0`
1. `rowstart=16`

This mirrors the existing project convention (`x_gap=0`, `y_gap=16`) used in
earlier notes and prompt materials.

## Test Artifact

Hardware validation script:

`examples/tests/test_phase3_displayio.py`

Helper driver used by the test:

`examples/tests/adafruit_rm690b0.py`

