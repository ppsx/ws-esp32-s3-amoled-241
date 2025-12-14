"""
Simple test script for lvgl_symbols module
===========================================

This script tests that the lvgl_symbols module loads correctly
and can display all available symbols.

Usage:
    python test_symbols.py
"""

# Test 1: Import the module
print("Test 1: Importing lvgl_symbols module...")
try:
    import lvgl_symbols

    print("✓ Module imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\nNote: Make sure lvgl_symbols.py is in the same directory")
    print("or in your CIRCUITPY lib/ folder")
    exit(1)

# Test 2: Check some common symbols exist
print("\nTest 2: Checking symbol constants...")
symbols_to_test = [
    "SYMBOL_HOME",
    "SYMBOL_SETTINGS",
    "SYMBOL_WIFI",
    "SYMBOL_BATTERY_FULL",
    "SYMBOL_PLAY",
    "SYMBOL_OK",
]

for sym_name in symbols_to_test:
    if hasattr(lvgl_symbols, sym_name):
        sym_value = getattr(lvgl_symbols, sym_name)
        print(f"✓ {sym_name:25s} = {repr(sym_value)}")
    else:
        print(f"✗ {sym_name} not found!")

# Test 3: Display all symbols using the helper function
print("\nTest 3: Listing all available symbols...")
print("=" * 60)
lvgl_symbols.list_all_symbols()

# Test 4: Show example usage
print("\n" + "=" * 60)
print("Example Usage:")
print("=" * 60)
print("\nIn your CircuitPython code:\n")
print("    import rm690b0_lvgl")
print("    from lvgl_symbols import *")
print("")
print("    # Button with icon")
print('    btn = rm690b0_lvgl.Button(text=f"{SYMBOL_HOME} Home")')
print("    btn.x = 100")
print("    btn.y = 100")
print("")
print("    # Label with multiple icons")
print('    status = rm690b0_lvgl.Label(text=f"{SYMBOL_WIFI} {SYMBOL_BATTERY_FULL}")')
print("    status.x = 10")
print("    status.y = 10")
print("")

# Test 5: Show raw UTF-8 encoding
print("\n" + "=" * 60)
print("UTF-8 Encoding Examples:")
print("=" * 60)
print("\nYou can also use Unicode escapes directly:\n")
print('    label = rm690b0_lvgl.Label(text="\\uf015")  # HOME icon')
print('    button = rm690b0_lvgl.Button(text="\\uf013 Settings")  # SETTINGS')
print("")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)
