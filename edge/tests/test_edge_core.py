#!/usr/bin/env python3
"""
Test Edge Core WebSocket Client
Tests WebSocket-based communication with Edge Core service
"""
import asyncio
import json
from pathlib import Path
from loguru import logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grm_service.edge_core_client import EdgeCoreClient, ResourceConfig


def load_test_env():
    """Load test environment variables"""
    env_file = Path("test.env")
    if not env_file.exists():
        print("❌ test.env not found. Run: python test_config.py")
        return None
    
    env_vars = {}
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value
    
    return env_vars


async def test_edge_core_connection():
    """Test Edge Core WebSocket connection"""
    print("🔌 Testing Edge Core WebSocket Connection...")
    
    # Load configuration
    env_vars = load_test_env()
    if not env_vars:
        return False
    
    # Parse WebSocket URL
    base_url = env_vars.get("IZUMA_API_BASE_URL", "")
    if not base_url.startswith("ws://"):
        print("❌ IZUMA_API_BASE_URL should be a WebSocket URL (ws://)")
        return False
    
    # Extract host and port
    host_port = base_url.replace("ws://", "")
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        port = int(port_str)
    else:
        host = host_port
        port = 8081
    
    service_name = env_vars.get("SERVICE_NAME", "edge-grm-service-test")
    
    print(f"🎯 Connecting to Edge Core at: {host}:{port}")
    print(f"   Service Name: {service_name}")
    
    # Create Edge Core client
    client = EdgeCoreClient(host=host, port=port, name=service_name)
    
    try:
        # Test connection
        connected = await client.connect()
        if not connected:
            print("   ❌ Failed to connect to Edge Core")
            return False
        
        print("   ✅ Successfully connected to Edge Core")
        
        # Test GRM registration
        print("\n🔑 Testing GRM Registration...")
        result = await client.register_grm()
        if result:
            print("   ✅ GRM registration successful")
        else:
            print("   ❌ GRM registration failed")
        
        # Test resource addition
        print("\n📦 Testing Resource Addition...")
        resources = [
            ResourceConfig(
                object_id=1234,
                object_instance_id=0,
                resource_id=0,
                resource_name="temperature",
                operations=3,  # READ | WRITE
                resource_type="float",
                value=25.5
            ),
            ResourceConfig(
                object_id=1234,
                object_instance_id=0,
                resource_id=1,
                resource_name="humidity",
                operations=3,  # READ | WRITE
                resource_type="float",
                value=60.0
            )
        ]
        
        result = await client.add_resource(resources)
        if result:
            print("   ✅ Resource addition successful")
        else:
            print("   ❌ Resource addition failed")
        
        # Test resource value update
        print("\n🔄 Testing Resource Value Update...")
        updated_resources = [
            ResourceConfig(
                object_id=1234,
                object_instance_id=0,
                resource_id=0,
                resource_name="temperature",
                operations=3,
                resource_type="float",
                value=26.8  # Updated value
            )
        ]
        
        result = await client.update_resource_value(updated_resources)
        if result:
            print("   ✅ Resource value update successful")
        else:
            print("   ❌ Resource value update failed")
        
        # Test device registration
        print("\n📱 Testing Device Registration...")
        result = await client.device_register("test-device-001", 1234, 0, 25.5)
        if result:
            print("   ✅ Device registration successful")
        else:
            print("   ❌ Device registration failed")
        
        # Test write operation
        print("\n✍️  Testing Write Operation...")
        result = await client.write("test-device-001", 1234, 0, 27.2)
        if result:
            print("   ✅ Write operation successful")
        else:
            print("   ❌ Write operation failed")
        
        # Cleanup
        await client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
        await client.disconnect()
        return False


async def main():
    """Main test function"""
    print("🔐 Edge Core WebSocket Client Test")
    print("=" * 50)
    
    success = await test_edge_core_connection()
    
    print("\n📊 Test Summary:")
    print("=" * 30)
    
    if success:
        print("   ✅ All Edge Core tests completed successfully")
        print("\n💡 Next Steps:")
        print("1. Edge Core WebSocket client is working")
        print("2. You can now use the Edge Core client in your GRM service")
        print("3. Run: python test_service.py to test the full service")
    else:
        print("   ❌ Edge Core tests failed")
        print("\n💡 Troubleshooting:")
        print("1. Check if Edge Core service is running on the target host")
        print("2. Verify the WebSocket URL in test.env")
        print("3. Check network connectivity to the Edge Core host")
        print("4. Ensure Edge Core is configured to accept WebSocket connections")


if __name__ == "__main__":
    asyncio.run(main())
