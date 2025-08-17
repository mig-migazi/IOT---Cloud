#!/usr/bin/env python3
"""
Simple API testing script
Run this script to test the API endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5001"

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_register_application():
    """Test application registration"""
    print("\nTesting application registration...")
    data = {
        "name": "Test Weather App",
        "description": "A test weather application",
        "version": "1.0.0",
        "developer": "Test Developer",
        "contact_email": "test@example.com",
        "category": "weather",
        "platform": "web"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/applications", json=data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 201:
            return result.get('application', {}).get('id')
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_applications():
    """Test getting all applications"""
    print("\nTesting get all applications...")
    try:
        response = requests.get(f"{BASE_URL}/api/applications")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Found {result.get('count', 0)} applications")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_application_by_id(app_id):
    """Test getting application by ID"""
    if not app_id:
        print("\nSkipping get application by ID (no ID available)")
        return False
        
    print(f"\nTesting get application by ID: {app_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/applications/{app_id}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Application: {result.get('application', {}).get('name')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_update_application(app_id):
    """Test updating application"""
    if not app_id:
        print("\nSkipping update application (no ID available)")
        return False
        
    print(f"\nTesting update application: {app_id}")
    data = {
        "version": "1.1.0",
        "description": "Updated test weather application"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/api/applications/{app_id}", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Updated version: {result.get('application', {}).get('version')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_regenerate_api_key(app_id):
    """Test regenerating API key"""
    if not app_id:
        print("\nSkipping regenerate API key (no ID available)")
        return False
        
    print(f"\nTesting regenerate API key: {app_id}")
    try:
        response = requests.post(f"{BASE_URL}/api/applications/{app_id}/regenerate-key")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"New API key generated: {result.get('api_key')[:10]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting API tests...")
    print("Make sure the server is running on http://localhost:5000")
    print("=" * 50)
    
    # Test health check
    if not test_health_check():
        print("Health check failed. Is the server running?")
        sys.exit(1)
    
    # Test application registration
    app_id = test_register_application()
    
    # Test getting all applications
    test_get_applications()
    
    # Test getting application by ID
    test_get_application_by_id(app_id)
    
    # Test updating application
    test_update_application(app_id)
    
    # Test regenerating API key
    test_regenerate_api_key(app_id)
    
    print("\n" + "=" * 50)
    print("API tests completed!")
    print("Note: The test application is still in the database.")
    print("You can delete it manually if needed.")

if __name__ == '__main__':
    main()
