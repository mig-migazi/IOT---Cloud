# FDI (Field Device Integration) Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [Core Components](#core-components)
4. [Protocol Adapter Pattern](#protocol-adapter-pattern)
5. [Data Models](#data-models)
6. [Communication Flows](#communication-flows)
7. [Integration with IoT Platform](#integration-with-iot-platform)
8. [API Reference](#api-reference)
9. [Usage Examples](#usage-examples)
10. [Extension Guide](#extension-guide)

---

## Overview

### What is FDI?

**Field Device Integration (FDI)** is an international standard (IEC 62769) that provides a unified approach for integrating field devices into control systems and automation platforms. Our implementation adapts FDI principles for modern IoT cloud architectures.

### Why FDI?

Traditional IoT platforms require custom integration code for each device type and protocol. FDI solves this by:

- **Standardized Device Definitions**: Single source of truth for device capabilities
- **Protocol Agnostic**: Abstract device integration from underlying protocols (MQTT, Modbus, OPC UA, HTTP)
- **Vendor Independence**: Devices from different manufacturers work seamlessly
- **Self-Describing Devices**: FDI packages contain all metadata, parameters, and commands
- **Dynamic Discovery**: Automatically discover and configure devices

### Key Benefits in Our IoT Platform

1. **Simplified Device Onboarding**: Add new device types by creating FDI packages
2. **Unified Device Management**: Single dashboard for all devices regardless of protocol
3. **Schema Registry Integration**: Automatic JSON schema generation from FDI packages
4. **Alarm System Integration**: Device parameters define alarm rules
5. **Protocol Flexibility**: Support MQTT, Modbus, HTTP, and custom protocols

---

## Architecture Principles

### 1. Protocol Adapter Pattern

Our FDI implementation uses the **Adapter Pattern** to abstract device communication protocols:

```
┌─────────────────┐
│   FDI Host      │ (Dashboard, OPC UA Client)
│   Applications  │
└────────┬────────┘
         │
         │ OPC UA (optional)
         │
┌────────▼────────────────────────────────┐
│      FDI Communication Server           │
│  (fdi_server.py - FDIServer class)      │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │  MQTT    │  │ Modbus   │  │  HTTP │ │
│  │ Adapter  │  │ Adapter  │  │Adapter│ │
│  └────┬─────┘  └────┬─────┘  └───┬───┘ │
└───────┼────────────┼────────────┼──────┘
        │            │            │
        │ Protocol-Specific Communication
        │            │            │
   ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
   │  MQTT   │  │ Modbus │  │  HTTP  │
   │ Devices │  │Devices │  │Devices │
   └─────────┘  └────────┘  └────────┘
```

**Key Principle**: Host applications interact with a uniform API, while protocol adapters handle device-specific communication.

### 2. FDI Package as Single Source of Truth

FDI packages define everything about a device:

```
┌──────────────────────────────────────┐
│         FDI Package                  │
├──────────────────────────────────────┤
│ • Device Type Metadata               │
│ • Parameters (measurements, configs) │
│ • Commands (actions device can do)   │
│ • Capabilities (what device supports)│
│ • Data Formats & Schemas             │
│ • Protocol Information               │
└──────────────────────────────────────┘
         │
         ├───► Schema Registry (JSON schemas)
         ├───► Alarm Rules (parameter thresholds)
         ├───► Dashboard UI (parameter display)
         └───► Device Discovery (capability matching)
```

### 3. Blob Storage for Package Management

FDI packages are stored in a **file-based blob storage** with manifest management:

```
/app/fdi-packages/
├── manifest.json              # Index of all packages
└── packages/
    ├── abc123def456/           # Package ID
    │   └── package.json        # Full FDI package definition
    ├── 789ghi012jkl/
    │   └── package.json
    └── ...
```

**Manifest Structure**:
```json
{
  "version": "1.0.0",
  "packages": {
    "abc123def456": {
      "package_id": "abc123def456",
      "device_type": "smart_breaker",
      "manufacturer": "ElectroCorp",
      "model": "SB-2000",
      "version": "2.1.0",
      "checksum": "sha256...",
      "file_path": "/app/fdi-packages/packages/abc123def456/package.json",
      "size_bytes": 15234,
      "stored_at": "2025-11-04T12:00:00Z"
    }
  }
}
```

---

## Core Components

### 1. FDI Package (`fdi_package.py`)

#### `FDIDeviceParameter`
Defines a single device parameter (measurement, configuration, status, or command parameter).

**Attributes**:
- `name`: Parameter identifier (e.g., "voltage_phase_a")
- `description`: Human-readable description
- `data_type`: Python/JSON type (float, integer, string, boolean, object)
- `unit`: Optional unit of measurement (V, A, °C, Hz)
- `min_value` / `max_value`: Valid range for numeric parameters
- `valid_values`: List of allowed values for enumerations
- `default_value`: Default value for configuration parameters
- `access_level`: "read_only", "read_write", or "write_only"
- `category`: "measurement", "configuration", "status", or "command"

**Example**:
```python
FDIDeviceParameter(
    name="voltage_phase_a",
    description="Phase A voltage",
    data_type="float",
    unit="V",
    min_value=110.0,
    max_value=130.0,
    category="measurement"
)
```

#### `FDIDeviceCommand`
Defines a command that can be executed on a device.

**Attributes**:
- `name`: Command identifier (e.g., "trip_breaker")
- `description`: What the command does
- `parameters`: List of `FDIDeviceParameter` objects (command arguments)
- `return_type`: Expected return type (boolean, object, string)
- `timeout_seconds`: Maximum execution time
- `requires_confirmation`: Whether operator confirmation is needed

**Example**:
```python
FDIDeviceCommand(
    name="set_trip_threshold",
    description="Set trip current threshold",
    parameters=[
        FDIDeviceParameter(
            name="threshold",
            description="New trip threshold value",
            data_type="float",
            unit="A",
            min_value=50.0,
            max_value=200.0
        )
    ],
    return_type="boolean",
    timeout_seconds=30
)
```

#### `FDIDeviceType`
Complete device type definition.

**Attributes**:
- `device_type`: Unique device type identifier (e.g., "smart_breaker")
- `name`: Human-readable device type name
- `description`: Device type description
- `category`: Device category (e.g., "electrical_protection")
- `manufacturer`: Manufacturer name
- `model`: Model identifier
- `version`: Firmware/device version
- `capabilities`: List of capability strings
- `parameters`: List of all device parameters
- `commands`: List of all device commands
- `data_format`: Data serialization format (json, xml, protobuf)
- `update_frequency`: Expected data update frequency
- `retention_policy`: Data retention period

#### `FDIPackage`
Container for complete FDI package with versioning and metadata.

**Methods**:
- `to_dict()`: Convert package to dictionary
- `to_json()`: Serialize package to JSON
- `validate()`: Validate package structure and required fields
- `from_dict(data)`: Deserialize package from dictionary

---

### 2. FDI Blob Storage (`fdi_blob_storage.py`)

#### `FDIPackageBlobStorage`
Manages persistent storage of FDI packages with manifest indexing.

**Key Methods**:

##### `store_package(package_data: Dict, package_id: str) -> bool`
Store a new FDI package or update existing one.

```python
storage = FDIPackageBlobStorage("/app/fdi-packages")
package = create_smart_breaker_fdi_package()
success = storage.store_package(package.to_dict(), package.package_id)
```

##### `retrieve_package(package_id: str) -> Optional[Dict]`
Retrieve a stored FDI package by ID.

```python
package_data = storage.retrieve_package("abc123def456")
if package_data:
    package = FDIPackage.from_dict(package_data)
```

##### `list_packages(device_type: str = None, manufacturer: str = None) -> List[Dict]`
List available packages with optional filtering.

```python
# List all packages
all_packages = storage.list_packages()

# List packages for specific device type
smart_breaker_packages = storage.list_packages(device_type="smart_breaker")

# List packages from specific manufacturer
electrocorp_packages = storage.list_packages(manufacturer="ElectroCorp")
```

##### `delete_package(package_id: str) -> bool`
Delete a package from storage.

```python
success = storage.delete_package("abc123def456")
```

##### `get_storage_stats() -> Dict`
Get storage statistics.

```python
stats = storage.get_storage_stats()
# Returns:
# {
#   "total_packages": 5,
#   "total_size_bytes": 76543,
#   "storage_path": "/app/fdi-packages",
#   "last_updated": "2025-11-04T12:00:00Z"
# }
```

**Storage Features**:
- **Checksum Validation**: SHA-256 checksums ensure data integrity
- **Atomic Operations**: File operations are atomic to prevent corruption
- **Manifest Caching**: Fast package lookup without reading files
- **Orphan Cleanup**: `cleanup_orphaned_files()` removes untracked packages

---

### 3. FDI Communication Server (`fdi_server.py`)

#### `DeviceProtocolAdapter` (Abstract Base Class)
Defines the interface that all protocol adapters must implement.

**Abstract Methods**:
```python
async def start() -> bool
async def stop()
async def discover_devices() -> List[Device]
async def get_device_data(device_id: str) -> Dict[str, Any]
async def set_device_parameter(device_id: str, parameter: str, value: Any) -> bool
async def send_device_command(device_id: str, command: str, parameters: Dict) -> bool
```

**Design Pattern**: Template Method Pattern - defines the contract for protocol adapters.

#### `MQTTAdapter` (Concrete Implementation)
MQTT protocol adapter for IoT devices.

**Architecture**:
```
┌────────────────────────────────────────┐
│         MQTTAdapter                    │
├────────────────────────────────────────┤
│ • Paho MQTT Client                     │
│ • Topic Subscriptions:                 │
│   - iot/+/raw       (telemetry)        │
│   - iot/+/status    (device status)    │
│   - iot/+/trends    (aggregated data)  │
│   - iot/+/command   (command responses)│
│ • Device Registry (in-memory)          │
│ • Auto-discovery on message receipt    │
└────────────────────────────────────────┘
```

**Key Features**:
- **Automatic Device Discovery**: Devices auto-register when they publish messages
- **Connection Management**: Automatic reconnection with exponential backoff
- **Topic Pattern Matching**: Wildcard subscriptions for device discovery
- **Status Tracking**: Last-seen timestamps and online/offline status
- **Command Publishing**: Send commands via `iot/{device_id}/command` topic

**Message Flow**:
```
Device publishes → iot/breaker-001/raw
                ↓
MQTT Adapter receives message
                ↓
Parse device_id from topic
                ↓
Create or update Device object
                ↓
Store in self.devices registry
                ↓
Device available for FDI queries
```

**Example Usage**:
```python
adapter = MQTTAdapter(broker_host="mqtt-broker", broker_port=1883)
await adapter.start()

# Discover devices
devices = await adapter.discover_devices()

# Get device data
data = await adapter.get_device_data("breaker-001")

# Send command
success = await adapter.send_device_command(
    "breaker-001", 
    "trip_breaker", 
    {}
)
```

#### `FDIServer`
Main FDI server orchestrating protocol adapters and OPC UA interface.

**Components**:
```
┌──────────────────────────────────────────────┐
│             FDIServer                        │
├──────────────────────────────────────────────┤
│ ┌──────────────────────────────────────┐    │
│ │   OPC UA Server (optional)           │    │
│ │   • Port 4840                        │    │
│ │   • FDI Methods exposed via OPC UA   │    │
│ │   • DiscoverDevices()                │    │
│ │   • GetDeviceParameters()            │    │
│ │   • SetDeviceParameters()            │    │
│ │   • SendDeviceCommand()              │    │
│ └──────────────────────────────────────┘    │
│                                              │
│ ┌──────────────────────────────────────┐    │
│ │   Protocol Adapter Registry          │    │
│ │   • adapters: Dict[str, Adapter]     │    │
│ │   • mqtt → MQTTAdapter               │    │
│ │   • modbus → ModbusAdapter (future)  │    │
│ └──────────────────────────────────────┘    │
│                                              │
│ ┌──────────────────────────────────────┐    │
│ │   Device Registry                    │    │
│ │   • devices: Dict[str, Device]       │    │
│ │   • Cross-protocol device tracking   │    │
│ └──────────────────────────────────────┘    │
│                                              │
│ ┌──────────────────────────────────────┐    │
│ │   FDI Package Storage                │    │
│ │   • FDIPackageBlobStorage            │    │
│ │   • Package lookup by device type    │    │
│ └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

**Key Methods**:

##### `async start()`
Initialize and start the FDI server.

```python
server = FDIServer(opcua_port=4840, storage_path="/app/fdi-packages")
await server.start()
# - Starts OPC UA server (if available)
# - Starts all protocol adapters
# - Begins device discovery
```

##### `async discover_devices(protocol: str = None) -> List[Device]`
Discover devices across all protocols or specific protocol.

```python
# Discover all devices
all_devices = await server.discover_devices()

# Discover only MQTT devices
mqtt_devices = await server.discover_devices(protocol="mqtt")
```

##### `async get_device_data(device_id: str) -> Dict`
Get current data from a device.

```python
data = await server.get_device_data("breaker-001")
# Returns:
# {
#   "device_id": "breaker-001",
#   "device_type": "smart_breaker",
#   "status": "online",
#   "last_seen": 1730736000.0,
#   "metrics": {
#     "voltage": {"phase_a": 120.0, "phase_b": 119.5, "phase_c": 121.0},
#     "current": {"phase_a": 45.2, "phase_b": 43.8, "phase_c": 44.5}
#   }
# }
```

##### `async set_device_parameter(device_id: str, parameters: Dict) -> bool`
Set one or more device parameters.

```python
success = await server.set_device_parameter(
    "breaker-001",
    {"trip_current_threshold": 100.0}
)
```

##### `async send_device_command(device_id: str, command: str, parameters: Dict) -> bool`
Send a command to a device.

```python
success = await server.send_device_command(
    "breaker-001",
    "trip_breaker",
    {}  # No parameters needed for this command
)
```

##### `get_fdi_package(device_type: str) -> Optional[FDIPackage]`
Retrieve FDI package for a device type.

```python
package = server.get_fdi_package("smart_breaker")
if package:
    print(f"Device type: {package.device_type.name}")
    print(f"Parameters: {len(package.device_type.parameters)}")
    print(f"Commands: {len(package.device_type.commands)}")
```

---

## Protocol Adapter Pattern

### Why Protocol Adapters?

IoT devices use various communication protocols:
- **MQTT**: Lightweight pub/sub for IoT
- **Modbus**: Industrial fieldbus protocol
- **OPC UA**: Industrial automation standard
- **HTTP/REST**: Web-based APIs
- **CoAP**: Constrained Application Protocol

The **Adapter Pattern** allows the FDI server to work with all protocols through a uniform interface.

### Creating a New Protocol Adapter

**Step 1**: Implement `DeviceProtocolAdapter` interface

```python
class ModbusAdapter(DeviceProtocolAdapter):
    def __init__(self, host: str, port: int = 502):
        self.host = host
        self.port = port
        self.client = None
        self.devices = {}
    
    async def start(self):
        """Initialize Modbus client"""
        from pymodbus.client import AsyncModbusTcpClient
        self.client = AsyncModbusTcpClient(self.host, self.port)
        await self.client.connect()
        return self.client.connected
    
    async def stop(self):
        """Disconnect Modbus client"""
        if self.client:
            self.client.close()
    
    async def discover_devices(self) -> List[Device]:
        """Scan Modbus network for devices"""
        discovered_devices = []
        # Scan slave IDs 1-247
        for slave_id in range(1, 248):
            try:
                # Read device identification
                result = await self.client.read_device_information(
                    slave=slave_id
                )
                if result:
                    device = Device(
                        device_id=f"modbus-{slave_id}",
                        device_type="modbus_device",
                        protocol="modbus",
                        status="online"
                    )
                    discovered_devices.append(device)
                    self.devices[device.device_id] = device
            except:
                continue
        return discovered_devices
    
    async def get_device_data(self, device_id: str) -> Dict:
        """Read holding registers from Modbus device"""
        slave_id = int(device_id.split('-')[1])
        result = await self.client.read_holding_registers(
            address=0, 
            count=10, 
            slave=slave_id
        )
        return {"registers": result.registers}
    
    async def set_device_parameter(self, device_id: str, 
                                   parameter: str, value: Any) -> bool:
        """Write to Modbus register"""
        # Map parameter name to register address
        register_map = {"setpoint": 0, "mode": 1}
        address = register_map.get(parameter)
        if address is None:
            return False
        
        slave_id = int(device_id.split('-')[1])
        result = await self.client.write_register(
            address=address, 
            value=value, 
            slave=slave_id
        )
        return not result.isError()
    
    async def send_device_command(self, device_id: str, 
                                  command: str, parameters: Dict) -> bool:
        """Execute Modbus command (write coil or register)"""
        # Command implementation here
        return True
```

**Step 2**: Register adapter with FDI server

```python
# In FDIServer._init_adapters()
modbus_adapter = ModbusAdapter(host="modbus-gateway", port=502)
self.adapters['modbus'] = modbus_adapter
```

**Step 3**: FDI server automatically uses the adapter

```python
# Discovery works across all protocols
devices = await server.discover_devices()
# Returns devices from MQTT, Modbus, and any other registered adapters

# Commands work transparently
await server.send_device_command("modbus-5", "start_pump", {})
# FDI server routes to ModbusAdapter automatically
```

---

## Data Models

### Device Data Model

```python
@dataclass
class Device:
    device_id: str              # Unique device identifier
    device_type: str            # Type from FDI package (e.g., "smart_breaker")
    protocol: str               # Communication protocol ("mqtt", "modbus", etc.)
    status: str                 # "online", "offline", "error"
    last_seen: float           # Unix timestamp of last communication
    metrics: Dict[str, Any]     # Current measurement values
    capabilities: Dict[str, Any] # Device capabilities
    fdi_package: Optional[FDIPackage]  # Associated FDI package
```

### FDI Package Data Model

```
FDIPackage
├── package_id: str
├── version: str
├── schema_version: str
├── created_at: str
├── metadata: Dict
└── device_type: FDIDeviceType
    ├── device_type: str
    ├── name: str
    ├── description: str
    ├── category: str
    ├── manufacturer: str
    ├── model: str
    ├── version: str
    ├── capabilities: List[str]
    ├── parameters: List[FDIDeviceParameter]
    │   ├── name: str
    │   ├── description: str
    │   ├── data_type: str
    │   ├── unit: Optional[str]
    │   ├── min_value: Optional[float]
    │   ├── max_value: Optional[float]
    │   ├── valid_values: Optional[List]
    │   ├── default_value: Optional[Any]
    │   ├── access_level: str
    │   └── category: str
    ├── commands: List[FDIDeviceCommand]
    │   ├── name: str
    │   ├── description: str
    │   ├── parameters: List[FDIDeviceParameter]
    │   ├── return_type: str
    │   ├── timeout_seconds: int
    │   └── requires_confirmation: bool
    ├── data_format: str
    ├── update_frequency: str
    └── retention_policy: str
```

---

## Communication Flows

### 1. Device Discovery Flow

```
┌──────────────┐
│   Dashboard  │
│   (User)     │
└──────┬───────┘
       │ 1. Click "Discover Devices"
       ▼
┌──────────────────────┐
│   FDI Server         │
│   discover_devices() │
└──────┬───────────────┘
       │ 2. Query all adapters
       ▼
┌──────────────────────┐
│   MQTT Adapter       │
│   discover_devices() │
└──────┬───────────────┘
       │ 3. Return devices from
       │    self.devices registry
       ▼
┌──────────────────────┐
│   Device Registry    │
│   {                  │
│     "breaker-001": {  │
│       "device_type": "smart_breaker",
│       "protocol": "mqtt",
│       "status": "online"
│     }                │
│   }                  │
└──────┬───────────────┘
       │ 4. Get FDI package for device_type
       ▼
┌──────────────────────┐
│   FDI Blob Storage   │
│   retrieve_package() │
└──────┬───────────────┘
       │ 5. Return FDI package
       ▼
┌──────────────────────┐
│   Dashboard          │
│   Display device     │
│   with parameters    │
│   and commands       │
└──────────────────────┘
```

### 2. Get Device Data Flow

```
Dashboard ──[GET /api/devices/breaker-001]──► Web UI (web_ui.py)
                                                      │
                                                      │ Call FDI Server API
                                                      ▼
                                             FDIServer.get_device_data()
                                                      │
                                                      │ Lookup device protocol
                                                      ▼
                                             MQTTAdapter.get_device_data()
                                                      │
                                                      │ Return cached metrics
                                                      ▼
                                             {
                                               "device_id": "breaker-001",
                                               "metrics": {
                                                 "voltage": {...},
                                                 "current": {...}
                                               }
                                             }
                                                      │
                                                      ▼
Dashboard ◄──[JSON Response]────────────────── Web UI
```

### 3. Send Command Flow

```
Dashboard ──[POST /api/devices/breaker-001/command]──► Web UI
                                                           │
                                                           │ {
                                                           │   "command": "trip_breaker",
                                                           │   "parameters": {}
                                                           │ }
                                                           ▼
                                              FDIServer.send_device_command()
                                                           │
                                                           │ Route to protocol adapter
                                                           ▼
                                              MQTTAdapter.send_device_command()
                                                           │
                                                           │ Publish MQTT message
                                                           ▼
┌───────────────────────────────────────────────────────────────┐
│ MQTT Broker                                                   │
│ Topic: iot/breaker-001/command                                │
│ Payload: {                                                    │
│   "command": "trip_breaker",                                  │
│   "parameters": {},                                           │
│   "timestamp": 1730736000.0                                   │
│ }                                                             │
└───────────────────────────────────────────────────────────────┘
                                    │
                                    │ Device subscribes to command topic
                                    ▼
                          ┌─────────────────┐
                          │  Smart Breaker  │
                          │  (Device)       │
                          │  • Receives cmd │
                          │  • Executes     │
                          │  • Publishes    │
                          │    status       │
                          └─────────────────┘
```

### 4. Automatic Device Registration (MQTT)

```
Smart Breaker Device
       │
       │ Publish telemetry
       ▼
iot/breaker-001/raw ──► MQTT Broker
                              │
                              │ Forward to subscribers
                              ▼
                     MQTTAdapter._on_message()
                              │
                              │ Parse topic & payload
                              │ Extract device_id
                              ▼
                     Is device in self.devices?
                     ┌────NO────┐      ┌────YES────┐
                     ▼                  ▼
              Create Device()     Update Device()
              - device_id         - status = "online"
              - device_type       - last_seen = now()
              - protocol = "mqtt" - metrics = payload
              - status = "online"
                     │                  │
                     └──────┬───────────┘
                            ▼
                  Store in self.devices
                            │
                            ▼
              Device available for FDI queries
```

---

## Integration with IoT Platform

### 1. Schema Registry Integration

FDI packages automatically generate JSON schemas for the Schema Registry:

```python
# In web_ui.py - auto_initialize_fdi()

# Get all FDI packages
packages = storage.list_packages()

for package_info in packages:
    package_data = storage.retrieve_package(package_info['package_id'])
    package = FDIPackage.from_dict(package_data)
    
    # Generate JSON schema from FDI parameters
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {}
    }
    
    for param in package.device_type.parameters:
        schema["properties"][param.name] = {
            "type": param.data_type,
            "description": param.description
        }
        if param.unit:
            schema["properties"][param.name]["unit"] = param.unit
    
    # Register schema with Schema Registry
    register_schema_with_registry(package.device_type.device_type, schema)
```

**Benefits**:
- Automatic schema generation (no manual schema creation)
- Schema versioning matches FDI package versions
- Consistent validation across platform

### 2. Alarm System Integration

Alarm rules are based on FDI parameter definitions:

```python
# Alarm rule creation from FDI package

fdi_package = server.get_fdi_package("smart_breaker")

for param in fdi_package.device_type.parameters:
    if param.category == "measurement" and param.min_value and param.max_value:
        # Create alarm rules for out-of-range conditions
        create_alarm_rule(
            device_type="smart_breaker",
            field_path=f"measurements.{param.name}",
            operator="<",
            threshold_value=param.min_value,
            severity="critical",
            alarm_message=f"{param.description} below safe range"
        )
        
        create_alarm_rule(
            device_type="smart_breaker",
            field_path=f"measurements.{param.name}",
            operator=">",
            threshold_value=param.max_value,
            severity="critical",
            alarm_message=f"{param.description} above safe range"
        )
```

**Benefits**:
- Alarm rules automatically reflect device capabilities
- Parameter constraints define alarm thresholds
- Consistent alarm definitions across device types

### 3. Dashboard Integration

The FDI dashboard (`web_ui.py`) provides a unified interface:

```python
@app.route('/api/devices', methods=['GET'])
async def get_devices():
    """Get all discovered devices with FDI metadata"""
    devices = await fdi_server.discover_devices()
    
    device_list = []
    for device in devices:
        # Get FDI package for device type
        fdi_package = fdi_server.get_fdi_package(device.device_type)
        
        device_info = {
            "device_id": device.device_id,
            "device_type": device.device_type,
            "protocol": device.protocol,
            "status": device.status,
            "last_seen": device.last_seen,
            "metrics": device.metrics
        }
        
        if fdi_package:
            device_info["fdi"] = {
                "name": fdi_package.device_type.name,
                "description": fdi_package.device_type.description,
                "manufacturer": fdi_package.device_type.manufacturer,
                "model": fdi_package.device_type.model,
                "parameters": [param.name for param in fdi_package.device_type.parameters],
                "commands": [cmd.name for cmd in fdi_package.device_type.commands]
            }
        
        device_list.append(device_info)
    
    return jsonify({"success": True, "devices": device_list})
```

### 4. Data Pipeline Integration

FDI packages inform the enrichment service:

```
Raw Message (iot.raw)
       │
       ▼
Enrichment Service
       │ Lookup FDI package for device_type
       ▼
FDI Package Manager
       │ Return device metadata, parameters, capabilities
       ▼
Enriched Message (iot.enriched)
       │ Includes:
       │ - Device type metadata from FDI
       │ - Parameter descriptions
       │ - Valid ranges
       │ - Units
       ▼
Alarm Processor
       │ Uses FDI parameter definitions to validate ranges
       ▼
iot.alarms topic
```

---

## API Reference

### REST API Endpoints (web_ui.py)

#### Device Management

**GET /api/devices**
- **Description**: List all discovered devices
- **Response**:
```json
{
  "success": true,
  "devices": [
    {
      "device_id": "breaker-001",
      "device_type": "smart_breaker",
      "protocol": "mqtt",
      "status": "online",
      "last_seen": 1730736000.0,
      "fdi": {
        "name": "Smart Circuit Breaker",
        "manufacturer": "ElectroCorp",
        "model": "SB-2000",
        "parameters": ["voltage_phase_a", "current_phase_a", ...],
        "commands": ["trip_breaker", "reset_breaker", ...]
      }
    }
  ]
}
```

**GET /api/devices/{device_id}**
- **Description**: Get specific device data and current metrics
- **Response**:
```json
{
  "success": true,
  "device": {
    "device_id": "breaker-001",
    "device_type": "smart_breaker",
    "status": "online",
    "metrics": {
      "voltage": {"phase_a": 120.0, "phase_b": 119.5, "phase_c": 121.0},
      "current": {"phase_a": 45.2, "phase_b": 43.8, "phase_c": 44.5}
    },
    "fdi_package": { /* Full FDI package data */ }
  }
}
```

**POST /api/devices/{device_id}/command**
- **Description**: Send a command to a device
- **Request Body**:
```json
{
  "command": "trip_breaker",
  "parameters": {}
}
```
- **Response**:
```json
{
  "success": true,
  "message": "Command sent successfully"
}
```

**PUT /api/devices/{device_id}/parameters**
- **Description**: Set device parameters
- **Request Body**:
```json
{
  "parameters": {
    "trip_current_threshold": 100.0,
    "voltage_threshold": 120.0
  }
}
```
- **Response**:
```json
{
  "success": true,
  "message": "Parameters updated successfully"
}
```

#### FDI Package Management

**GET /api/fdi/packages**
- **Description**: List all FDI packages
- **Query Parameters**:
  - `device_type` (optional): Filter by device type
  - `manufacturer` (optional): Filter by manufacturer
- **Response**:
```json
{
  "success": true,
  "packages": [
    {
      "package_id": "abc123def456",
      "device_type": "smart_breaker",
      "manufacturer": "ElectroCorp",
      "model": "SB-2000",
      "version": "2.1.0",
      "created_at": "2025-11-04T12:00:00Z"
    }
  ]
}
```

**GET /api/fdi/packages/{package_id}**
- **Description**: Get full FDI package details
- **Response**: Complete FDI package JSON

**POST /api/fdi/packages**
- **Description**: Create/store a new FDI package
- **Request Body**: FDI package JSON
- **Response**:
```json
{
  "success": true,
  "package_id": "abc123def456"
}
```

**DELETE /api/fdi/packages/{package_id}**
- **Description**: Delete an FDI package
- **Response**:
```json
{
  "success": true,
  "message": "Package deleted successfully"
}
```

#### FDI Server Control

**POST /api/fdi/server/start**
- **Description**: Start the FDI server
- **Response**:
```json
{
  "success": true,
  "message": "FDI server started"
}
```

**POST /api/fdi/server/stop**
- **Description**: Stop the FDI server
- **Response**:
```json
{
  "success": true,
  "message": "FDI server stopped"
}
```

**GET /api/fdi/server/status**
- **Description**: Get FDI server status
- **Response**:
```json
{
  "success": true,
  "status": {
    "running": true,
    "opcua_port": 4840,
    "adapters": ["mqtt"],
    "devices_count": 5,
    "packages_count": 3
  }
}
```

### OPC UA Methods (Optional)

If OPC UA is available, the following methods are exposed on the OPC UA server at `opc.tcp://<host>:4840`:

**DiscoverDevices(protocol_filter: String) → String**
- **Description**: Discover devices on specified protocol or all protocols
- **Parameters**:
  - `protocol_filter`: Protocol name ("mqtt", "modbus", etc.) or empty for all
- **Returns**: JSON string array of devices

**GetDeviceParameters(device_id: String) → String**
- **Description**: Get current parameters and measurements from a device
- **Parameters**:
  - `device_id`: Device identifier
- **Returns**: JSON string with device data

**SetDeviceParameters(device_id: String, parameters_json: String) → Boolean**
- **Description**: Set device parameters
- **Parameters**:
  - `device_id`: Device identifier
  - `parameters_json`: JSON string with parameter name/value pairs
- **Returns**: Success boolean

**SendDeviceCommand(device_id: String, command: String, parameters_json: String) → Boolean**
- **Description**: Send a command to a device
- **Parameters**:
  - `device_id`: Device identifier
  - `command`: Command name
  - `parameters_json`: JSON string with command parameters
- **Returns**: Success boolean

---

## Usage Examples

### Example 1: Creating and Storing an FDI Package

```python
from fdi_package import FDIPackage, FDIDeviceType, FDIDeviceParameter, FDIDeviceCommand
from fdi_blob_storage import FDIPackageBlobStorage

# Define device parameters
parameters = [
    FDIDeviceParameter(
        name="temperature",
        description="Sensor temperature",
        data_type="float",
        unit="°C",
        min_value=-40.0,
        max_value=85.0,
        category="measurement"
    ),
    FDIDeviceParameter(
        name="humidity",
        description="Relative humidity",
        data_type="float",
        unit="%",
        min_value=0.0,
        max_value=100.0,
        category="measurement"
    )
]

# Define device commands
commands = [
    FDIDeviceCommand(
        name="calibrate",
        description="Calibrate the sensor",
        parameters=[],
        return_type="boolean"
    )
]

# Create device type
device_type = FDIDeviceType(
    device_type="temp_humidity_sensor",
    name="Temperature & Humidity Sensor",
    description="Environmental monitoring sensor",
    category="environmental_monitoring",
    manufacturer="SensorCorp",
    model="THS-100",
    version="1.0.0",
    capabilities=["temperature_monitoring", "humidity_monitoring"],
    parameters=parameters,
    commands=commands
)

# Create FDI package
package = FDIPackage(device_type)
package.add_metadata("installation_location", "indoor")

# Validate package
if package.validate():
    # Store package
    storage = FDIPackageBlobStorage("/app/fdi-packages")
    success = storage.store_package(package.to_dict(), package.package_id)
    if success:
        print(f"Package stored successfully: {package.package_id}")
```

### Example 2: Starting FDI Server and Discovering Devices

```python
import asyncio
from fdi_server import FDIServer

async def main():
    # Create and start FDI server
    server = FDIServer(opcua_port=4840, storage_path="/app/fdi-packages")
    await server.start()
    
    # Wait for adapters to initialize
    await asyncio.sleep(5)
    
    # Discover devices
    devices = await server.discover_devices()
    print(f"Discovered {len(devices)} devices:")
    for device in devices:
        print(f"  - {device.device_id} ({device.device_type}) via {device.protocol}")
        
        # Get device data
        data = await server.get_device_data(device.device_id)
        print(f"    Status: {data.get('status')}")
        print(f"    Metrics: {data.get('metrics')}")
    
    # Keep server running
    try:
        while server.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Sending Commands to Devices

```python
import asyncio
from fdi_server import FDIServer

async def control_breaker():
    server = FDIServer()
    await server.start()
    
    device_id = "breaker-001"
    
    # Trip the breaker
    print("Tripping breaker...")
    success = await server.send_device_command(device_id, "trip_breaker", {})
    if success:
        print("Breaker tripped successfully")
    
    # Wait 5 seconds
    await asyncio.sleep(5)
    
    # Reset the breaker
    print("Resetting breaker...")
    success = await server.send_device_command(device_id, "reset_breaker", {})
    if success:
        print("Breaker reset successfully")
    
    # Set trip threshold
    print("Setting trip threshold...")
    success = await server.send_device_command(
        device_id, 
        "set_trip_threshold",
        {"threshold": 95.0}
    )
    if success:
        print("Threshold updated successfully")
    
    await server.stop()

asyncio.run(control_breaker())
```

### Example 4: Querying FDI Package Information

```python
from fdi_blob_storage import FDIPackageBlobStorage
from fdi_package import FDIPackage

# Initialize storage
storage = FDIPackageBlobStorage("/app/fdi-packages")

# List all packages
packages = storage.list_packages()
print(f"Total packages: {len(packages)}")

# List packages by device type
smart_breaker_packages = storage.list_packages(device_type="smart_breaker")
print(f"Smart breaker packages: {len(smart_breaker_packages)}")

# Get specific package
if smart_breaker_packages:
    package_id = smart_breaker_packages[0]['package_id']
    package_data = storage.retrieve_package(package_id)
    
    if package_data:
        package = FDIPackage.from_dict(package_data)
        
        print(f"Device Type: {package.device_type.name}")
        print(f"Manufacturer: {package.device_type.manufacturer}")
        print(f"Model: {package.device_type.model}")
        print(f"\nParameters:")
        for param in package.device_type.parameters:
            print(f"  - {param.name} ({param.data_type})")
            if param.unit:
                print(f"    Unit: {param.unit}")
            if param.min_value and param.max_value:
                print(f"    Range: {param.min_value} - {param.max_value}")
        
        print(f"\nCommands:")
        for cmd in package.device_type.commands:
            print(f"  - {cmd.name}: {cmd.description}")
            if cmd.parameters:
                print(f"    Parameters:")
                for param in cmd.parameters:
                    print(f"      • {param.name} ({param.data_type})")

# Get storage statistics
stats = storage.get_storage_stats()
print(f"\nStorage Stats:")
print(f"  Total packages: {stats['total_packages']}")
print(f"  Total size: {stats['total_size_bytes']} bytes")
```

### Example 5: Creating a Custom Protocol Adapter

```python
from fdi_server import DeviceProtocolAdapter, Device
from typing import Dict, Any, List
import aiohttp

class HTTPAdapter(DeviceProtocolAdapter):
    """HTTP/REST protocol adapter for devices with REST APIs"""
    
    def __init__(self, base_urls: List[str]):
        self.base_urls = base_urls
        self.devices = {}
        self.session = None
    
    async def start(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        return True
    
    async def stop(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def discover_devices(self) -> List[Device]:
        """Discover devices by polling HTTP endpoints"""
        discovered = []
        
        for base_url in self.base_urls:
            try:
                async with self.session.get(f"{base_url}/api/info") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        device = Device(
                            device_id=data['device_id'],
                            device_type=data.get('device_type', 'http_device'),
                            protocol='http',
                            status='online',
                            last_seen=time.time()
                        )
                        discovered.append(device)
                        self.devices[device.device_id] = device
            except:
                continue
        
        return discovered
    
    async def get_device_data(self, device_id: str) -> Dict[str, Any]:
        """Get device data via HTTP GET"""
        if device_id not in self.devices:
            return {}
        
        # Find device's base URL
        for base_url in self.base_urls:
            try:
                async with self.session.get(f"{base_url}/api/data") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('device_id') == device_id:
                            return data
            except:
                continue
        
        return {}
    
    async def set_device_parameter(self, device_id: str, 
                                   parameter: str, value: Any) -> bool:
        """Set device parameter via HTTP PUT"""
        for base_url in self.base_urls:
            try:
                async with self.session.put(
                    f"{base_url}/api/parameters/{parameter}",
                    json={"value": value}
                ) as resp:
                    return resp.status == 200
            except:
                continue
        return False
    
    async def send_device_command(self, device_id: str, 
                                  command: str, parameters: Dict) -> bool:
        """Send command via HTTP POST"""
        for base_url in self.base_urls:
            try:
                async with self.session.post(
                    f"{base_url}/api/commands/{command}",
                    json=parameters
                ) as resp:
                    return resp.status == 200
            except:
                continue
        return False

# Register with FDI server
http_adapter = HTTPAdapter(base_urls=["http://device1", "http://device2"])
server.adapters['http'] = http_adapter
```

---

## Extension Guide

### Adding New Device Types

**Step 1**: Create FDI package definition

```python
def create_solar_inverter_fdi_package() -> FDIPackage:
    parameters = [
        FDIDeviceParameter(
            name="dc_voltage",
            description="DC input voltage",
            data_type="float",
            unit="V",
            min_value=0.0,
            max_value=1000.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="ac_power",
            description="AC output power",
            data_type="float",
            unit="W",
            min_value=0.0,
            max_value=10000.0,
            category="measurement"
        ),
        # ... more parameters
    ]
    
    commands = [
        FDIDeviceCommand(
            name="start_inverter",
            description="Start power conversion",
            parameters=[],
            return_type="boolean"
        ),
        # ... more commands
    ]
    
    device_type = FDIDeviceType(
        device_type="solar_inverter",
        name="Solar Inverter",
        description="Photovoltaic inverter with grid-tie capability",
        category="renewable_energy",
        manufacturer="SolarTech",
        model="SI-5000",
        version="1.0.0",
        capabilities=["dc_to_ac_conversion", "mppt", "grid_sync"],
        parameters=parameters,
        commands=commands
    )
    
    return FDIPackage(device_type)
```

**Step 2**: Store FDI package

```python
package = create_solar_inverter_fdi_package()
storage = FDIPackageBlobStorage("/app/fdi-packages")
storage.store_package(package.to_dict(), package.package_id)
```

**Step 3**: Device automatically integrates

- Schema Registry automatically generates JSON schema
- Alarm system automatically creates rules based on min/max values
- Dashboard automatically displays device with parameters and commands

### Adding Custom Capabilities

FDI capabilities are free-form strings that describe what a device can do:

```python
# Example capabilities
capabilities = [
    "voltage_monitoring",
    "current_monitoring",
    "power_monitoring",
    "remote_control",
    "diagnostics",
    "firmware_update",  # Custom capability
    "predictive_maintenance",  # Custom capability
    "energy_metering"  # Custom capability
]
```

Use capabilities to:
- Filter devices by features
- Enable/disable dashboard features
- Route devices to specific applications
- Configure alarm rules

### Extending with Metadata

FDI packages support arbitrary metadata:

```python
package.add_metadata("installation_date", "2025-11-04")
package.add_metadata("warranty_expiry", "2028-11-04")
package.add_metadata("maintenance_schedule", "quarterly")
package.add_metadata("certifications", ["UL", "CE", "CSA"])
package.add_metadata("communication_protocol", {
    "primary": "mqtt",
    "fallback": "http",
    "settings": {
        "mqtt": {"qos": 1, "retain": False},
        "http": {"timeout": 30}
    }
})
```

---

## Best Practices

### 1. FDI Package Design

**DO**:
- Use descriptive parameter names (`voltage_phase_a` not `v_a`)
- Include units for all measurements
- Define min/max ranges for safety-critical parameters
- Provide comprehensive descriptions
- Group related parameters with consistent naming

**DON'T**:
- Use ambiguous names (`value1`, `param_x`)
- Mix units (use meters everywhere, not meters+feet)
- Omit range constraints on safety parameters
- Create overly deep parameter hierarchies

### 2. Protocol Adapter Implementation

**DO**:
- Implement all abstract methods
- Handle connection failures gracefully
- Use async/await consistently
- Cache device data appropriately
- Log all errors with context

**DON'T**:
- Block the event loop with synchronous I/O
- Raise unhandled exceptions
- Store sensitive credentials in code
- Poll devices too frequently

### 3. Device Discovery

**DO**:
- Implement timeout mechanisms
- Update `last_seen` timestamps
- Mark devices offline after timeout
- Cache discovered devices
- Re-discover periodically

**DON'T**:
- Rediscover on every request
- Keep offline devices indefinitely
- Skip error handling
- Assume devices are always available

### 4. Security Considerations

**DO**:
- Validate all parameter values
- Require confirmation for critical commands
- Log all parameter changes and commands
- Implement authentication for OPC UA
- Use TLS for MQTT connections

**DON'T**:
- Trust device-provided data blindly
- Execute commands without validation
- Store passwords in FDI packages
- Allow unrestricted parameter access

---

## Troubleshooting

### Common Issues

**Issue**: Devices not discovered
- **Check**: MQTT broker connectivity
- **Check**: Topic subscriptions are correct
- **Check**: Devices are publishing to expected topics
- **Solution**: Review `MQTTAdapter` logs for connection issues

**Issue**: FDI package not found
- **Check**: Package is stored in blob storage
- **Check**: Manifest is up-to-date
- **Check**: `device_type` matches exactly
- **Solution**: Run `storage.list_packages()` to verify

**Issue**: Commands not reaching devices
- **Check**: Device is online (`status == "online"`)
- **Check**: Device subscribes to command topic
- **Check**: Protocol adapter is started
- **Solution**: Test with MQTT client directly

**Issue**: OPC UA server not starting
- **Check**: `asyncua` library is installed
- **Check**: Port 4840 is not in use
- **Check**: Firewall allows connections
- **Solution**: OPC UA is optional, server works without it

### Debug Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for structlog
import structlog
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
)
```

### Health Checks

```python
# Check FDI server health
async def health_check():
    # Check adapters
    for name, adapter in server.adapters.items():
        if not adapter.connected:
            print(f"⚠️ {name} adapter not connected")
    
    # Check device count
    devices = await server.discover_devices()
    if len(devices) == 0:
        print("⚠️ No devices discovered")
    
    # Check FDI packages
    packages = server.storage.list_packages()
    if len(packages) == 0:
        print("⚠️ No FDI packages stored")
```

---

## Performance Considerations

### Caching Strategies

1. **Device Registry Cache**: Adapters cache discovered devices
2. **FDI Package Cache**: Packages loaded once and reused
3. **Metric Cache**: Device data cached until next update

### Scalability

**Horizontal Scaling**:
- Multiple FDI servers with load balancer
- Shared FDI package storage (NFS, S3)
- Dedicated adapters per protocol

**Vertical Scaling**:
- Async I/O prevents thread overhead
- Event-driven architecture scales to 1000s of devices
- In-memory caching reduces database load

### Resource Usage

**Memory**:
- ~1KB per device in registry
- ~10-50KB per FDI package
- Metric caching adds ~2KB per device

**Network**:
- MQTT: Minimal bandwidth (KB/s per device)
- OPC UA: Higher bandwidth (10s of KB/s)
- HTTP polling: Depends on interval

---

## Conclusion

This FDI implementation provides a **flexible, extensible, and standards-based approach** to device integration in our IoT platform. Key advantages:

✅ **Protocol Agnostic**: Support any device protocol via adapters
✅ **Self-Describing**: FDI packages contain complete device definitions
✅ **Automatic Integration**: Schemas, alarms, and dashboards auto-generate
✅ **Vendor Independence**: Works with devices from any manufacturer
✅ **Scalable Architecture**: Async I/O and caching for performance
✅ **Standards-Based**: Adapts IEC 62769 FDI standard

For questions or contributions, see the main project README or contact the development team.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-04
**Author**: IoT Platform Team

