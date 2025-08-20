#!/usr/bin/env python3
"""
Simple MQTT Test Script
Test MQTT connectivity and message publishing to verify the setup
"""

import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime

def on_connect(client, userdata, flags, rc):
    """Callback when MQTT client connects"""
    if rc == 0:
        print("✅ Connected to MQTT broker successfully!")
    else:
        print(f"❌ Failed to connect to MQTT broker, return code: {rc}")

def on_publish(client, userdata, mid):
    """Callback when MQTT message is published"""
    print(f"📤 Message published successfully (ID: {mid})")

def on_disconnect(client, userdata, rc):
    """Callback when MQTT client disconnects"""
    print(f"🔌 Disconnected from MQTT broker (return code: {rc})")

def main():
    """Main test function"""
    print("🚀 Starting MQTT connectivity test...")
    
    # Create MQTT client
    client = mqtt.Client(client_id="mqtt_test_client")
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to MQTT broker
        print("🔗 Connecting to MQTT broker at localhost:1883...")
        client.connect("localhost", 1883, 60)
        
        # Start the client loop
        client.loop_start()
        
        # Wait for connection
        time.sleep(2)
        
        # Test message
        test_message = {
            "device_id": "test-device-001",
            "device_type": "test_device",
            "timestamp": datetime.now().isoformat(),
            "event_type": "test",
            "message": "Hello MQTT from test script!"
        }
        
        # Publish test message
        topic = "iot/test-device-001/raw"
        print(f"📤 Publishing test message to topic: {topic}")
        print(f"📝 Message: {json.dumps(test_message, indent=2)}")
        
        result = client.publish(topic, json.dumps(test_message), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("✅ Message queued for publishing successfully!")
        else:
            print(f"❌ Failed to queue message, return code: {result.rc}")
        
        # Wait for message to be published
        time.sleep(2)
        
        print("✅ MQTT test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during MQTT test: {e}")
    
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        client.loop_stop()
        client.disconnect()
        print("✅ Test completed!")

if __name__ == "__main__":
    main()
