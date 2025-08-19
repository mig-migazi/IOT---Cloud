#!/usr/bin/env python3
"""
Script to register test applications in the Application Registry Service
This demonstrates how applications can register for specific device types
"""

import requests
import json
import time

# Configuration
APP_REGISTRY_URL = "http://localhost:5002"  # External port from docker-compose

# Test applications to register
TEST_APPLICATIONS = [
    {
        "name": "Smart Breaker Dashboard",
        "description": "Real-time monitoring dashboard for smart breaker devices",
        "version": "1.0.0",
        "developer": "IoT Platform Team",
        "contact_email": "dashboard@iot-platform.com",
        "category": "monitoring",
        "platform": "web",
        "devicetypes": ["smart_breaker"],
        "status": "active"
    },
    {
        "name": "Power Analytics Engine",
        "description": "Advanced analytics and reporting for electrical power data",
        "version": "2.1.0",
        "developer": "Data Science Team",
        "contact_email": "analytics@iot-platform.com",
        "category": "analytics",
        "platform": "api",
        "devicetypes": ["smart_breaker", "smart_meter"],
        "status": "active"
    },
    {
        "name": "Maintenance Scheduler",
        "description": "Predictive maintenance scheduling based on device health data",
        "version": "1.5.0",
        "developer": "Operations Team",
        "contact_email": "maintenance@iot-platform.com",
        "category": "operations",
        "platform": "web",
        "devicetypes": ["smart_breaker"],
        "status": "active"
    },
    {
        "name": "Environmental Monitor",
        "description": "Environmental sensor data collection and analysis",
        "version": "1.0.0",
        "developer": "Environmental Team",
        "contact_email": "env@iot-platform.com",
        "category": "monitoring",
        "platform": "mobile",
        "devicetypes": ["environmental_sensor"],
        "status": "active"
    }
]

def wait_for_service(url, max_attempts=30):
    """Wait for the app registry service to be available"""
    print(f"Waiting for app registry service at {url}...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ App registry service is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"Attempt {attempt + 1}/{max_attempts} - Service not ready yet...")
        time.sleep(2)
    
    print("❌ App registry service failed to start")
    return False

def register_application(app_data):
    """Register a single application"""
    try:
        response = requests.post(
            f"{APP_REGISTRY_URL}/api/applications",
            json=app_data,
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            app_id = result['application']['id']
            print(f"✅ Registered: {app_data['name']} (ID: {app_id})")
            return app_id
        else:
            print(f"❌ Failed to register {app_data['name']}: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error registering {app_data['name']}: {e}")
        return None

def main():
    """Main function to register all test applications"""
    print("🚀 Starting Application Registration Process")
    print("=" * 50)
    
    # Wait for service to be ready
    if not wait_for_service(APP_REGISTRY_URL):
        return
    
    print("\n📝 Registering test applications...")
    print("-" * 50)
    
    registered_count = 0
    for app_data in TEST_APPLICATIONS:
        app_id = register_application(app_data)
        if app_id:
            registered_count += 1
        print()
    
    print("=" * 50)
    print(f"🎯 Registration complete: {registered_count}/{len(TEST_APPLICATIONS)} applications registered")
    
    if registered_count > 0:
        print(f"\n🌐 App registry service available at: {APP_REGISTRY_URL}")
        print("📊 You can now view registered applications and test the enrichment flow!")
        
        # Test querying by device type
        print("\n🧪 Testing device type queries...")
        test_device_types = ["smart_breaker", "smart_meter", "environmental_sensor"]
        
        for device_type in test_device_types:
            try:
                response = requests.get(f"{APP_REGISTRY_URL}/api/applications/by-device-type/{device_type}")
                if response.status_code == 200:
                    data = response.json()
                    count = data['count']
                    print(f"   📱 {device_type}: {count} applications registered")
                else:
                    print(f"   ❌ {device_type}: Query failed")
            except Exception as e:
                print(f"   ❌ {device_type}: Error - {e}")

if __name__ == "__main__":
    main()
