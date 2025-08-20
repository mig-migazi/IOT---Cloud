#!/usr/bin/env python3
"""
Step-by-step test to find where simulator hangs
"""

import sys
import time

print("Step 1: Basic imports")
import json
import random
from datetime import datetime
print("✓ Basic imports done")

print("Step 2: Kafka imports")
from kafka import KafkaProducer
print("✓ Kafka imports done")

print("Step 3: Create config")
from dataclasses import dataclass

@dataclass
class BreakerConfig:
    device_id: str = "breaker-001"
    rated_current: float = 100.0
    rated_voltage: float = 480.0

config = BreakerConfig()
print("✓ Config created")

print("Step 4: Create breaker state")
class BreakerState:
    def __init__(self, config):
        self.config = config
        self.trends_data = {
            'voltage_phase_a': [],
            'voltage_phase_b': [],
            'voltage_phase_c': [],
            'current_phase_a': [],
            'current_phase_b': [],
            'current_phase_c': [],
            'power_active': [],
            'power_reactive': [],
            'power_apparent': [],
            'frequency': [],
            'temperature': []
        }
        self.last_trends_reset = time.time()
        self.trends_interval = 300

breaker_state = BreakerState(config)
print("✓ Breaker state created")

print("Step 5: Create Kafka producer")
producer = KafkaProducer(
    bootstrap_servers=['redpanda:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
print("✓ Kafka producer created")

print("Step 6: Test message creation")
message = {
    "device_id": "breaker-001",
    "device_type": "smart_breaker",
    "timestamp": datetime.now().isoformat(),
    "event_type": "telemetry",
    "measurements": {"voltage": 120.0, "current": 50.0}
}
print("✓ Message created")

print("Step 7: Test message sending")
future = producer.send('iot.raw', value=message)
print("✓ Message sent")

print("Step 8: Wait for confirmation")
record_metadata = future.get(timeout=10)
print(f"✓ Message confirmed: {record_metadata.topic}")

print("Step 9: Close producer")
producer.close()
print("✓ Producer closed")

print("=== ALL STEPS COMPLETED SUCCESSFULLY ===")
