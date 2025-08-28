# RedPanda to TimescaleDB Connector

This service connects RedPanda (Kafka-compatible streaming platform) to TimescaleDB for time-series IoT data storage and analytics.

## 🎯 Purpose

The connector serves as a bridge between the streaming layer (RedPanda) and the time-series database (TimescaleDB), enabling:

- **Real-time data ingestion** from IoT devices via RedPanda topics
- **Time-series optimization** using TimescaleDB's hypertables and continuous aggregates
- **Efficient storage** with automatic compression and retention policies
- **Built-in aggregation** leveraging TimescaleDB's continuous aggregates instead of application-level aggregation

## 🏗️ Architecture

```
IoT Devices → MQTT → RedPanda → RedPanda Connector → TimescaleDB
                                    ↓
                              Real-time Analytics
                              Historical Trends
                              Continuous Aggregates
```

## 📊 Data Flow

1. **Raw Data**: IoT messages from `iot.raw` topic stored in `iot_raw_data` table
2. **Enriched Data**: Processed messages from `iot.enriched` topic stored in `iot_enriched_data` table  
3. **Device-Specific Data**: Smart breaker data from `iot.smart_breaker.enriched` stored in `smart_breaker_data` table
4. **Automatic Aggregation**: TimescaleDB creates hourly and daily continuous aggregates
5. **Compression & Retention**: Automatic data compression after 1 hour, retention for 30 days

## 🚀 Features

### **TimescaleDB Optimizations**
- **Hypertables**: Automatic partitioning by time for efficient queries
- **Continuous Aggregates**: Pre-computed hourly and daily aggregations
- **Compression**: Automatic compression of old data chunks
- **Retention**: Configurable data retention policies

### **Data Types Supported**
- **Raw IoT Data**: Unprocessed device messages
- **Enriched Data**: Messages with device metadata and FDI package information
- **Smart Breaker Data**: Structured electrical measurements (voltage, current, temperature, etc.)

### **Real-time Processing**
- **Multi-threaded consumers**: Separate threads for each topic type
- **Connection pooling**: Efficient database connection management
- **Error handling**: Robust error handling with detailed logging

## 🔧 Configuration

### **Environment Variables**
```bash
# RedPanda Configuration
REDPANDA_BROKERS=redpanda:29092
RAW_TOPIC=iot.raw
ENRICHED_TOPIC=iot.enriched
SMART_BREAKER_TOPIC=iot.smart_breaker.enriched

# TimescaleDB Configuration
TIMESCALEDB_HOST=timescaledb
TIMESCALEDB_PORT=5432
TIMESCALEDB_DB=iot_cloud
TIMESCALEDB_USER=iot_user
TIMESCALEDB_PASSWORD=iot_password
```

### **Database Schema**
The connector automatically creates and manages:
- `iot_raw_data`: Raw IoT messages
- `iot_enriched_data`: Enriched device data
- `smart_breaker_data`: Smart breaker specific measurements
- `device_metadata`: Device information and capabilities
- Continuous aggregates for hourly and daily statistics

## 📈 Analytics Capabilities

### **Built-in Aggregations**
- **Hourly Stats**: Average, min, max, count for each hour
- **Daily Stats**: Daily aggregations for trend analysis
- **Real-time Queries**: Efficient time-range queries using hypertables

### **Query Examples**
```sql
-- Get last 24 hours of voltage data
SELECT time_bucket('1 hour', time) as bucket, 
       AVG(voltage_phase_a) as avg_voltage
FROM smart_breaker_data 
WHERE time > NOW() - INTERVAL '24 hours'
GROUP BY bucket ORDER BY bucket;

-- Use continuous aggregate for daily stats
SELECT * FROM smart_breaker_daily_stats 
WHERE bucket > NOW() - INTERVAL '7 days';
```

## 🚀 Getting Started

### **1. Start the Services**
```bash
docker-compose up -d timescaledb redpanda-connector
```

### **2. Verify Connection**
Check the connector logs:
```bash
docker-compose logs redpanda-connector
```

### **3. Monitor Data Flow**
View the TimescaleDB dashboard tab in the FDI Package Manager UI at `http://localhost:5004`

## 🔍 Monitoring

### **Health Checks**
- Database connection pool status
- Consumer group offsets
- Message processing statistics
- Error rates and counts

### **Metrics**
- Messages processed per second
- Data points stored
- Database connection pool utilization
- Consumer lag

## 🛠️ Troubleshooting

### **Common Issues**

1. **Database Connection Failed**
   - Check TimescaleDB service is running
   - Verify connection credentials
   - Check network connectivity

2. **No Messages Being Processed**
   - Verify RedPanda topics exist
   - Check consumer group configuration
   - Monitor consumer logs for errors

3. **High Memory Usage**
   - Adjust connection pool size
   - Monitor TimescaleDB memory settings
   - Check for memory leaks in long-running queries

### **Logs**
```bash
# View connector logs
docker-compose logs -f redpanda-connector

# Check database connectivity
docker exec -it iot-cloud-timescaledb psql -U iot_user -d iot_cloud -c "SELECT version();"
```

## 🔮 Future Enhancements

- **Real-time Dashboards**: Grafana integration for advanced visualizations
- **Alerting**: Configurable alerts based on data thresholds
- **Data Export**: CSV/JSON export capabilities
- **Advanced Analytics**: Machine learning integration for predictive maintenance
- **Multi-tenant Support**: Isolated data storage per customer/organization

## 📚 Resources

- [TimescaleDB Documentation](https://docs.timescale.com/)
- [RedPanda Documentation](https://docs.redpanda.com/)
- [Kafka Python Client](https://kafka-python.readthedocs.io/)
- [PostgreSQL Python Driver](https://www.psycopg.org/docs/)
