#!/usr/bin/env python3
"""
Simple Smart Breaker Simulator - GUARANTEED TO WORK
"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

print("🚀 Starting Simple Smart Breaker Simulator...")

# Create Kafka producer
try:
    producer = KafkaProducer(
        bootstrap_servers=['redpanda:29092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("✓ Kafka producer created")
except Exception as e:
    print(f"❌ Failed to create producer: {e}")
    exit(1)

device_id = "breaker-001"
message_count = 0
burst_count = 0

print("📡 Starting message generation...")

try:
    while True:
        try:
            # 25% chance of burst
            if random.random() < 0.25:
                burst_size = random.randint(3, 6)
                print(f"💥 Generating burst of {burst_size} messages")
                burst_count += 1
                
                # Send burst messages
                for i in range(burst_size):
                    message = {
                        "device_id": device_id,
                        "device_type": "smart_breaker",
                        "timestamp": datetime.now().isoformat(),
                        "event_type": "telemetry",
                        "measurements": {
                            "voltage": round(random.uniform(110.0, 130.0), 2),
                            "current": round(random.uniform(0.0, 100.0), 2),
                            "power": round(random.uniform(5000.0, 12000.0), 2),
                            "temperature": round(random.uniform(20.0, 80.0), 2)
                        }
                    }
                    
                    producer.send('iot.raw', value=message)
                    message_count += 1
                    print(f"  ✓ Burst message {i+1}/{burst_size} sent (Total: {message_count})")
                    time.sleep(0.2)
                
                # Send trends message after burst
                trends = {
                    "device_id": device_id,
                    "device_type": "smart_breaker",
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "trends",
                    "a": "Trends",
                    "p": device_id,
                    "trends": [
                        {
                            "c": "1001",
                            "t": int(time.time()),
                            "v": str(round(random.uniform(110.0, 130.0), 2)),
                            "avg": str(round(random.uniform(115.0, 125.0), 2)),
                            "min": str(round(random.uniform(110.0, 115.0), 2)),
                            "max": str(round(random.uniform(125.0, 130.0), 2))
                        }
                    ]
                }
                
                producer.send('iot.raw', value=trends)
                message_count += 1
                print(f"  ✓ Trends message sent (Total: {message_count})")
                
            else:
                # Normal single message
                message = {
                    "device_id": device_id,
                    "device_type": "smart_breaker",
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "telemetry",
                    "measurements": {
                        "voltage": round(random.uniform(110.0, 130.0), 2),
                        "current": round(random.uniform(0.0, 100.0), 2),
                        "power": round(random.uniform(5000.0, 12000.0), 2),
                        "temperature": round(random.uniform(20.0, 80.0), 2)
                    }
                }
                
                producer.send('iot.raw', value=message)
                message_count += 1
                print(f"📡 Normal message {message_count} sent")
            
            # Random wait for dynamic rates
            wait_time = random.uniform(3, 8)
            print(f"⏳ Waiting {wait_time:.1f}s... (Total: {message_count}, Bursts: {burst_count})")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"❌ Error in message loop: {e}")
            time.sleep(2)
            
except KeyboardInterrupt:
    print("\n🛑 Shutdown requested...")
finally:
    print("🧹 Cleaning up...")
    producer.flush()
    producer.close()
    print(f"✅ Simulator stopped. Total messages: {message_count}, Bursts: {burst_count}")
