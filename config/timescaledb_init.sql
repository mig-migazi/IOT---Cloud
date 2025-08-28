-- TimescaleDB Initialization Script for IoT Cloud Platform
-- This script sets up the database schema optimized for time-series IoT data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create tables for different types of IoT data
-- Raw IoT data table (from MQTT bridge)
CREATE TABLE IF NOT EXISTS iot_raw_data (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    payload JSONB,
    message_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enriched IoT data table (from enrichment service)
CREATE TABLE IF NOT EXISTS iot_enriched_data (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    device_type TEXT,
    device_name TEXT,
    topic TEXT NOT NULL,
    measurements JSONB,
    metadata JSONB,
    message_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Smart breaker specific data table
CREATE TABLE IF NOT EXISTS smart_breaker_data (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    voltage_phase_a NUMERIC(10,3),
    voltage_phase_b NUMERIC(10,3),
    voltage_phase_c NUMERIC(10,3),
    current_phase_a NUMERIC(10,3),
    current_phase_b NUMERIC(10,3),
    current_phase_c NUMERIC(10,3),
    power_factor NUMERIC(5,3),
    frequency NUMERIC(6,2),
    temperature NUMERIC(6,2),
    status TEXT,
    alarms JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Device metadata table (static device information)
CREATE TABLE IF NOT EXISTS device_metadata (
    device_id TEXT PRIMARY KEY,
    device_type TEXT NOT NULL,
    device_name TEXT,
    location TEXT,
    manufacturer TEXT,
    model TEXT,
    capabilities JSONB,
    fdi_package_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_iot_raw_data_time ON iot_raw_data (time DESC);
CREATE INDEX IF NOT EXISTS idx_iot_raw_data_device ON iot_raw_data (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_iot_raw_data_topic ON iot_raw_data (topic, time DESC);

CREATE INDEX IF NOT EXISTS idx_iot_enriched_data_time ON iot_enriched_data (time DESC);
CREATE INDEX IF NOT EXISTS idx_iot_enriched_data_device ON iot_enriched_data (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_iot_enriched_data_type ON iot_enriched_data (device_type, time DESC);

CREATE INDEX IF NOT EXISTS idx_smart_breaker_data_time ON smart_breaker_data (time DESC);
CREATE INDEX IF NOT EXISTS idx_smart_breaker_data_device ON smart_breaker_data (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_smart_breaker_data_status ON smart_breaker_data (status, time DESC);

-- Convert tables to hypertables for time-series optimization
SELECT create_hypertable('iot_raw_data', 'time', if_not_exists => TRUE);
SELECT create_hypertable('iot_enriched_data', 'time', if_not_exists => TRUE);
SELECT create_hypertable('smart_breaker_data', 'time', if_not_exists => TRUE);

-- Set compression policies for data retention
-- Compress chunks older than 1 hour
SELECT add_compression_policy('iot_raw_data', INTERVAL '1 hour');
SELECT add_compression_policy('iot_enriched_data', INTERVAL '1 hour');
SELECT add_compression_policy('smart_breaker_data', INTERVAL '1 hour');

-- Set retention policies (keep data for 30 days)
SELECT add_retention_policy('iot_raw_data', INTERVAL '30 days');
SELECT add_retention_policy('iot_enriched_data', INTERVAL '30 days');
SELECT add_retention_policy('smart_breaker_data', INTERVAL '30 days');

-- Create continuous aggregates for common queries
-- Hourly aggregations for smart breaker data
CREATE MATERIALIZED VIEW IF NOT EXISTS smart_breaker_hourly_stats
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    device_id,
    AVG(voltage_phase_a) as avg_voltage_a,
    AVG(voltage_phase_b) as avg_voltage_b,
    AVG(voltage_phase_c) as avg_voltage_c,
    AVG(current_phase_a) as avg_current_a,
    AVG(current_phase_b) as avg_current_b,
    AVG(current_phase_c) as avg_current_c,
    AVG(power_factor) as avg_power_factor,
    AVG(frequency) as avg_frequency,
    AVG(temperature) as avg_temperature,
    COUNT(*) as measurement_count,
    MIN(time) as first_measurement,
    MAX(time) as last_measurement
FROM smart_breaker_data
GROUP BY bucket, device_id;

-- Daily aggregations for smart breaker data
CREATE MATERIALIZED VIEW IF NOT EXISTS smart_breaker_daily_stats
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    device_id,
    AVG(voltage_phase_a) as avg_voltage_a,
    AVG(voltage_phase_b) as avg_voltage_b,
    AVG(voltage_phase_c) as avg_voltage_c,
    AVG(current_phase_a) as avg_current_a,
    AVG(current_phase_b) as avg_current_b,
    AVG(current_phase_c) as avg_current_c,
    AVG(power_factor) as avg_power_factor,
    AVG(frequency) as avg_frequency,
    AVG(temperature) as avg_temperature,
    COUNT(*) as measurement_count,
    MIN(time) as first_measurement,
    MAX(time) as last_measurement
FROM smart_breaker_data
GROUP BY bucket, device_id;

-- Set refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('smart_breaker_hourly_stats',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('smart_breaker_daily_stats',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- Create a function to update device metadata
CREATE OR REPLACE FUNCTION update_device_metadata(
    p_device_id TEXT,
    p_device_type TEXT,
    p_device_name TEXT DEFAULT NULL,
    p_location TEXT DEFAULT NULL,
    p_manufacturer TEXT DEFAULT NULL,
    p_model TEXT DEFAULT NULL,
    p_capabilities JSONB DEFAULT NULL,
    p_fdi_package_id TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO device_metadata (
        device_id, device_type, device_name, location, 
        manufacturer, model, capabilities, fdi_package_id
    ) VALUES (
        p_device_id, p_device_type, p_device_name, p_location,
        p_manufacturer, p_model, p_capabilities, p_fdi_package_id
    )
    ON CONFLICT (device_id) DO UPDATE SET
        device_type = EXCLUDED.device_type,
        device_name = COALESCE(EXCLUDED.device_name, device_metadata.device_name),
        location = COALESCE(EXCLUDED.location, device_metadata.location),
        manufacturer = COALESCE(EXCLUDED.manufacturer, device_metadata.manufacturer),
        model = COALESCE(EXCLUDED.model, device_metadata.model),
        capabilities = COALESCE(EXCLUDED.capabilities, device_metadata.capabilities),
        fdi_package_id = COALESCE(EXCLUDED.fdi_package_id, device_metadata.fdi_package_id),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to the iot_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iot_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO iot_user;

-- Create a view for easy access to latest device status
CREATE OR REPLACE VIEW latest_device_status AS
SELECT DISTINCT ON (device_id)
    device_id,
    device_type,
    device_name,
    time,
    measurements,
    metadata
FROM iot_enriched_data
ORDER BY device_id, time DESC;

-- Grant access to the view
GRANT SELECT ON latest_device_status TO iot_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialization completed successfully';
    RAISE NOTICE 'Hypertables created for: iot_raw_data, iot_enriched_data, smart_breaker_data';
    RAISE NOTICE 'Continuous aggregates created for: smart_breaker_hourly_stats, smart_breaker_daily_stats';
    RAISE NOTICE 'Database ready for IoT time-series data ingestion';
END $$;
