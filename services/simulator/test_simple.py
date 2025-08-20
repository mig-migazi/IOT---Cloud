#!/usr/bin/env python3
"""Simple test script to debug simulator issues"""

import json
import time
from kafka import KafkaProducer

def test_kafka():
    """Test basic Kafka connectivity"""
    print("Testing Kafka connectivity...")
    
    try:
        # Create producer
        producer = KafkaProducer(
            bootstrap_servers=['redpanda:29092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
        
        print("Producer created successfully")
        
        # Test connection
        metrics = producer.metrics()
        print("Connection test successful")
        
        # Send a test message
        test_msg = {"test": "message", "timestamp": time.time()}
        future = producer.send('iot.raw', key='test', value=test_msg)
        record_metadata = future.get(timeout=10)
        print(f"Test message sent successfully to {record_metadata.topic}")
        
        producer.close()
        print("Test completed successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kafka()
