#!/usr/bin/env python3
"""
Test Periodic Update Filtering
Tests that only resources with periodic_update=True are updated
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grm_service.resource_manager_async import AsyncResourceManager
from grm_service.edge_core_client import EdgeCoreClient


async def test_periodic_update_filtering():
    """Test that only resources with periodic_update=True are updated"""
    print("🧪 Testing Periodic Update Filtering...")
    
    # Create a mock Edge Core client (we won't actually connect)
    class MockEdgeCoreClient:
        def __init__(self):
            self.connected = True
        
        async def update_resource_value(self, resources):
            print(f"   📤 Would update {len(resources)} resources in Edge Core:")
            for resource in resources:
                print(f"      - {resource.resource_name}: {resource.value} (periodic_update={resource.periodic_update})")
            return True
    
    # Create resource manager with mock client
    mock_client = MockEdgeCoreClient()
    resource_manager = AsyncResourceManager(mock_client)
    
    # Load resources
    print("\n📦 Loading resources from resources.json...")
    loaded = resource_manager.load_local_resources("resources.json")
    if not loaded:
        print("   ❌ Failed to load resources")
        return False
    
    print(f"   ✅ Loaded {len(resource_manager.local_resources)} resources")
    
    # Show all resources and their periodic_update settings
    print("\n📋 Resource Configuration:")
    for resource in resource_manager.local_resources:
        print(f"   - {resource.resource_name}: periodic_update={resource.periodic_update}")
    
    # Generate simulated values (this should only include periodic_update=True resources)
    print("\n🔄 Generating simulated values...")
    updated_resources = resource_manager.generate_simulated_values()
    
    print(f"   ✅ Generated values for {len(updated_resources)} resources")
    
    # Verify that only resources with periodic_update=True are included
    expected_count = sum(1 for r in resource_manager.local_resources if r.periodic_update)
    actual_count = len(updated_resources)
    
    print(f"\n📊 Results:")
    print(f"   Expected resources with periodic_update=True: {expected_count}")
    print(f"   Actual resources updated: {actual_count}")
    
    if expected_count == actual_count:
        print("   ✅ Periodic update filtering working correctly!")
        return True
    else:
        print("   ❌ Periodic update filtering not working correctly!")
        return False


async def main():
    """Main test function"""
    print("🔐 Periodic Update Filtering Test")
    print("=" * 50)
    
    success = await test_periodic_update_filtering()
    
    print("\n📊 Test Summary:")
    print("=" * 30)
    
    if success:
        print("   ✅ Periodic update filtering test passed")
        print("\n💡 The service will now only update resources with periodic_update=true")
    else:
        print("   ❌ Periodic update filtering test failed")


if __name__ == "__main__":
    asyncio.run(main())
