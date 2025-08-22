#!/usr/bin/env python3
"""
Test script for FDI package creation and validation
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fdi_package import create_smart_breaker_fdi_package, FDIPackage

def test_fdi_package():
    """Test FDI package creation and validation"""
    print("🧪 Testing FDI Package Creation...")
    
    try:
        # Create smart breaker package
        package = create_smart_breaker_fdi_package()
        
        print(f"✅ Package created successfully")
        print(f"   Package ID: {package.package_id}")
        print(f"   Device Type: {package.device_type.device_type}")
        print(f"   Manufacturer: {package.device_type.manufacturer}")
        print(f"   Model: {package.device_type.model}")
        print(f"   Version: {package.device_type.version}")
        print(f"   Parameters: {len(package.device_type.parameters)}")
        print(f"   Commands: {len(package.device_type.commands)}")
        
        # Validate package
        print("\n🔍 Validating package...")
        if package.validate():
            print("✅ Package validation successful")
        else:
            print("❌ Package validation failed")
            return False
        
        # Convert to dictionary and back
        print("\n🔄 Testing serialization...")
        package_dict = package.to_dict()
        package_json = package.to_json()
        
        print(f"   Dictionary keys: {list(package_dict.keys())}")
        print(f"   JSON length: {len(package_json)} characters")
        
        # Test reconstruction
        reconstructed_package = FDIPackage.from_dict(package_dict)
        if reconstructed_package.package_id == package.package_id:
            print("✅ Package reconstruction successful")
        else:
            print("❌ Package reconstruction failed")
            return False
        
        # Test metadata
        print("\n📊 Testing metadata...")
        package.add_metadata("test_key", "test_value")
        package.add_metadata("test_number", 42)
        
        if "test_key" in package.metadata and "test_number" in package.metadata:
            print("✅ Metadata addition successful")
        else:
            print("❌ Metadata addition failed")
            return False
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_extraction():
    """Test parameter extraction from measurements"""
    print("\n🔧 Testing parameter extraction...")
    
    try:
        package = create_smart_breaker_fdi_package()
        
        # Test measurement metadata extraction
        from fdi_package import FDIPackage
        package_dict = package.to_dict()
        
        # Simulate what the enrichment service would do
        device_type_data = package_dict.get('device_type', {})
        parameters = device_type_data.get('parameters', [])
        
        measurement_metadata = {}
        for param in parameters:
            param_name = param.get('name', '')
            if param_name:
                measurement_metadata[param_name] = {
                    'unit': param.get('unit'),
                    'description': param.get('description', ''),
                    'min_value': param.get('min_value'),
                    'max_value': param.get('max_value'),
                    'data_type': param.get('data_type', 'unknown'),
                    'category': param.get('category', 'measurement'),
                    'access_level': param.get('access_level', 'read_write')
                }
        
        print(f"   Extracted {len(measurement_metadata)} measurement parameters")
        
        # Check for specific parameters
        expected_params = ['voltage_phase_a', 'current_phase_a', 'power_active', 'temperature']
        for param in expected_params:
            if param in measurement_metadata:
                print(f"   ✅ Found {param}: {measurement_metadata[param]['unit']}")
            else:
                print(f"   ❌ Missing {param}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parameter extraction test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting FDI Package Tests...\n")
    
    success = True
    
    # Run tests
    if not test_fdi_package():
        success = False
    
    if not test_parameter_extraction():
        success = False
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
