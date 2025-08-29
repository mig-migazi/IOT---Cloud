#!/usr/bin/env python3
from kafka import KafkaConsumer
import json

# Test consumer for iot.raw topic
consumer = KafkaConsumer(
    'iot.raw',
    bootstrap_servers=['redpanda:29092'],
    auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None
)

print('Checking messages in iot.raw topic...')
count = 0
for msg in consumer:
    count += 1
    if count <= 3:  # Show first 3 messages
        print(f'  Message {count}: {msg.value}')
    if count >= 10:  # Stop after 10 messages
        break

consumer.close()
print(f'Total messages found: {count}')
