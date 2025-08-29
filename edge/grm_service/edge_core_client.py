"""
Edge Core WebSocket Client for GRM Service
Implements WebSocket-based communication similar to DMAgent's edge_core.rs
"""
import asyncio
import json
import base64
import struct
from typing import Dict, Any, List, Optional, Callable, Awaitable
from loguru import logger
import websockets
from websockets.exceptions import ConnectionClosed, InvalidURI
from .config import settings
import time


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


class CloudUpdateMessage:
    """Cloud update message structure"""
    def __init__(self, data: Dict[str, Any]):
        self.message_type = data.get("type", "unknown")
        self.timestamp = data.get("timestamp")
        self.device_id = data.get("device_id")
        self.resource_updates = data.get("resource_updates", [])
        self.metadata = data.get("metadata", {})
    
    def is_resource_update(self) -> bool:
        return self.message_type == "resource_update"
    
    def is_configuration_update(self) -> bool:
        return self.message_type == "configuration_update"
    
    def is_command(self) -> bool:
        return self.message_type == "command"


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
    """WebSocket client for Edge Core communication with cloud update support"""
    
    def __init__(self, host: str = "192.168.1.198", port: int = 8081, name: str = "edge-grm-service"):
        self.host = host
        self.port = port
        self.name = name
        self.websocket = None
        self.connected = False
        self.api_path = "/1/grm"
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Cloud update handling
        self.cloud_update_callback: Optional[Callable[[CloudUpdateMessage], Awaitable[None]]] = None
        self.message_listener_task: Optional[asyncio.Task] = None
        self.listening = False
        
        # Message queue for handling concurrent operations
        self.message_queue = asyncio.Queue()
        self.pending_requests = {}  # request_id -> future
        self.next_request_id = 1
        
        logger.info(f"Edge Core client initialized for {host}:{port}")
    
    def set_cloud_update_callback(self, callback: Callable[[CloudUpdateMessage], Awaitable[None]]):
        """Set callback for handling cloud updates"""
        self.cloud_update_callback = callback
        logger.info("Cloud update callback registered")
    
    def _encode_value_base64(self, value: float) -> str:
        """Encode float value to base64 (similar to Rust implementation)"""
        # Convert float to 8-byte big-endian representation
        value_bytes = struct.pack('>d', value)
        return base64.b64encode(value_bytes).decode('utf-8')
    
    def _decode_value_base64(self, value_base64: str) -> float:
        """Decode base64 value to float"""
        try:
            value_bytes = base64.b64decode(value_base64)
            return struct.unpack('>d', value_bytes)[0]
        except Exception as e:
            logger.error(f"Failed to decode base64 value: {e}")
            return 0.0
    
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
        # Stop message listening
        await self.stop_message_listening()
        
        if self.websocket and self.connected:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from Edge Core")
    
    async def start_message_listening(self):
        """Start listening for cloud updates"""
        if self.listening:
            logger.warning("Message listening already started")
            return
        
        if not self.connected or not self.websocket:
            logger.error("Cannot start message listening: not connected")
            return
        
        self.listening = True
        self.message_listener_task = asyncio.create_task(self._message_listener_loop())
        logger.info("Started cloud message listening")
    
    async def stop_message_listening(self):
        """Stop listening for cloud updates"""
        if not self.listening:
            return
        
        self.listening = False
        
        if self.message_listener_task and not self.message_listener_task.done():
            self.message_listener_task.cancel()
            try:
                await self.message_listener_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped cloud message listening")
    
    async def _message_listener_loop(self):
        """Continuous loop for listening to cloud messages"""
        logger.info("Cloud message listener loop started")
        
        while self.listening and self.connected:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                await self._handle_incoming_message(message)
                
            except asyncio.TimeoutError:
                # Timeout is expected, continue listening
                continue
            except ConnectionClosed:
                logger.warning("WebSocket connection closed during message listening")
                self.connected = False
                break
            except Exception as e:
                logger.error(f"Error in message listener loop: {e}")
                await asyncio.sleep(1.0)  # Brief pause before retrying
        
        logger.info("Cloud message listener loop ended")
    
    async def _handle_incoming_message(self, message: str):
        """Handle incoming message from Edge Core"""
        try:
            logger.debug(f"Received message: {message}")
            
            # Parse message
            data = json.loads(message)
            
            # Check if it's a JSON-RPC write command (cloud update)
            if self._is_jsonrpc_write_command(data):
                await self._handle_jsonrpc_write_command(data)
                return
            
            # Check if it's a JSON-RPC response (for our requests)
            if "jsonrpc" in data and "id" in data:
                request_id = data.get("id")
                if request_id in self.pending_requests:
                    # This is a response to one of our requests
                    future = self.pending_requests.pop(request_id)
                    future.set_result(data)
                    logger.debug("JSON-RPC response handled")
                else:
                    logger.debug("Received JSON-RPC response (handled by request/response)")
                return
            
            # Check if it's a cloud update message
            if self._is_cloud_update_message(data):
                await self._handle_cloud_update(data)
            else:
                logger.debug(f"Unknown message type: {data.get('type', 'unknown')}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse incoming message: {e}")
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")
    
    def _is_jsonrpc_write_command(self, data: Dict[str, Any]) -> bool:
        """Check if message is a JSON-RPC write command from Edge Core"""
        return (
            isinstance(data, dict) and
            data.get("jsonrpc") == "2.0" and
            data.get("method") == "write" and
            "params" in data and
            "uri" in data.get("params", {})
        )
    
    async def _handle_jsonrpc_write_command(self, data: Dict[str, Any]):
        """Handle JSON-RPC write command from Edge Core as cloud update"""
        try:
            params = data.get("params", {})
            uri = params.get("uri", {})
            value_base64 = params.get("value", "")
            
            # Decode the value
            value = self._decode_value_base64(value_base64)
            
            # Get resource details for better logging
            object_id = uri.get("objectId")
            instance_id = uri.get("objectInstanceId")
            resource_id = uri.get("resourceId")
            
            # Try to find the resource name from local resources (if available)
            resource_name = "unknown"
            if hasattr(self, 'resource_manager') and self.resource_manager:
                resource = self.resource_manager.find_resource(object_id, instance_id, resource_id)
                if resource:
                    resource_name = resource.resource_name
            
            # Log a clear, user-friendly message
            logger.info(f"🌐 CLOUD UPDATE RECEIVED: {resource_name} (ID: {object_id}:{instance_id}:{resource_id}) = {value}")
            
            # Create cloud update message structure
            cloud_update_data = {
                "type": "resource_update",
                "timestamp": time.time(),
                "device_id": "edge-core",
                "resource_updates": [
                    {
                        "object_id": object_id,
                        "instance_id": instance_id,
                        "resource_id": resource_id,
                        "value": value
                    }
                ]
            }
            
            # Process as cloud update
            await self._handle_cloud_update(cloud_update_data)
            
        except Exception as e:
            logger.error(f"Error handling JSON-RPC write command: {e}")
    
    def _is_cloud_update_message(self, data: Dict[str, Any]) -> bool:
        """Check if message is a cloud update"""
        return (
            isinstance(data, dict) and
            "type" in data and
            data["type"] in ["resource_update", "configuration_update", "command"]
        )
    
    async def _handle_cloud_update(self, data: Dict[str, Any]):
        """Handle cloud update message"""
        try:
            cloud_update = CloudUpdateMessage(data)
            logger.info(f"Received cloud update: {cloud_update.message_type}")
            
            # Log update details
            if cloud_update.is_resource_update():
                logger.info(f"Resource update for device {cloud_update.device_id}: "
                           f"{len(cloud_update.resource_updates)} resources")
            elif cloud_update.is_configuration_update():
                logger.info(f"Configuration update for device {cloud_update.device_id}")
            elif cloud_update.is_command():
                logger.info(f"Command received for device {cloud_update.device_id}")
            
            # Call registered callback if available
            if self.cloud_update_callback:
                try:
                    await self.cloud_update_callback(cloud_update)
                except Exception as e:
                    logger.error(f"Error in cloud update callback: {e}")
            else:
                logger.warning("No cloud update callback registered")
                
        except Exception as e:
            logger.error(f"Error processing cloud update: {e}")
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send JSON-RPC request and wait for response"""
        return await self._send_request_with_timeout(method, params, timeout=30.0)
    
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
        """Update resource values in Edge Core with retry logic"""
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
        
        # Try with longer timeout for resource updates
        result = await self._send_request_with_retry("write_resource_value", params, max_retries=2, timeout=60.0)
        
        if result:
            logger.info("Resource value update successful")
        else:
            logger.error("Resource value update failed")
        
        return result
    
    async def _send_request_with_retry(self, method: str, params: Dict[str, Any], max_retries: int = 2, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Send JSON-RPC request with retry logic and configurable timeout"""
        for attempt in range(max_retries):
            try:
                result = await self._send_request_with_timeout(method, params, timeout)
                if result:
                    return result
                else:
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.warning(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0)  # Brief pause before retry
        
        return None
    
    async def _send_request_with_timeout(self, method: str, params: Dict[str, Any], timeout: float) -> Optional[Dict[str, Any]]:
        """Send JSON-RPC request with custom timeout"""
        if not self.connected or not self.websocket:
            logger.error("Not connected to Edge Core")
            return None
        
        try:
            # Create JSON-RPC request
            request_id = self.next_request_id
            self.next_request_id += 1
            
            request = JsonRpcRequest(method, params, request_id)
            request_str = json.dumps(request.to_dict())
            
            logger.debug(f"Sending request: {request_str}")
            
            # Create future for response
            future = asyncio.Future()
            self.pending_requests[request_id] = future
            
            # Send request
            await self.websocket.send(request_str)
            
            # Wait for response with custom timeout
            try:
                response_data = await asyncio.wait_for(future, timeout=timeout)
                response = JsonRpcResponse(response_data)
                
                if response.is_error():
                    error_msg = response.get_error()
                    logger.error(f"JSON-RPC error: {error_msg}")
                    return None
                
                return response.result
                
            except asyncio.TimeoutError:
                # Remove from pending requests
                self.pending_requests.pop(request_id, None)
                logger.error(f"Request timeout for method: {method} (timeout: {timeout}s)")
                return None
            
        except (ConnectionClosed, json.JSONDecodeError) as e:
            logger.error(f"Communication error: {e}")
            self.connected = False
            return None
        except Exception as e:
            logger.error(f"Unexpected error in _send_request: {e}")
            return None
    
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
