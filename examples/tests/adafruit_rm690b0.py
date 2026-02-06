# SPDX-FileCopyrightText: Copyright (c) 2026 Przemyslaw Patrick Socha
#
# SPDX-License-Identifier: MIT

"""
displayio driver for RM690B0 AMOLED over qspibus.

This is a temporary phase-3 helper module kept in the hardware test folder.
It wraps `busdisplay.BusDisplay` with the RM690B0 init sequence used by this
board.
"""

from busdisplay import BusDisplay

try:
    from typing import Any
    import qspibus
except ImportError:
    pass

__version__ = "0.3.0-phase3"
__repo__ = "https://github.com/pps/ws-esp32-s3-amoled-241"

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
    """RM690B0 displayio driver for Waveshare ESP32-S3 AMOLED 2.41."""

    def __init__(
        self,
        bus: "qspibus.QSPIBus",
        *,
        width: int = 600,
        height: int = 450,
        colstart: int = 0,
        rowstart: int = 16,
        rotation: int = 0,
        **kwargs: "Any",
    ) -> None:
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
