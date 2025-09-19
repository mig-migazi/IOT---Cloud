#!/usr/bin/env python3
"""
Simple Alarm Processor Service
Reads from iot.enriched topic and evaluates alarm rules
"""

import json
import os
import time
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from jsonpath_ng import jsonpath, parse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'redpanda:29092')
DB_HOST = os.getenv('DB_HOST', 'timescaledb')
DB_NAME = os.getenv('DB_NAME', 'iot_cloud')
DB_USER = os.getenv('DB_USER', 'iot_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'iot_password')
RULE_CACHE_TTL_SECONDS = int(os.getenv('RULE_CACHE_TTL_SECONDS', '30'))

class AlarmProcessor:
    def __init__(self):
        self.db_connection = None
        self.rules_cache = {}
        self.last_cache_update = 0
        self.kafka_consumer = None
        self.kafka_producer = None
        
    def connect_database(self):
        """Connect to TimescaleDB"""
        try:
            self.db_connection = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=5432
            )
            logger.info("Connected to TimescaleDB")
        except Exception as e:
            logger.error(f"Failed to connect to TimescaleDB: {e}")
            raise
    
    def connect_kafka(self):
        """Connect to Kafka/Redpanda"""
        try:
            self.kafka_consumer = KafkaConsumer(
                'iot.enriched',
                bootstrap_servers=[KAFKA_BROKER],
                group_id='alarm-processor-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest'
            )
            
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            
            logger.info("Connected to Kafka/Redpanda")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def load_rules(self):
        """Load alarm rules from database"""
        if not self.db_connection:
            self.connect_database()
            
        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Load rules with conditions
                cursor.execute("""
                    SELECT 
                        r.id, r.rule_name, r.device_type_id, r.category_id, 
                        r.priority, r.description, r.is_active,
                        c.field_path, c.operator, c.threshold_value, 
                        c.threshold_unit, c.logical_operator
                    FROM alarm_rules r
                    LEFT JOIN rule_conditions c ON r.id = c.rule_id
                    WHERE r.is_active = true
                    ORDER BY r.id, c.condition_order
                """)
                
                rules = {}
                for row in cursor.fetchall():
                    rule_id = row['id']
                    if rule_id not in rules:
                        rules[rule_id] = {
                            'id': rule_id,
                            'name': row['rule_name'],
                            'device_type_id': row['device_type_id'],
                            'priority': row['priority'],
                            'description': row['description'],
                            'conditions': []
                        }
                    
                    if row['field_path']:
                        rules[rule_id]['conditions'].append({
                            'field_path': row['field_path'],
                            'operator': row['operator'],
                            'threshold_value': row['threshold_value'],
                            'threshold_unit': row['threshold_unit'],
                            'logical_operator': row['logical_operator']
                        })
                
                self.rules_cache = rules
                self.last_cache_update = time.time()
                logger.info(f"Loaded {len(rules)} alarm rules")
                
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            raise
    
    def get_rules_for_device_type(self, device_type_id):
        """Get rules for a specific device type"""
        if time.time() - self.last_cache_update > RULE_CACHE_TTL_SECONDS:
            self.load_rules()
        
        return [rule for rule in self.rules_cache.values() 
                if rule['device_type_id'] == device_type_id]
    
    def evaluate_message(self, message_data):
        """Evaluate a message against alarm rules"""
        device_type_id = message_data.get('device_type_id', 1)  # Default to smart_breaker
        rules = self.get_rules_for_device_type(device_type_id)
        
        triggered_alarms = []
        
        for rule in rules:
            if self._evaluate_rule(message_data, rule):
                alarm = self._create_alarm(message_data, rule)
                triggered_alarms.append(alarm)
        
        return triggered_alarms
    
    def _evaluate_rule(self, message_data, rule):
        """Evaluate a single rule against message data"""
        conditions = rule.get('conditions', [])
        if not conditions:
            return False
        
        # Simple AND logic for now
        for condition in conditions:
            if not self._evaluate_condition(message_data, condition):
                return False
        
        return True
    
    def _evaluate_condition(self, message_data, condition):
        """Evaluate a single condition"""
        field_path = condition['field_path']
        operator = condition['operator']
        threshold_value = condition['threshold_value']
        
        try:
            # Extract value using JSON path
            jsonpath_expr = parse(field_path)
            matches = jsonpath_expr.find(message_data)
            
            if not matches:
                return False
            
            value = matches[0].value
            
            # Convert threshold to appropriate type
            if isinstance(threshold_value, str):
                try:
                    threshold_value = float(threshold_value)
                except ValueError:
                    pass
            
            # Apply operator
            if operator == 'gt':
                return float(value) > float(threshold_value)
            elif operator == 'lt':
                return float(value) < float(threshold_value)
            elif operator == 'eq':
                return value == threshold_value
            elif operator == 'gte':
                return float(value) >= float(threshold_value)
            elif operator == 'lte':
                return float(value) <= float(threshold_value)
            elif operator == 'out_of_range':
                if isinstance(threshold_value, dict):
                    min_val = float(threshold_value.get('min', 0))
                    max_val = float(threshold_value.get('max', 100))
                    return float(value) < min_val or float(value) > max_val
            elif operator == 'in_range':
                if isinstance(threshold_value, dict):
                    min_val = float(threshold_value.get('min', 0))
                    max_val = float(threshold_value.get('max', 100))
                    return min_val <= float(value) <= max_val
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition {field_path} {operator} {threshold_value}: {e}")
            return False
    
    def _create_alarm(self, message_data, rule):
        """Create an alarm object"""
        return {
            'alarm_type': rule['name'],
            'device_id': message_data.get('device_id'),
            'device_type': message_data.get('device_type'),
            'severity': self._get_severity_level(rule['priority']),
            'status': 'active',
            'triggered_at': datetime.utcnow().isoformat() + 'Z',
            'alarm_message': rule['description'],
            'alarm_data': message_data,
            'rule_id': rule['id']
        }
    
    def _get_severity_level(self, priority):
        """Convert priority to severity level"""
        if priority == 1:
            return 'critical'
        elif priority == 2:
            return 'high'
        elif priority == 3:
            return 'medium'
        else:
            return 'low'
    
    def store_alarm_in_db(self, alarm: Dict[str, Any]):
        """Store alarm in TimescaleDB"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alarm_instances (
                        alarm_type, device_id, device_type_id, severity, status,
                        triggered_at, alarm_message, alarm_data, rule_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    alarm['alarm_type'],
                    alarm['device_id'],
                    alarm.get('device_type_id', 1),  # Default to smart_breaker
                    alarm['severity'],
                    alarm['status'],
                    alarm['triggered_at'],
                    alarm['alarm_message'],
                    json.dumps(alarm['alarm_data']),
                    alarm['rule_id']
                ))
                self.db_connection.commit()
                logger.debug(f"Stored alarm {alarm['alarm_type']} in database")
        except Exception as e:
            logger.error(f"Failed to store alarm in database: {e}")
            # Don't raise - we still want to publish to Kafka
    
    def process_messages(self):
        """Main processing loop"""
        logger.info("Starting alarm processor...")
        
        # Connect to services
        self.connect_database()
        self.connect_kafka()
        self.load_rules()
        
        logger.info("Alarm processor ready, listening for messages...")
        
        try:
            for message in self.kafka_consumer:
                try:
                    message_data = message.value
                    logger.debug(f"Processing message: {message_data.get('device_id', 'unknown')}")
                    
                    # Evaluate message against rules
                    triggered_alarms = self.evaluate_message(message_data)
                    
                    # Publish alarms to Kafka topic
                    for alarm in triggered_alarms:
                        logger.info(f"ALARM TRIGGERED: {alarm['alarm_type']} for {alarm['device_id']}")
                        self.kafka_producer.send('iot.alarms', value=alarm)
                    
                    # Flush producer to ensure messages are sent
                    self.kafka_producer.flush()
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Shutting down alarm processor...")
        finally:
            if self.kafka_consumer:
                self.kafka_consumer.close()
            if self.kafka_producer:
                self.kafka_producer.close()
            if self.db_connection:
                self.db_connection.close()

def main():
    """Main entry point"""
    processor = AlarmProcessor()
    processor.process_messages()

if __name__ == "__main__":
    main()