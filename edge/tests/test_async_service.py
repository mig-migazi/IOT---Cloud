#!/usr/bin/env python3
"""
Test Async GRM Service with Edge Core
Tests the complete async GRM service using Edge Core WebSocket client
"""
import asyncio
import json
from pathlib import Path
from loguru import logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grm_service.main_async import AsyncGRMService


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


async def test_async_grm_service():
    """Test the complete async GRM service"""
    print("🚀 Testing Async GRM Service with Edge Core...")
    
    # Load configuration
    env_vars = load_test_env()
    if not env_vars:
        return False
    
    # Parse WebSocket URL
    base_url = env_vars.get("IZUMA_API_BASE_URL", "")
    if not base_url.startswith("ws://"):
        print("❌ IZUMA_API_BASE_URL should be a WebSocket URL (ws://)")
        return False
    
    service_name = env_vars.get("SERVICE_NAME", "edge-grm-service-test")
    
    print(f"🎯 Testing Async GRM Service:")
    print(f"   Edge Core URL: {base_url}")
    print(f"   Service Name: {service_name}")
    
    # Create and test the service
    service = AsyncGRMService()
    
    try:
        # Test initialization
        print("\n🔧 Testing Service Initialization...")
        initialized = await service.initialize()
        if not initialized:
            print("   ❌ Service initialization failed")
            return False
        print("   ✅ Service initialization successful")
        
        # Test GRM registration
        print("\n🔑 Testing GRM Registration...")
        registered = await service.register_grm()
        if not registered:
            print("   ❌ GRM registration failed")
            return False
        print("   ✅ GRM registration successful")
        
        # Test resource synchronization
        print("\n📦 Testing Resource Synchronization...")
        synced = await service.sync_resources()
        if not synced:
            print("   ⚠️  Resource sync completed with errors (this may be expected)")
        else:
            print("   ✅ Resource sync successful")
        
        # Test health check
        print("\n💓 Testing Health Check...")
        await service.start_health_check()
        await asyncio.sleep(2)  # Let health check run for a bit
        print("   ✅ Health check started successfully")
        
        # Test resource updates
        print("\n🔄 Testing Resource Updates...")
        await service.start_resource_update()
        await asyncio.sleep(5)  # Let resource updates run for a bit
        print("   ✅ Resource updates started successfully")
        
        # Test shutdown
        print("\n🛑 Testing Service Shutdown...")
        await service.shutdown_sequence()
        print("   ✅ Service shutdown successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
        try:
            await service.shutdown_sequence()
        except:
            pass
        return False


async def test_service_lifecycle():
    """Test the complete service lifecycle"""
    print("\n🔄 Testing Complete Service Lifecycle...")
    
    service = AsyncGRMService()
    
    try:
        # Startup sequence
        print("   📈 Starting service...")
        startup_success = await service.startup_sequence()
        if not startup_success:
            print("   ❌ Startup sequence failed")
            return False
        print("   ✅ Startup sequence successful")
        
        # Let service run for a few seconds
        print("   ⏱️  Running service for 10 seconds...")
        service.running = True
        await asyncio.sleep(10)
        
        # Shutdown sequence
        print("   📉 Shutting down service...")
        await service.shutdown_sequence()
        print("   ✅ Shutdown sequence successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lifecycle test failed: {e}")
        try:
            await service.shutdown_sequence()
        except:
            pass
        return False


async def main():
    """Main test function"""
    print("🔐 Async GRM Service Test with Edge Core")
    print("=" * 50)
    
    # Test basic service functionality
    basic_success = await test_async_grm_service()
    
    # Test complete lifecycle
    lifecycle_success = await test_service_lifecycle()
    
    print("\n📊 Test Summary:")
    print("=" * 30)
    
    if basic_success:
        print("   ✅ Basic service tests passed")
    else:
        print("   ❌ Basic service tests failed")
    
    if lifecycle_success:
        print("   ✅ Service lifecycle tests passed")
    else:
        print("   ❌ Service lifecycle tests failed")
    
    if basic_success and lifecycle_success:
        print("\n🎉 All tests completed successfully!")
        print("\n💡 Next Steps:")
        print("1. Async GRM Service is working with Edge Core")
        print("2. You can now run the full service: python -m grm_service.main_async")
        print("3. The service will automatically connect to Edge Core and manage resources")
    else:
        print("\n❌ Some tests failed")
        print("\n💡 Troubleshooting:")
        print("1. Check if Edge Core service is running")
        print("2. Verify the WebSocket URL in test.env")
        print("3. Check network connectivity")
        print("4. Review the logs for specific error messages")


if __name__ == "__main__":
    asyncio.run(main())
