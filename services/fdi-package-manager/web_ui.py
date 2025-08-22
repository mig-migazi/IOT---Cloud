#!/usr/bin/env python3
"""
FDI Package Manager Web UI
Provides a web interface for managing FDI packages, devices, and monitoring
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import asyncio
import threading
import time
from datetime import datetime
import structlog

# Import our FDI components
from fdi_package import FDIPackage, create_smart_breaker_fdi_package
from fdi_blob_storage import FDIPackageBlobStorage
from fdi_server import FDIServer

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = Flask(__name__)

# Global FDI components
fdi_storage = None
fdi_server = None
server_thread = None

def auto_initialize_fdi():
    """Auto-initialize FDI components when module is imported"""
    global fdi_storage, fdi_server, server_thread
    
    try:
        print("🚀 AUTO-INIT: Starting FDI initialization...")
        logger.info("🚀 Auto-initializing FDI components...")
        
        # Initialize storage
        fdi_storage = FDIPackageBlobStorage()
        print("✅ AUTO-INIT: FDI storage initialized")
        
        # Initialize server
        fdi_server = FDIServer()
        print("✅ AUTO-INIT: FDI server initialized")
        
        # Start FDI server in background thread
        def run_fdi_server_auto():
            try:
                print("🖥️ AUTO-INIT: Starting FDI server...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(fdi_server.start())
                print("✅ AUTO-INIT: FDI server started successfully!")
                
                # Keep running
                while fdi_server.running:
                    loop.run_until_complete(asyncio.sleep(1))
            except Exception as e:
                print(f"❌ AUTO-INIT: FDI server error: {e}")
                logger.error("FDI server thread error", error=str(e))
        
        # Start server thread
        server_thread = threading.Thread(target=run_fdi_server_auto, daemon=True)
        server_thread.start()
        print("✅ AUTO-INIT: FDI server thread started")
        
        # Wait for initialization
        time.sleep(5)
        
        print("🎉 AUTO-INIT: FDI initialization complete!")
        logger.info("FDI auto-initialization complete!")
        
    except Exception as e:
        print(f"❌ AUTO-INIT ERROR: {e}")
        logger.error("FDI auto-initialization failed", error=str(e))

# Auto-initialize when module is imported
print("🔄 AUTO-INIT: Module imported, starting auto-initialization...")
auto_initialize_fdi()

# Initialize when first request is made to any endpoint
def ensure_fdi_initialized():
    """Ensure FDI components are initialized"""
    if not fdi_server or not fdi_server.running:
        print("🔄 FLASK-INIT: Re-initializing FDI components...")
        auto_initialize_fdi()
    else:
        print("🔄 FLASK-INIT: FDI components already running")

# Add initialization check to key endpoints
def check_and_init_fdi():
    """Check and initialize FDI if needed"""
    ensure_fdi_initialized()

def init_fdi_components():
    """Initialize FDI components"""
    global fdi_storage, fdi_server
    
    try:
        # Initialize storage
        fdi_storage = FDIPackageBlobStorage()
        
        # Initialize server (but don't start it yet)
        fdi_server = FDIServer()
        
        logger.info("FDI components initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize FDI components", error=str(e))

def start_fdi_server():
    """Start FDI server in background thread"""
    global fdi_server, server_thread
    
    try:
        logger.info("start_fdi_server called", fdi_server_exists=fdi_server is not None, server_thread_exists=server_thread is not None)
        
        if fdi_server and not server_thread:
            logger.info("Starting FDI server thread...")
            server_thread = threading.Thread(target=run_fdi_server, daemon=True)
            server_thread.start()
            logger.info("FDI server started in background thread")
        else:
            logger.warning("FDI server not started", fdi_server_exists=fdi_server is not None, server_thread_exists=server_thread is not None)
            
    except Exception as e:
        logger.error("Failed to start FDI server", error=str(e))

def run_fdi_server():
    """Run FDI server in thread"""
    try:
        logger.info("FDI server thread starting...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("Starting FDI server...")
        loop.run_until_complete(fdi_server.start())
        logger.info("FDI server started successfully")
        
        # Keep running
        try:
            while fdi_server.running:
                loop.run_until_complete(asyncio.sleep(1))
        except KeyboardInterrupt:
            logger.info("FDI server thread interrupted")
            pass
        
        # Stop server
        logger.info("Stopping FDI server...")
        loop.run_until_complete(fdi_server.stop())
        loop.close()
        logger.info("FDI server stopped")
        
    except Exception as e:
        logger.error("FDI server thread error", error=str(e))

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/packages')
def list_packages():
    """List all FDI packages"""
    try:
        if not fdi_storage:
            return jsonify({'error': 'FDI storage not initialized'}), 500
        
        packages = fdi_storage.list_packages()
        return jsonify({
            'success': True,
            'packages': packages,
            'total': len(packages)
        })
        
    except Exception as e:
        logger.error("Error listing packages", error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/packages/<package_id>')
def get_package(package_id):
    """Get specific FDI package"""
    try:
        if not fdi_storage:
            return jsonify({'error': 'FDI storage not initialized'}), 500
        
        package_data = fdi_storage.retrieve_package(package_id)
        if package_data:
            return jsonify({
                'success': True,
                'package': package_data
            })
        else:
            return jsonify({'error': 'Package not found'}), 404
            
    except Exception as e:
        logger.error("Error getting package", package_id=package_id, error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/packages', methods=['POST'])
def create_package():
    """Create new FDI package"""
    try:
        if not fdi_storage:
            return jsonify({'error': 'FDI storage not initialized'}), 500
        
        data = request.get_json()
        package_type = data.get('package_type', 'smart_breaker')
        
        # Create package based on type
        if package_type == 'smart_breaker':
            package = create_smart_breaker_fdi_package()
        else:
            return jsonify({'error': f'Unknown package type: {package_type}'}), 400
        
        # Validate package
        if not package.validate():
            return jsonify({'error': 'Package validation failed'}), 400
        
        # Store package
        package_data = package.to_dict()
        success = fdi_storage.store_package(package_data, package.package_id)
        
        if success:
            return jsonify({
                'success': True,
                'package_id': package.package_id,
                'message': 'Package created successfully'
            })
        else:
            return jsonify({'error': 'Failed to store package'}), 500
            
    except Exception as e:
        logger.error("Error creating package", error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/packages/<package_id>', methods=['DELETE'])
def delete_package(package_id):
    """Delete FDI package"""
    try:
        if not fdi_storage:
            return jsonify({'error': 'FDI storage not initialized'}), 500
        
        success = fdi_storage.delete_package(package_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Package deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete package'}), 500
            
    except Exception as e:
        logger.error("Error deleting package", package_id=package_id, error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices')
def list_devices():
    """List discovered devices"""
    try:
        # Access the global variables directly
        global fdi_server
        
        if not fdi_server:
            return jsonify({'error': 'FDI server not initialized'}), 500
        
        # Get devices from MQTT adapter directly
        mqtt_adapter = fdi_server.adapters.get('mqtt')
        if not mqtt_adapter:
            return jsonify({'error': 'MQTT adapter not available'}), 500
        
        # Get devices from MQTT adapter
        devices = []
        for device_id, device in mqtt_adapter.devices.items():
            devices.append({
                'device_id': device.device_id,
                'device_type': device.device_type,
                'protocol': device.protocol,
                'status': device.status,
                'last_seen': device.last_seen,
                'capabilities': device.capabilities or []
            })
        
        print(f"🔄 API: Found {len(devices)} devices: {[d['device_id'] for d in devices]}")
        
        return jsonify({
            'success': True,
            'devices': devices,
            'total': len(devices)
        })
        
    except Exception as e:
        logger.error("Error listing devices", error=str(e))
        print(f"❌ API ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>')
def get_device(device_id):
    """Get device details"""
    try:
        # Access the global variables directly
        global fdi_server
        
        if not fdi_server:
            return jsonify({'error': 'FDI server not initialized'}), 500
        
        # Get devices from MQTT adapter directly
        mqtt_adapter = fdi_server.adapters.get('mqtt')
        if not mqtt_adapter:
            return jsonify({'error': 'MQTT adapter not available'}), 500
        
        if device_id in mqtt_adapter.devices:
            device = mqtt_adapter.devices[device_id]
            
            # Get current data
            device_data = asyncio.run(fdi_server.get_device_data(device_id))
            
            print(f"🔄 API DEVICE: Found device {device_id}, returning details")
            
            # Get rich device data including current measurements
            rich_device_data = {
                'device_id': device.device_id,
                'device_type': device.device_type,
                'protocol': device.protocol,
                'status': device.status,
                'last_seen': device.last_seen,
                'capabilities': device.capabilities or [],
                'current_data': device_data,
                'live_measurements': device.metrics or {},
                'fdi_mapping': {
                    'voltage': {
                        'description': 'Phase voltage measurements',
                        'unit': 'V',
                        'access': 'read_only',
                        'fdi_parameter': 'voltage_phase'
                    },
                    'current': {
                        'description': 'Phase current measurements', 
                        'unit': 'A',
                        'access': 'read_only',
                        'fdi_parameter': 'current_phase'
                    },
                    'power': {
                        'description': 'Power measurements and factor',
                        'unit': 'W',
                        'access': 'read_only',
                        'fdi_parameter': 'power_measurement'
                    },
                    'temperature': {
                        'description': 'Device temperature',
                        'unit': '°C',
                        'access': 'read_only',
                        'fdi_parameter': 'temperature'
                    },
                    'status': {
                        'description': 'Device operational status',
                        'access': 'read_only',
                        'fdi_parameter': 'operational_status'
                    },
                    'protection': {
                        'description': 'Protection system status',
                        'access': 'read_only',
                        'fdi_parameter': 'protection_status'
                    }
                }
            }
            
            return jsonify({
                'success': True,
                'device': rich_device_data
            })
        else:
            print(f"❌ API DEVICE: Device {device_id} not found in MQTT adapter")
            print(f"   Available devices: {list(mqtt_adapter.devices.keys())}")
            return jsonify({'error': 'Device not found'}), 404
            
    except Exception as e:
        logger.error("Error getting device", device_id=device_id, error=str(e))
        print(f"❌ API DEVICE ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/command', methods=['POST'])
def send_device_command(device_id):
    """Send command to device"""
    try:
        if not fdi_server:
            return jsonify({'error': 'FDI server not initialized'}), 500
        
        data = request.get_json()
        command = data.get('command')
        parameters = data.get('parameters', {})
        
        if not command:
            return jsonify({'error': 'Command is required'}), 400
        
        # Send command
        success = asyncio.run(fdi_server.send_device_command(device_id, command, parameters))
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Command {command} sent successfully'
            })
        else:
            return jsonify({'error': 'Failed to send command'}), 500
            
    except Exception as e:
        logger.error("Error sending command", device_id=device_id, error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/parameter', methods=['POST'])
def set_device_parameter(device_id):
    """Set device parameter (simulated)"""
    try:
        # Access the global variables directly
        global fdi_server
        
        if not fdi_server:
            return jsonify({'error': 'FDI server not initialized'}), 500
        
        # Get devices from MQTT adapter directly
        mqtt_adapter = fdi_server.adapters.get('mqtt')
        if not mqtt_adapter:
            return jsonify({'error': 'MQTT adapter not available'}), 500
        
        if device_id not in mqtt_adapter.devices:
            return jsonify({'error': 'Device not found'}), 404
        
        data = request.get_json()
        parameter = data.get('parameter')
        value = data.get('value')
        
        if parameter is None or value is None:
            return jsonify({'error': 'Parameter and value are required'}), 400
        
        device = mqtt_adapter.devices[device_id]
        
        # Simulate parameter change by updating device metrics
        # In a real system, this would send a command to the device
        if hasattr(device, 'metrics') and device.metrics:
            # Handle nested parameter format (e.g., "temperature.value")
            if '.' in parameter:
                category, key = parameter.split('.', 1)
                if category in device.metrics and key in device.metrics[category]:
                    old_value = device.metrics[category][key]
                    device.metrics[category][key] = value
                    print(f"🔄 SIMULATED PARAMETER CHANGE: {device_id}.{category}.{key}: {old_value} -> {value}")
                    
                    return jsonify({
                        'success': True,
                        'message': f'Parameter {category}.{key} changed from {old_value} to {value} (simulated)',
                        'old_value': old_value,
                        'new_value': value,
                        'simulated': True
                    })
                else:
                    return jsonify({'error': f'Parameter {category}.{key} not found in device'}), 400
            else:
                # Handle direct parameter format (e.g., "temperature")
                if parameter in device.metrics:
                    old_value = device.metrics[parameter]
                    device.metrics[parameter] = value
                    print(f"🔄 SIMULATED PARAMETER CHANGE: {device_id}.{parameter}: {old_value} -> {value}")
                    
                    return jsonify({
                        'success': True,
                        'message': f'Parameter {parameter} changed from {old_value} to {value} (simulated)',
                        'old_value': old_value,
                        'new_value': value,
                        'simulated': True
                    })
                else:
                    return jsonify({'error': f'Parameter {parameter} not found in device'}), 400
        else:
            return jsonify({'error': 'Device has no metrics data'}), 400
            
    except Exception as e:
        logger.error("Error setting parameter", device_id=device_id, error=str(e))
        print(f"❌ API PARAMETER ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/measurements')
def get_device_measurements(device_id):
    """Get current device measurements"""
    try:
        # Access the global variables directly
        global fdi_server
        
        if not fdi_server:
            return jsonify({'error': 'FDI server not initialized'}), 500
        
        # Get devices from MQTT adapter directly
        mqtt_adapter = fdi_server.adapters.get('mqtt')
        if not mqtt_adapter:
            return jsonify({'error': 'MQTT adapter not available'}), 500
        
        if device_id not in mqtt_adapter.devices:
            return jsonify({'error': 'Device not found'}), 404
        
        device = mqtt_adapter.devices[device_id]
        
        # Return current measurements with FDI mapping
        measurements = {
            'device_id': device_id,
            'timestamp': device.last_seen,
            'measurements': device.metrics or {},
            'fdi_mapping': {
                'voltage': {
                    'description': 'Phase voltage measurements',
                    'unit': 'V',
                    'access': 'read_only',
                    'fdi_parameter': 'voltage_phase'
                },
                'current': {
                    'description': 'Phase current measurements', 
                    'unit': 'A',
                    'access': 'read_only',
                    'fdi_parameter': 'current_phase'
                },
                'power': {
                    'description': 'Power measurements and factor',
                    'unit': 'W',
                    'access': 'read_only',
                    'fdi_parameter': 'power_measurement'
                },
                'temperature': {
                    'description': 'Device temperature',
                    'unit': '°C',
                    'access': 'read_only',
                    'fdi_parameter': 'temperature'
                },
                'status': {
                    'description': 'Device operational status',
                    'access': 'read_only',
                    'fdi_parameter': 'operational_status'
                },
                'protection': {
                    'description': 'Protection system status',
                    'access': 'read_only',
                    'fdi_parameter': 'protection_status'
                }
            }
        }
        
        print(f"🔄 API MEASUREMENTS: Returning measurements for {device_id}")
        
        return jsonify({
            'success': True,
            'data': measurements
        })
        
    except Exception as e:
        logger.error("Error getting measurements", device_id=device_id, error=str(e))
        print(f"❌ API MEASUREMENTS ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/status')
def server_status():
    """Get FDI server status"""
    try:
        # Access the global variables directly
        global fdi_server, fdi_storage
        
        if not fdi_server:
            return jsonify({'error': 'FDI server not initialized'}), 500
        
        # Get devices count from MQTT adapter
        mqtt_adapter = fdi_server.adapters.get('mqtt')
        devices_count = len(mqtt_adapter.devices) if mqtt_adapter else 0
        
        status = {
            'running': fdi_server.running,
            'opcua_port': fdi_server.opcua_port,
            'adapters': list(fdi_server.adapters.keys()),
            'devices_count': devices_count,
            'storage_stats': fdi_storage.get_storage_stats() if fdi_storage else {}
        }
        
        print(f"🔄 API STATUS: Server running={status['running']}, devices={devices_count}")
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error("Error getting server status", error=str(e))
        print(f"❌ API STATUS ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/start', methods=['POST'])
def start_server():
    """Start FDI server"""
    try:
        start_fdi_server()
        return jsonify({
            'success': True,
            'message': 'FDI server starting'
        })
        
    except Exception as e:
        logger.error("Error starting server", error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/stop', methods=['POST'])
def stop_server():
    """Stop FDI server"""
    try:
        if fdi_server and fdi_server.running:
            asyncio.run(fdi_server.stop())
            return jsonify({
                'success': True,
                'message': 'FDI server stopping'
            })
        else:
            return jsonify({'error': 'Server not running'}), 400
            
    except Exception as e:
        logger.error("Error stopping server", error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/fdi-package/<device_type>')
def get_fdi_package_for_device(device_type):
    """Get FDI package for device type"""
    try:
        if not fdi_server:
            return jsonify({'error': 'FDI server not initialized'}), 500
        
        package = fdi_server.get_fdi_package(device_type)
        
        if package:
            return jsonify({
                'success': True,
                'package': package.to_dict()
            })
        else:
            return jsonify({'error': f'No FDI package found for device type: {device_type}'}), 404
            
    except Exception as e:
        logger.error("Error getting FDI package", device_type=device_type, error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'FDI Package Manager Web UI',
        'timestamp': datetime.now().isoformat(),
        'fdi_storage_initialized': fdi_storage is not None,
        'fdi_server_initialized': fdi_server is not None
    })

if __name__ == '__main__':
    # Initialize FDI components
    init_fdi_components()
    
    # Start web server
    logger.info("Starting FDI Package Manager Web UI...")
    app.run(host='0.0.0.0', port=5000, debug=False)
