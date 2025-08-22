#!/usr/bin/env python3
"""
FDI Communication Server - Protocol-Agnostic Bridge

This server acts as a bridge between FDI Host tools (via OPC UA) and various device protocols (MQTT, Modbus, etc.).
It implements the Communication Server Plugin pattern for FDI architecture.

Architecture:
- FDI Host (e.g., Siemens PDM) connects via OPC UA
- Devices connect via their native protocols (MQTT/SparkplugB, Modbus, etc.)
- This server bridges between them using protocol adapters
"""

import asyncio
import os
import time
import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

# OPC UA for FDI Host communication
try:
    from asyncua import Server, ua
    OPCUA_AVAILABLE = True
except ImportError:
    OPCUA_AVAILABLE = False
    # Create dummy classes for compatibility
    class Server:
        pass
    class ua:
        class VariantType:
            String = "String"
            Boolean = "Boolean"
        class Variant:
            def __init__(self, value, variant_type):
                self.Value = type('Value', (), {'Value': value})()

# MQTT for device communication
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

# Structured logging
import structlog

# Import our FDI components
from fdi_package import FDIPackage, FDIDeviceType
from fdi_blob_storage import FDIPackageBlobStorage

# Configure structlog
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

@dataclass
class Device:
    """Generic device representation"""
    device_id: str
    device_type: str
    protocol: str  # e.g., "mqtt", "modbus", "opcua", "http"
    status: str = "offline"
    last_seen: float = 0
    metrics: Dict[str, Any] = None
    capabilities: Dict[str, Any] = None
    fdi_package: Optional[FDIPackage] = None

class DeviceProtocolAdapter(ABC):
    """Abstract base class for device protocol adapters"""
    
    @abstractmethod
    async def start(self):
        """Start the adapter"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the adapter"""
        pass
    
    @abstractmethod
    async def discover_devices(self) -> List[Device]:
        """Discover devices on this protocol"""
        pass
    
    @abstractmethod
    async def get_device_data(self, device_id: str) -> Dict[str, Any]:
        """Get current data from a device"""
        pass
    
    @abstractmethod
    async def set_device_parameter(self, device_id: str, parameter: str, value: Any) -> bool:
        """Set a device parameter"""
        pass
    
    @abstractmethod
    async def send_device_command(self, device_id: str, command: str, parameters: Dict[str, Any] = None) -> bool:
        """Send a command to a device"""
        pass

class MQTTAdapter(DeviceProtocolAdapter):
    """MQTT protocol adapter for device communication"""
    
    def __init__(self, broker_host: str = "mqtt-broker", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = None
        self.devices: Dict[str, Device] = {}
        self.connected = False
        
    async def start(self):
        """Start MQTT adapter"""
        try:
            if not MQTT_AVAILABLE:
                logger.error("MQTT library not available")
                return False
                
            logger.info("Starting MQTT adapter...")
            
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start the MQTT loop
            self.client.loop_start()
            
            # Wait for connection to establish
            max_wait = 10  # Wait up to 10 seconds
            wait_count = 0
            while not self.connected and wait_count < max_wait:
                await asyncio.sleep(1)
                wait_count += 1
                logger.debug(f"Waiting for MQTT connection... ({wait_count}/{max_wait})")
            
            if not self.connected:
                logger.error("MQTT connection failed to establish within timeout")
                return False
            
            # Subscribe to device topics
            logger.info("Subscribing to MQTT topics...")
            self.client.subscribe("iot/+/raw")
            self.client.subscribe("iot/+/status")
            self.client.subscribe("iot/+/trends")
            self.client.subscribe("iot/+/command")
            
            logger.info(f"✅ Subscribed to topics: iot/+/raw, iot/+/status, iot/+/trends, iot/+/command")
            
            logger.info("MQTT adapter started successfully and connected to broker")
            return True
            
        except Exception as e:
            logger.error("Failed to start MQTT adapter", error=str(e))
            return False
    
    async def stop(self):
        """Stop MQTT adapter"""
        try:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            logger.info("MQTT adapter stopped")
        except Exception as e:
            logger.error("Error stopping MQTT adapter", error=str(e))
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Connected to MQTT broker successfully")
        else:
            self.connected = False
            logger.error("❌ Failed to connect to MQTT broker", return_code=rc)
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        if rc == 0:
            logger.info("🔄 Disconnected from MQTT broker (clean disconnect)")
        else:
            logger.warning(f"⚠️ Unexpected disconnect from MQTT broker (rc={rc})")
    
    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Extract device ID from topic
            device_id = topic.split('/')[1]
            
            print(f"🔍 MQTT MESSAGE RECEIVED: {topic} from {device_id}")
            print(f"   Payload keys: {list(payload.keys())}")
            print(f"   Current devices: {list(self.devices.keys())}")
            
            # Update or create device
            if device_id not in self.devices:
                self.devices[device_id] = Device(
                    device_id=device_id,
                    device_type=payload.get('device_type', 'unknown'),
                    protocol='mqtt',
                    status='online',
                    last_seen=time.time(),
                    metrics=payload.get('measurements', {}),
                    capabilities=payload.get('capabilities', [])
                )
                print(f"✅ NEW DEVICE CREATED: {device_id}")
                logger.info(f"New device discovered via MQTT: {device_id} ({payload.get('device_type', 'unknown')})")
            else:
                device = self.devices[device_id]
                device.status = 'online'
                device.last_seen = time.time()
                device.metrics = payload.get('measurements', {})
                print(f"🔄 DEVICE UPDATED: {device_id}")
                logger.debug(f"Device {device_id} updated via MQTT")
                
            print(f"📊 TOTAL DEVICES AFTER UPDATE: {len(self.devices)}")
            logger.info(f"📨 MQTT message processed: {topic} from {device_id}")
            
        except Exception as e:
            print(f"❌ MQTT MESSAGE ERROR: {e}")
            logger.error("Error processing MQTT message", error=str(e))
    
    async def discover_devices(self) -> List[Device]:
        """Discover devices on MQTT"""
        return list(self.devices.values())
    
    async def get_device_data(self, device_id: str) -> Dict[str, Any]:
        """Get current data from a device"""
        if device_id in self.devices:
            device = self.devices[device_id]
            return {
                'device_id': device.device_id,
                'device_type': device.device_type,
                'status': device.status,
                'last_seen': device.last_seen,
                'metrics': device.metrics or {},
                'capabilities': device.capabilities or []
            }
        return {}
    
    async def set_device_parameter(self, device_id: str, parameter: str, value: Any) -> bool:
        """Set a device parameter via MQTT"""
        try:
            if not self.connected:
                return False
                
            topic = f"iot/{device_id}/config"
            message = {
                'command': 'set_parameter',
                'parameter': parameter,
                'value': value,
                'timestamp': time.time()
            }
            
            result = self.client.publish(topic, json.dumps(message))
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error("Failed to set device parameter", device_id=device_id, parameter=parameter, error=str(e))
            return False
    
    async def send_device_command(self, device_id: str, command: str, parameters: Dict[str, Any] = None) -> bool:
        """Send a command to a device via MQTT"""
        try:
            if not self.connected:
                return False
                
            topic = f"iot/{device_id}/command"
            message = {
                'command': command,
                'parameters': parameters or {},
                'timestamp': time.time()
            }
            
            result = self.client.publish(topic, json.dumps(message))
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error("Failed to send device command", device_id=device_id, command=command, error=str(e))
            return False

class FDIServer:
    """Main FDI Communication Server"""
    
    def __init__(self, opcua_port: int = 4840, storage_path: str = "/app/fdi-packages"):
        self.opcua_port = opcua_port
        self.storage = FDIPackageBlobStorage(storage_path)
        self.adapters: Dict[str, DeviceProtocolAdapter] = {}
        self.devices: Dict[str, Device] = {}
        self.server = None
        self.running = False
        
        # Initialize protocol adapters
        self._init_adapters()
    
    def _init_adapters(self):
        """Initialize protocol adapters"""
        try:
            # MQTT adapter
            mqtt_adapter = MQTTAdapter()
            self.adapters['mqtt'] = mqtt_adapter
            
            logger.info("Protocol adapters initialized", adapters=list(self.adapters.keys()))
            
        except Exception as e:
            logger.error("Failed to initialize adapters", error=str(e))
    
    async def start(self):
        """Start the FDI server"""
        try:
            # Try to start OPC UA server (optional)
            await self._start_opcua_server()
            
            # Start protocol adapters
            await self._start_adapters()
            
            self.running = True
            logger.info("FDI server started successfully")
            
        except Exception as e:
            logger.error("Failed to start FDI server", error=str(e))
            raise
    
    async def _start_opcua_server(self):
        """Start OPC UA server"""
        try:
            if not OPCUA_AVAILABLE:
                logger.warning("OPC UA not available, skipping OPC UA server")
                return
                
            self.server = Server()
            await self.server.init()
            
            # Set server endpoint
            self.server.set_endpoint(f"opc.tcp://0.0.0.0:{self.opcua_port}")
            
            # Set server name
            uri = "http://iot-cloud.com/fdi"
            idx = await self.server.register_namespace(uri)
            
            # Create server object - try different approaches for compatibility
            try:
                server_obj = await self.server.get_objects_node()
            except Exception as e:
                logger.warning(f"get_objects_node() failed, trying alternative: {e}")
                # Try alternative approach
                server_obj = self.server.get_objects_node()
            
            # Add FDI methods
            await self._add_fdi_methods(server_obj, idx)
            
            # Start server
            await self.server.start()
            
            logger.info(f"OPC UA server started on port {self.opcua_port}")
            
        except Exception as e:
            logger.warning(f"Failed to start OPC UA server, continuing without OPC UA: {e}")
            self.server = None
    
    async def _add_fdi_methods(self, server_obj, idx):
        """Add FDI methods to OPC UA server"""
        try:
            # Create FDI methods object
            fdi_obj = await server_obj.add_object(idx, "FDIMethods")
            
            # DiscoverDevices method
            discover_method = await fdi_obj.add_method(
                idx, "DiscoverDevices",
                self._discover_devices_method_wrapper,
                [ua.VariantType.String],  # protocol filter
                [ua.VariantType.String]   # return device list as JSON
            )
            
            # GetDeviceParameters method
            get_params_method = await fdi_obj.add_method(
                idx, "GetDeviceParameters",
                self._get_device_parameters_method_wrapper,
                [ua.VariantType.String],  # device_id
                [ua.VariantType.String]   # return parameters as JSON
            )
            
            # SetDeviceParameters method
            set_params_method = await fdi_obj.add_method(
                idx, "SetDeviceParameters",
                self._set_device_parameters_method_wrapper,
                [ua.VariantType.String, ua.VariantType.String],  # device_id, parameters_json
                [ua.VariantType.Boolean]  # success
            )
            
            # SendDeviceCommand method
            send_cmd_method = await fdi_obj.add_method(
                idx, "SendDeviceCommand",
                self._send_device_command_method_wrapper,
                [ua.VariantType.String, ua.VariantType.String, ua.VariantType.String],  # device_id, command, parameters_json
                [ua.VariantType.Boolean]  # success
            )
            
            logger.info("FDI methods added to OPC UA server")
            
        except Exception as e:
            logger.error("Failed to add FDI methods", error=str(e))
    
    async def _discover_devices_method(self, parent, protocol_filter):
        """OPC UA method: DiscoverDevices"""
        try:
            protocol = protocol_filter.Value.Value if protocol_filter.Value else None
            devices = await self.discover_devices(protocol)
            
            # Convert to JSON
            device_list = []
            for device in devices:
                device_list.append({
                    'device_id': device.device_id,
                    'device_type': device.device_type,
                    'protocol': device.protocol,
                    'status': device.status,
                    'last_seen': device.last_seen
                })
            
            return ua.Variant(json.dumps(device_list), ua.VariantType.String)
            
        except Exception as e:
            logger.error("DiscoverDevices method error", error=str(e))
            return ua.Variant("[]", ua.VariantType.String)
    
    async def _get_device_parameters_method(self, parent, device_id):
        """OPC UA method: GetDeviceParameters"""
        try:
            device_id_str = device_id.Value.Value
            data = await self.get_device_data(device_id_str)
            
            return ua.Variant(json.dumps(data), ua.VariantType.String)
            
        except Exception as e:
            logger.error("GetDeviceParameters method error", error=str(e))
            return ua.Variant("{}", ua.VariantType.String)
    
    async def _set_device_parameters_method(self, parent, device_id, parameters_json):
        """OPC UA method: SetDeviceParameters"""
        try:
            device_id_str = device_id.Value.Value
            params_str = parameters_json.Value.Value
            
            params = json.loads(params_str)
            success = await self.set_device_parameter(device_id_str, params)
            
            return ua.Variant(success, ua.VariantType.Boolean)
            
        except Exception as e:
            logger.error("SetDeviceParameters method error", error=str(e))
            return ua.Variant(False, ua.VariantType.Boolean)
    
    async def _send_device_command_method(self, parent, device_id, command, parameters_json):
        """OPC UA method: SendDeviceCommand"""
        try:
            device_id_str = device_id.Value.Value
            command_str = command.Value.Value
            params_str = parameters_json.Value.Value
            
            params = json.loads(params_str) if params_str else {}
            success = await self.send_device_command(device_id_str, command_str, params)
            
            return ua.Variant(success, ua.VariantType.Boolean)
            
        except Exception as e:
            logger.error("SendDeviceCommand method error", error=str(e))
            return ua.Variant(False, ua.VariantType.Boolean)
    
    # Wrapper methods for OPC UA (to avoid bound method issues)
    async def _discover_devices_method_wrapper(self, parent, protocol_filter):
        """Wrapper for DiscoverDevices OPC UA method"""
        return await self._discover_devices_method(parent, protocol_filter)
    
    async def _get_device_parameters_method_wrapper(self, parent, device_id):
        """Wrapper for GetDeviceParameters OPC UA method"""
        return await self._get_device_parameters_method(parent, device_id)
    
    async def _set_device_parameters_method_wrapper(self, parent, device_id, parameters_json):
        """Wrapper for SetDeviceParameters OPC UA method"""
        return await self._set_device_parameters_method(parent, device_id, parameters_json)
    
    async def _send_device_command_method_wrapper(self, parent, device_id, command, parameters_json):
        """Wrapper for SendDeviceCommand OPC UA method"""
        return await self._send_device_command_method(parent, device_id, command, parameters_json)
    
    async def _start_adapters(self):
        """Start all protocol adapters"""
        try:
            for name, adapter in self.adapters.items():
                await adapter.start()
                logger.info(f"Started {name} adapter")
                
        except Exception as e:
            logger.error("Failed to start adapters", error=str(e))
    
    async def stop(self):
        """Stop the FDI server"""
        try:
            self.running = False
            
            # Stop adapters
            for name, adapter in self.adapters.items():
                await adapter.stop()
                logger.info(f"Stopped {name} adapter")
            
            # Stop OPC UA server
            if self.server:
                await self.server.stop()
                logger.info("OPC UA server stopped")
            
            logger.info("FDI server stopped")
            
        except Exception as e:
            logger.error("Error stopping FDI server", error=str(e))
    
    async def discover_devices(self, protocol: str = None) -> List[Device]:
        """Discover devices across all protocols or specific protocol"""
        try:
            all_devices = []
            
            for name, adapter in self.adapters.items():
                if protocol and name != protocol:
                    continue
                    
                try:
                    devices = await adapter.discover_devices()
                    all_devices.extend(devices)
                    
                    # Update our device registry
                    for device in devices:
                        self.devices[device.device_id] = device
                        logger.debug(f"Device discovered: {device.device_id} ({device.device_type}) via {name}")
                        
                except Exception as e:
                    logger.error(f"Error discovering devices on {name} adapter", error=str(e))
            
            logger.info(f"Device discovery completed: {len(all_devices)} devices found")
            return all_devices
            
        except Exception as e:
            logger.error("Error discovering devices", error=str(e))
            return []
    
    async def get_device_data(self, device_id: str) -> Dict[str, Any]:
        """Get data from a specific device"""
        try:
            if device_id in self.devices:
                device = self.devices[device_id]
                adapter = self.adapters.get(device.protocol)
                
                if adapter:
                    return await adapter.get_device_data(device_id)
            
            return {}
            
        except Exception as e:
            logger.error("Error getting device data", device_id=device_id, error=str(e))
            return {}
    
    async def set_device_parameter(self, device_id: str, parameters: Dict[str, Any]) -> bool:
        """Set parameters on a device"""
        try:
            if device_id in self.devices:
                device = self.devices[device_id]
                adapter = self.adapters.get(device.protocol)
                
                if adapter:
                    success = True
                    for param, value in parameters.items():
                        if not await adapter.set_device_parameter(device_id, param, value):
                            success = False
                    return success
            
            return False
            
        except Exception as e:
            logger.error("Error setting device parameters", device_id=device_id, error=str(e))
            return False
    
    async def send_device_command(self, device_id: str, command: str, parameters: Dict[str, Any] = None) -> bool:
        """Send a command to a device"""
        try:
            if device_id in self.devices:
                device = self.devices[device_id]
                adapter = self.adapters.get(device.protocol)
                
                if adapter:
                    return await adapter.send_device_command(device_id, command, parameters or {})
            
            return False
            
        except Exception as e:
            logger.error("Error sending device command", device_id=device_id, error=str(e))
            return False
    
    def get_fdi_package(self, device_type: str) -> Optional[FDIPackage]:
        """Get FDI package for a device type"""
        try:
            # Search for packages by device type
            packages = self.storage.list_packages(device_type=device_type)
            
            if packages:
                # Get the first available package
                package_id = packages[0]['package_id']
                package_data = self.storage.retrieve_package(package_id)
                
                if package_data:
                    return FDIPackage.from_dict(package_data)
            
            return None
            
        except Exception as e:
            logger.error("Error getting FDI package", device_type=device_type, error=str(e))
            return None

async def main():
    """Main entry point"""
    try:
        # Create and start FDI server
        server = FDIServer()
        
        # Start the server
        await server.start()
        
        # Keep running
        try:
            while server.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        
        # Stop the server
        await server.stop()
        
    except Exception as e:
        logger.error("FDI server error", error=str(e))
        raise

if __name__ == "__main__":
    asyncio.run(main())
