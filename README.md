# ⚡ IoT Cloud Platform

A lightweight, cloud-ready IoT data pipeline with **MQTT-based device communication**, real-time message enrichment, application registry, and **tabbed visualization dashboard** featuring **device-type specific topics** for application data isolation.

## 🏗️ Architecture

```
Smart Breaker Simulator → MQTT Broker → MQTT-Kafka Bridge → RedPanda (iot.raw) → Enrichment Service → RedPanda (iot.enriched) → Web Dashboard
                                    ↓                                    ↓
                            App Registry Service                    Device-Type Topics
                                    ↓                                    ↓
                            Application Registrations         iot.smart_breaker.enriched
                                                                    ↓
                                                            Smart Grid Monitor Tab
```

### Core Services

- **Smart Breaker Simulator**: Generates realistic IoT telemetry + trends data with **burst logic** (3-8 second intervals) via **MQTT**
- **MQTT Broker**: Eclipse Mosquitto for IoT device communication and message routing
- **MQTT-Kafka Bridge**: Connects MQTT topics to RedPanda/Kafka for seamless integration
- **RedPanda**: Event streaming platform (Kafka-compatible) for message brokering
- **Enrichment Service**: Adds device metadata, context, and routes data to **both general AND device-type specific topics**
- **App Registry Service**: Manages applications that register interest in specific device types
- **Web Dashboard**: **Tabbed interface** with IoT Overview + Smart Grid Monitor for application-specific data isolation

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
   - **Web Dashboard**: http://localhost:5001 (with IoT Overview + Smart Grid Monitor tabs)
   - **RedPanda Console**: http://localhost:8086
   - **RedPanda API**: localhost:9092 (external), localhost:29092 (internal)
   - **MQTT Broker**: localhost:1883 (MQTT), localhost:9001 (WebSocket)
   - **App Registry Service**: http://localhost:5002

## 📊 Data Flow

### Message Routing & Topics
The system now supports **MQTT-based IoT communication** with seamless Kafka integration:

**MQTT Topics (Device → MQTT Broker):**
- **`iot/{device_id}/raw`** → Raw telemetry data
- **`iot/{device_id}/trends`** → Aggregated trends data  
- **`iot/{device_id}/status`** → Device status information

**Kafka Topics (MQTT Bridge → RedPanda):**
- **`iot.raw`** → Raw device messages (from MQTT)
- **`iot.enriched`** → General enriched messages (all device types)
- **`iot.smart_breaker.enriched`** → Smart breaker data only (for Smart Grid Monitor app)
- **Future topics**: `iot.smart_meter.enriched`, `iot.environmental_sensor.enriched`

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

### Trends Data (aggregated metrics)
```json
{
  "device_id": "breaker-001",
  "device_type": "smart_breaker",
  "timestamp": "2025-08-20T18:00:54.117782Z",
  "event_type": "trends",
  "trends": [
    {
      "c": "voltage_phase_a",
      "t": 1755625237,
      "v": "117.27",
      "avg": "118.5",
      "min": "115.2",
      "max": "122.1"
    }
  ]
}
```

## 🔧 Configuration

### Device Registry
Edit `config/device-registry.json` to define device types and their capabilities.

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
│   ├── device-registry.json   # Device type definitions
│   └── mosquitto.conf         # MQTT broker configuration
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
│   ├── web-app/               # Tabbed web dashboard
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

- **Real-time Telemetry**: Smart breaker simulator generates realistic electrical measurements with **dynamic burst logic**
- **Trends Aggregation**: Collects and aggregates historical data during message bursts
- **Intelligent Enrichment**: Automatically detects device types and adds metadata
- **Application Registry**: Centralized service for managing application registrations
- **Device Type Mapping**: Dynamic device type detection and metadata enrichment
- **Tabbed Dashboard**: **IoT Overview** (system-wide) + **Smart Grid Monitor** (smart breaker only)
- **Data Isolation**: Each application sees only its relevant device type data
- **Multi-Topic Architecture**: Route data to general and device-specific topics
- **Kafka Integration**: Full RedPanda/Kafka compatibility for event streaming
- **MQTT Protocol**: Industry-standard IoT messaging with QoS 1 and structured topics

## 🔧 Development

- **Tabbed Dashboard**: 
  - **IoT Overview Tab**: System-wide message flow and status at http://localhost:5001
  - **Smart Grid Monitor Tab**: Smart breaker data only (application isolation)
- **RedPanda Console**: Monitor topics and consumers at http://localhost:8086
- **Service Logs**: `docker-compose logs -f [service-name]`
- **Test App Registry**: http://localhost:5002/api/applications
- **Topic Monitoring**: Check device-type specific topics in RedPanda Console

### Testing the Pipeline

1. **Start all services**: `docker-compose up -d`
2. **Check simulator logs**: `docker-compose logs -f smart-breaker-simulator`
3. **Monitor enrichment**: `docker-compose logs -f enrichment-service`
4. **View dashboard**: Open http://localhost:5001
5. **Test tabbed interface**: Switch between IoT Overview and Smart Grid Monitor tabs
6. **Verify data isolation**: Smart Grid Monitor shows only smart breaker data
7. **Check topics**: Verify `iot.smart_breaker.enriched` topic in RedPanda Console
8. **Register test apps**: Use the curl commands above

## 🏗️ New Architecture Features

### **MQTT Integration & IoT Standards**
- **MQTT Protocol**: Industry-standard IoT messaging protocol (QoS 1, retain messages)
- **Topic Hierarchy**: Structured topics like `iot/{device_id}/{data_type}` for easy routing
- **Bridge Architecture**: Seamless MQTT → Kafka integration for hybrid IoT/streaming systems
- **Device Status**: Real-time device online/offline status via MQTT status topics

### **Tabbed Dashboard Interface**
- **IoT Overview Tab**: System-wide monitoring, all device types, general status
- **Smart Grid Monitor Tab**: Application-specific view showing ONLY smart breaker data
- **Data Isolation**: Each tab shows relevant data without cross-contamination

### **Device-Type Specific Topics**
- **Multi-Topic Routing**: Enrichment service publishes to both general and device-specific topics
- **Application Isolation**: Each app subscribes to its relevant topic (e.g., `iot.smart_breaker.enriched`)
- **Scalable Design**: Easy to add new device types and corresponding topics

### **Burst Logic & Dynamic Messaging**
- **Variable Intervals**: Simulator generates messages every 3-8 seconds (not fixed 5-second intervals)
- **Burst Generation**: 25% chance of sending 3-6 messages in rapid succession
- **Trends Integration**: Trends data sent after burst messages for better data analysis

## 🚀 Deployment

The platform is containerized with Docker and ready for cloud deployment:

- **Local Development**: `docker-compose up -d`
- **Production**: Use `docker-compose.prod.yml` (create as needed)
- **Kubernetes**: Convert docker-compose to K8s manifests

## 🔧 Troubleshooting

### Common Issues & Solutions

1. **MQTT Bridge Asyncio Errors**: Fixed - replaced `asyncio.sleep()` with `time.sleep()`
2. **Simulator Logging Issues**: Fixed - switched from `structlog` to standard `logging`
3. **Docker Caching Issues**: Use `docker-compose down [service] && docker rmi -f [image]` to force rebuilds
4. **Service Startup Order**: Services have proper health checks and dependencies

### Service Status Check

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs -f smart-breaker-simulator
docker-compose logs -f mqtt-kafka-bridge
docker-compose logs -f enrichment-service
docker-compose logs -f web-app

# Force rebuild a service
docker-compose down [service-name]
docker rmi -f iot-cloud-[service-name]:latest
docker-compose up -d [service-name]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test with `docker-compose up -d`
5. Ensure all services start correctly
6. Submit a pull request

### Development Guidelines

- **Service Integration**: New services should integrate with the existing Kafka topics
- **API Design**: Follow RESTful patterns established by the app registry service
- **Configuration**: Use environment variables for service configuration
- **Testing**: Test with the existing simulator and enrichment pipeline
- **MQTT Standards**: Follow MQTT topic naming conventions: `iot/{device_id}/{data_type}`

## 📄 License

MIT License - see LICENSE file for details.

## 🎯 Current Status

**✅ FULLY OPERATIONAL** - All services running and communicating successfully:

- **MQTT Simulator**: ✅ Sending data to MQTT topics with burst logic
- **MQTT Broker**: ✅ Eclipse Mosquitto running and healthy
- **MQTT Bridge**: ✅ Successfully forwarding MQTT → Kafka (15,950+ messages processed)
- **Enrichment Service**: ✅ Processing and routing messages to device-specific topics
- **Web Dashboard**: ✅ Accessible with tabbed interface
- **App Registry**: ✅ Managing application registrations
- **Data Flow**: ✅ Complete MQTT → Kafka → Enrichment → Dashboard pipeline working

**Message Count**: 15,950+ and continuously increasing
**Last Test**: 2025-08-20 18:01:17 UTC
**Status**: All systems operational and processing real-time IoT data
