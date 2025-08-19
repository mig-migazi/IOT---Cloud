#!/usr/bin/env python3
"""
Script to register test applications with the IoT Cloud App Registry Service
This will populate the registry with sample applications for testing the enrichment flow
"""

import requests
import json
import time

# App registry service URL
APP_REGISTRY_URL = "http://localhost:5002"

# Test applications to register
TEST_APPLICATIONS = [
    {
        "name": "Smart Breaker Dashboard",
        "developer": "IoT Solutions Inc.",
        "description": "Real-time monitoring dashboard for smart circuit breakers",
        "platform": "Web",
        "category": "Monitoring",
        "devicetypes": ["smart_breaker"],
        "status": "active",
        "version": "1.0.0"
    },
    {
        "name": "Power Analytics Engine",
        "developer": "Energy Analytics Corp.",
        "description": "Advanced power consumption analysis and reporting",
        "platform": "Cloud",
        "category": "Analytics",
        "devicetypes": ["smart_breaker", "smart_meter"],
        "status": "active",
        "version": "2.1.0"
    },
    {
        "name": "Predictive Maintenance AI",
        "developer": "AI Maintenance Systems",
        "description": "AI-powered predictive maintenance for electrical equipment",
        "platform": "AI/ML",
        "category": "Maintenance",
        "devicetypes": ["smart_breaker", "smart_meter"],
        "status": "active",
        "version": "1.5.0"
    },
    {
        "name": "Environmental Monitor",
        "developer": "Green Tech Solutions",
        "description": "Environmental monitoring and alerting system",
        "platform": "IoT",
        "category": "Environmental",
        "devicetypes": ["environmental_sensor"],
        "status": "active",
        "version": "1.2.0"
    },
    {
        "name": "Grid Management System",
        "developer": "Power Grid Corp.",
        "description": "Comprehensive grid management and optimization",
        "platform": "Enterprise",
        "category": "Grid Management",
        "devicetypes": ["smart_breaker", "smart_meter", "environmental_sensor"],
        "status": "active",
        "version": "3.0.0"
    }
]

def wait_for_service(url, max_attempts=30):
    """Wait for the app registry service to be available"""
    print(f"Waiting for app registry service at {url}...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{url}/api/applications", timeout=5)
            if response.status_code == 200:
                print("✅ App registry service is available!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            print(f"   Attempt {attempt + 1}/{max_attempts} - waiting...")
            time.sleep(2)
    
    print("❌ App registry service is not available")
    return False

def register_application(app_data):
    """Register a single application with the app registry"""
    try:
        print(f"📝 Registering: {app_data['name']}")
        
        response = requests.post(
            f"{APP_REGISTRY_URL}/api/applications",
            json=app_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            app_id = result.get('id')
            print(f"   ✅ Success! Application ID: {app_id}")
            return app_id
        else:
            print(f"   ❌ Failed with status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return None

def main():
    """Main function to register all test applications"""
    print("🚀 Starting Application Registration Process")
    print("=" * 50)
    
    # Wait for service to be available
    if not wait_for_service(APP_REGISTRY_URL):
        print("Cannot proceed without app registry service")
        return
    
    print("\n📝 Registering test applications...")
    print("-" * 30)
    
    registered_count = 0
    for app_data in TEST_APPLICATIONS:
        app_id = register_application(app_data)
        if app_id:
            registered_count += 1
        print()
    
    print(f"🎯 Registration complete: {registered_count}/{len(TEST_APPLICATIONS)} applications registered")
    
    if registered_count > 0:
        print(f"\n🌐 App registry service available at: {APP_REGISTRY_URL}")
        print("📊 You can now view registered applications and test the enrichment flow!")
        
        # Test the new endpoints
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
        
        print(f"\n🎉 Setup complete! Now restart the enrichment service to see application IDs in enriched messages.")
        print("   Command: docker-compose restart enrichment-service")

if __name__ == "__main__":
    main()
