#!/usr/bin/env python3
"""
IoT Data Enrichment Service
Enriches raw IoT messages with device metadata and context
Now integrates with Application Registry Service to include application registration information
"""

import json
import time
import structlog
import requests
from kafka import KafkaConsumer, KafkaProducer
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class IoTEnrichmentService:
    def __init__(self):
        self.logger = structlog.get_logger()
        self.device_registry = self.load_device_registry()
        self.app_registry_url = os.getenv('APP_REGISTRY_URL', 'http://appregistryservice:5000')
        self.setup_kafka_producer()
        self.setup_kafka_consumer()
        
    def load_device_registry(self) -> Dict[str, Any]:
        """Load device type registry from JSON file"""
        try:
            # Try multiple possible paths for the device registry
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'device-registry.json'),
                '/app/config/device-registry.json',
                'config/device-registry.json'
            ]
            
            registry = {}
            for registry_path in possible_paths:
                try:
                    if os.path.exists(registry_path):
                        with open(registry_path, 'r') as f:
                            registry = json.load(f)
                        self.logger.info("Device registry loaded successfully", 
                                       device_types=len(registry.get('device_types', {})),
                                       registry_path=registry_path)
                        return registry
                except Exception as e:
                    self.logger.warning(f"Failed to load registry from {registry_path}: {e}")
                    continue
            
            self.logger.error("Could not load device registry from any location")
            return {}
        except Exception as e:
            self.logger.error("Failed to load device registry", error=str(e))
            return {}
    
    def query_app_registry(self, device_type: str) -> List[Dict[str, Any]]:
        """Query the Application Registry Service for applications registered for a device type"""
        try:
            url = f"{self.app_registry_url}/api/applications/by-device-type/{device_type}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                applications = data.get('applications', [])
                self.logger.info(f"Found {len(applications)} applications for device type {device_type}")
                return applications
            else:
                self.logger.warning(f"App registry query failed with status {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to query app registry for {device_type}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error querying app registry: {e}")
            return []
    
    def setup_kafka_producer(self):
        """Setup Kafka producer for enriched messages"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=['redpanda:29092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            self.logger.info("Kafka producer setup successfully")
        except Exception as e:
            self.logger.error("Failed to setup Kafka producer", error=str(e))
            raise
    
    def setup_kafka_consumer(self):
        """Setup Kafka consumer for raw messages"""
        try:
            self.consumer = KafkaConsumer(
                'iot.raw',
                bootstrap_servers=['redpanda:29092'],
                auto_offset_reset='earliest',
                group_id='iot-enrichment-service',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None
            )
            self.logger.info("Kafka consumer setup successfully")
        except Exception as e:
            self.logger.error("Failed to setup Kafka consumer", error=str(e))
            raise
    
    def determine_device_type(self, message: Dict[str, Any]) -> Optional[str]:
        """Determine device type from message content"""
        try:
            # Look for device_type in message first (our hack for POC)
            if 'device_type' in message:
                return message['device_type']
            
            # Check if this is a trends message (new format)
            if 'trends' in message and isinstance(message['trends'], list):
                # This is a trends message, check for device type context
                if 'device_type' in message:
                    return message['device_type']
                # Could also infer from trends data structure if needed
                return 'smart_breaker'  # Default for trends from smart breaker
            
            # Infer from measurements structure (existing format)
            measurements = message.get('measurements', {})
            
            # Smart breaker detection
            if all(key in measurements for key in ['voltage', 'current', 'power', 'frequency']):
                if 'phase_a' in measurements.get('voltage', {}):
                    return 'smart_breaker'
            
            # Smart meter detection
            if 'energy' in measurements or 'demand' in measurements:
                return 'smart_meter'
            
            # Environmental sensor detection
            if all(key in measurements for key in ['temperature', 'humidity']):
                return 'environmental_sensor'
            
            # Default fallback
            return 'unknown'
            
        except Exception as e:
            self.logger.error("Error determining device type", error=str(e), message=message)
            return 'unknown'
    
    def enrich_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich raw message with device metadata and context"""
        try:
            device_type = self.determine_device_type(message)
            
            # Get device type metadata from registry
            device_metadata = self.device_registry.get('device_types', {}).get(device_type, {})
            
            # Query app registry for applications interested in this device type
            registered_applications = self.query_app_registry(device_type)
            
            # Create enriched message
            enriched_message = message.copy()
            
            # Add device type metadata
            if device_metadata:
                enriched_message['device_metadata'] = {
                    'device_type': device_type,
                    'device_type_name': device_metadata.get('name', 'Unknown Device Type'),
                    'device_type_description': device_metadata.get('description', ''),
                    'device_category': device_metadata.get('category', 'unknown'),
                    'capabilities': device_metadata.get('capabilities', []),
                    'data_format': device_metadata.get('data_format', 'json'),
                    'update_frequency': device_metadata.get('update_frequency', 'unknown'),
                    'retention_policy': device_metadata.get('retention_policy', 'unknown')
                }
                
                # Add measurement metadata if available
                if 'measurements' in device_metadata:
                    enriched_message['measurement_metadata'] = device_metadata['measurements']
            else:
                # Fallback for unknown device types
                enriched_message['device_metadata'] = {
                    'device_type': device_type,
                    'device_type_name': 'Unknown Device Type',
                    'device_type_description': 'Device type not found in registry',
                    'device_category': 'unknown',
                    'capabilities': [],
                    'data_format': 'json',
                    'update_frequency': 'unknown',
                    'retention_policy': 'unknown'
                }
            
            # Add application registration information
            enriched_message['application_registry'] = {
                'device_type': device_type,
                'registered_applications_count': len(registered_applications),
                'applications': registered_applications,
                'query_timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%f')
            }
            
            # Add enrichment processing information
            enriched_message['enrichment_info'] = {
                'enriched_at': time.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                'enrichment_service': 'iot-enrichment-service',
                'enrichment_version': '1.0.0',
                'device_type_detected': device_type,
                'app_registry_integration': True
            }
            
            # Add data quality indicators
            enriched_message['data_quality'] = {
                'timestamp_valid': 'timestamp' in message,
                'measurements_complete': self.validate_measurements(message, device_metadata),
                'enrichment_success': True
            }
            
            # Add message type classification
            if 'trends' in message and isinstance(message['trends'], list):
                enriched_message['_kafka_info'] = {
                    'message_type': 'trends',
                    'trends_count': len(message['trends']),
                    'has_aggregates': any('avg' in trend or 'min' in trend or 'max' in trend for trend in message['trends'])
                }
            elif 'measurements' in message:
                enriched_message['_kafka_info'] = {
                    'message_type': 'telemetry',
                    'measurements_count': len(message.get('measurements', {}))
                }
            else:
                enriched_message['_kafka_info'] = {
                    'message_type': 'unknown'
                }
            
            return enriched_message
            
        except Exception as e:
            self.logger.error("Error enriching message", error=str(e), message=message)
            # Return original message with error info
            message['enrichment_error'] = str(e)
            message['enrichment_info'] = {
                'enriched_at': time.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                'enrichment_service': 'iot-enrichment-service',
                'enrichment_version': '1.0.0',
                'error': True
            }
            return message
    
    def validate_measurements(self, message: Dict[str, Any], device_metadata: Dict[str, Any]) -> bool:
        """Validate that message contains expected measurements for device type"""
        try:
            # Handle trends messages differently
            if 'trends' in message and isinstance(message['trends'], list):
                # For trends, validate that we have at least some trend data
                if not message['trends']:
                    return False
                
                # Check that each trend has required fields
                for trend in message['trends']:
                    if not all(key in trend for key in ['c', 't']):  # channel and timestamp required
                        return False
                return True
            
            # Handle regular telemetry messages
            measurements = message.get('measurements', {})
            expected_measurements = device_metadata.get('measurements', {})
            
            if not expected_measurements:
                return True  # No validation possible
            
            # Check if required measurements are present
            required_keys = list(expected_measurements.keys())
            present_keys = list(measurements.keys())
            
            # Calculate completeness percentage
            present_count = sum(1 for key in required_keys if key in present_keys)
            completeness = present_count / len(required_keys) if required_keys else 1.0
            
            return completeness >= 0.7  # At least 70% of expected measurements present
            
        except Exception as e:
            self.logger.error("Error validating measurements", error=str(e))
            return False
    
    def process_messages(self):
        """Main message processing loop"""
        self.logger.info("Starting message processing loop")
        message_count = 0
        
        try:
            for message in self.consumer:
                try:
                    # Extract message data
                    raw_message = message.value
                    device_id = message.key or raw_message.get('device_id', 'unknown')
                    
                    self.logger.info("Processing message", 
                                   device_id=device_id,
                                   message_type=raw_message.get('event_type', 'unknown'))
                    
                    # Enrich the message
                    enriched_message = self.enrich_message(raw_message)
                    
                    # Send enriched message to Kafka
                    self.producer.send(
                        'iot.enriched',
                        key=device_id,
                        value=enriched_message
                    )
                    
                    message_count += 1
                    
                    # Log statistics every 10 messages
                    if message_count % 10 == 0:
                        self.logger.info("Message processing statistics", 
                                       total_messages=message_count,
                                       last_device_id=device_id)
                    
                except Exception as e:
                    self.logger.error("Error processing individual message", 
                                    error=str(e), 
                                    device_id=device_id if 'device_id' in locals() else 'unknown')
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("Shutting down enrichment service")
        except Exception as e:
            self.logger.error("Fatal error in message processing", error=str(e))
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'consumer'):
                self.consumer.close()
            if hasattr(self, 'producer'):
                self.producer.close()
            self.logger.info("Enrichment service shutdown complete")
        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))

def main():
    """Main entry point"""
    print("🚀 Starting IoT Enrichment Service...")
    
    try:
        service = IoTEnrichmentService()
        print("✅ Service initialized successfully")
        print("📡 Starting message processing...")
        service.process_messages()
    except Exception as e:
        print(f"❌ Failed to start enrichment service: {e}")
        exit(1)

if __name__ == "__main__":
    main()
