#!/usr/bin/env python3
"""Send test messages to Kafka to test the dashboard"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

def send_test_messages():
    """Send test messages to Kafka"""
    print("Connecting to Kafka...")
    
    try:
        # Create producer
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],  # Use external port
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
        
        print("Connected to Kafka successfully")
        
        message_count = 0
        
        # Send messages with varying rates to simulate dynamic behavior
        while True:
            try:
                # Randomly decide message rate (burst or normal)
                if random.random() < 0.3:  # 30% chance of burst
                    burst_size = random.randint(3, 8)
                    print(f"Sending burst of {burst_size} messages...")
                    
                    for i in range(burst_size):
                        # Send telemetry message
                        telemetry = {
                            "device_id": "breaker-001",
                            "device_type": "smart_breaker",
                            "timestamp": datetime.now().isoformat(),
                            "event_type": "telemetry",
                            "measurements": {
                                "voltage": random.uniform(110, 130),
                                "current": random.uniform(0, 100),
                                "temperature": random.uniform(20, 80),
                                "power": random.uniform(1000, 5000)
                            }
                        }
                        
                        producer.send('iot.raw', key='breaker-001', value=telemetry)
                        message_count += 1
                        print(f"  Burst message {i+1}/{burst_size} sent")
                        
                        time.sleep(0.1)  # Small delay between burst messages
                    
                    # Send trends message after burst
                    trends = {
                        "device_id": "breaker-001",
                        "device_type": "smart_breaker",
                        "timestamp": datetime.now().isoformat(),
                        "event_type": "trends",
                        "a": "Trends",
                        "p": "breaker-001",
                        "trends": [
                            {
                                "c": "1001",
                                "t": int(time.time()),
                                "v": str(round(random.uniform(110, 130), 2)),
                                "avg": str(round(random.uniform(110, 130), 2)),
                                "min": str(round(random.uniform(110, 130), 2)),
                                "max": str(round(random.uniform(110, 130), 2))
                            }
                        ]
                    }
                    
                    producer.send('iot.raw', key='breaker-001', value=trends)
                    message_count += 1
                    print("  Trends message sent")
                    
                else:
                    # Normal single message
                    telemetry = {
                        "device_id": "breaker-001",
                        "device_type": "smart_breaker",
                        "timestamp": datetime.now().isoformat(),
                        "event_type": "telemetry",
                        "measurements": {
                            "voltage": random.uniform(110, 130),
                            "current": random.uniform(0, 100),
                            "temperature": random.uniform(20, 80),
                            "power": random.uniform(1000, 5000)
                        }
                    }
                    
                    producer.send('iot.raw', key='breaker-001', value=telemetry)
                    message_count += 1
                    print(f"Normal message {message_count} sent")
                
                # Wait between cycles
                wait_time = random.uniform(2, 8)  # Random wait time
                print(f"Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
        
        producer.close()
        print(f"Total messages sent: {message_count}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_test_messages()
