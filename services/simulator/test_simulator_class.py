#!/usr/bin/env python3
"""
Test the main simulator class constructor
"""

import sys
import time

print("Step 1: Import main simulator")
from smart_breaker_simulator import SmartBreakerSimulator, BreakerConfig
print("✓ Main simulator imported")

print("Step 2: Create config")
config = BreakerConfig(device_id="breaker-001")
print("✓ Config created")

print("Step 3: Create simulator instance")
simulator = SmartBreakerSimulator(config)
print("✓ Simulator instance created")

print("Step 4: Check simulator attributes")
print(f"  - device_id: {simulator.config.device_id}")
print(f"  - running: {simulator.running}")
print(f"  - kafka_connected: {simulator.kafka_connected}")
print("✓ Attributes checked")

print("Step 5: Test basic methods")
print("  - Testing generate_telemetry...")
try:
    telemetry = simulator.generate_telemetry()
    print("✓ generate_telemetry works")
except Exception as e:
    print(f"✗ generate_telemetry failed: {e}")

print("Step 6: Cleanup")
simulator.stop()
print("✓ Simulator stopped")

print("=== SIMULATOR CLASS TEST COMPLETED ===")
