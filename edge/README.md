# Edge GRM Service

A Gateway Resource Manager (GRM) service for edge devices that registers with IzumaNetworks and manages IoT resources.

## Overview

This service provides:
- Automatic GRM registration with IzumaNetworks
- Resource synchronization based on local configuration
- Health monitoring and status reporting
- Error recovery and retry mechanisms
- Containerized deployment

## Features

- **GRM Registration**: Automatically registers as a Gateway Resource Manager
- **Resource Management**: Loads and syncs resources from `resources.json`
- **Health Monitoring**: Continuous health checks and status reporting
- **Error Recovery**: Automatic retry mechanisms for failed operations
- **Configuration Management**: Environment-based configuration
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Architecture

```
edge/
├── grm_service/           # Main service package
│   ├── main_async.py     # Async service orchestrator (includes logging setup)
│   ├── edge_core_client.py # Edge Core WebSocket client
│   ├── resource_manager_async.py # Async resource management
│   └── config.py         # Configuration management
├── tests/                # Test suite
│   ├── run_tests.py      # Test runner
│   ├── test_edge_core.py # Edge Core WebSocket tests
│   ├── test_async_service.py # Async service tests
│   ├── test_periodic_update.py # Periodic update tests
│   ├── test_temperature_fahrenheit.py # Temperature tests
│   └── test_config.py    # Configuration tests
├── resources.json        # Resource definitions
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── env.example          # Environment variables example
└── README.md           # This file
```

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Docker (optional)
- IzumaNetworks API credentials

### 2. Configuration

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your IzumaNetworks credentials:

```bash
IZUMA_API_KEY=your_actual_api_key
IZUMA_DEVICE_ID=your_device_id
```

### 3. Installation

#### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python3 -m grm_service.main_async
```

#### Docker Deployment

```bash
# Build the container
docker build -t edge-grm-service .

# Run the container
docker run --env-file .env edge-grm-service
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IZUMA_API_BASE_URL` | Edge Core WebSocket URL | `ws://192.168.1.198:8081` |
| `IZUMA_DEVICE_ID` | Device ID for GRM registration | Required |
| `SERVICE_NAME` | Service name for registration | `edge-grm-service` |
| `SERVICE_VERSION` | Service version | `1.0.0` |
| `RESOURCES_FILE` | Path to resources configuration | `resources.json` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HEALTH_CHECK_INTERVAL` | Health check interval (seconds) | `30` |
| `RESOURCE_UPDATE_INTERVAL` | Resource update interval (seconds) | `60` |
| `MAX_RETRIES` | Maximum retry attempts | `3` |
| `RETRY_DELAY` | Base delay between retries (seconds) | `5` |

### Resource Configuration

Resources are defined in `resources.json` with the following format:

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `object_id` | int | Object identifier | Required |
| `object_instance_id` | int | Object instance identifier | Required |
| `resource_id` | int | Resource identifier | Required |
| `resource_name` | string | Human-readable resource name | Required |
| `operations` | int | Resource operations (1=READ, 2=WRITE, 3=READ/WRITE) | 3 |
| `resource_type` | string | Data type (float, integer, string, boolean) | "float" |
| `value` | any | Initial resource value | Required |
| `periodic_update` | boolean | Whether to update this resource periodically | true |

```json
[
  {
    "object_id": 1234,
    "object_instance_id": 0,
    "resource_id": 0,
    "resource_name": "temperature",
    "operations": 3,
    "resource_type": "float",
    "value": 70.0,
    "periodic_update": true
  },
  {
    "object_id": 1111,
    "object_instance_id": 0,
    "resource_id": 2,
    "resource_name": "device_type",
    "operations": 1,
    "resource_type": "string",
    "value": "smartbreaker",
    "periodic_update": false
  }
]
```

## API Reference

### IzumaNetworks Client

The `IzumaClient` class provides methods for interacting with IzumaNetworks:

- `register_grm(service_info)`: Register as a GRM
- `unregister_grm()`: Unregister GRM
- `register_resource(resource)`: Register a resource
- `update_resource(resource_id, resource)`: Update a resource
- `delete_resource(resource_id)`: Delete a resource
- `get_resources()`: Get all registered resources
- `health_check()`: Perform health check

### Resource Manager

The `ResourceManager` class handles resource operations:

- `load_local_resources(file_path)`: Load resources from file
- `validate_local_resources()`: Validate all local resources
- `sync_resources()`: Synchronize with IzumaNetworks
- `register_single_resource(resource)`: Register a single resource
- `update_single_resource(resource)`: Update a single resource
- `delete_single_resource(object_id, object_instance_id, resource_id)`: Delete a resource

## Service Lifecycle

### Startup Sequence

1. **Initialization**: Validate configuration and initialize components
2. **GRM Registration**: Register as a Gateway Resource Manager
3. **Resource Sync**: Load and synchronize local resources
4. **Health Monitoring**: Start health check thread

### Shutdown Sequence

1. **Stop Health Monitoring**: Stop health check thread
2. **GRM Unregistration**: Unregister from IzumaNetworks
3. **Cleanup**: Clean up resources and connections

## Logging

The service uses structured logging with the following features:

- **File Rotation**: Logs are rotated at 10MB with 7-day retention
- **Console Output**: Logs are also output to console
- **Structured Format**: Includes timestamp, level, module, function, line, and message
- **Configurable Level**: Set via `LOG_LEVEL` environment variable

## Error Handling

The service includes comprehensive error handling:

- **Retry Logic**: Exponential backoff for failed API calls
- **Graceful Degradation**: Service continues running even if some operations fail
- **Detailed Logging**: All errors are logged with context
- **Health Monitoring**: Continuous health checks detect issues

## Simulated Data Generation

The service generates realistic simulated sensor data for testing and demonstration:

### Temperature Sensor
- **Unit**: Fahrenheit (°F)
- **Range**: 66-88°F (19-31°C equivalent)
- **Base Temperature**: 77°F (25°C)
- **Variation**: ±9°F sine wave cycle (60 seconds)
- **Noise**: ±2°F random variation

### Humidity Sensor
- **Unit**: Percentage (%)
- **Range**: 40-80%
- **Base Humidity**: 60%
- **Variation**: ±20% sine wave cycle (120 seconds)
- **Noise**: ±2% random variation

### Device Type
- **Type**: Static string value
- **Value**: "smartbreaker"
- **Update**: Never updated (periodic_update=false)

## Development

### Running Tests

```bash
# Run all tests
python3 tests/run_tests.py

# Run individual tests
python3 tests/test_edge_core.py          # Test Edge Core WebSocket client
python3 tests/test_async_service.py      # Test complete async service
python3 tests/test_periodic_update.py    # Test periodic update filtering
python3 tests/test_temperature_fahrenheit.py  # Test temperature in Fahrenheit
python3 tests/test_config.py             # Test configuration setup
```

### Code Style

The project follows PEP 8 style guidelines. Use a linter like `flake8` or `black`:

```bash
pip install black flake8
black grm_service/
flake8 grm_service/
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check `IZUMA_API_KEY` configuration
2. **Device ID Not Found**: Verify `IZUMA_DEVICE_ID` is correct
3. **Resource Sync Failed**: Check `resources.json` format and network connectivity
4. **Health Check Failed**: Verify IzumaNetworks API availability

### Debug Mode

Enable debug logging by setting:

```bash
LOG_LEVEL=DEBUG
```

### Manual Testing

Test individual components:

```python
from grm_service.edge_core_client import EdgeCoreClient
from grm_service.resource_manager_async import AsyncResourceManager

# Test Edge Core connection
client = EdgeCoreClient()
await client.connect()

# Test resource loading
manager = AsyncResourceManager(client)
manager.load_local_resources("resources.json")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
