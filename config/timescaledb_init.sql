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

-- ============================================================================
-- ALARM RULES SYSTEM
-- ============================================================================

-- Device Types Table (linked to FDI packages)
CREATE TABLE IF NOT EXISTS device_types (
    id SERIAL PRIMARY KEY,
    device_type VARCHAR(100) UNIQUE NOT NULL,
    device_type_name VARCHAR(200) NOT NULL,
    fdi_package_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alarm Rule Categories
CREATE TABLE IF NOT EXISTS alarm_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    severity_level VARCHAR(20) DEFAULT 'medium' -- low, medium, high, critical
);

-- Alarm Rules Table
CREATE TABLE IF NOT EXISTS alarm_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    device_type_id INTEGER REFERENCES device_types(id),
    category_id INTEGER REFERENCES alarm_categories(id),
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1, -- 1=highest, 10=lowest
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    description TEXT
);

-- Rule Conditions Table (supports complex conditions)
CREATE TABLE IF NOT EXISTS rule_conditions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alarm_rules(id) ON DELETE CASCADE,
    condition_order INTEGER NOT NULL, -- for AND/OR logic
    field_path VARCHAR(500) NOT NULL, -- JSON path like "measurements.voltage.phase_a"
    operator VARCHAR(30) NOT NULL, -- see supported operators below
    threshold_value JSONB, -- can be single value, array, or complex object
    threshold_unit VARCHAR(50), -- V, A, °C, etc.
    logical_operator VARCHAR(10) DEFAULT 'AND', -- AND, OR, NOT
    time_window INTEGER, -- for time-based conditions (seconds)
    consecutive_count INTEGER, -- for consecutive condition checks
    description TEXT -- human readable description of condition
);

-- Rule Actions Table (what happens when alarm triggers)
CREATE TABLE IF NOT EXISTS rule_actions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alarm_rules(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL, -- publish_alarm, send_notification, log_event
    action_config JSONB, -- configuration for the action
    action_order INTEGER DEFAULT 1
);

-- Alarm Instances Table (actual triggered alarms) - Time-series table
CREATE TABLE IF NOT EXISTS alarm_instances (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alarm_rules(id),
    device_id VARCHAR(100) NOT NULL,
    device_type_id INTEGER REFERENCES device_types(id),
    alarm_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved, suppressed
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(100),
    alarm_data JSONB, -- the actual telemetry data that triggered the alarm
    alarm_message TEXT,
    resolution_notes TEXT
);

-- Rule Templates Table (for common rule patterns)
CREATE TABLE IF NOT EXISTS rule_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    device_type_id INTEGER REFERENCES device_types(id),
    template_config JSONB NOT NULL, -- JSON structure of the rule
    is_system_template BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for alarm system performance
CREATE INDEX IF NOT EXISTS idx_alarm_rules_device_type ON alarm_rules(device_type_id);
CREATE INDEX IF NOT EXISTS idx_alarm_rules_active ON alarm_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_rule_conditions_rule_id ON rule_conditions(rule_id);
CREATE INDEX IF NOT EXISTS idx_alarm_instances_device_id ON alarm_instances(device_id);
CREATE INDEX IF NOT EXISTS idx_alarm_instances_triggered_at ON alarm_instances(triggered_at);
CREATE INDEX IF NOT EXISTS idx_alarm_instances_status ON alarm_instances(status);

-- Convert alarm_instances to hypertable for time-series optimization
SELECT create_hypertable('alarm_instances', 'triggered_at', if_not_exists => TRUE);

-- Set compression and retention policies for alarm instances
SELECT add_compression_policy('alarm_instances', INTERVAL '1 hour');
SELECT add_retention_policy('alarm_instances', INTERVAL '90 days'); -- Keep alarms longer than telemetry

-- Insert default categories
INSERT INTO alarm_categories (category_name, description, severity_level) VALUES
('safety', 'Safety-related alarms that require immediate attention', 'critical'),
('performance', 'Performance degradation alarms', 'medium'),
('maintenance', 'Maintenance-related alarms', 'low'),
('communication', 'Communication and connectivity issues', 'high'),
('environmental', 'Environmental condition alarms', 'medium')
ON CONFLICT (category_name) DO NOTHING;

-- Insert default device types (based on your current setup)
INSERT INTO device_types (device_type, device_type_name, fdi_package_id) VALUES
('smart_breaker', 'Smart Circuit Breaker', 'smart-breaker-fdi-v1.0'),
('smart_meter', 'Smart Energy Meter', 'smart-meter-fdi-v1.0'),
('environmental_sensor', 'Environmental Sensor', 'env-sensor-fdi-v1.0')
ON CONFLICT (device_type) DO NOTHING;

-- Grant permissions to the iot_user for alarm tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iot_user;

-- ============================================================================
-- SAMPLE ALARM RULES FOR SMART BREAKER SIMULATOR
-- ============================================================================

-- Insert sample alarm rules for smart_breaker device type
INSERT INTO alarm_rules (rule_name, device_type_id, category_id, priority, description) VALUES
-- VOLTAGE ALARMS
('High Voltage Phase A', 1, 1, 1, 'Phase A voltage exceeds safe operating range (>125V)'),
('Low Voltage Phase A', 1, 1, 1, 'Phase A voltage below safe operating range (<115V)'),
('High Voltage Phase B', 1, 1, 1, 'Phase B voltage exceeds safe operating range (>125V)'),
('Low Voltage Phase B', 1, 1, 1, 'Phase B voltage below safe operating range (<115V)'),
('High Voltage Phase C', 1, 1, 1, 'Phase C voltage exceeds safe operating range (>125V)'),
('Low Voltage Phase C', 1, 1, 1, 'Phase C voltage below safe operating range (<115V)'),

-- TEMPERATURE ALARMS
('High Temperature', 1, 1, 1, 'Device temperature exceeds safe operating range (>75°C)'),
('Critical Temperature', 1, 1, 1, 'Device temperature critical (>80°C)'),

-- CURRENT ALARMS
('High Current Phase A', 1, 1, 2, 'Phase A current exceeds rated capacity (>90A)'),
('High Current Phase B', 1, 1, 2, 'Phase B current exceeds rated capacity (>90A)'),
('High Current Phase C', 1, 1, 2, 'Phase C current exceeds rated capacity (>90A)'),

-- POWER ALARMS
('High Active Power', 1, 2, 2, 'Active power consumption exceeds threshold (>11000W)'),
('Low Power Factor', 1, 2, 3, 'Power factor below acceptable threshold (<0.85)'),

-- FREQUENCY ALARMS
('Frequency Out of Range', 1, 1, 2, 'Grid frequency outside acceptable range (59.5-60.5 Hz)'),

-- PROTECTION ALARMS
('Ground Fault Detected', 1, 1, 1, 'Ground fault current detected (>3A)'),
('Arc Fault Detected', 1, 1, 1, 'Arc fault condition detected'),
('High Trip Count', 1, 3, 3, 'Excessive trip count indicates maintenance needed (>8 trips)'),

-- OPERATIONAL ALARMS
('High Load Percentage', 1, 2, 2, 'Load percentage exceeds recommended threshold (>85%)'),
('Maintenance Due', 1, 3, 3, 'Device maintenance is due');

-- VOLTAGE RULE CONDITIONS
INSERT INTO rule_conditions (rule_id, condition_order, field_path, operator, threshold_value, threshold_unit, logical_operator, description) VALUES
-- High Voltage Phase A (rule_id = 1)
(1, 1, 'measurements.voltage.phase_a', 'gt', '125.0', 'V', 'AND', 'Phase A voltage > 125V'),

-- Low Voltage Phase A (rule_id = 2)
(2, 1, 'measurements.voltage.phase_a', 'lt', '115.0', 'V', 'AND', 'Phase A voltage < 115V'),

-- High Voltage Phase B (rule_id = 3)
(3, 1, 'measurements.voltage.phase_b', 'gt', '125.0', 'V', 'AND', 'Phase B voltage > 125V'),

-- Low Voltage Phase B (rule_id = 4)
(4, 1, 'measurements.voltage.phase_b', 'lt', '115.0', 'V', 'AND', 'Phase B voltage < 115V'),

-- High Voltage Phase C (rule_id = 5)
(5, 1, 'measurements.voltage.phase_c', 'gt', '125.0', 'V', 'AND', 'Phase C voltage > 125V'),

-- Low Voltage Phase C (rule_id = 6)
(6, 1, 'measurements.voltage.phase_c', 'lt', '115.0', 'V', 'AND', 'Phase C voltage < 115V'),

-- TEMPERATURE RULE CONDITIONS
-- High Temperature (rule_id = 7)
(7, 1, 'measurements.temperature.value', 'gt', '75.0', '°C', 'AND', 'Temperature > 75°C'),

-- Critical Temperature (rule_id = 8)
(8, 1, 'measurements.temperature.value', 'gt', '80.0', '°C', 'AND', 'Temperature > 80°C'),

-- CURRENT RULE CONDITIONS
-- High Current Phase A (rule_id = 9)
(9, 1, 'measurements.current.phase_a', 'gt', '90.0', 'A', 'AND', 'Phase A current > 90A'),

-- High Current Phase B (rule_id = 10)
(10, 1, 'measurements.current.phase_b', 'gt', '90.0', 'A', 'AND', 'Phase B current > 90A'),

-- High Current Phase C (rule_id = 11)
(11, 1, 'measurements.current.phase_c', 'gt', '90.0', 'A', 'AND', 'Phase C current > 90A'),

-- POWER RULE CONDITIONS
-- High Active Power (rule_id = 12)
(12, 1, 'measurements.power.active', 'gt', '11000.0', 'W', 'AND', 'Active power > 11000W'),

-- Low Power Factor (rule_id = 13)
(13, 1, 'measurements.power.factor', 'lt', '0.85', '', 'AND', 'Power factor < 0.85'),

-- FREQUENCY RULE CONDITIONS
-- Frequency Out of Range (rule_id = 14)
(14, 1, 'measurements.frequency.value', 'out_of_range', '{"min": 59.5, "max": 60.5}', 'Hz', 'AND', 'Frequency outside 59.5-60.5 Hz'),

-- PROTECTION RULE CONDITIONS
-- Ground Fault Detected (rule_id = 15)
(15, 1, 'measurements.protection.ground_fault_current', 'gt', '3.0', 'A', 'AND', 'Ground fault current > 3A'),

-- Arc Fault Detected (rule_id = 16)
(16, 1, 'measurements.protection.arc_fault_detected', 'eq', 'true', '', 'AND', 'Arc fault detected'),

-- High Trip Count (rule_id = 17)
(17, 1, 'measurements.protection.trip_count', 'gt', '8', '', 'AND', 'Trip count > 8'),

-- OPERATIONAL RULE CONDITIONS
-- High Load Percentage (rule_id = 18)
(18, 1, 'measurements.operational.load_percentage', 'gt', '85.0', '%', 'AND', 'Load percentage > 85%'),

-- Maintenance Due (rule_id = 19)
(19, 1, 'measurements.operational.maintenance_due', 'eq', 'true', '', 'AND', 'Maintenance due flag is true');

-- RULE ACTIONS
INSERT INTO rule_actions (rule_id, action_type, action_config, action_order) VALUES
-- Safety rules (critical/high severity)
(1, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(2, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(3, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(4, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(5, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(6, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(7, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(8, 'publish_alarm', '{"topic": "iot.alarms", "severity": "critical", "auto_acknowledge": false}', 1),
(15, 'publish_alarm', '{"topic": "iot.alarms", "severity": "critical", "auto_acknowledge": false}', 1),
(16, 'publish_alarm', '{"topic": "iot.alarms", "severity": "critical", "auto_acknowledge": false}', 1),

-- Performance rules (medium severity)
(9, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(10, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(11, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(12, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(13, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(14, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(18, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),

-- Maintenance rules (low severity)
(17, 'publish_alarm', '{"topic": "iot.alarms", "severity": "low", "auto_acknowledge": true}', 1),
(19, 'publish_alarm', '{"topic": "iot.alarms", "severity": "low", "auto_acknowledge": true}', 1);

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialization completed successfully';
    RAISE NOTICE 'Hypertables created for: iot_raw_data, iot_enriched_data, smart_breaker_data, alarm_instances';
    RAISE NOTICE 'Continuous aggregates created for: smart_breaker_hourly_stats, smart_breaker_daily_stats';
    RAISE NOTICE 'Alarm rules system initialized with device types and categories';
    RAISE NOTICE 'Database ready for IoT time-series data ingestion and alarm processing';
END $$;
