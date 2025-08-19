# ⚡ IoT Cloud Platform

A lightweight, cloud-ready IoT data pipeline with real-time message enrichment, application registry, and visualization dashboard.

## 🏗️ Architecture

```
Smart Breaker Simulator → RedPanda (iot.raw) → Enrichment Service → RedPanda (iot.enriched) → Web Dashboard
                                    ↓
                            App Registry Service
                                    ↓
                            Application Registrations
```

### Core Services

- **Smart Breaker Simulator**: Generates realistic IoT telemetry + trends data every 5 seconds
- **RedPanda**: Event streaming platform (Kafka-compatible) for message brokering
- **Enrichment Service**: Adds device metadata, context, and application registrations to raw messages
- **App Registry Service**: Manages applications that register interest in specific device types
- **Web Dashboard**: Real-time visualization of message flow, system status, and application registrations

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
   - **Web Dashboard**: http://localhost:5001
   - **RedPanda Console**: http://localhost:8086
   - **RedPanda API**: localhost:9092 (external), localhost:29092 (internal)
   - **App Registry Service**: http://localhost:5002

## 📊 Data Flow

### Raw Message (from simulator)
```json
{
  "device_id": "breaker-001",
  "device_type": "smart_breaker",
  "timestamp": "2025-08-19T17:40:37.594176",
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
        "name": "Smart Breaker Dashboard",
        "developer": "IoT Solutions Inc.",
        "platform": "web",
        "category": "Monitoring",
        "status": "active"
      }
    ]
  },
  "enrichment_info": {
    "enriched_at": "2025-08-19T17:40:37.594176",
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
  "timestamp": "2025-08-19T17:40:00",
  "event_type": "trends",
  "trends": [
    {
      "c": "voltage_phase_a",
      "v": 117.27,
      "avg": 118.5,
      "min": 115.2,
      "max": 122.1,
      "t": 1755625237
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
│   └── device-registry.json   # Device type definitions
├── services/                   # Microservices
│   ├── enrichment/            # Message enrichment service
│   │   ├── enrichment_service.py
│   │   └── requirements.txt
│   ├── simulator/             # Smart breaker simulator
│   │   ├── smart_breaker_simulator.py
│   │   └── requirements.txt
│   ├── web-app/               # Web dashboard
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

- **Real-time Telemetry**: Smart breaker simulator generates realistic electrical measurements
- **Trends Aggregation**: Collects and aggregates historical data every 5 minutes
- **Intelligent Enrichment**: Automatically detects device types and adds metadata
- **Application Registry**: Centralized service for managing application registrations
- **Device Type Mapping**: Dynamic device type detection and metadata enrichment
- **Real-time Dashboard**: Beautiful dark IoT command center with live data visualization
- **Kafka Integration**: Full RedPanda/Kafka compatibility for event streaming

## 🔧 Development

- **Real-time Dashboard**: View message flow at http://localhost:5001
- **RedPanda Console**: Monitor topics and consumers at http://localhost:8086
- **Service Logs**: `docker-compose logs -f [service-name]`
- **Test App Registry**: http://localhost:5002/api/applications

### Testing the Pipeline

1. **Start all services**: `docker-compose up -d`
2. **Check simulator logs**: `docker-compose logs -f smart-breaker-simulator`
3. **Monitor enrichment**: `docker-compose logs -f enrichment-service`
4. **View dashboard**: Open http://localhost:5001
5. **Register test apps**: Use the curl commands above

## 🚀 Deployment

The platform is containerized with Docker and ready for cloud deployment:

- **Local Development**: `docker-compose up -d`
- **Production**: Use `docker-compose.prod.yml` (create as needed)
- **Kubernetes**: Convert docker-compose to K8s manifests

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

## 📄 License

MIT License - see LICENSE file for details.
