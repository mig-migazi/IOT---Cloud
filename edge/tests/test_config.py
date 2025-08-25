#!/usr/bin/env python3
"""
Test configuration for GRM Service
This script helps set up the environment for testing with a remote Izuma agent
"""
import os
import sys
from pathlib import Path

def create_test_env():
    """Create test environment file"""
    env_content = """# Test Configuration for Remote Izuma Agent
# Update these values with your actual remote Izuma agent details

# Remote Izuma Agent Configuration
IZUMA_API_BASE_URL=http://YOUR_REMOTE_LINUX_IP:8080
IZUMA_ACCESS_KEY=your_test_access_key_here

IZUMA_AUTH_TYPE=bearer
IZUMA_DEVICE_ID=edge-test-device-001

# Service Configuration
SERVICE_NAME=edge-grm-service-test
SERVICE_VERSION=1.0.0

# Resource Configuration
RESOURCES_FILE=resources.json

# Logging Configuration
LOG_LEVEL=DEBUG

# Health Check Configuration
HEALTH_CHECK_INTERVAL=10

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY=2
"""
    
    env_file = Path("test.env")
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"✅ Created test environment file: {env_file}")
    print("📝 Please update the following values in test.env:")
    print("   - IZUMA_API_BASE_URL: Set to your remote Linux machine IP and port")
    print("   - IZUMA_ACCESS_KEY: Set to your test access key")
    print("   - IZUMA_AUTH_TYPE: Set to bearer or custom")
    print("   - IZUMA_DEVICE_ID: Set to a unique device ID for testing")

def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        return False
    else:
        print(f"✅ Python version: {sys.version}")
    
    # Check if requirements are installed
    try:
        import requests
        import pydantic
        import loguru
        print("✅ Required packages are installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    
    # Check if resources.json exists
    if Path("resources.json").exists():
        print("✅ resources.json found")
    else:
        print("❌ resources.json not found")
        return False
    
    return True

def test_network_connectivity(host, port):
    """Test network connectivity to remote host"""
    import socket
    import requests
    
    print(f"🌐 Testing connectivity to {host}:{port}...")
    
    # Test basic socket connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Socket connection to {host}:{port} successful")
        else:
            print(f"❌ Socket connection to {host}:{port} failed")
            return False
    except Exception as e:
        print(f"❌ Socket connection error: {e}")
        return False
    
    # Test HTTP connection
    try:
        url = f"http://{host}:{port}/health"
        response = requests.get(url, timeout=5)
        print(f"✅ HTTP connection successful (Status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️  HTTP connection failed: {e}")
        print("   This might be expected if the Izuma agent doesn't have a health endpoint")
        return True  # Don't fail for HTTP issues

def main():
    """Main test setup function"""
    print("🚀 GRM Service Test Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return
    
    # Create test environment
    create_test_env()
    
    print("\n📋 Next Steps:")
    print("1. Update test.env with your remote Izuma agent details")
    print("2. Run: python test_connectivity.py")
    print("3. Run: python test_service.py")
    print("4. Run: python run.py (to start the full service)")

if __name__ == "__main__":
    main()
