"""
Edge Core WebSocket Client for GRM Service
Implements WebSocket-based communication similar to DMAgent's edge_core.rs
"""
import asyncio
import json
import base64
import struct
from typing import Dict, Any, List, Optional
from loguru import logger
import websockets
from websockets.exceptions import ConnectionClosed, InvalidURI
from .config import settings


class JsonRpcRequest:
    """JSON-RPC 2.0 Request"""
    def __init__(self, method: str, params: Dict[str, Any], request_id: int = 1):
        self.jsonrpc = "2.0"
        self.method = method
        self.params = params
        self.id = request_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params,
            "id": self.id
        }


class JsonRpcResponse:
    """JSON-RPC 2.0 Response"""
    def __init__(self, data: Dict[str, Any]):
        self.jsonrpc = data.get("jsonrpc", "2.0")
        self.result = data.get("result")
        self.error = data.get("error")
        self.id = data.get("id")
    
    def is_error(self) -> bool:
        return self.error is not None
    
    def get_error(self) -> Optional[str]:
        if self.error:
            return str(self.error)
        return None


class ResourceConfig:
    """Resource configuration for Edge Core"""
    def __init__(self, object_id: int, object_instance_id: int, resource_id: int,
                 resource_name: Optional[str], operations: int, resource_type: str, value: float, 
                 periodic_update: bool = True):
        self.object_id = object_id
        self.object_instance_id = object_instance_id
        self.resource_id = resource_id
        self.resource_name = resource_name
        self.operations = operations
        self.resource_type = resource_type
        self.value = value
        self.periodic_update = periodic_update


class EdgeCoreClient:
    """WebSocket client for Edge Core communication"""
    
    def __init__(self, host: str = "192.168.1.198", port: int = 8081, name: str = "edge-grm-service"):
        self.host = host
        self.port = port
        self.name = name
        self.websocket = None
        self.connected = False
        self.api_path = "/1/grm"
        self.max_retries = 3
        self.retry_delay = 1.0
        
        logger.info(f"Edge Core client initialized for {host}:{port}")
    
    def _encode_value_base64(self, value: float) -> str:
        """Encode float value to base64 (similar to Rust implementation)"""
        # Convert float to 8-byte big-endian representation
        value_bytes = struct.pack('>d', value)
        return base64.b64encode(value_bytes).decode('utf-8')
    
    async def connect(self) -> bool:
        """Connect to Edge Core via WebSocket"""
        url = f"ws://{self.host}:{self.port}{self.api_path}"
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to connect to Edge Core at {url} (attempt {attempt + 1}/{self.max_retries})")
                
                self.websocket = await websockets.connect(url)
                self.connected = True
                
                logger.info(f"Successfully connected to Edge Core at {self.host}:{self.port}")
                return True
                
            except (ConnectionRefusedError, InvalidURI, OSError) as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
        
        logger.error(f"Failed to connect to Edge Core after {self.max_retries} attempts")
        return False
    
    async def disconnect(self):
        """Disconnect from Edge Core"""
        if self.websocket and self.connected:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from Edge Core")
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send JSON-RPC request and wait for response"""
        if not self.connected or not self.websocket:
            logger.error("Not connected to Edge Core")
            return None
        
        try:
            # Create JSON-RPC request
            request = JsonRpcRequest(method, params)
            request_str = json.dumps(request.to_dict())
            
            logger.debug(f"Sending request: {request_str}")
            
            # Send request
            await self.websocket.send(request_str)
            
            # Wait for response
            response_str = await self.websocket.recv()
            logger.debug(f"Received response: {response_str}")
            
            # Parse response
            response_data = json.loads(response_str)
            response = JsonRpcResponse(response_data)
            
            if response.is_error():
                error_msg = response.get_error()
                logger.error(f"JSON-RPC error: {error_msg}")
                return None
            
            return response.result
            
        except (ConnectionClosed, json.JSONDecodeError) as e:
            logger.error(f"Communication error: {e}")
            self.connected = False
            return None
    
    async def register_grm(self) -> Optional[Dict[str, Any]]:
        """Register as Gateway Resource Manager"""
        params = {"name": self.name}
        
        logger.info(f"Registering as GRM with name: {self.name}")
        
        result = await self._send_request("gw_resource_manager_register", params)
        
        if result:
            logger.info("GRM registration successful")
        else:
            logger.error("GRM registration failed")
        
        return result
    
    async def add_resource(self, resources: List[ResourceConfig]) -> Optional[Dict[str, Any]]:
        """Add resources to Edge Core"""
        # Convert resources to Edge Core format
        objects = []
        
        for resource in resources:
            value_base64 = self._encode_value_base64(resource.value)
            
            obj = {
                "objectId": resource.object_id,
                "objectInstances": [{
                    "objectInstanceId": resource.object_instance_id,
                    "resources": [{
                        "resourceId": resource.resource_id,
                        "resourceName": resource.resource_name,
                        "operations": resource.operations,
                        "type": resource.resource_type,
                        "value": value_base64
                    }]
                }]
            }
            objects.append(obj)
        
        params = {"objects": objects}
        
        logger.info(f"Adding {len(resources)} resources to Edge Core")
        
        result = await self._send_request("add_resource", params)
        
        if result:
            logger.info("Resource addition successful")
        else:
            logger.error("Resource addition failed")
        
        return result
    
    async def update_resource_value(self, resources: List[ResourceConfig]) -> Optional[Dict[str, Any]]:
        """Update resource values in Edge Core"""
        # Convert resources to Edge Core format
        objects = []
        
        for resource in resources:
            value_base64 = self._encode_value_base64(resource.value)
            
            obj = {
                "objectId": resource.object_id,
                "objectInstances": [{
                    "objectInstanceId": resource.object_instance_id,
                    "resources": [{
                        "resourceId": resource.resource_id,
                        "resourceName": resource.resource_name,
                        "operations": resource.operations,
                        "type": resource.resource_type,
                        "value": value_base64
                    }]
                }]
            }
            objects.append(obj)
        
        params = {"objects": objects}
        
        logger.info(f"Updating {len(resources)} resource values in Edge Core")
        
        result = await self._send_request("write_resource_value", params)
        
        if result:
            logger.info("Resource value update successful")
        else:
            logger.error("Resource value update failed")
        
        return result
    
    async def delete_resource(self, object_id: int, instance_id: int, resource_id: int) -> Optional[Dict[str, Any]]:
        """Delete a resource from Edge Core"""
        params = {
            "objects": [{
                "objectId": object_id,
                "objectInstances": [{
                    "objectInstanceId": instance_id,
                    "resources": [{
                        "resourceId": resource_id
                    }]
                }]
            }]
        }
        
        logger.info(f"Deleting resource: object_id={object_id}, instance_id={instance_id}, resource_id={resource_id}")
        
        result = await self._send_request("delete_resource", params)
        
        if result:
            logger.info("Resource deletion successful")
        else:
            logger.error("Resource deletion failed")
        
        return result
    
    async def device_register(self, device_id: str, object_id: int, instance_id: int, value: float) -> Optional[Dict[str, Any]]:
        """Register a device with Edge Core"""
        value_base64 = self._encode_value_base64(value)
        
        params = {
            "deviceId": device_id,
            "objects": [{
                "objectId": object_id,
                "objectInstances": [{
                    "objectInstanceId": instance_id,
                    "resources": [{
                        "resourceId": 0,
                        "resourceName": "Example Value",
                        "operations": 3,  # READ | WRITE
                        "type": "float",
                        "value": value_base64
                    }]
                }]
            }]
        }
        
        logger.info(f"Registering device: {device_id}")
        
        result = await self._send_request("device_register", params)
        
        if result:
            logger.info("Device registration successful")
        else:
            logger.error("Device registration failed")
        
        return result
    
    async def write(self, device_id: str, object_id: int, instance_id: int, value: float) -> Optional[Dict[str, Any]]:
        """Write value to device"""
        value_base64 = self._encode_value_base64(value)
        
        params = {
            "deviceId": device_id,
            "objects": [{
                "objectId": object_id,
                "objectInstances": [{
                    "objectInstanceId": instance_id,
                    "resources": [{
                        "resourceId": 0,
                        "type": "float",
                        "value": value_base64
                    }]
                }]
            }]
        }
        
        logger.info(f"Writing value {value} to device: {device_id}")
        
        result = await self._send_request("write", params)
        
        if result:
            logger.info("Write operation successful")
        else:
            logger.error("Write operation failed")
        
        return result
