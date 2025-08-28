#!/usr/bin/env python3
"""
RedPanda to TimescaleDB Connector Service
Consumes IoT data from RedPanda topics and stores it in TimescaleDB for time-series analysis
"""

import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class TimescaleDBConnector:
    """Connector for storing IoT data in TimescaleDB"""
    
    def __init__(self):
        # Database configuration
        self.db_config = {
            'host': os.getenv('TIMESCALEDB_HOST', 'timescaledb'),
            'port': int(os.getenv('TIMESCALEDB_PORT', '5432')),
            'database': os.getenv('TIMESCALEDB_DB', 'iot_cloud'),
            'user': os.getenv('TIMESCALEDB_USER', 'iot_user'),
            'password': os.getenv('TIMESCALEDB_PASSWORD', 'iot_password')
        }
        
        # Connection pool
        self.connection_pool = None
        
        # Statistics
        self.stats = {
            'messages_processed': 0,
            'raw_data_stored': 0,
            'enriched_data_stored': 0,
            'smart_breaker_data_stored': 0,
            'errors': 0,
            'last_message_time': None
        }
        
        logger.info("TimescaleDB Connector initialized", db_host=self.db_config['host'])
    
    def setup_connection_pool(self):
        """Initialize database connection pool"""
        try:
            self.connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **self.db_config
            )
            logger.info("Database connection pool established")
        except Exception as e:
            logger.error("Failed to create connection pool", error=str(e))
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        if self.connection_pool:
            return self.connection_pool.getconn()
        return None
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self.connection_pool and conn:
            self.connection_pool.putconn(conn)
    
    def store_raw_data(self, message_data: Dict[str, Any]) -> bool:
        """Store raw IoT data in TimescaleDB"""
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("No database connection available")
                return False
            
            cursor = conn.cursor()
            
            # Extract data from message
            timestamp = message_data.get('timestamp', datetime.now(timezone.utc))
            device_id = message_data.get('device_id', 'unknown')
            topic = message_data.get('topic', 'unknown')
            payload = message_data.get('payload', {})
            message_id = message_data.get('message_id', None)
            
            # Insert into raw data table
            cursor.execute("""
                INSERT INTO iot_raw_data (time, device_id, topic, payload, message_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (timestamp, device_id, topic, json.dumps(payload), message_id))
            
            conn.commit()
            cursor.close()
            self.return_connection(conn)
            
            self.stats['raw_data_stored'] += 1
            logger.debug("Raw data stored successfully", device_id=device_id, topic=topic)
            return True
            
        except Exception as e:
            logger.error("Failed to store raw data", error=str(e), device_id=device_id)
            self.stats['errors'] += 1
            if conn:
                conn.rollback()
                self.return_connection(conn)
            return False
    
    def store_enriched_data(self, message_data: Dict[str, Any]) -> bool:
        """Store enriched IoT data in TimescaleDB"""
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("No database connection available")
                return False
            
            cursor = conn.cursor()
            
            # Extract data from message
            timestamp = message_data.get('timestamp', datetime.now(timezone.utc))
            device_id = message_data.get('device_id', 'unknown')
            device_type = message_data.get('device_type')
            device_name = message_data.get('device_name')
            topic = message_data.get('topic', 'unknown')
            measurements = message_data.get('measurements', {})
            metadata = message_data.get('metadata', {})
            message_id = message_data.get('message_id', None)
            
            # Insert into enriched data table
            cursor.execute("""
                INSERT INTO iot_enriched_data 
                (time, device_id, device_type, device_name, topic, measurements, metadata, message_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (timestamp, device_id, device_type, device_name, topic, 
                  json.dumps(measurements), json.dumps(metadata), message_id))
            
            # Update device metadata if available
            if device_type:
                cursor.execute("""
                    SELECT update_device_metadata(%s, %s, %s, %s, %s, %s, %s, %s)
                """, (device_id, device_type, device_name, None, None, None, 
                      json.dumps(metadata.get('capabilities', {})), metadata.get('fdi_package_id')))
            
            conn.commit()
            cursor.close()
            self.return_connection(conn)
            
            self.stats['enriched_data_stored'] += 1
            logger.debug("Enriched data stored successfully", device_id=device_id, device_type=device_type)
            return True
            
        except Exception as e:
            logger.error("Failed to store enriched data", error=str(e), device_id=device_id)
            self.stats['errors'] += 1
            if conn:
                conn.rollback()
                self.return_connection(conn)
            return False
    
    def store_smart_breaker_data(self, message_data: Dict[str, Any]) -> bool:
        """Store smart breaker specific data in TimescaleDB"""
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("No database connection available")
                return False
            
            cursor = conn.cursor()
            
            # Extract measurements
            measurements = message_data.get('measurements', {})
            timestamp = message_data.get('timestamp', datetime.now(timezone.utc))
            device_id = message_data.get('device_id', 'unknown')
            
            # Extract specific smart breaker metrics
            voltage = measurements.get('voltage', {})
            current = measurements.get('current', {})
            
            # Insert into smart breaker table
            cursor.execute("""
                INSERT INTO smart_breaker_data (
                    time, device_id, voltage_phase_a, voltage_phase_b, voltage_phase_c,
                    current_phase_a, current_phase_b, current_phase_c, power_factor,
                    frequency, temperature, status, alarms, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                timestamp, device_id,
                voltage.get('phase_a'), voltage.get('phase_b'), voltage.get('phase_c'),
                current.get('phase_a'), current.get('phase_b'), current.get('phase_c'),
                measurements.get('power_factor'),
                measurements.get('frequency'),
                measurements.get('temperature'),
                measurements.get('status', 'normal'),
                json.dumps(measurements.get('alarms', [])),
                json.dumps(message_data.get('metadata', {}))
            ))
            
            conn.commit()
            cursor.close()
            self.return_connection(conn)
            
            self.stats['smart_breaker_data_stored'] += 1
            logger.debug("Smart breaker data stored successfully", device_id=device_id)
            return True
            
        except Exception as e:
            logger.error("Failed to store smart breaker data", error=str(e), device_id=device_id)
            self.stats['errors'] += 1
            if conn:
                conn.rollback()
                self.return_connection(conn)
            return False
    
    def close(self):
        """Close the connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

class RedPandaConnector:
    """Main connector service consuming from RedPanda and storing in TimescaleDB"""
    
    def __init__(self):
        # RedPanda configuration
        self.kafka_brokers = os.getenv('REDPANDA_BROKERS', 'redpanda:29092').split(',')
        self.raw_topic = os.getenv('RAW_TOPIC', 'iot.raw')
        self.enriched_topic = os.getenv('ENRICHED_TOPIC', 'iot.enriched')
        self.smart_breaker_topic = os.getenv('SMART_BREAKER_TOPIC', 'iot.smart_breaker.enriched')
        
        # Initialize TimescaleDB connector
        self.timescale_connector = TimescaleDBConnector()
        
        # Kafka consumers
        self.consumers = {}
        
        logger.info("RedPanda Connector initialized", 
                   kafka_brokers=self.kafka_brokers,
                   topics=[self.raw_topic, self.enriched_topic, self.smart_breaker_topic])
    
    def setup_consumers(self):
        """Initialize Kafka consumers for different topics"""
        try:
            # Consumer for raw data
            self.consumers['raw'] = KafkaConsumer(
                self.raw_topic,
                bootstrap_servers=self.kafka_brokers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='timescale-raw-consumer',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None
            )
            
            # Consumer for enriched data
            self.consumers['enriched'] = KafkaConsumer(
                self.enriched_topic,
                bootstrap_servers=self.kafka_brokers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='timescale-enriched-consumer',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None
            )
            
            # Consumer for smart breaker data
            self.consumers['smart_breaker'] = KafkaConsumer(
                self.smart_breaker_topic,
                bootstrap_servers=self.kafka_brokers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='timescale-smart-breaker-consumer',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None
            )
            
            logger.info("Kafka consumers initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Kafka consumers", error=str(e))
            raise
    
    def process_raw_messages(self):
        """Process raw IoT messages"""
        consumer = self.consumers.get('raw')
        if not consumer:
            return
        
        try:
            for message in consumer:
                try:
                    # Extract message data
                    message_data = {
                        'timestamp': datetime.fromtimestamp(message.timestamp / 1000, timezone.utc),
                        'device_id': message.value.get('device_id', 'unknown'),
                        'topic': message.topic,
                        'payload': message.value,
                        'message_id': message.value.get('message_id')
                    }
                    
                    # Store in TimescaleDB
                    if self.timescale_connector.store_raw_data(message_data):
                        self.timescale_connector.stats['messages_processed'] += 1
                        self.timescale_connector.stats['last_message_time'] = datetime.now(timezone.utc)
                    
                except Exception as e:
                    logger.error("Error processing raw message", error=str(e))
                    self.timescale_connector.stats['errors'] += 1
                    
        except Exception as e:
            logger.error("Error in raw message consumer", error=str(e))
    
    def process_enriched_messages(self):
        """Process enriched IoT messages"""
        consumer = self.consumers.get('enriched')
        if not consumer:
            return
        
        try:
            for message in consumer:
                try:
                    # Extract message data
                    message_data = {
                        'timestamp': datetime.fromtimestamp(message.timestamp / 1000, timezone.utc),
                        'device_id': message.value.get('device_id', 'unknown'),
                        'device_type': message.value.get('device_type'),
                        'device_name': message.value.get('device_name'),
                        'topic': message.topic,
                        'measurements': message.value.get('measurements', {}),
                        'metadata': message.value.get('metadata', {}),
                        'message_id': message.value.get('message_id')
                    }
                    
                    # Store in TimescaleDB
                    if self.timescale_connector.store_enriched_data(message_data):
                        self.timescale_connector.stats['messages_processed'] += 1
                        self.timescale_connector.stats['last_message_time'] = datetime.now(timezone.utc)
                    
                except Exception as e:
                    logger.error("Error processing enriched message", error=str(e))
                    self.timescale_connector.stats['errors'] += 1
                    
        except Exception as e:
            logger.error("Error in enriched message consumer", error=str(e))
    
    def process_smart_breaker_messages(self):
        """Process smart breaker specific messages"""
        consumer = self.consumers.get('smart_breaker')
        if not consumer:
            return
        
        try:
            for message in consumer:
                try:
                    # Extract message data
                    message_data = {
                        'timestamp': datetime.fromtimestamp(message.timestamp / 1000, timezone.utc),
                        'device_id': message.value.get('device_id', 'unknown'),
                        'device_type': message.value.get('device_type'),
                        'device_name': message.value.get('device_name'),
                        'topic': message.topic,
                        'measurements': message.value.get('measurements', {}),
                        'metadata': message.value.get('metadata', {}),
                        'message_id': message.value.get('message_id')
                    }
                    
                    # Store in TimescaleDB
                    if self.timescale_connector.store_smart_breaker_data(message_data):
                        self.timescale_connector.stats['messages_processed'] += 1
                        self.timescale_connector.stats['last_message_time'] = datetime.now(timezone.utc)
                    
                except Exception as e:
                    logger.error("Error processing smart breaker message", error=str(e))
                    self.timescale_connector.stats['errors'] += 1
                    
        except Exception as e:
            logger.error("Error in smart breaker message consumer", error=str(e))
    
    def start(self):
        """Start the connector service"""
        try:
            logger.info("Starting RedPanda to TimescaleDB connector...")
            
            # Setup database connection
            self.timescale_connector.setup_connection_pool()
            
            # Setup Kafka consumers
            self.setup_consumers()
            
            logger.info("Connector started successfully. Processing messages...")
            
            # Start processing messages (this will block)
            import threading
            
            # Start consumers in separate threads
            raw_thread = threading.Thread(target=self.process_raw_messages, daemon=True)
            enriched_thread = threading.Thread(target=self.process_enriched_messages, daemon=True)
            smart_breaker_thread = threading.Thread(target=self.process_smart_breaker_messages, daemon=True)
            
            raw_thread.start()
            enriched_thread.start()
            smart_breaker_thread.start()
            
            # Keep main thread alive and log stats periodically
            while True:
                time.sleep(60)  # Log stats every minute
                stats = self.timescale_connector.stats
                logger.info("Connector statistics", 
                           messages_processed=stats['messages_processed'],
                           raw_stored=stats['raw_data_stored'],
                           enriched_stored=stats['enriched_data_stored'],
                           smart_breaker_stored=stats['smart_breaker_data_stored'],
                           errors=stats['errors'])
                
        except KeyboardInterrupt:
            logger.info("Shutting down connector...")
        except Exception as e:
            logger.error("Fatal error in connector", error=str(e))
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Close consumers
            for consumer in self.consumers.values():
                if consumer:
                    consumer.close()
            
            # Close database connections
            self.timescale_connector.close()
            
            logger.info("Connector cleanup completed")
            
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))

if __name__ == "__main__":
    connector = RedPandaConnector()
    connector.start()
