#!/usr/bin/env python3
"""
Test script for FDI parser
"""

import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fdi.fdi_parser import parse_fdi_file

def test_fdi_parser():
    """Test FDI parser with smart breaker profile"""
    print("🧪 Testing FDI Parser...")
    
    try:
        # Path to the smart breaker FDI file
        fdi_file_path = "fdi/device-profiles/smart-breaker.fdi"
        
        if not os.path.exists(fdi_file_path):
            print(f"❌ FDI file not found: {fdi_file_path}")
            return False
        
        print(f"📁 Parsing FDI file: {fdi_file_path}")
        
        # Parse the FDI file
        fdi_data = parse_fdi_file(fdi_file_path)
        
        if fdi_data is None:
            print("❌ Failed to parse FDI file")
            return False
        
        print("✅ FDI file parsed successfully")
        
        # Display parsed data structure
        print("\n📊 Parsed FDI Data Structure:")
        print(f"   Device Identity: {len(fdi_data.get('device_identity', {}))} fields")
        print(f"   Device Type: {len(fdi_data.get('device_type', {}))} fields")
        print(f"   Capabilities: {len(fdi_data.get('capabilities', {}))} sections")
        print(f"   Configuration: {len(fdi_data.get('configuration', {}))} sections")
        print(f"   Documentation: {len(fdi_data.get('documentation', {}))} sections")
        
        # Show device identity details
        print("\n🆔 Device Identity:")
        identity = fdi_data.get('device_identity', {})
        for key, value in identity.items():
            print(f"   {key}: {value}")
        
        # Show device type details
        print("\n🏷️ Device Type:")
        device_type = fdi_data.get('device_type', {})
        for key, value in device_type.items():
            print(f"   {key}: {value}")
        
        # Show capabilities summary
        print("\n🔧 Device Capabilities:")
        capabilities = fdi_data.get('capabilities', {})
        
        # Communication protocols
        protocols = capabilities.get('communication_protocols', [])
        print(f"   Communication Protocols: {len(protocols)}")
        for protocol in protocols:
            print(f"     - {protocol.get('name', 'Unknown')} v{protocol.get('version', 'Unknown')} ({protocol.get('transport', 'Unknown')})")
        
        # Device functions
        functions = capabilities.get('device_functions', [])
        print(f"   Device Functions: {len(functions)}")
        for function in functions:
            print(f"     - {function.get('name', 'Unknown')}: {function.get('description', 'No description')}")
        
        # Device commands
        commands = capabilities.get('device_commands', [])
        print(f"   Device Commands: {len(commands)}")
        for command in commands:
            print(f"     - {command.get('name', 'Unknown')}: {command.get('description', 'No description')}")
        
        # Device alarms
        alarms = capabilities.get('device_alarms', [])
        print(f"   Device Alarms: {len(alarms)}")
        for alarm in alarms:
            print(f"     - {alarm.get('name', 'Unknown')} ({alarm.get('severity', 'Unknown')}): {alarm.get('description', 'No description')}")
        
        # Device events
        events = capabilities.get('device_events', [])
        print(f"   Device Events: {len(events)}")
        for event in events:
            print(f"     - {event.get('name', 'Unknown')}: {event.get('description', 'No description')}")
        
        # Show configuration summary
        print("\n⚙️ Device Configuration:")
        config = fdi_data.get('configuration', {})
        
        # Default settings
        default_settings = config.get('default_settings', [])
        print(f"   Default Settings: {len(default_settings)}")
        for setting in default_settings[:5]:  # Show first 5
            print(f"     - {setting.get('name', 'Unknown')}: {setting.get('value', 'Unknown')} {setting.get('units', '')}")
        
        if len(default_settings) > 5:
            print(f"     ... and {len(default_settings) - 5} more")
        
        # Configuration profiles
        profiles = config.get('configuration_profiles', [])
        print(f"   Configuration Profiles: {len(profiles)}")
        for profile in profiles:
            print(f"     - {profile.get('name', 'Unknown')}: {profile.get('description', 'No description')}")
        
        # Show documentation summary
        print("\n📚 Device Documentation:")
        docs = fdi_data.get('documentation', {})
        
        # Manuals
        manuals = docs.get('manuals', [])
        print(f"   Manuals: {len(manuals)}")
        for manual in manuals:
            print(f"     - {manual.get('name', 'Unknown')} v{manual.get('version', 'Unknown')} ({manual.get('language', 'Unknown')})")
        
        # Data sheets
        data_sheets = docs.get('data_sheets', [])
        print(f"   Data Sheets: {len(data_sheets)}")
        for sheet in data_sheets:
            print(f"     - {sheet.get('name', 'Unknown')} v{sheet.get('version', 'Unknown')} ({sheet.get('language', 'Unknown')})")
        
        # Save parsed data to JSON for inspection
        output_file = "parsed_fdi_data.json"
        with open(output_file, 'w') as f:
            json.dump(fdi_data, f, indent=2, default=str)
        
        print(f"\n💾 Parsed data saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting FDI Parser Tests...\n")
    
    success = test_fdi_parser()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
