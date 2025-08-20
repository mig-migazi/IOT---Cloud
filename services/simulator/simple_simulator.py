#!/usr/bin/env python3
"""Minimal working simulator for testing"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

def main():
    """Simple main function"""
    print("Starting simple simulator...")
    
    try:
        # Create Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=['redpanda:29092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
        
        print("Kafka producer created successfully")
        
        # Simple telemetry loop
        message_count = 0
        while True:
            try:
                # Generate simple telemetry
                telemetry = {
                    "device_id": "breaker-001",
                    "device_type": "smart_breaker",
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "telemetry",
                    "measurements": {
                        "voltage": random.uniform(110, 130),
                        "current": random.uniform(0, 100),
                        "temperature": random.uniform(20, 80)
                    }
                }
                
                # Send to Kafka
                future = producer.send('iot.raw', key='breaker-001', value=telemetry)
                record_metadata = future.get(timeout=10)
                
                message_count += 1
                print(f"Message {message_count} sent successfully to {record_metadata.topic}")
                
                # Wait 5 seconds
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error sending message: {e}")
                time.sleep(1)
        
        producer.close()
        print("Simulator stopped")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
