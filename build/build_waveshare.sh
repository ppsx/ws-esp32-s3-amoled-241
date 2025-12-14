#!/bin/bash

# Build script for Waveshare ESP32-S3 Touch AMOLED 2.41 CircuitPython port
# This script builds the CircuitPython firmware for the board

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Board configuration
BOARD_NAME="waveshare_esp32_s3_amoled_241"
PORT_DIR="ports/espressif"
BUILD_DIR="${PORT_DIR}/build-${BOARD_NAME}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[BUILD]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if we're in the CircuitPython root directory
    if [ ! -f "main.c" ] || [ ! -d "ports" ]; then
        print_error "This script must be run from the CircuitPython root directory"
        exit 1
    fi

    # Check for ESP-IDF
    if [ -z "$IDF_PATH" ]; then
        print_warning "IDF_PATH not set. Attempting to install and source ESP-IDF..."
        if [ -f "ports/espressif/esp-idf/install.sh" ] && [ -z "${IDF_PATH}" ]; then
            ports/espressif/esp-idf/install.sh
        fi
        if [ -f "ports/espressif/esp-idf/export.sh" ] && [ -z "${IDF_PATH}" ]; then
            source ports/espressif/esp-idf/export.sh
        else
            print_error "ESP-IDF not found. Please install ESP-IDF and set IDF_PATH"
            echo "Visit: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/"
            exit 1
        fi
    fi

    # Check for required tools
    command -v python3 >/dev/null 2>&1 || { print_error "python3 is required but not installed."; exit 1; }
    command -v make >/dev/null 2>&1 || { print_error "make is required but not installed."; exit 1; }
    command -v git >/dev/null 2>&1 || { print_error "git is required but not installed."; exit 1; }

    print_status "Prerequisites check passed"
}

# Function to update submodules
update_submodules() {
    print_status "Updating git submodules..."
    git submodule update --init --recursive
    print_status "Submodules updated"
}

# Function to fetch port dependencies
fetch_port_deps() {
    print_status "Fetching port dependencies..."
    cd ${PORT_DIR}

    # Fetch ESP-IDF specific dependencies
    if [ ! -d "esp-idf" ]; then
        print_status "Fetching ESP-IDF components..."
        make fetch-port-submodules
    fi

    cd ../..
    print_status "Port dependencies fetched"
}

# Function to build mpy-cross
build_mpy_cross() {
    print_status "Building mpy-cross..."
    make -C mpy-cross -j$(nproc)
    print_status "mpy-cross built successfully"
}

# Function to clean QSTR
clean_qstr() {
    print_status "Cleaning QSTR generated headers for ${BOARD_NAME} board..."
    # Remove generated header files that contain QSTR definitions
    if [ -d "${BUILD_DIR}/genhdr" ]; then
        print_status "Removing generated headers in ${BUILD_DIR}/genhdr/"
        rm -rf ${BUILD_DIR}/genhdr/
        print_status "Generated headers removed."
    else
        print_status "No generated headers found to clean."
    fi

    # Also remove the qstr preprocessed files
    if [ -d "${BUILD_DIR}" ]; then
        print_status "Removing QSTR intermediate files..."
        find ${BUILD_DIR} -name "*.pp" -delete 2>/dev/null || true
        find ${BUILD_DIR} -name "qstr*.txt" -delete 2>/dev/null || true
        find ${BUILD_DIR} -name "qstr*.h" -delete 2>/dev/null || true
        print_status "QSTR intermediate files removed."
    fi
    print_status "QSTR cleaning completed"
}

# Function to clean build
clean_build() {
    print_status "Cleaning previous build..."
    cd ${PORT_DIR}
    make BOARD=${BOARD_NAME} clean
    cd ../..
    print_status "Build cleaned"
}

# Function to build the board
build_board() {
    print_status "Building ${BOARD_NAME}..."
    cd ${PORT_DIR}

    # Set build variables
    export BOARD=${BOARD_NAME}

    # Build with parallel jobs
    make BOARD=${BOARD_NAME} -j$(nproc)

    cd ../..
    print_status "Build completed successfully!"
}

# Function to show build output
show_output() {
    print_status "Build output location:"
    echo "  Firmware: ${BUILD_DIR}/firmware.bin"
    echo "  Bootloader: ${BUILD_DIR}/bootloader/bootloader.bin"
    echo "  Partition table: ${BUILD_DIR}/partition_table/partition-table.bin"
    echo ""
    print_status "Combined UF2 file:"
    echo "  ${BUILD_DIR}/firmware.uf2"
}

# Function to flash the board
flash_board() {
    print_status "Flashing board..."
    cd ${PORT_DIR}

    # Detect port
    PORT=$(ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null | head -n1)
    if [ -z "$PORT" ]; then
        print_error "No USB serial port detected. Please connect the board."
        exit 1
    fi

    print_status "Using port: $PORT"
    make BOARD=${BOARD_NAME} flash PORT=${PORT}
    cd ../..
    print_status "Board flashed successfully!"
}

# Function to monitor serial output
monitor_serial() {
    print_status "Opening serial monitor..."

    # Detect port
    PORT=$(ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null | head -n1)
    if [ -z "$PORT" ]; then
        print_error "No USB serial port detected. Please connect the board."
        exit 1
    fi

    print_status "Monitoring $PORT (Ctrl+A then K to exit)"
    screen $PORT 115200
}

# Main script
main() {
    echo "======================================"
    echo "Waveshare ESP32-S3 Touch AMOLED 2.41"
    echo "CircuitPython Build Script"
    echo "======================================"
    echo ""

    # Parse command line arguments
    case "${1:-build}" in
        prerequisites|prereq)
            check_prerequisites
            ;;
        submodules|subs)
            update_submodules
            ;;
        fetch)
            fetch_port_deps
            ;;
        mpy-cross|mpy)
            build_mpy_cross
            ;;
        clean)
            check_prerequisites
            clean_build
            ;;
        clean_qstr)
            check_prerequisites
            clean_qstr
            ;;
        build)
            check_prerequisites
            build_mpy_cross
            build_board
            show_output
            ;;
        rebuild)
            check_prerequisites
            clean_build
            build_board
            show_output
            ;;
        full)
            check_prerequisites
            update_submodules
            fetch_port_deps
            build_mpy_cross
            clean_build
            build_board
            show_output
            ;;
        flash|deploy)
            check_prerequisites
            flash_board
            ;;
        build-flash|bf)
            check_prerequisites
            build_mpy_cross
            build_board
            show_output
            flash_board
            ;;
        monitor|serial)
            monitor_serial
            ;;
        help|--help|-h)
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  build         - Build the firmware (default)"
            echo "  rebuild       - Clean and build"
            echo "  full          - Full build with all dependencies"
            echo "  clean         - Clean build artifacts"
            echo "  clean_qstr    - Clean qstr artifacts"
            echo "  flash         - Flash firmware to board"
            echo "  build-flash   - Build and flash"
            echo "  monitor       - Open serial monitor"
            echo "  prerequisites - Check build prerequisites"
            echo "  submodules    - Update git submodules"
            echo "  fetch         - Fetch port dependencies"
            echo "  mpy-cross     - Build mpy-cross only"
            echo "  help          - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0              # Build firmware"
            echo "  $0 clean        # Clean build"
            echo "  $0 build-flash  # Build and flash"
            echo "  $0 monitor      # Open serial monitor"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
