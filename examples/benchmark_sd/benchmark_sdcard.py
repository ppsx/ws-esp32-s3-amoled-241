# Copyright (c) 2025 Przemyslaw Patrick Socha

"""
SD Card Benchmark: sdioio
===========================

This script benchmarks the performance of CircuitPython `sdioio` in 1-bit mode.

Tests performed:
1. Write Speed (64KB chunks)
2. Read Speed (Allocating new buffers)
3. Read Speed (Zero-copy into pre-allocated buffer)

Configuration:
- 40 MHz SDIO Clock (Optimal for Performance)
- 64 KB Transfer/Chunk Size (Optimal for ESP32-S3 DMA)
"""

import board
import sdioio
import storage
import os
import time
import gc
import microcontroller

# Configuration
BAUDRATE = 40_000_000  # 40 MHz
TEST_FILE_SIZE = 4 * 1024 * 1024  # 4 MB file for robust testing
CHUNK_SIZE = 64 * 1024  # 64 KB chunks
FILENAME = "/sd/benchmark.bin"

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def run_benchmark(name, mount_func):
    print(f"\n{'='*60}")
    print(f"BENCHMARKING: {name}")
    print(f"{'='*60}")
    
    try:
        # Initialize and Mount
        vfs = mount_func()
        storage.mount(vfs, "/sd")
        print("Mounted successfully.")
    except Exception as e:
        print(f"Failed to mount {name}: {e}")
        return None

    results = {}
    
    try:
        # 1. WRITE TEST
        print(f"\n[Test 1] Writing {format_bytes(TEST_FILE_SIZE)} file...")
        buffer = bytearray(CHUNK_SIZE) # Empty buffer just for writing
        # Fill with some pattern
        for i in range(len(buffer)):
            buffer[i] = i % 255
            
        gc.collect()
        start = time.monotonic()
        with open(FILENAME, "wb") as f:
            written = 0
            while written < TEST_FILE_SIZE:
                c = f.write(buffer)
                written += c
        end = time.monotonic()
        
        duration = end - start
        speed = TEST_FILE_SIZE / duration
        print(f"  Time: {duration:.3f} s")
        print(f"  Speed: {format_bytes(speed)}/s")
        results['write'] = speed

        # 2. READ TEST (Allocation)
        print(f"\n[Test 2] Reading (Standard .read(), allocating buffers)...")
        gc.collect()
        start = time.monotonic()
        with open(FILENAME, "rb") as f:
            while True:
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
        end = time.monotonic()
        
        duration = end - start
        speed = TEST_FILE_SIZE / duration
        print(f"  Time: {duration:.3f} s")
        print(f"  Speed: {format_bytes(speed)}/s")
        results['read_alloc'] = speed

        # 3. READ TEST (Zero-Copy)
        print(f"\n[Test 3] Reading (Zero-copy .readinto(), pre-allocated)...")
        read_buf = bytearray(CHUNK_SIZE)
        gc.collect()
        start = time.monotonic()
        with open(FILENAME, "rb") as f:
            while True:
                n = f.readinto(read_buf)
                if not n:
                    break
        end = time.monotonic()
        
        duration = end - start
        speed = TEST_FILE_SIZE / duration
        print(f"  Time: {duration:.3f} s")
        print(f"  Speed: {format_bytes(speed)}/s")
        results['read_zerocopy'] = speed

        # Cleanup
        os.remove(FILENAME)
        
    except Exception as e:
        print(f"Error during benchmark: {e}")
    finally:
        storage.umount("/sd")
        if hasattr(vfs, 'deinit'):
            vfs.deinit()
        pass

    return results

# Wrappers for initialization
# Global holders to prevent GC init issues during function return
sd_obj = None

def mount_sdioio():
    global sd_obj
    print(f"Initializing sdioio with frequency={BAUDRATE}...")
    sd_obj = sdioio.SDCard(
        clock=board.SDIO_CLK,
        command=board.SDIO_CMD,
        data=[board.SDIO_D0],
        frequency=BAUDRATE,
    )
    return storage.VfsFat(sd_obj)

def cleanup_sdioio():
    global sd_obj
    if sd_obj:
        sd_obj.deinit()
    sd_obj = None
    gc.collect()

# Main Execution
print("\n" + "="*60)
print("SD CARD PERFORMANCE BENCHMARK")
print(f"Clock: {BAUDRATE/1000000:.1f} MHz | File Size: {format_bytes(TEST_FILE_SIZE)}")
print("="*60)

# Run sdioio benchmark
cleanup_sdioio() # Pre-clean
res_sd = run_benchmark("sdioio", mount_sdioio)
cleanup_sdioio()

# Results Summary
print("\n" + "="*60)
print("RESULTS SUMMARY")
print("="*60)
print(f"{'Operation':<20} | {'sdioio':<15}")
print("-" * 40)

ops = [('Write', 'write'), ('Read (Alloc)', 'read_alloc'), ('Read (ZeroCopy)', 'read_zerocopy')]

for label, key in ops:
    val_sd = res_sd.get(key, 0) if res_sd else 0
    str_sd = format_bytes(val_sd) + "/s" if val_sd else "N/A"
    print(f"{label:<20} | {str_sd:<15}")

print("="*60)
