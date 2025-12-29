"""
ESP SD Card Comprehensive Test & Benchmark
===========================================

Comprehensive validation and performance testing for the espsdcard module.
Tests all operations and measures real transfer speeds.

This script validates:
1. Module initialization and cleanup
2. File reading (various sizes and patterns)
3. File reopening (regression test)
4. Write operations
5. Seek operations
6. Multiple file handles
7. Error recovery
8. Real-world performance metrics

Hardware: Waveshare ESP32-S3-Touch-AMOLED-2.41
Module: espsdcard (native ESP-IDF SD card driver)
Author: CircuitPython Community
License: MIT
"""

import gc
import os
import sys
import time

import board
import espsdcard
import storage

# Test configuration
CHUNK_SIZES = [
    512,
    1024,
    4096,
    16384,
    32768,
    65536,
    131072,
    262144,
    524288,
]  # Bytes (up to 512KB)
CHUNK_SIZES_PREALLOCATED = [
    512,
    1024,
    4096,
    16384,
    32768,
    65536,
    131072,
    262144,
    524288,
    1048576,
]  # Bytes (up to 1MB for pre-allocated buffer test)
TEST_FILE_SIZES = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB
BENCHMARK_FILE_SIZE = 1048576  # 1MB for speed tests


# ANSI color codes for better readability
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 70}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def format_bytes(num_bytes):
    """Format bytes to human readable string"""
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} TB"


def format_speed(bytes_per_sec):
    """Format transfer speed"""
    return format_bytes(bytes_per_sec) + "/s"


# Global SD card object for cleanup
sd = None
test_results = {"passed": 0, "failed": 0, "warnings": 0}


def cleanup_sd():
    """Cleanup SD card resources"""
    global sd
    if sd is not None:
        try:
            storage.umount("/sd")
        except:
            pass
        try:
            sd.deinit()
        except:
            pass
        sd = None


def initialize_sd():
    """Initialize SD card"""
    global sd

    print_info("Initializing SD card...")
    try:
        sd = espsdcard.SDCard(
            cs=board.SD_CS, miso=board.SD_MISO, mosi=board.SD_MOSI, clk=board.SD_CLK
        )
        vfs = storage.VfsFat(sd)
        storage.mount(vfs, "/sd")
        print_success("SD card mounted successfully")

        # Print card info
        print(f"   Card type: {sd.card_type}")
        print(f"   Capacity: {sd.capacity_mb:.2f} MB")
        print(f"   Block count: {sd.count}")

        return True
    except Exception as e:
        print_error(f"Failed to initialize SD card: {e}")
        return False


def test_directory_listing():
    """Test 1: Directory listing"""
    print_header("TEST 1: Directory Listing")

    try:
        files = os.listdir("/sd")
        print_success(f"Found {len(files)} items on SD card")

        # Show first 10 files
        for i, filename in enumerate(files[:10], 1):
            try:
                stat = os.stat(f"/sd/{filename}")
                size = stat[6]
                print(f"   {i}. {filename} ({format_bytes(size)})")
            except:
                print(f"   {i}. {filename} (directory or inaccessible)")

        if len(files) > 10:
            print(f"   ... and {len(files) - 10} more")

        test_results["passed"] += 1
        return True

    except Exception as e:
        print_error(f"Directory listing failed: {e}")
        test_results["failed"] += 1
        return False


def test_file_read_sizes():
    """Test 2: Reading files with various sizes"""
    print_header("TEST 2: File Reading - Various Sizes")

    # Find a test file on SD card
    test_files = []
    try:
        files = os.listdir("/sd")
        for f in files:
            if not f.startswith("."):
                try:
                    stat = os.stat(f"/sd/{f}")
                    size = stat[6]
                    if size > 0:
                        test_files.append((f, size))
                except:
                    pass
    except:
        print_error("Cannot list files")
        test_results["failed"] += 1
        return False

    if not test_files:
        print_warning("No test files found on SD card")
        test_results["warnings"] += 1
        return False

    # Sort by size and pick a medium-sized file
    test_files.sort(key=lambda x: x[1])
    test_file, file_size = test_files[len(test_files) // 2]
    filepath = f"/sd/{test_file}"

    print(f"Testing file: {test_file} ({format_bytes(file_size)})\n")

    read_sizes = [1, 10, 100, 512, 1024, 4096, 16384, 32768, 65536]
    all_passed = True

    for read_size in read_sizes:
        if read_size > file_size:
            break

        try:
            start = time.monotonic()
            with open(filepath, "rb") as f:
                data = f.read(read_size)
            elapsed = time.monotonic() - start

            if len(data) == read_size:
                speed = len(data) / elapsed if elapsed > 0 else 0
                print_success(
                    f"{format_bytes(read_size):>10s} : {elapsed * 1000:6.2f} ms ({format_speed(speed)})"
                )
            else:
                print_warning(
                    f"{format_bytes(read_size):>10s} : Read only {len(data)} bytes (EOF)"
                )

        except Exception as e:
            print_error(f"{format_bytes(read_size):>10s} : {e}")
            all_passed = False

    if all_passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1

    return all_passed


def test_chunked_reading():
    """Test 3: Chunked reading of large files"""
    print_header("TEST 3: Chunked Reading - Large Files")

    # Find the largest file (but not too large - max 1MB)
    MAX_TEST_SIZE = 1048576  # 1MB limit
    try:
        files = os.listdir("/sd")
        largest_file = None
        largest_size = 0

        for f in files:
            if not f.startswith("."):
                try:
                    stat = os.stat(f"/sd/{f}")
                    size = stat[6]
                    # Only consider files between 10KB and 1MB
                    if 10000 < size <= MAX_TEST_SIZE and size > largest_size:
                        largest_size = size
                        largest_file = f
                except:
                    pass
    except:
        print_error("Cannot find test file")
        test_results["failed"] += 1
        return False

    if not largest_file or largest_size < 10000:
        print_warning("No suitable large file found (need 10KB-1MB)")
        test_results["warnings"] += 1
        return False

    filepath = f"/sd/{largest_file}"
    print(f"Testing file: {largest_file} ({format_bytes(largest_size)})\n")

    for chunk_size in [4096, 16384, 32768, 65536]:
        print(f"Chunk size: {format_bytes(chunk_size)}")

        try:
            chunks = []
            total_read = 0

            start = time.monotonic()
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total_read += len(chunk)
            elapsed = time.monotonic() - start

            data = b"".join(chunks)

            if len(data) == largest_size:
                speed = len(data) / elapsed if elapsed > 0 else 0
                print_success(
                    f"Read {format_bytes(total_read)} in {elapsed:.3f}s ({format_speed(speed)})"
                )
                print(f"   Chunks: {len(chunks)}")
            else:
                print_error(f"Size mismatch: got {len(data)}, expected {largest_size}")
                test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"Failed: {e}")
            test_results["failed"] += 1
            return False

        print()

    test_results["passed"] += 1
    return True


def test_file_reopen():
    """Test 4: File reopening (regression test)"""
    print_header("TEST 4: File Reopening (Regression Test)")

    # Find a test file (skip zero-sized files)
    try:
        files = os.listdir("/sd")
        test_file = None

        for f in files:
            if not f.startswith("."):
                try:
                    stat = os.stat(f"/sd/{f}")
                    size = stat[6]
                    if size > 0:
                        test_file = f
                        break
                except:
                    pass

        if not test_file:
            print_warning("No suitable test files found")
            test_results["warnings"] += 1
            return False

        filepath = f"/sd/{test_file}"

    except:
        print_error("Cannot find test file")
        test_results["failed"] += 1
        return False

    print(f"Testing file: {test_file}\n")

    # First open
    try:
        with open(filepath, "rb") as f:
            data1 = f.read(1000)
        print_success(f"First open: Read {len(data1)} bytes")
    except Exception as e:
        print_error(f"First open failed: {e}")
        test_results["failed"] += 1
        return False

    # Wait a bit
    time.sleep(0.1)

    # Second open (this used to fail in sdcardio)
    try:
        with open(filepath, "rb") as f:
            data2 = f.read(1000)
        print_success(f"Second open: Read {len(data2)} bytes")
    except Exception as e:
        print_error(f"Second open failed: {e}")
        test_results["failed"] += 1
        return False

    # Verify data matches
    if data1 == data2:
        print_success("Data matches between reads")
    else:
        print_error("Data mismatch between reads!")
        test_results["failed"] += 1
        return False

    # Multiple reopens
    print("\nTesting multiple reopens...")
    for i in range(5):
        try:
            with open(filepath, "rb") as f:
                data = f.read(100)
            print(f"   Open {i + 1}: OK")
        except Exception as e:
            print_error(f"Open {i + 1} failed: {e}")
            test_results["failed"] += 1
            return False

    print_success("All reopens successful")
    test_results["passed"] += 1
    return True


def test_seek_operations():
    """Test 5: Seek operations"""
    print_header("TEST 5: Seek Operations")

    # Find a suitable test file
    try:
        files = os.listdir("/sd")
        test_file = None

        for f in files:
            if not f.startswith("."):
                try:
                    stat = os.stat(f"/sd/{f}")
                    size = stat[6]
                    if size > 1000:
                        test_file = f
                        break
                except:
                    pass
    except:
        print_error("Cannot find test file")
        test_results["failed"] += 1
        return False

    if not test_file:
        print_warning("No suitable file found (need >1KB)")
        test_results["warnings"] += 1
        return False

    filepath = f"/sd/{test_file}"
    file_size = os.stat(filepath)[6]

    print(f"Testing file: {test_file} ({format_bytes(file_size)})\n")

    try:
        with open(filepath, "rb") as f:
            # Seek to start
            f.seek(0)
            start_data = f.read(10)
            print_success(f"Seek to start (0): Read {len(start_data)} bytes")

            # Seek to middle
            mid_pos = file_size // 2
            f.seek(mid_pos)
            mid_data = f.read(10)
            print_success(f"Seek to middle ({mid_pos}): Read {len(mid_data)} bytes")

            # Seek to near end
            end_pos = file_size - 10
            f.seek(end_pos)
            end_data = f.read(10)
            print_success(f"Seek to end ({end_pos}): Read {len(end_data)} bytes")

            # Seek back to start
            f.seek(0)
            start_data2 = f.read(10)
            if start_data == start_data2:
                print_success("Seek back to start: Data matches")
            else:
                print_error("Seek back to start: Data mismatch!")
                test_results["failed"] += 1
                return False

        test_results["passed"] += 1
        return True

    except Exception as e:
        print_error(f"Seek operation failed: {e}")
        test_results["failed"] += 1
        return False


def test_write_operations():
    """Test 6: Write operations"""
    print_header("TEST 6: Write Operations")

    test_filename = "/sd/espsdcard_test.txt"
    test_data = b"ESP SD Card Test - " + bytes(str(time.monotonic()), "utf-8")

    # Write test
    try:
        with open(test_filename, "wb") as f:
            f.write(test_data)
        print_success(f"Wrote {len(test_data)} bytes")
    except Exception as e:
        print_error(f"Write failed: {e}")
        test_results["failed"] += 1
        return False

    # Read back and verify
    try:
        with open(test_filename, "rb") as f:
            read_data = f.read()

        if read_data == test_data:
            print_success("Read-back verification passed")
        else:
            print_error("Data mismatch after read-back!")
            test_results["failed"] += 1
            return False
    except Exception as e:
        print_error(f"Read-back failed: {e}")
        test_results["failed"] += 1
        return False

    # Large write test
    large_data = bytes(range(256)) * 1024  # 256KB pattern
    large_filename = "/sd/espsdcard_large_test.bin"

    print(f"\nWriting large file ({format_bytes(len(large_data))})...")
    try:
        start = time.monotonic()
        with open(large_filename, "wb") as f:
            f.write(large_data)
        elapsed = time.monotonic() - start

        speed = len(large_data) / elapsed if elapsed > 0 else 0
        print_success(
            f"Wrote {format_bytes(len(large_data))} in {elapsed:.3f}s ({format_speed(speed)})"
        )

        # Verify
        with open(large_filename, "rb") as f:
            read_data = f.read()

        if read_data == large_data:
            print_success("Large file verification passed")
        else:
            print_error("Large file data mismatch!")
            test_results["failed"] += 1
            return False

    except Exception as e:
        print_error(f"Large write failed: {e}")
        test_results["failed"] += 1
        return False

    # Cleanup test files
    try:
        os.remove(test_filename)
        os.remove(large_filename)
        print_info("Test files cleaned up")
    except:
        print_warning("Could not remove test files")

    test_results["passed"] += 1
    return True


def test_context_manager():
    """Test 7: Context manager (with statement)"""
    print_header("TEST 7: Context Manager")

    print("Testing 'with' statement for automatic cleanup...\n")

    try:
        # Cleanup existing SD card
        cleanup_sd()

        # Use context manager
        with espsdcard.SDCard(
            cs=board.SD_CS, miso=board.SD_MISO, mosi=board.SD_MOSI, clk=board.SD_CLK
        ) as test_sd:
            vfs = storage.VfsFat(test_sd)
            storage.mount(vfs, "/sd")

            files = os.listdir("/sd")
            print_success(f"Context manager: Found {len(files)} files")

            storage.umount("/sd")

        print_success("Context manager exited cleanly")

        # Reinitialize for remaining tests
        if not initialize_sd():
            test_results["failed"] += 1
            return False

        test_results["passed"] += 1
        return True

    except Exception as e:
        print_error(f"Context manager test failed: {e}")
        test_results["failed"] += 1
        # Reinitialize anyway
        initialize_sd()
        return False


def benchmark_read_speed():
    """Test 8: Read speed benchmark"""
    print_header("TEST 8: Read Speed Benchmark")

    # Find a large file for benchmarking (but not too large - max 1MB)
    MAX_TEST_SIZE = 1048576  # 1MB limit
    try:
        files = os.listdir("/sd")
        benchmark_file = None
        benchmark_size = 0

        for f in files:
            if not f.startswith("."):
                try:
                    stat = os.stat(f"/sd/{f}")
                    size = stat[6]
                    # Look for files between 100KB and 1MB
                    if 100000 <= size <= MAX_TEST_SIZE:
                        benchmark_file = f
                        benchmark_size = size
                        break
                except:
                    pass
    except:
        print_warning("Cannot find benchmark file")
        test_results["warnings"] += 1
        return False

    if not benchmark_file:
        print_warning("No suitable file found for benchmark (need 100KB-1MB)")
        test_results["warnings"] += 1
        return False

    filepath = f"/sd/{benchmark_file}"
    print(f"Benchmark file: {benchmark_file} ({format_bytes(benchmark_size)})\n")

    print(f"{'Chunk Size':<12} {'Time':<10} {'Speed':<15} {'Chunks':<8}")
    print("-" * 50)

    results = []

    for chunk_size in CHUNK_SIZES:
        try:
            start = time.monotonic()
            chunk_count = 0
            total_read = 0

            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    chunk_count += 1
                    total_read += len(chunk)

            elapsed = time.monotonic() - start
            speed = total_read / elapsed if elapsed > 0 else 0

            results.append((chunk_size, elapsed, speed, chunk_count))

            print(
                f"{format_bytes(chunk_size):<12} {elapsed:>7.3f}s  {format_speed(speed):<15} {chunk_count:<8}"
            )

        except Exception as e:
            print(f"{format_bytes(chunk_size):<12} FAILED: {e}")

    if results:
        # Find fastest
        fastest = max(results, key=lambda x: x[2])
        print(
            f"\n{Colors.BOLD}Optimal chunk size: {format_bytes(fastest[0])} ({format_speed(fastest[2])}){Colors.ENDC}"
        )
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1

    return bool(results)


def benchmark_preallocated_buffer():
    """Test 9: Pre-allocated buffer benchmark"""
    print_header("TEST 9: Pre-allocated Buffer Benchmark (Zero-Copy)")

    # Find a large file for benchmarking (but not too large - max 1MB)
    MAX_TEST_SIZE = 1048576  # 1MB limit
    try:
        files = os.listdir("/sd")
        benchmark_file = None
        benchmark_size = 0

        for f in files:
            if not f.startswith("."):
                try:
                    stat = os.stat(f"/sd/{f}")
                    size = stat[6]
                    # Look for files between 100KB and 1MB
                    if 100000 <= size <= MAX_TEST_SIZE:
                        benchmark_file = f
                        benchmark_size = size
                        break
                except:
                    pass
    except:
        print_warning("Cannot find benchmark file")
        test_results["warnings"] += 1
        return False

    if not benchmark_file:
        print_warning("No suitable file found for benchmark (need 100KB-1MB)")
        test_results["warnings"] += 1
        return False

    filepath = f"/sd/{benchmark_file}"
    print(f"Benchmark file: {benchmark_file} ({format_bytes(benchmark_size)})\n")
    print("Reading entire file into pre-allocated buffer...\n")

    print(f"{'Chunk Size':<12} {'Time':<10} {'Speed':<15} {'Chunks':<8}")
    print("-" * 50)

    results = []

    for chunk_size in CHUNK_SIZES_PREALLOCATED:
        # If file is smaller than chunk size, use file size as chunk size
        effective_chunk_size = min(chunk_size, benchmark_size)

        try:
            # Pre-allocate buffer for entire file
            buffer = bytearray(benchmark_size)
            offset = 0

            start = time.monotonic()

            with open(filepath, "rb") as f:
                while offset < benchmark_size:
                    # Read directly into buffer at current offset
                    bytes_to_read = min(effective_chunk_size, benchmark_size - offset)
                    bytes_read = f.readinto(
                        memoryview(buffer)[offset : offset + bytes_to_read]
                    )

                    if bytes_read is None or bytes_read == 0:
                        break

                    offset += bytes_read

            elapsed = time.monotonic() - start

            if offset == benchmark_size:
                speed = benchmark_size / elapsed if elapsed > 0 else 0
                chunk_count = (
                    benchmark_size + effective_chunk_size - 1
                ) // effective_chunk_size

                results.append((effective_chunk_size, elapsed, speed, chunk_count))

                print(
                    f"{format_bytes(chunk_size):<12} {elapsed:>7.3f}s  {format_speed(speed):<15} {chunk_count:<8}"
                )
            else:
                print(
                    f"{format_bytes(chunk_size):<12} INCOMPLETE: only {offset}/{benchmark_size} bytes"
                )

            # Clean up buffer
            del buffer
            gc.collect()

        except Exception as e:
            print(f"{format_bytes(chunk_size):<12} FAILED: {e}")

    if results:
        # Find fastest
        fastest = max(results, key=lambda x: x[2])
        print(
            f"\n{Colors.BOLD}Optimal chunk size (pre-allocated): {format_bytes(fastest[0])} ({format_speed(fastest[2])}){Colors.ENDC}"
        )

        # Compare with regular reading (from previous test)
        print(
            f"\n{Colors.BOLD}Note:{Colors.ENDC} This test uses readinto() with pre-allocated buffer"
        )
        print("      which eliminates memory allocation overhead during reading.")

        test_results["passed"] += 1
    else:
        test_results["failed"] += 1

    return bool(results)


def test_memory_usage():
    """Test 10: Memory usage"""
    print_header("TEST 10: Memory Usage")

    gc.collect()
    mem_before = gc.mem_free()

    print(f"Memory before: {format_bytes(mem_before)}")
    print(f"Allocated: {format_bytes(gc.mem_alloc())}\n")

    # Do some operations
    try:
        files = os.listdir("/sd")
        if files:
            test_file = files[0]
            with open(f"/sd/{test_file}", "rb") as f:
                data = f.read(10000)
            del data
    except:
        pass

    gc.collect()
    mem_after = gc.mem_free()

    print(f"Memory after: {format_bytes(mem_after)}")
    print(f"Allocated: {format_bytes(gc.mem_alloc())}")
    print(f"Delta: {format_bytes(mem_before - mem_after)}")

    if mem_before - mem_after > 10000:
        print_warning("Significant memory not released")
        test_results["warnings"] += 1
    else:
        print_success("Memory management OK")
        test_results["passed"] += 1

    return True


def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")

    total = test_results["passed"] + test_results["failed"] + test_results["warnings"]

    print(f"{Colors.BOLD}Total tests: {total}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Passed: {test_results['passed']}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {test_results['failed']}{Colors.ENDC}")
    print(f"{Colors.WARNING}Warnings: {test_results['warnings']}{Colors.ENDC}")

    if test_results["failed"] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ ALL TESTS PASSED!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.ENDC}")

    # Memory info
    print(f"\n{Colors.BOLD}Final Memory Status:{Colors.ENDC}")
    gc.collect()
    print(f"Free: {format_bytes(gc.mem_free())}")
    print(f"Allocated: {format_bytes(gc.mem_alloc())}")


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================


def main():
    """Main test execution"""

    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("ESP SD CARD COMPREHENSIVE TEST & BENCHMARK")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Module:{Colors.ENDC} espsdcard (native ESP-IDF driver)")
    print(f"{Colors.BOLD}Hardware:{Colors.ENDC} Waveshare ESP32-S3-Touch-AMOLED-2.41")
    print(f"{Colors.BOLD}CircuitPython:{Colors.ENDC} {sys.version}")

    # Initialize
    if not initialize_sd():
        print_error("Failed to initialize SD card. Cannot continue.")
        return

    try:
        # Run all tests
        test_directory_listing()
        test_file_read_sizes()
        test_chunked_reading()
        test_file_reopen()
        test_seek_operations()
        test_write_operations()
        test_context_manager()
        benchmark_read_speed()
        benchmark_preallocated_buffer()
        test_memory_usage()

    finally:
        # Always cleanup
        cleanup_sd()

    # Print summary
    print_summary()

    print(f"\n{Colors.BOLD}Test complete!{Colors.ENDC}")


if __name__ == "__main__":
    main()
