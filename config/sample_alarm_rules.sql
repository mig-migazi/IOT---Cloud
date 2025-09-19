-- Sample Alarm Rules for Smart Breaker Simulator
-- Based on actual telemetry ranges from smart_breaker_simulator_mqtt.py

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
