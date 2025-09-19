-- Alarm Rules Schema for TimescaleDB
-- This schema supports device-type specific alarm rules based on FDI ontologies
-- Integrates with existing iot_cloud database

-- Device Types Table (linked to FDI packages)
CREATE TABLE device_types (
    id SERIAL PRIMARY KEY,
    device_type VARCHAR(100) UNIQUE NOT NULL,
    device_type_name VARCHAR(200) NOT NULL,
    fdi_package_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alarm Rule Categories
CREATE TABLE alarm_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    severity_level VARCHAR(20) DEFAULT 'medium' -- low, medium, high, critical
);

-- Alarm Rules Table
CREATE TABLE alarm_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    device_type_id INTEGER REFERENCES device_types(id),
    category_id INTEGER REFERENCES alarm_categories(id),
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1, -- 1=highest, 10=lowest
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    description TEXT
);

-- Rule Conditions Table (supports complex conditions)
CREATE TABLE rule_conditions (
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

-- Supported Operators:
-- BASIC: eq, ne, gt, gte, lt, lte, is_null, is_not_null
-- RANGE: between, not_between, in_range, out_of_range, in, not_in
-- STRING: contains, not_contains, starts_with, ends_with, regex, not_regex
-- ARRAY: array_contains, array_not_contains, array_size, array_empty
-- TIME: duration_gt, duration_lt, time_since_last, consecutive_gt, consecutive_lt
-- AGGREGATE: avg_gt, avg_lt, max_gt, min_lt, sum_gt, count_gt
-- COMPLEX: any_field_gt, all_fields_gt, field_ratio_gt, field_difference_gt

-- Rule Actions Table (what happens when alarm triggers)
CREATE TABLE rule_actions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alarm_rules(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL, -- publish_alarm, send_notification, log_event
    action_config JSONB, -- configuration for the action
    action_order INTEGER DEFAULT 1
);

-- Alarm Instances Table (actual triggered alarms)
CREATE TABLE alarm_instances (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alarm_rules(id),
    device_id VARCHAR(100) NOT NULL,
    device_type_id INTEGER REFERENCES device_types(id),
    alarm_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved, suppressed
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100),
    alarm_data JSONB, -- the actual telemetry data that triggered the alarm
    alarm_message TEXT,
    resolution_notes TEXT
);

-- Rule Templates Table (for common rule patterns)
CREATE TABLE rule_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    device_type_id INTEGER REFERENCES device_types(id),
    template_config JSONB NOT NULL, -- JSON structure of the rule
    is_system_template BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_alarm_rules_device_type ON alarm_rules(device_type_id);
CREATE INDEX idx_alarm_rules_active ON alarm_rules(is_active);
CREATE INDEX idx_rule_conditions_rule_id ON rule_conditions(rule_id);
CREATE INDEX idx_alarm_instances_device_id ON alarm_instances(device_id);
CREATE INDEX idx_alarm_instances_triggered_at ON alarm_instances(triggered_at);
CREATE INDEX idx_alarm_instances_status ON alarm_instances(status);

-- Insert default categories
INSERT INTO alarm_categories (category_name, description, severity_level) VALUES
('safety', 'Safety-related alarms that require immediate attention', 'critical'),
('performance', 'Performance degradation alarms', 'medium'),
('maintenance', 'Maintenance-related alarms', 'low'),
('communication', 'Communication and connectivity issues', 'high'),
('environmental', 'Environmental condition alarms', 'medium');

-- Insert default device types (based on your current setup)
INSERT INTO device_types (device_type, device_type_name, fdi_package_id) VALUES
('smart_breaker', 'Smart Circuit Breaker', 'smart-breaker-fdi-v1.0'),
('smart_meter', 'Smart Energy Meter', 'smart-meter-fdi-v1.0'),
('environmental_sensor', 'Environmental Sensor', 'env-sensor-fdi-v1.0');

-- Example alarm rules for smart_breaker (comprehensive examples)
INSERT INTO alarm_rules (rule_name, device_type_id, category_id, priority, description) VALUES
-- BASIC THRESHOLD RULES
('High Voltage Phase A', 1, 1, 1, 'Voltage on Phase A exceeds safe operating range'),
('Low Voltage Phase A', 1, 1, 1, 'Voltage on Phase A below safe operating range'),
('High Temperature', 1, 1, 1, 'Device temperature exceeds safe operating range'),
('Low Power Factor', 1, 2, 3, 'Power factor below acceptable threshold'),

-- RANGE-BASED RULES
('Voltage Out of Range', 1, 1, 1, 'Any phase voltage outside acceptable range'),
('Temperature Range Check', 1, 1, 2, 'Temperature outside normal operating range'),

-- COMPLEX MULTI-FIELD RULES
('All Phases High Voltage', 1, 1, 1, 'All three phases exceed voltage threshold'),
('Phase Imbalance', 1, 2, 2, 'Significant voltage imbalance between phases'),
('High Load with High Temperature', 1, 1, 1, 'High load combined with high temperature'),

-- TIME-BASED RULES
('Sustained High Temperature', 1, 1, 1, 'High temperature sustained for extended period'),
('Consecutive Voltage Spikes', 1, 1, 2, 'Multiple voltage spikes in short time'),

-- COMMUNICATION RULES
('Communication Loss', 1, 4, 2, 'Device communication timeout detected'),
('Data Quality Issues', 1, 4, 3, 'Missing or invalid measurement data'),

-- AGGREGATE RULES
('Average Power Too High', 1, 2, 2, 'Average power consumption exceeds threshold'),
('Peak Current Exceeded', 1, 1, 1, 'Peak current exceeds rated capacity');

-- BASIC THRESHOLD CONDITIONS
INSERT INTO rule_conditions (rule_id, condition_order, field_path, operator, threshold_value, threshold_unit, logical_operator, description) VALUES
-- High Voltage Phase A
(1, 1, 'measurements.voltage.phase_a', 'gt', '125.0', 'V', 'AND', 'Phase A voltage above 125V'),

-- Low Voltage Phase A  
(2, 1, 'measurements.voltage.phase_a', 'lt', '115.0', 'V', 'AND', 'Phase A voltage below 115V'),

-- High Temperature
(3, 1, 'measurements.temperature.value', 'gt', '75.0', '°C', 'AND', 'Temperature above 75°C'),

-- Low Power Factor
(4, 1, 'measurements.power.factor', 'lt', '0.85', '', 'AND', 'Power factor below 0.85');

-- RANGE-BASED CONDITIONS
INSERT INTO rule_conditions (rule_id, condition_order, field_path, operator, threshold_value, threshold_unit, logical_operator, description) VALUES
-- Voltage Out of Range (any phase)
(5, 1, 'measurements.voltage.phase_a', 'out_of_range', '{"min": 115.0, "max": 125.0}', 'V', 'OR', 'Phase A out of range'),
(5, 2, 'measurements.voltage.phase_b', 'out_of_range', '{"min": 115.0, "max": 125.0}', 'V', 'OR', 'Phase B out of range'),
(5, 3, 'measurements.voltage.phase_c', 'out_of_range', '{"min": 115.0, "max": 125.0}', 'V', 'OR', 'Phase C out of range'),

-- Temperature Range Check
(6, 1, 'measurements.temperature.value', 'not_between', '{"min": 20.0, "max": 75.0}', '°C', 'AND', 'Temperature outside 20-75°C range');

-- COMPLEX MULTI-FIELD CONDITIONS
INSERT INTO rule_conditions (rule_id, condition_order, field_path, operator, threshold_value, threshold_unit, logical_operator, description) VALUES
-- All Phases High Voltage
(7, 1, 'measurements.voltage.phase_a', 'gt', '125.0', 'V', 'AND', 'Phase A > 125V'),
(7, 2, 'measurements.voltage.phase_b', 'gt', '125.0', 'V', 'AND', 'Phase B > 125V'),
(7, 3, 'measurements.voltage.phase_c', 'gt', '125.0', 'V', 'AND', 'Phase C > 125V'),

-- Phase Imbalance (voltage difference between phases)
(8, 1, 'measurements.voltage.phase_a', 'field_difference_gt', '{"field": "measurements.voltage.phase_b", "threshold": 10.0}', 'V', 'OR', 'Phase A-B difference > 10V'),
(8, 2, 'measurements.voltage.phase_b', 'field_difference_gt', '{"field": "measurements.voltage.phase_c", "threshold": 10.0}', 'V', 'OR', 'Phase B-C difference > 10V'),
(8, 3, 'measurements.voltage.phase_c', 'field_difference_gt', '{"field": "measurements.voltage.phase_a", "threshold": 10.0}', 'V', 'OR', 'Phase C-A difference > 10V'),

-- High Load with High Temperature
(9, 1, 'measurements.power.active', 'gt', '10000.0', 'W', 'AND', 'Active power > 10kW'),
(9, 2, 'measurements.temperature.value', 'gt', '70.0', '°C', 'AND', 'Temperature > 70°C');

-- TIME-BASED CONDITIONS
INSERT INTO rule_conditions (rule_id, condition_order, field_path, operator, threshold_value, threshold_unit, logical_operator, time_window, consecutive_count, description) VALUES
-- Sustained High Temperature (5 minutes)
(10, 1, 'measurements.temperature.value', 'duration_gt', '75.0', '°C', 'AND', 300, NULL, 'Temperature > 75°C for 5+ minutes'),

-- Consecutive Voltage Spikes (3 consecutive readings)
(11, 1, 'measurements.voltage.phase_a', 'consecutive_gt', '130.0', 'V', 'OR', NULL, 3, 'Phase A > 130V for 3+ consecutive readings'),
(11, 2, 'measurements.voltage.phase_b', 'consecutive_gt', '130.0', 'V', 'OR', NULL, 3, 'Phase B > 130V for 3+ consecutive readings'),
(11, 3, 'measurements.voltage.phase_c', 'consecutive_gt', '130.0', 'V', 'OR', NULL, 3, 'Phase C > 130V for 3+ consecutive readings');

-- COMMUNICATION CONDITIONS
INSERT INTO rule_conditions (rule_id, condition_order, field_path, operator, threshold_value, threshold_unit, logical_operator, time_window, description) VALUES
-- Communication Loss (no data for 2 minutes)
(12, 1, 'timestamp', 'time_since_last', '120', 'seconds', 'AND', 120, 'No data received for 2+ minutes'),

-- Data Quality Issues
(13, 1, 'measurements.voltage.phase_a', 'is_null', NULL, 'V', 'OR', NULL, 'Phase A voltage missing'),
(13, 2, 'measurements.temperature.value', 'is_null', NULL, '°C', 'OR', NULL, 'Temperature missing'),
(13, 3, 'data_quality.measurements_complete', 'eq', 'false', '', 'OR', NULL, 'Incomplete measurement data');

-- AGGREGATE CONDITIONS
INSERT INTO rule_conditions (rule_id, condition_order, field_path, operator, threshold_value, threshold_unit, logical_operator, time_window, description) VALUES
-- Average Power Too High (10-minute average)
(14, 1, 'measurements.power.active', 'avg_gt', '11000.0', 'W', 'AND', 600, '10-minute average power > 11kW'),

-- Peak Current Exceeded
(15, 1, 'measurements.current.phase_a', 'max_gt', '95.0', 'A', 'OR', 300, 'Phase A current peak > 95A in 5 minutes'),
(15, 2, 'measurements.current.phase_b', 'max_gt', '95.0', 'A', 'OR', 300, 'Phase B current peak > 95A in 5 minutes'),
(15, 3, 'measurements.current.phase_c', 'max_gt', '95.0', 'A', 'OR', 300, 'Phase C current peak > 95A in 5 minutes');

-- RULE ACTIONS
INSERT INTO rule_actions (rule_id, action_type, action_config, action_order) VALUES
-- Safety rules (high priority)
(1, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(2, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(3, 'publish_alarm', '{"topic": "iot.alarms", "severity": "critical", "auto_acknowledge": false}', 1),
(5, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(7, 'publish_alarm', '{"topic": "iot.alarms", "severity": "critical", "auto_acknowledge": false}', 1),
(9, 'publish_alarm', '{"topic": "iot.alarms", "severity": "critical", "auto_acknowledge": false}', 1),
(10, 'publish_alarm', '{"topic": "iot.alarms", "severity": "critical", "auto_acknowledge": false}', 1),
(11, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": false}', 1),
(15, 'publish_alarm', '{"topic": "iot.alarms", "severity": "critical", "auto_acknowledge": false}', 1),

-- Performance rules (medium priority)
(4, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(6, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(8, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),
(14, 'publish_alarm', '{"topic": "iot.alarms", "severity": "medium", "auto_acknowledge": true}', 1),

-- Communication rules
(12, 'publish_alarm', '{"topic": "iot.alarms", "severity": "high", "auto_acknowledge": true}', 1),
(13, 'publish_alarm', '{"topic": "iot.alarms", "severity": "low", "auto_acknowledge": true}', 1);
