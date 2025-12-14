"""
ESP-NOW Test Script
===================

Simple test to verify ESP-NOW functionality on the ESP32-S3 board.

This script demonstrates:
1. Initializing ESP-NOW
2. Getting your device's MAC address
3. Sending and receiving messages

Hardware: Waveshare ESP32-S3-Touch-AMOLED-2.41
Module: espnow
Author: CircuitPython Community
License: MIT
"""

import time

import espnow
import wifi

print("=" * 60)
print("ESP-NOW Test Script")
print("=" * 60)
print()

# Step 1: Initialize ESP-NOW
print("Step 1: Initializing ESP-NOW...")
try:
    e = espnow.ESPNow()
    print("✅ ESP-NOW initialized successfully!")
except Exception as ex:
    print(f"❌ Failed to initialize ESP-NOW: {ex}")
    raise

# Step 2: Get MAC address
print("\nStep 2: Getting MAC address...")
try:
    mac = wifi.radio.mac_address
    mac_str = ":".join([f"{b:02X}" for b in mac])
    print(f"✅ Your MAC address: {mac_str}")
    print(f"   (Use this address on other devices to communicate with this one)")
except Exception as ex:
    print(f"❌ Failed to get MAC address: {ex}")

# Step 3: Check for peers
print("\nStep 3: Checking peers...")
peer_count = len(e.peers)
print(f"   Current peers: {peer_count}")

if peer_count == 0:
    print("\n⚠️  No peers configured yet.")
    print("   To add a peer, use:")
    print("   >>> peer = espnow.Peer(mac=b'\\xAA\\xBB\\xCC\\xDD\\xEE\\xFF')")
    print("   >>> e.peers.append(peer)")

# Step 4: Test receiving (non-blocking)
print("\nStep 4: Checking for messages...")
print("   Listening for 5 seconds...")

received_any = False
for i in range(5):
    if e:  # Check if data available
        packet = e.read()
        if packet:
            received_any = True
            sender_mac = ":".join([f"{b:02X}" for b in packet.mac])
            print(f"   ✅ Received from {sender_mac}:")
            print(f"      Message: {packet.msg}")
            print(f"      RSSI: {packet.rssi} dBm")

    time.sleep(1)
    if (i + 1) % 5 == 0:
        print(f"   ... {i + 1} seconds")

if not received_any:
    print("   No messages received (this is normal if no other device is sending)")

# Step 5: Test sending (if peers exist)
print("\nStep 5: Testing send...")
if peer_count > 0:
    try:
        message = f"Hello from ESP32-S3 at {time.monotonic()}"
        e.send(message)
        print(f"✅ Sent: '{message}'")
    except Exception as ex:
        print(f"❌ Failed to send: {ex}")
else:
    print("   Skipped (no peers configured)")

# Summary
print("\n" + "=" * 60)
print("ESP-NOW Test Summary")
print("=" * 60)
print(f"✅ ESP-NOW module: Working")
print(f"✅ MAC address: {mac_str}")
print(f"📡 Peers: {peer_count}")
print(f"📨 Messages received: {'Yes' if received_any else 'No'}")

# Example usage
print("\n" + "=" * 60)
print("Next Steps - Two Device Communication")
print("=" * 60)
print("""
To communicate between two ESP32-S3 boards:

DEVICE 1 (Sender):
------------------
import espnow
e = espnow.ESPNow()
peer = espnow.Peer(mac=b'\\xAA\\xBB\\xCC\\xDD\\xEE\\xFF')  # MAC of Device 2
e.peers.append(peer)
e.send("Hello Device 2!")

DEVICE 2 (Receiver):
--------------------
import espnow
e = espnow.ESPNow()
while True:
    if e:
        packet = e.read()
        if packet:
            print(f"Received: {packet.msg}")

TWO-WAY:
--------
Both devices add each other as peers, then both can send() and read()

BROADCAST:
----------
Use broadcast MAC: b'\\xFF\\xFF\\xFF\\xFF\\xFF\\xFF'
All nearby ESP-NOW devices will receive (no need to add as peer)
""")

print("Test complete! ✅")
