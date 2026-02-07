# Firmware for Waveshare ESP32-S3 Touch AMOLED 2.41

Pre-built CircuitPython 10.0.3 firmware with RM690B0 display driver support.

## Available Firmware Versions

### 1. `firmware-rm690b0.bin` (Stable - Recommended)

**Status:** ✅ Production Ready

**Features:**

- Complete RM690B0 display driver
- Native text rendering (7 built-in fonts)
- Graphics primitives (lines, circles, rectangles, fills)
- Image support (BMP/JPEG with hardware acceleration)
- Double buffering with `swap_buffers()`
- Brightness control API
- Stable and optimized

**Use for:**

- Production applications
- Embedded displays
- Games and animations
- Simple UIs
- Fast performance requirements

**Size:** ~2-3 MB

---

### 2. `firmware-rm690b0-lvgl.bin` (Beta)

**Status:** ⚠️ Functional with Known Issues

**Features:**

- All features from `firmware-rm690b0.bin`
- Full LVGL 8.x integration
- Python widget API (20+ widget types)
- TTF font support via Tiny TTF
- Touch integration with automatic coordinate transformation
- Event system with Python callbacks
- Rich UI capabilities

**Use for:**

- Prototyping rich UIs
- Widget-based interfaces
- Complex interactive applications
- TTF font rendering

**Known Issue:** LVGL+touch can lose responsiveness under heavy GC pressure or repeated `gc.collect()` calls.

**Workarounds:**

- Avoid explicit `gc.collect()` in UI loop
- Load TTF fonts once at startup
- Minimize large heap allocations during interaction

**Size:** ~3-4 MB

---

## Flashing Instructions

### Prerequisites

1. **Hardware:**
   - Waveshare ESP32-S3 Touch AMOLED 2.41 board
   - USB-C cable (must support data, not just charging)

2. **Software:**
   - Python 3.7+ installed
   - `esptool.py` installed: `pip install esptool`

3. **Check Installation:**

   ```bash
   esptool.py --version
   # Should show: esptool.py v4.x or newer
   ```

---

### Method 1: Quick Flash (Recommended)

**Linux/macOS:**

```bash
# For stable version (rm690b0 only)
esptool.py --chip esp32s3 -p /dev/ttyACM0 \
  --before=default_reset --after=no_reset --baud 921600 \
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB \
  0x0 firmware-rm690b0.bin

# For LVGL version (rm690b0 + LVGL)
esptool.py --chip esp32s3 -p /dev/ttyACM0 \
  --before=default_reset --after=no_reset --baud 921600 \
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB \
  0x0 firmware-rm690b0-lvgl.bin
```

**Windows:**

```bash
# For stable version (rm690b0 only)
esptool.py --chip esp32s3 -p COM3 ^
  --before=default_reset --after=no_reset --baud 921600 ^
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB ^
  0x0 firmware-rm690b0.bin

# For LVGL version (rm690b0 + LVGL)
esptool.py --chip esp32s3 -p COM3 ^
  --before=default_reset --after=no_reset --baud 921600 ^
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB ^
  0x0 firmware-rm690b0-lvgl.bin
```

---

### Method 2: Step-by-Step Flash

#### Step 1: Connect the Board

1. Connect the board to your computer via USB-C cable
2. Board should appear as a serial device

**Find the port:**

```bash
# Linux
ls /dev/ttyACM* /dev/ttyUSB*
# Typical: /dev/ttyACM0

# macOS
ls /dev/cu.usbmodem*
# Typical: /dev/cu.usbmodem14201

# Windows - Device Manager → Ports (COM & LPT)
# Typical: COM3, COM4, etc.
```

#### Step 2: Erase Flash (Optional but Recommended)

```bash
# Linux/macOS
esptool.py --chip esp32s3 -p /dev/ttyACM0 erase_flash

# Windows
esptool.py --chip esp32s3 -p COM3 erase_flash
```

**Note:** This ensures a clean installation but will erase all existing data.

#### Step 3: Flash Firmware

Choose your firmware version:

**Option A: Stable (rm690b0 only):**

```bash
# Linux/macOS
esptool.py --chip esp32s3 -p /dev/ttyACM0 \
  --before=default_reset --after=no_reset --baud 921600 \
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB \
  0x0 firmware-rm690b0.bin

# Windows
esptool.py --chip esp32s3 -p COM3 ^
  --before=default_reset --after=no_reset --baud 921600 ^
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB ^
  0x0 firmware-rm690b0.bin
```

**Option B: Beta (rm690b0 + LVGL):**

```bash
# Linux/macOS
esptool.py --chip esp32s3 -p /dev/ttyACM0 \
  --before=default_reset --after=no_reset --baud 921600 \
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB \
  0x0 firmware-rm690b0-lvgl.bin

# Windows
esptool.py --chip esp32s3 -p COM3 ^
  --before=default_reset --after=no_reset --baud 921600 ^
  write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB ^
  0x0 firmware-rm690b0-lvgl.bin
```

#### Step 4: Reset Board

After flashing completes:

1. Press the RESET button on the board, OR
2. Disconnect and reconnect USB cable

The board should now appear as `CIRCUITPY` drive.

---

## Command Parameters Explained

| Parameter      | Value                    | Description                           |
| -------------- | ------------------------ | ------------------------------------- |
| `--chip`       | `esp32s3`                | Target chip type                      |
| `-p`           | `/dev/ttyACM0` or `COM3` | Serial port                           |
| `--before`     | `default_reset`          | Reset before operation                |
| `--after`      | `no_reset`               | Don't reset after (allows inspection) |
| `--baud`       | `921600`                 | Baud rate (faster = quicker flash)    |
| `--flash_mode` | `dio`                    | Dual I/O mode for flash               |
| `--flash_freq` | `80m`                    | Flash frequency 80 MHz                |
| `--flash_size` | `16MB`                   | Total flash size                      |
| `0x0`          | -                        | Start address (bootloader)            |

---

## Troubleshooting

### Issue: "Serial port not found"

**Solutions:**

1. Check USB cable supports data (not just charging)
2. Install USB-to-Serial drivers if needed
3. Check Device Manager (Windows) or `dmesg` (Linux)
4. Try different USB port
5. Check permissions on Linux: `sudo usermod -a -G dialout $USER`

### Issue: "Failed to connect"

**Solutions:**

1. Hold BOOT button while connecting USB
2. Press BOOT + RESET, release RESET, then release BOOT
3. Lower baud rate: use `--baud 115200` instead
4. Try different USB cable
5. Check if board is in bootloader mode

### Issue: "Wrong boot mode detected"

**Solutions:**

1. The board is already in a running state
2. Hold BOOT button and press RESET
3. Try: `esptool.py --chip esp32s3 -p PORT --before=default_reset chip_id`
4. Then flash again

### Issue: "Timed out waiting for packet header"

**Solutions:**

1. Lower baud rate: `--baud 460800` or `--baud 115200`
2. Use better USB cable
3. Try different USB port (preferably USB 2.0)
4. Avoid USB hubs

### Issue: Flash successful but board doesn't boot

**Solutions:**

1. Press RESET button on board
2. Check if CIRCUITPY drive appears (wait 5-10 seconds)
3. Re-flash with `erase_flash` first
4. Try different firmware version
5. Check power supply (use powered USB hub if needed)

### Issue: Permission denied (Linux)

**Solutions:**

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or run with sudo (not recommended)
sudo esptool.py ...

# Check port permissions
ls -l /dev/ttyACM0

# Set permissions temporarily
sudo chmod 666 /dev/ttyACM0
```

### Issue: CIRCUITPY drive doesn't appear

**Possible causes:**

1. Board needs reset - press RESET button
2. USB cable is charge-only (no data)
3. Filesystem not initialized - re-flash firmware
4. Check dmesg/Device Manager for USB enumeration

**Fix:**

```bash
# Linux - check USB messages
dmesg | tail -20

# Should see:
# usb-storage: USB Mass Storage device detected
# sd 0:0:0:0: Attached scsi removable disk
```

---

## Verification

After successful flash:

1. **Board resets automatically** (or press RESET)
2. **CIRCUITPY drive appears** (wait 5-10 seconds)
3. **Serial REPL available** at same port (115200 baud)

### Test Basic Functionality

#### Option 1: Serial REPL

```bash
# Connect to serial console
screen /dev/ttyACM0 115200
# or
minicom -D /dev/ttyACM0 -b 115200
# or
putty (Windows)
```

Press Enter, you should see:

```text
>>>
```

Test display:

```python
import rm690b0
display = rm690b0.RM690B0()
display.init_display()
display.fill_color(0xF800)  # Red screen
display.swap_buffers()
```

#### Option 2: File Execution

Create `code.py` on CIRCUITPY drive:

```python
import rm690b0

display = rm690b0.RM690B0()
display.init_display()

# Clear screen
display.fill_color(0x0000)

# Draw text
display.set_font(1)
display.text(50, 200, "Firmware OK!", 0xFFFF)

display.swap_buffers()
```

Board will automatically run this on reset.

---

## Switching Between Versions

You can switch between firmware versions at any time:

1. Flash the other firmware version following instructions above
2. Reset the board
3. CIRCUITPY drive will have CircuitPython with selected features

**Note:** Your files on CIRCUITPY drive are preserved when switching firmware versions (unless you use `erase_flash`).

---

## Flash Time Estimates

| Baud Rate | firmware-rm690b0.bin | firmware-rm690b0-lvgl.bin |
| --------- | -------------------- | ------------------------- |
| 115200    | ~60 seconds          | ~80 seconds               |
| 460800    | ~20 seconds          | ~25 seconds               |
| 921600    | ~10 seconds          | ~15 seconds               |

**Recommended:** Use 921600 for fastest flashing.

---

## Next Steps

After flashing:

1. **Copy Examples:**

   ```bash
   cp ../examples/test_all_fonts.py /media/$USER/CIRCUITPY/code.py
   ```

2. **For LVGL firmware:**

   ```bash
   # Copy TTF fonts
   cp -r ../examples/fonts /media/$USER/CIRCUITPY/
   
   # Copy libraries
   cp -r ../examples/lib /media/$USER/CIRCUITPY/
   ```

3. **Read Documentation:**
   - [RM690B0_DRIVER.md](../docs/RM690B0_DRIVER.md) - Display driver API
   - [RM690B0_LVGL.md](../docs/RM690B0_LVGL.md) - LVGL integration guide
   - [examples/README.md](../examples/README.md) - All examples

4. **Run Examples:**
   - See [../examples/](../examples/) for 25+ ready-to-run demos

---

## Advanced Options

### Verify Flash Without Writing

```bash
esptool.py --chip esp32s3 -p /dev/ttyACM0 \
  verify_flash 0x0 firmware-rm690b0.bin
```

### Read Flash Content

```bash
esptool.py --chip esp32s3 -p /dev/ttyACM0 \
  read_flash 0x0 0x400000 backup.bin
```

### Check Chip Info

```bash
esptool.py --chip esp32s3 -p /dev/ttyACM0 chip_id
esptool.py --chip esp32s3 -p /dev/ttyACM0 flash_id
```

### Slower Flash (More Reliable)

```bash
esptool.py --chip esp32s3 -p /dev/ttyACM0 \
  --baud 115200 \
  write_flash --flash_mode dio --flash_freq 40m --flash_size 16MB \
  0x0 firmware-rm690b0.bin
```

---

## Technical Details

### Firmware Build Information

**Base:** CircuitPython 10.0.3  
**Board:** Waveshare ESP32-S3 Touch AMOLED 2.41  
**Chip:** ESP32-S3 (Dual-core Xtensa LX7)  
**Flash:** 16 MB  
**PSRAM:** 8 MB  
**Toolchain:** ESP-IDF v5.x  

### Memory Layout

| Address | Size     | Content                    |
| ------- | -------- | -------------------------- |
| 0x0000  | Variable | Bootloader + firmware      |
| 0x8000  | Variable | Partition table            |
| 0x10000 | Variable | CircuitPython application  |
| 0xE000  | 8 KB     | OTA data                   |
| 0x2000  | 24 KB    | NVS (Non-Volatile Storage) |

### Modules Included

**firmware-rm690b0.bin:**

- `rm690b0` - Display driver
- `board` - Pin definitions
- `busio` - I2C, SPI, UART
- `digitalio` - GPIO
- `analogio` - ADC
- `time` - Time functions
- `gc` - Garbage collection
- `os`, `sys` - System functions
- `storage` - Filesystem
- `wifi` - WiFi support
- `espnow` - ESP-NOW protocol
- `sdioio` - SD card support (1-bit mode)
- Standard CircuitPython libraries

**firmware-rm690b0-lvgl.bin:**

- All modules from `firmware-rm690b0.bin`
- `rm690b0_lvgl` - LVGL integration
- LVGL 8.x library compiled in
- 20+ Python widget classes
- TTF font support (Tiny TTF)

---

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section above
2. Review [documentation](../docs/)
3. See [project status](../docs/project_status_summary.md)
4. Open issue on GitHub repository

---

## License

Firmware based on CircuitPython 10.0.3 (MIT License)  
RM690B0 driver and LVGL integration: MIT License

See [../README.md](../README.md) for complete license information.

---

**Happy Flashing!** 🚀
