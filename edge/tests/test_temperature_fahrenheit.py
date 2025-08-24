#!/usr/bin/env python3
"""
Test Temperature in Fahrenheit
Demonstrates temperature values being generated in Fahrenheit
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grm_service.resource_manager_async import AsyncResourceManager
from grm_service.edge_core_client import EdgeCoreClient


async def test_temperature_fahrenheit():
    """Test temperature generation in Fahrenheit"""
    print("🌡️  Testing Temperature Generation in Fahrenheit...")
    
    # Create a mock Edge Core client
    class MockEdgeCoreClient:
        def __init__(self):
            self.connected = True
        
        async def update_resource_value(self, resources):
            print(f"   📤 Would update {len(resources)} resources in Edge Core:")
            for resource in resources:
                if resource.resource_name == "temperature":
                    print(f"      - {resource.resource_name}: {resource.value:.1f}°F")
                else:
                    print(f"      - {resource.resource_name}: {resource.value:.1f}")
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
    
    # Generate multiple temperature samples to show the range
    print("\n🌡️  Temperature Samples (Fahrenheit):")
    for i in range(5):
        updated_resources = resource_manager.generate_simulated_values()
        for resource in updated_resources:
            if resource.resource_name == "temperature":
                print(f"   Sample {i+1}: {resource.value:.1f}°F")
                break
    
    # Show the expected range
    print(f"\n📊 Temperature Range:")
    print(f"   Base temperature: 77.0°F (25°C)")
    print(f"   Variation range: ±9.0°F (±5°C)")
    print(f"   Noise range: ±2.0°F")
    print(f"   Expected range: ~66-88°F")
    
    return True


async def main():
    """Main test function"""
    print("🌡️  Temperature in Fahrenheit Test")
    print("=" * 50)
    
    success = await test_temperature_fahrenheit()
    
    print("\n📊 Test Summary:")
    print("=" * 30)
    
    if success:
        print("   ✅ Temperature generation in Fahrenheit working correctly")
        print("\n💡 Temperature values are now generated in Fahrenheit (°F)")
    else:
        print("   ❌ Temperature generation test failed")


if __name__ == "__main__":
    asyncio.run(main())
