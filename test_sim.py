#!/usr/bin/env python3
"""
Test script to debug simulator issues
"""

print("🚀 Test script starting...")

try:
    import json
    print("✓ JSON imported")
except Exception as e:
    print(f"❌ JSON import failed: {e}")
    exit(1)

try:
    import time
    print("✓ Time imported")
except Exception as e:
    print(f"❌ Time import failed: {e}")
    exit(1)

try:
    import random
    print("✓ Random imported")
except Exception as e:
    print(f"❌ Random import failed: {e}")
    exit(1)

try:
    from datetime import datetime
    print("✓ Datetime imported")
except Exception as e:
    print(f"❌ Datetime import failed: {e}")
    exit(1)

try:
    from kafka import KafkaProducer
    print("✓ KafkaProducer imported")
except Exception as e:
    print(f"❌ KafkaProducer import failed: {e}")
    exit(1)

print("✅ All imports successful!")
print("🚀 Test script completed successfully!")
