# 🚀 IOT-Cloud

A lightweight, cloud-ready IoT data pipeline with real-time message enrichment and visualization.

## ��️ Architecture

```
Smart Breaker Simulator → RedPanda (iot.raw) → Enrichment Service → RedPanda (iot.enriched) → Web Dashboard
```

- **Smart Breaker Simulator**: Generates realistic IoT device data
- **RedPanda**: Event streaming platform (Kafka-compatible)
- **Enrichment Service**: Adds device metadata and context to raw messages
- **Web Dashboard**: Real-time visualization of message flow

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
   - **Web Dashboard**: http://localhost:5000
   - **RedPanda Console**: http://localhost:8086
   - **RedPanda API**: localhost:9092

## 📊 Data Flow

### Raw Message (from simulator)
```json
{
  "device_id": "breaker-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "measurements": {
    "voltage": 120.5,
    "current": 15.2,
    "frequency": 60.0,
    "power": 1830.6,
    "temperature": 45.2,
    "status": "normal",
    "trip_count": 0,
    "operating_hours": 8760
  }
}
```

### Enriched Message (after enrichment service)
```json
{
  "device_id": "breaker-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "device_metadata": {
    "device_type": "smart_breaker",
    "device_name": "Main Circuit Breaker",
    "location": "Electrical Room A",
    "manufacturer": "ElectroCorp",
    "model": "SB-2000"
  },
  "measurements": {
    "voltage": {
      "value": 120.5,
      "unit": "V",
      "description": "Line voltage",
      "min_value": 110.0,
      "max_value": 130.0,
      "data_type": "float"
    }
  }
}
```

## ⚙️ Configuration

### Device Registry
Edit `config/device-registry.json` to define your devices.

### Environment Variables
Copy `config/config.env.example` to `config/config.env` and customize.

## 📁 Project Structure

```
IOT-Cloud/
├── config/                     # Configuration files
├── services/                   # Microservices
│   ├── enrichment/            # Message enrichment service
│   ├── simulator/             # Smart breaker simulator
│   └── web-app/               # Web dashboard
├── docker-compose.yml          # Service orchestration
├── setup.sh                    # Initial setup script
└── README.md                   # This file
```

## 🔧 Development

- **Real-time Dashboard**: View message flow at http://localhost:5000
- **RedPanda Console**: Monitor topics and consumers at http://localhost:8086
- **Service Logs**: `docker-compose logs -f [service-name]`

## 🚀 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment options.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `docker-compose up -d`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
