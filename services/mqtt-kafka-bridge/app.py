#!/usr/bin/env python3
"""
MQTT to Kafka Bridge Service
Bridges MQTT topics to RedPanda/Kafka topics for IoT data ingestion
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any
import paho.mqtt.client as mqtt
from kafka import KafkaProducer
from kafka.errors import KafkaError
import structlog

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

class MQTTKafkaBridge:
    """Bridge service connecting MQTT topics to Kafka topics"""
    
    def __init__(self):
        # Configuration from environment variables
        self.mqtt_broker = os.getenv('MQTT_BROKER', 'mqtt-broker:1883')
        self.mqtt_topics = os.getenv('MQTT_TOPICS', 'iot/+/raw').split(',')
        self.kafka_brokers = os.getenv('KAFKA_BROKERS', 'redpanda:29092').split(',')
        self.kafka_topic = os.getenv('KAFKA_TOPIC', 'iot.raw')
        
        # MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        
        # Kafka producer
        self.kafka_producer = None
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_published': 0,
            'errors': 0,
            'last_message_time': None
        }
        
        logger.info("MQTT to Kafka Bridge initialized", 
                   mqtt_broker=self.mqtt_broker,
                   mqtt_topics=self.mqtt_topics,
                   kafka_brokers=self.kafka_brokers,
                   kafka_topic=self.kafka_topic)
    
    def setup_kafka_producer(self):
        """Initialize Kafka producer"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.kafka_brokers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Kafka producer", error=str(e))
            raise
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when MQTT client connects"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to configured topics
            for topic in self.mqtt_topics:
                client.subscribe(topic)
                logger.info("Subscribed to MQTT topic", topic=topic)
        else:
            logger.error("Failed to connect to MQTT broker", return_code=rc)
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback when MQTT client disconnects"""
        logger.warning("Disconnected from MQTT broker", return_code=rc)
        if rc != 0:
            logger.info("Attempting to reconnect...")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Callback when MQTT message is received"""
        try:
            self.stats['messages_received'] += 1
            self.stats['last_message_time'] = asyncio.get_event_loop().time()
            
            logger.info("MQTT message received", 
                       topic=msg.topic,
                       payload_size=len(msg.payload),
                       qos=msg.qos)
            
            # Parse MQTT payload
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning("Invalid JSON payload, treating as string", error=str(e))
                payload = {
                    "raw_payload": msg.payload.decode('utf-8', errors='ignore'),
                    "mqtt_topic": msg.topic,
                    "mqtt_qos": msg.qos,
                    "parse_error": str(e)
                }
            
            # Add MQTT metadata
            enriched_payload = {
                **payload,
                "_mqtt_info": {
                    "topic": msg.topic,
                    "qos": msg.qos,
                    "retain": msg.retain,
                    "timestamp": asyncio.get_event_loop().time()
                }
            }
            
            # Extract device ID from topic or payload for Kafka key
            device_id = self.extract_device_id(msg.topic, payload)
            
            # Publish to Kafka
            self.publish_to_kafka(device_id, enriched_payload)
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error("Error processing MQTT message", error=str(e))
    
    def extract_device_id(self, topic: str, payload: Dict[str, Any]) -> str:
        """Extract device ID from MQTT topic or payload"""
        # Try to get device_id from payload first
        if isinstance(payload, dict) and 'device_id' in payload:
            return str(payload['device_id'])
        
        # Extract from topic pattern (e.g., iot/device-001/raw -> device-001)
        topic_parts = topic.split('/')
        if len(topic_parts) >= 3:
            return topic_parts[1]
        
        # Fallback to topic hash
        return f"mqtt_{hash(topic) % 10000:04d}"
    
    def publish_to_kafka(self, key: str, value: Dict[str, Any]):
        """Publish message to Kafka topic"""
        if not self.kafka_producer:
            logger.error("Kafka producer not initialized")
            return
        
        try:
            # Send message to Kafka
            future = self.kafka_producer.send(
                self.kafka_topic,
                key=key,
                value=value
            )
            
            # Handle async result
            def on_send_success(record_metadata):
                self.stats['messages_published'] += 1
                logger.info("Message published to Kafka successfully",
                           topic=record_metadata.topic,
                           partition=record_metadata.partition,
                           offset=record_metadata.offset)
            
            def on_send_error(excp):
                self.stats['errors'] += 1
                logger.error("Failed to publish message to Kafka", error=str(excp))
            
            future.add_callback(on_send_success)
            future.add_errback(on_send_error)
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error("Error publishing to Kafka", error=str(e))
    
    def start(self):
        """Start the MQTT to Kafka bridge"""
        try:
            # Setup Kafka producer
            self.setup_kafka_producer()
            
            # Connect to MQTT broker
            logger.info("Connecting to MQTT broker", broker=self.mqtt_broker)
            self.mqtt_client.connect(self.mqtt_broker, 1883, 60)
            
            # Start MQTT client loop
            self.mqtt_client.loop_start()
            
            logger.info("MQTT to Kafka Bridge started successfully")
            
            # Keep the service running
            try:
                while True:
                    asyncio.sleep(1)
                    # Log statistics every 30 seconds
                    if self.stats['messages_received'] % 30 == 0 and self.stats['messages_received'] > 0:
                        logger.info("Bridge statistics", stats=self.stats)
            except KeyboardInterrupt:
                logger.info("Shutdown requested...")
                
        except Exception as e:
            logger.error("Failed to start bridge", error=str(e))
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up bridge resources...")
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        if self.kafka_producer:
            self.kafka_producer.flush()
            self.kafka_producer.close()
        
        logger.info("Bridge cleanup completed")

def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    
    bridge = MQTTKafkaBridge()
    bridge.start()

if __name__ == "__main__":
    main()
