#!/usr/bin/env python3
"""
Debug script to figure out what's wrong with the simulator
"""

import sys
import traceback

print("=== DEBUG SIMULATOR START ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    print("1. Importing json...")
    import json
    print("✓ json imported")
    
    print("2. Importing time...")
    import time
    print("✓ time imported")
    
    print("3. Importing random...")
    import random
    print("✓ random imported")
    
    print("4. Importing datetime...")
    from datetime import datetime
    print("✓ datetime imported")
    
    print("5. Importing kafka...")
    from kafka import KafkaProducer
    print("✓ kafka imported")
    
    print("6. Testing Kafka producer creation...")
    producer = KafkaProducer(
        bootstrap_servers=['redpanda:29092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("✓ Kafka producer created successfully")
    
    print("7. Testing message creation...")
    message = {
        "device_id": "breaker-001",
        "device_type": "smart_breaker",
        "timestamp": datetime.now().isoformat(),
        "event_type": "telemetry",
        "measurements": {
            "voltage": 120.0,
            "current": 50.0
        }
    }
    print(f"✓ Message created: {message}")
    
    print("8. Testing message sending...")
    future = producer.send('iot.raw', value=message)
    print("✓ Message sent to Kafka")
    
    print("9. Waiting for send confirmation...")
    record_metadata = future.get(timeout=10)
    print(f"✓ Message confirmed: topic={record_metadata.topic}, partition={record_metadata.partition}, offset={record_metadata.offset}")
    
    print("10. Closing producer...")
    producer.close()
    print("✓ Producer closed")
    
    print("=== ALL TESTS PASSED ===")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("Full traceback:")
    traceback.print_exc()
    sys.exit(1)
