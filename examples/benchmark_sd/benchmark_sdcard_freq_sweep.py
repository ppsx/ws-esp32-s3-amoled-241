"""
Benchmark: sdioio Frequency Sweep

Tests SD card performance at different frequencies

Tests performed:
- WRITE
- READ (alloc)
- READ (readinto)

for frequencies: 10/20/25/40 MHz
"""

import board
import gc
import os
import sdioio
import storage
import time

TEST_FILE = "/sd/benchmark_freq_sweep.bin"
TEST_SIZE = 2 * 1024 * 1024  # 2 MB
CHUNK_SIZE = 64 * 1024       # 64 KB
FREQUENCIES = (10_000_000, 20_000_000, 25_000_000, 40_000_000)


def format_bytes(value):
    units = ("B", "KB", "MB", "GB")
    index = 0
    value = float(value)
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    return "{:.2f} {}".format(value, units[index])


def format_speed(bytes_per_second):
    return "{}/s".format(format_bytes(bytes_per_second))


def normalize_frequency_hz(raw_frequency):
    if raw_frequency < 1_000_000:
        return raw_frequency * 1000
    return raw_frequency


def fill_pattern(buffer):
    for i in range(len(buffer)):
        buffer[i] = i & 0xFF


def benchmark_write():
    buffer = bytearray(CHUNK_SIZE)
    fill_pattern(buffer)

    remaining = TEST_SIZE
    start = time.monotonic()
    with open(TEST_FILE, "wb") as f:
        while remaining > 0:
            current = CHUNK_SIZE if remaining >= CHUNK_SIZE else remaining
            f.write(memoryview(buffer)[:current])
            remaining -= current
    elapsed = time.monotonic() - start
    return TEST_SIZE / elapsed, elapsed


def benchmark_read_alloc():
    start = time.monotonic()
    with open(TEST_FILE, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
    elapsed = time.monotonic() - start
    return TEST_SIZE / elapsed, elapsed


def benchmark_read_readinto():
    buffer = bytearray(CHUNK_SIZE)
    start = time.monotonic()
    with open(TEST_FILE, "rb") as f:
        while True:
            count = f.readinto(buffer)
            if not count:
                break
    elapsed = time.monotonic() - start
    return TEST_SIZE / elapsed, elapsed


def cleanup_file_if_exists():
    try:
        if TEST_FILE in os.listdir("/sd"):
            os.remove(TEST_FILE)
    except Exception:
        pass


def run_for_frequency(freq_hz):
    sd = None
    mounted = False
    result = {
        "requested_hz": freq_hz,
        "actual_raw": None,
        "actual_hz": None,
        "write_bps": None,
        "read_alloc_bps": None,
        "read_into_bps": None,
        "error": None,
    }

    try:
        print("\n------------------------------------------------------------")
        print("Frequency test: {} Hz".format(freq_hz))
        print("------------------------------------------------------------")

        print("[1/5] Initializing SD card...")
        sd = sdioio.SDCard(
            clock=board.SDIO_CLK,
            command=board.SDIO_CMD,
            data=[board.SDIO_D0],
            frequency=freq_hz,
        )
        result["actual_raw"] = getattr(sd, "frequency", freq_hz)
        result["actual_hz"] = normalize_frequency_hz(result["actual_raw"])
        print(
            "  OK: SDCard initialized (actual {:.2f} MHz, raw={})".format(
                result["actual_hz"] / 1_000_000,
                result["actual_raw"],
            )
        )

        print("[2/5] Mounting...")
        vfs = storage.VfsFat(sd)
        storage.mount(vfs, "/sd")
        mounted = True
        print("  OK: mounted /sd")

        _ = os.listdir("/sd")

        print("[3/5] WRITE benchmark...")
        gc.collect()
        write_bps, write_time = benchmark_write()
        result["write_bps"] = write_bps
        print("  OK: {} ({:.3f} s)".format(format_speed(write_bps), write_time))

        print("[4/5] READ benchmark (alloc)...")
        gc.collect()
        read_alloc_bps, read_alloc_time = benchmark_read_alloc()
        result["read_alloc_bps"] = read_alloc_bps
        print("  OK: {} ({:.3f} s)".format(format_speed(read_alloc_bps), read_alloc_time))

        print("[5/5] READ benchmark (readinto)...")
        gc.collect()
        read_into_bps, read_into_time = benchmark_read_readinto()
        result["read_into_bps"] = read_into_bps
        print("  OK: {} ({:.3f} s)".format(format_speed(read_into_bps), read_into_time))

    except Exception as exc:
        result["error"] = str(exc)
        print("  FAIL: {}".format(exc))
        import traceback
        traceback.print_exception(type(exc), exc, exc.__traceback__)

    finally:
        if mounted:
            cleanup_file_if_exists()
            try:
                storage.umount("/sd")
                print("  Cleanup: unmounted /sd")
            except Exception as cleanup_exc:
                print("  Cleanup warning (umount): {}".format(cleanup_exc))
        if sd is not None:
            try:
                sd.deinit()
                print("  Cleanup: deinitialized SDCard")
            except Exception as cleanup_exc:
                print("  Cleanup warning (deinit): {}".format(cleanup_exc))

    return result


def print_summary(results):
    print("\n" + "=" * 78)
    print("FREQUENCY SWEEP SUMMARY")
    print("=" * 78)
    print(
        "{:<10} {:<10} {:<16} {:<16} {:<16} {:<8}".format(
            "req_MHz",
            "act_MHz",
            "WRITE",
            "READ(alloc)",
            "READ(readinto)",
            "status",
        )
    )
    print("-" * 78)

    best = None
    for entry in results:
        req_mhz = "{:.0f}".format(entry["requested_hz"] / 1_000_000)
        act_mhz = (
            "{:.2f}".format(entry["actual_hz"] / 1_000_000)
            if entry["actual_hz"] is not None
            else "-"
        )

        if entry["error"] is not None:
            print(
                "{:<10} {:<10} {:<16} {:<16} {:<16} {:<8}".format(
                    req_mhz, act_mhz, "-", "-", "-", "FAIL"
                )
            )
            continue

        write = "{:.2f} KB/s".format(entry["write_bps"] / 1024)
        read_alloc = "{:.2f} KB/s".format(entry["read_alloc_bps"] / 1024)
        read_into = "{:.2f} KB/s".format(entry["read_into_bps"] / 1024)
        print(
            "{:<10} {:<10} {:<16} {:<16} {:<16} {:<8}".format(
                req_mhz, act_mhz, write, read_alloc, read_into, "OK"
            )
        )

        if best is None or entry["read_into_bps"] > best["read_into_bps"]:
            best = entry

    print("=" * 78)

    if best is not None:
        print(
            "BEST READ(readinto): req {} MHz, act {:.2f} MHz, {:.2f} KB/s".format(
                int(best["requested_hz"] / 1_000_000),
                best["actual_hz"] / 1_000_000,
                best["read_into_bps"] / 1024,
            )
        )
    else:
        print("Brak udanych pomiarow.")

    failed = [r for r in results if r["error"] is not None]
    if failed:
        print("\nFAILED FREQUENCIES:")
        for entry in failed:
            print(
                "- {} MHz: {}".format(
                    int(entry["requested_hz"] / 1_000_000), entry["error"]
                )
            )
    print("=" * 78)


print("=" * 78)
print("SDIOIO Frequency Sweep Benchmark (Waveshare ESP32-S3 AMOLED 2.41)")
print("=" * 78)
print("Config:")
print("  Frequencies: {}".format(", ".join(str(int(f / 1_000_000)) + "MHz" for f in FREQUENCIES)))
print("  Test size  : {}".format(format_bytes(TEST_SIZE)))
print("  Chunk size : {}".format(format_bytes(CHUNK_SIZE)))

all_results = []
for freq in FREQUENCIES:
    gc.collect()
    all_results.append(run_for_frequency(freq))
    time.sleep(0.25)

print_summary(all_results)
