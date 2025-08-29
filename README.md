# ⚡ IoT Cloud Platform with FDI Integration & TimescaleDB

A comprehensive, cloud-ready IoT data pipeline featuring **FDI (Field Device Integration) package management**, **MQTT-based device communication**, real-time message enrichment, **TimescaleDB time-series storage**, and an **advanced dashboard** with device management, analytics, and monitoring capabilities.

## 🏗️ Architecture

```
Smart Breaker Simulator → MQTT Broker → MQTT-Kafka Bridge → RedPanda → Enrichment Service → RedPanda → RedPanda Connector → TimescaleDB
                                    ↓                                    ↓                    ↓
                            App Registry Service                    Device-Type Topics    Time-Series Storage
                                    ↓                                    ↓                    ↓
                            Application Registrations         iot.smart_breaker.enriched  Continuous Aggregates
                                    ↓                                    ↓                    ↓
                            FDI Package Manager              Smart Grid Monitor Tab    Analytics Dashboard
                                    ↓                                    ↓                    ↓
                            Device Definitions &            Real-time Monitoring      Historical Data Analysis
                            Configuration Management
```

### Core Services

- **Smart Breaker Simulator**: Generates realistic IoT telemetry + trends data with **burst logic** (3-8 second intervals) via **MQTT**
- **MQTT Broker**: Eclipse Mosquitto for IoT device communication and message routing
- **MQTT-Kafka Bridge**: Connects MQTT topics to RedPanda/Kafka for seamless integration
- **RedPanda**: Event streaming platform (Kafka-compatible) for message brokering
- **Enrichment Service**: Adds device metadata, context, and routes data to **both general AND device-type specific topics**
- **App Registry Service**: Manages applications that register interest in specific device types
- **FDI Package Manager**: **NEW** - Manages Field Device Integration packages, provides OPC UA interface, and web UI for device management
- **RedPanda Connector**: **NEW** - Consumes messages from RedPanda and stores them in TimescaleDB for time-series analysis
- **TimescaleDB**: **NEW** - PostgreSQL extension for time-series data with continuous aggregates and compression
- **Advanced Dashboard**: **NEW** - Comprehensive interface with FDI Management, Data Analytics, and RedPanda/Kafka Metrics tabs

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   git clone https://github.com/mig-migazi/IOT---Cloud.git
   cd IOT-Cloud
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access services**:
   - **FDI Dashboard**: http://localhost:5004 (Main interface with all features)
   - **RedPanda Console**: http://localhost:8086
   - **RedPanda API**: localhost:9092 (external), localhost:29092 (internal)
   - **MQTT Broker**: localhost:1883 (MQTT), localhost:9001 (WebSocket)
   - **App Registry Service**: http://localhost:5002
   - **TimescaleDB**: localhost:5432 (PostgreSQL)

## 🎛️ Advanced Dashboard Guide

The FDI Dashboard provides a comprehensive interface for managing your IoT platform. Access it at **http://localhost:5004** to monitor devices, manage FDI packages, analyze data, and track system performance.

### 🚀 **Tab 1: FDI Management**

The main tab for managing Field Device Integration packages and monitoring device status.

#### **Server Status Section**
- **Server Status**: Shows if the FDI server is running or stopped
- **Devices Count**: Number of currently discovered IoT devices
- **Packages Count**: Total FDI packages stored in the system
- **OPC UA Port**: Port for OPC UA server communication (4840)
- **Controls**: Start/Stop server, refresh status

#### **FDI Packages Section**
- **Create Smart Breaker Package**: Generates a sample FDI package for smart breakers
- **Package List**: Displays all stored FDI packages with metadata
- **Package Details**: View package contents, device parameters, and commands
- **Package Management**: Store, retrieve, and manage device definitions

#### **Devices Section**
- **Device Discovery**: Shows all discovered IoT devices in real-time
- **Device Status**: Current operational status and last communication time
- **Device Details**: Click "View" to see live measurements and FDI mapping
- **Parameter Control**: Simulate device parameter changes for testing

#### **Device Commands Section**
- **Device Selection**: Choose target device from dropdown
- **Command Types**: Trip breaker, reset breaker, set thresholds, get diagnostics
- **Parameter Input**: Set specific values for commands
- **Command Execution**: Send commands to devices via MQTT

### 📊 **Tab 2: Data Analytics & Monitoring**

Comprehensive monitoring and analytics for your IoT data pipeline.

#### **System Overview Section**
- **System Status**: Overall platform health indicator
- **Active Devices**: Real-time count of connected devices
- **Data Throughput**: Messages per minute flowing through the system
- **Last Update**: Timestamp of most recent data activity
- **Controls**: Refresh all stats, system health check

#### **📡 Live Data Stream Section**
- **Live Indicator**: Blinking green dot showing real-time activity
- **Message Counter**: Total messages processed in current session
- **Real-time Feed**: Live stream of incoming messages and system events
- **Message Types**: Device telemetry, pipeline status, system notifications
- **Controls**: Clear stream, export data to file

#### **🚀 Kafka/RedPanda Pipeline Section**
- **MQTT Input**: Status of MQTT broker and device connections
- **RedPanda Topics**: Health of Kafka topics and message flow
- **TimescaleDB**: Database status and storage performance
- **Pipeline Flow**: Visual representation of data movement through the system

#### **📋 Topic Details Section**
- **iot.raw**: Raw IoT device messages from MQTT
- **iot.enriched**: General enriched messages with metadata
- **iot.smart_breaker.enriched**: Smart breaker specific data
- **Performance Metrics**: Messages per second, total messages, lag

#### **📊 TimescaleDB Analytics Section**
- **Data Points**: Total records stored in time-series database
- **Devices Stored**: Number of devices with historical data
- **Compression Ratio**: Data compression efficiency
- **Query Performance**: Database query response times

#### **📈 Data Analytics Section**
- **Device Selection**: Choose specific device for analysis
- **Metric Selection**: Select measurement type (voltage, current, temperature, etc.)
- **Timeframe Selection**: Choose analysis period (1h, 6h, 24h, 7d, 30d)
- **Data Loading**: Load and display historical data from TimescaleDB

### 🔄 **Tab 3: RedPanda/Kafka Metrics**

Dedicated monitoring for your event streaming infrastructure.

#### **🔄 RedPanda/Kafka Overview**
- **Broker Status**: Health of RedPanda broker
- **Active Topics**: Number of active Kafka topics
- **Active Consumers**: Number of consumer applications
- **Message Throughput**: Messages per second flowing through the system

#### **📊 Topic Performance**
- **Topic Details**: Individual topic performance metrics
- **Partitions**: Number of topic partitions
- **Replication**: Replication factor for fault tolerance
- **Messages/sec**: Real-time message throughput per topic
- **Total Messages**: Cumulative message count
- **Lag**: Consumer lag for each topic

#### **👥 Consumer Groups**
- **redpanda-connect**: Official RedPanda Connect service for TimescaleDB storage
- **enrichment-service**: Service processing and enriching messages
- **Group Status**: Active/Inactive status of consumer groups
- **Topics**: Topics consumed by each group
- **Members**: Number of consumer instances
- **Last Commit**: Timestamp of last offset commit

#### **📈 Message Flow Analytics**
- **Pipeline Visualization**: MQTT → RedPanda → TimescaleDB flow diagram
- **Flow Metrics**: Real-time data movement statistics
- **System Health**: Overall pipeline health indicators
- **Export Report**: Generate comprehensive flow analysis report

### 🎯 **Real-Time Features**

#### **Live Data Updates**
- **Auto-refresh**: Dashboard updates every 10-30 seconds
- **Real-time Counters**: Message counts and device numbers update live
- **Live Stream**: Continuous feed of system activity
- **Visual Indicators**: Pulsing, blinking, and animated elements

#### **Interactive Controls**
- **Device Management**: Add, remove, and configure devices
- **Parameter Control**: Simulate device parameter changes
- **Command Execution**: Send commands to devices in real-time
- **Data Export**: Download data streams and analytics

#### **System Monitoring**
- **Health Checks**: Continuous monitoring of all services
- **Performance Metrics**: Real-time performance indicators
- **Error Tracking**: Monitor and alert on system issues
- **Resource Usage**: Track system resource consumption

### 🔧 **Dashboard Configuration**

#### **Access Control**
- **Port Configuration**: Default port 5004 (configurable)
- **Network Access**: Accessible from any network interface
- **Security**: Basic authentication and access controls

#### **Customization**
- **Theme**: Modern, responsive design
- **Layout**: Configurable dashboard layout
- **Widgets**: Customizable monitoring widgets
- **Alerts**: Configurable alerting and notifications

#### **Integration**
- **API Endpoints**: RESTful API for external integrations
- **WebSocket**: Real-time updates for external applications
- **Export Formats**: JSON, CSV, and text export options
- **Third-party Tools**: Integration with monitoring and alerting systems

## 📊 Data Flow

### Message Routing & Topics
The system supports **MQTT-based IoT communication** with seamless Kafka integration and time-series storage:

**MQTT Topics (Device → MQTT Broker):**
- **`iot/{device_id}/raw`** → Raw telemetry data
- **`iot/{device_id}/trends`** → Aggregated trends data  
- **`iot/{device_id}/status`** → Device status information

**Kafka Topics (MQTT Bridge → RedPanda):**
- **`iot.raw`** → Raw device messages (from MQTT)
- **`iot.enriched`** → General enriched messages (all device types)
- **`iot.smart_breaker.enriched`** → Smart breaker data only (for Smart Grid Monitor app)

**TimescaleDB Tables:**
- **`iot_raw_data`** → Raw messages with time-series optimization
- **`iot_enriched_data`** → Enriched messages with device metadata
- **`smart_breaker_data`** → Smart breaker specific data
- **`device_metadata`** → Device configuration and capabilities

### Raw Message (from simulator)
```json
{
  "device_id": "breaker-001",
  "device_type": "smart_breaker",
  "timestamp": "2025-08-20T18:00:54.117782Z",
  "event_type": "telemetry",
  "measurements": {
    "voltage": {"phase_a": 117.27, "phase_b": 112.34, "phase_c": 114.52, "unit": "V"},
    "current": {"phase_a": 69.94, "phase_b": 33.83, "phase_c": 54.86, "unit": "A"},
    "power": {"active": 5775.99, "reactive": 1945.16, "apparent": 6094.73, "factor": 0.948, "unit": "W"},
    "frequency": {"value": 59.28, "unit": "Hz"},
    "temperature": {"value": 34.92, "unit": "°C"},
    "status": {"breaker": 1, "position": 1, "communication": 1},
    "protection": {"trip_count": 5, "ground_fault_current": 0.0, "arc_fault_detected": false},
    "operational": {"load_percentage": 48.1, "operating_hours": 982.8, "maintenance_due": true}
  }
}
```

### Enriched Message (after enrichment service)
```json
{
  "device_id": "breaker-001",
  "device_type": "smart_breaker",
  "device_metadata": {
    "device_type": "smart_breaker",
    "device_type_name": "Smart Circuit Breaker",
    "device_type_description": "Intelligent circuit breaker with monitoring and protection capabilities",
    "device_category": "electrical_protection",
    "capabilities": ["voltage_monitoring", "current_monitoring", "power_monitoring", "frequency_monitoring"],
    "data_format": "json",
    "update_frequency": "5_seconds",
    "retention_policy": "30_days"
  },
  "application_registry": {
    "device_type": "smart_breaker",
    "registered_applications_count": 1,
    "applications": [
      {
        "id": "91dd8f4d-350c-42a2-8c07-cc0e7ac7ad98",
        "name": "Smart Grid Monitor",
        "developer": "IoT Solutions Inc.",
        "platform": "web",
        "category": "monitoring",
        "status": "active"
      }
    ]
  },
  "enrichment_info": {
    "enriched_at": "2025-08-20T18:00:54.117782Z",
    "enrichment_service": "iot-enrichment-service",
    "enrichment_version": "1.0.0",
    "device_type_detected": "smart_breaker",
    "app_registry_integration": true
  },
  "measurements": { /* ... original measurements ... */ }
}
```

## 🔧 Configuration

### FDI Package Management
The system now uses **FDI (Field Device Integration) packages** as the single source of truth for device definitions:

- **FDI Packages**: Stored in blob storage with device parameters, commands, and metadata
- **Device Registry**: Automatically populated from FDI packages
- **OPC UA Interface**: Optional OPC UA server for industrial integration
- **Web UI**: Comprehensive dashboard for managing FDI packages and devices

### Device Registry
Edit `config/device-registry.json` for legacy device types, or use the FDI Package Manager for new devices.

### App Registry
Applications can register for specific device types via the App Registry Service API:

```bash
# Register an application
curl -X POST http://localhost:5002/api/applications \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your App Name",
    "developer": "Your Company",
    "description": "What your app does",
    "platform": "web|mobile|desktop|api",
    "category": "Your Category",
    "devicetypes": ["smart_breaker", "smart_meter"],
    "version": "1.0.0",
    "contact_email": "your@email.com"
  }'

# Query applications by device type
curl http://localhost:5002/api/applications/by-device-type/smart_breaker
```

## 📁 Project Structure

```
IOT-Cloud/
├── config/                     # Configuration files
│   ├── device-registry.json   # Legacy device type definitions
│   ├── mosquitto.conf         # MQTT broker configuration
│   └── timescaledb_init.sql   # TimescaleDB schema and policies
├── services/                   # Microservices
│   ├── enrichment/            # Message enrichment service
│   │   ├── enrichment_service.py
│   │   └── requirements.txt
│   ├── simulator/             # Smart breaker simulator
│   │   ├── smart_breaker_simulator.py          # Legacy Kafka version
│   │   ├── smart_breaker_simulator_mqtt.py     # Current MQTT version
│   │   └── requirements.txt
│   ├── mqtt-kafka-bridge/     # MQTT to Kafka bridge service
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── fdi-package-manager/   # NEW: FDI package management service
│   │   ├── fdi_package.py     # FDI package data structures
│   │   ├── fdi_blob_storage.py # Package storage and manifest
│   │   ├── fdi_server.py      # FDI communication server
│   │   ├── web_ui.py          # Web dashboard and API
│   │   ├── main.py            # Service entry point
│   │   ├── templates/         # Dashboard HTML templates
│   │   └── requirements.txt
│   ├── redpanda-connect/      # NEW: Official RedPanda Connect for TimescaleDB
│   │   ├── connector.py       # Main connector application
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── web-app/               # Legacy web dashboard
│   │   ├── app.py
│   │   ├── templates/
│   │   └── requirements.txt
│   ├── smart-grid-monitor/    # Smart Grid Monitor service
│   │   ├── app.py
│   │   ├── templates/
│   │   └── requirements.txt
│   └── appregistryservice/    # Application registry service
│       ├── src/
│       │   ├── app.py
│       │   ├── models.py
│       │   └── schemas.py
│       └── requirements.txt
├── docker-compose.yml          # Service orchestration
├── setup.sh                    # Initial setup script
└── README.md                   # This file
```

## 🚀 Features

### **Core IoT Capabilities**
- **Real-time Telemetry**: Smart breaker simulator generates realistic electrical measurements with **dynamic burst logic**
- **Trends Aggregation**: Collects and aggregates historical data during message bursts
- **Intelligent Enrichment**: Automatically detects device types and adds metadata from FDI packages
- **Application Registry**: Centralized service for managing application registrations
- **Device Type Mapping**: Dynamic device type detection and metadata enrichment

### **NEW: FDI Package Management**
- **FDI Packages**: Standard Field Device Integration packages for device definitions
- **Blob Storage**: File-based storage for FDI packages with manifest management
- **OPC UA Interface**: Optional OPC UA server for industrial protocol integration
- **Device Discovery**: Automatic device discovery and status monitoring
- **Parameter Control**: Real-time device parameter setting and monitoring

### **NEW: TimescaleDB Integration**
- **Time-Series Storage**: Optimized storage for IoT time-series data
- **Continuous Aggregates**: Automatic hourly and daily aggregations
- **Compression Policies**: Automatic data compression for historical data
- **Retention Policies**: Configurable data retention and cleanup
- **Hypertables**: Automatic time-based partitioning for performance

### **NEW: Advanced Dashboard**
- **FDI Management Tab**: Manage FDI packages, view devices, and control parameters
- **Data Analytics Tab**: Query TimescaleDB data with device and metric selection
- **RedPanda/Kafka Metrics Tab**: Monitor message flow, topics, and consumer groups
- **Real-time Updates**: Live data refresh and device status monitoring
- **Timezone Support**: Proper timezone conversion for data display

### **Data Pipeline Features**
- **Multi-Topic Architecture**: Route data to general and device-specific topics
- **Kafka Integration**: Full RedPanda/Kafka compatibility for event streaming
- **MQTT Protocol**: Industry-standard IoT messaging with QoS 1 and structured topics
- **Data Persistence**: Long-term storage in TimescaleDB with aggregation

## 🔧 Development

### **Dashboard Access**
- **Main Dashboard**: http://localhost:5004 (FDI Package Manager with all features)
- **Legacy Dashboard**: http://localhost:5001 (Basic IoT overview)

### **Service Monitoring**
- **RedPanda Console**: Monitor topics and consumers at http://localhost:8086
- **Service Logs**: `docker-compose logs -f [service-name]`
- **Test App Registry**: http://localhost:5002/api/applications
- **TimescaleDB**: Connect with `psql -h localhost -U iot_user -d iot_cloud`

### **Testing the Pipeline**

1. **Start all services**: `docker-compose up -d`
2. **Check simulator logs**: `docker-compose logs -f smart-breaker-simulator`
3. **Monitor enrichment**: `docker-compose logs -f enrichment-service`
4. **View main dashboard**: Open http://localhost:5004
5. **Test FDI features**: Create and manage FDI packages
6. **Monitor data flow**: Check RedPanda/Kafka metrics tab
7. **Query analytics**: Use the Data Analytics tab with TimescaleDB
8. **Verify data storage**: Check TimescaleDB tables and continuous aggregates

## 🏗️ New Architecture Features

### **FDI Integration & Device Management**
- **FDI Packages**: Standard Field Device Integration packages for device definitions
- **Blob Storage**: File-based storage with manifest management
- **OPC UA Server**: Optional industrial protocol integration
- **Device Discovery**: Real-time device status monitoring
- **Parameter Control**: Live device parameter setting

### **TimescaleDB Time-Series Storage**
- **Hypertables**: Automatic time-based partitioning
- **Continuous Aggregates**: Pre-computed hourly and daily aggregations
- **Compression**: Automatic data compression for historical data
- **Retention**: Configurable data retention policies
- **Performance**: Optimized for time-series queries

### **Advanced Dashboard Interface**
- **FDI Management**: Package management, device monitoring, parameter control
- **Data Analytics**: TimescaleDB querying with device and metric selection
- **RedPanda Metrics**: Message flow monitoring, topic performance, consumer groups
- **Real-time Updates**: Live data refresh and status monitoring
- **Timezone Support**: Proper timezone conversion and display

### **Enhanced Data Pipeline**
- **RedPanda Connector**: Dedicated service for TimescaleDB integration
- **Data Persistence**: Long-term storage with aggregation
- **Performance Monitoring**: Comprehensive metrics and health checks
- **Scalable Architecture**: Easy to add new device types and data sources

## 🚀 Deployment

The platform is containerized with Docker and ready for cloud deployment:

- **Local Development**: `docker-compose up -d`
- **Production**: Use `docker-compose.prod.yml` (create as needed)
- **Kubernetes**: Convert docker-compose to K8s manifests

## 🔧 Troubleshooting

### Common Issues & Solutions

1. **Docker Caching Issues**: Use `docker-compose down --volumes --rmi all` to force complete rebuilds
2. **FDI Service Not Starting**: Check logs with `docker-compose logs fdi-package-manager`
3. **TimescaleDB Connection**: Verify service is healthy with `docker-compose ps timescaledb`
4. **RedPanda Connector**: Check for data type adaptation errors in logs
5. **Dashboard Not Loading**: Ensure FDI service is running and accessible

### Service Status Check

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs -f smart-breaker-simulator
docker-compose logs -f mqtt-kafka-bridge
docker-compose logs -f enrichment-service
docker-compose logs -f fdi-package-manager
docker-compose logs -f redpanda-connect
docker-compose logs -f timescaledb

# Force rebuild all services
docker-compose down --volumes --rmi all
docker-compose up --build -d

# Check TimescaleDB
docker exec -it iot-cloud-timescaledb psql -U iot_user -d iot_cloud -c "\dt"
docker exec -it iot-cloud-timescaledb psql -U iot_user -d iot_cloud -c "\dc"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test with `docker-compose up -d`
5. Ensure all services start correctly
6. Submit a pull request

### Development Guidelines

- **Service Integration**: New services should integrate with existing Kafka topics and TimescaleDB
- **API Design**: Follow RESTful patterns established by the FDI Package Manager
- **Configuration**: Use environment variables for service configuration
- **Testing**: Test with existing simulator and enrichment pipeline
- **MQTT Standards**: Follow MQTT topic naming conventions: `iot/{device_id}/{data_type}`
- **FDI Standards**: Follow Field Device Integration standards for device definitions

## 📄 License

MIT License - see LICENSE file for details.

## 🎯 Current Status

**✅ FULLY OPERATIONAL** - All services running with new FDI and TimescaleDB features:

- **MQTT Simulator**: ✅ Sending data to MQTT topics with burst logic
- **MQTT Broker**: ✅ Eclipse Mosquitto running and healthy
- **MQTT Bridge**: ✅ Successfully forwarding MQTT → Kafka
- **Enrichment Service**: ✅ Processing and routing messages with FDI integration
- **FDI Package Manager**: ✅ Managing device definitions and providing web UI
- **RedPanda Connector**: ✅ Storing data in TimescaleDB
- **TimescaleDB**: ✅ Time-series storage with continuous aggregates
- **Advanced Dashboard**: ✅ Comprehensive interface with all features
- **App Registry**: ✅ Managing application registrations
- **Data Flow**: ✅ Complete MQTT → Kafka → Enrichment → TimescaleDB pipeline working

**New Features**: FDI Package Management, TimescaleDB Integration, Advanced Dashboard
**Status**: All systems operational with enhanced capabilities
