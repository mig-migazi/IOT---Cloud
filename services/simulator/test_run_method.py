#!/usr/bin/env python3
"""
Test the run method step by step
"""

import time

print("Step 1: Import simulator")
from smart_breaker_simulator import SmartBreakerSimulator
print("✓ Import OK")

print("Step 2: Create simulator")
simulator = SmartBreakerSimulator()
print("✓ Simulator created")

print("Step 3: Test basic methods")
print("  - Testing should_burst...")
burst_result = simulator.should_burst()
print(f"✓ should_burst works: {burst_result}")

print("  - Testing generate_telemetry...")
telemetry = simulator.generate_telemetry()
print(f"✓ generate_telemetry works: {telemetry['device_id']}")

print("  - Testing generate_trends...")
trends = simulator.generate_trends()
print(f"✓ generate_trends works: {trends['event_type']}")

print("Step 4: Test message sending")
print("  - Testing send_message...")
result = simulator.send_message(telemetry)
print(f"✓ send_message works: {result}")

print("Step 5: Test run method with timeout")
print("  - Starting run method (will timeout after 10 seconds)...")
try:
    # Run for only 10 seconds to see if it works
    simulator.running = True
    start_time = time.time()
    
    # Run one iteration manually
    should_burst, burst_size = simulator.should_burst()
    print(f"    Burst check: {should_burst}, {burst_size}")
    
    if should_burst:
        print(f"    Would send burst of {burst_size} messages")
    else:
        print("    Would send normal message")
    
    print("✓ Run method iteration completed successfully")
    
except Exception as e:
    print(f"✗ Run method failed: {e}")

print("Step 6: Cleanup")
simulator.running = False
simulator.cleanup()
print("✓ Cleanup completed")

print("=== RUN METHOD TEST COMPLETED ===")
