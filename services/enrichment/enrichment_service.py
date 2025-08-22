#!/usr/bin/env python3
"""
IoT Data Enrichment Service
Enriches raw IoT messages with device metadata and context
Now integrates with FDI Package Manager for device definitions and Application Registry Service
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
        self.fdi_package_manager_url = os.getenv('FDI_PACKAGE_MANAGER_URL', 'http://fdi-package-manager:5000')
        self.app_registry_url = os.getenv('APP_REGISTRY_URL', 'http://appregistryservice:5000')
        self.fallback_device_registry = self.load_fallback_device_registry()
        self.setup_kafka_producer()
        self.setup_kafka_consumer()
        
    def load_fallback_device_registry(self) -> Dict[str, Any]:
        """Load fallback device type registry from JSON file (for backward compatibility)"""
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
                        self.logger.info("Fallback device registry loaded successfully", 
                                       device_types=len(registry.get('device_types', {})),
                                       registry_path=registry_path)
                        return registry
                except Exception as e:
                    self.logger.warning(f"Failed to load fallback registry from {registry_path}: {e}")
                    continue
            
            self.logger.warning("Could not load fallback device registry from any location")
            return {}
        except Exception as e:
            self.logger.error("Failed to load fallback device registry", error=str(e))
            return {}
    
    def get_fdi_package(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Get FDI package for a device type from the FDI Package Manager"""
        try:
            url = f"{self.fdi_package_manager_url}/api/fdi-package/{device_type}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    package = data.get('package', {})
                    self.logger.info(f"Retrieved FDI package for device type {device_type}", 
                                   package_id=package.get('package_id'))
                    return package
                else:
                    self.logger.warning(f"FDI package query failed: {data.get('error')}")
                    return None
            else:
                self.logger.warning(f"FDI package query failed with status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to query FDI package manager for {device_type}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error querying FDI package manager: {e}")
            return None
    
    def get_device_metadata_from_fdi(self, fdi_package: Dict[str, Any]) -> Dict[str, Any]:
        """Extract device metadata from FDI package"""
        try:
            device_type_data = fdi_package.get('device_type', {})
            
            metadata = {
                'device_type': device_type_data.get('device_type', 'unknown'),
                'device_type_name': device_type_data.get('name', 'Unknown Device Type'),
                'device_type_description': device_type_data.get('description', ''),
                'device_category': device_type_data.get('category', 'unknown'),
                'capabilities': device_type_data.get('capabilities', []),
                'data_format': device_type_data.get('data_format', 'json'),
                'update_frequency': device_type_data.get('update_frequency', 'unknown'),
                'retention_policy': device_type_data.get('retention_policy', 'unknown'),
                'manufacturer': device_type_data.get('manufacturer', 'unknown'),
                'model': device_type_data.get('model', 'unknown'),
                'version': device_type_data.get('version', 'unknown')
            }
            
            # Add measurement metadata if available
            if 'parameters' in device_type_data:
                metadata['measurement_metadata'] = self._extract_measurement_metadata_from_fdi(device_type_data['parameters'])
            
            return metadata
            
        except Exception as e:
            self.logger.error("Error extracting device metadata from FDI package", error=str(e))
            return {}
    
    def _extract_measurement_metadata_from_fdi(self, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract measurement metadata from FDI package parameters"""
        try:
            measurement_metadata = {}
            
            for param in parameters:
                param_name = param.get('name', '')
                if param_name:
                    measurement_metadata[param_name] = {
                        'unit': param.get('unit'),
                        'description': param.get('description', ''),
                        'min_value': param.get('min_value'),
                        'max_value': param.get('max_value'),
                        'data_type': param.get('data_type', 'unknown'),
                        'category': param.get('category', 'measurement'),
                        'access_level': param.get('access_level', 'read_write')
                    }
            
            return measurement_metadata
            
        except Exception as e:
            self.logger.error("Error extracting measurement metadata from FDI package", error=str(e))
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
                auto_offset_reset='latest',  # Start from latest to avoid replaying old messages
                group_id='iot-enrichment-service',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None
            )
            self.logger.info("Kafka consumer setup successfully")
        except Exception as e:
            self.logger.error("Failed to setup Kafka consumer", error=str(e))
            raise
    
    def determine_device_type(self, message: Dict[str, Any]) -> str:
        """Determine device type from message content"""
        try:
            # Try to get device type from message
            device_type = message.get('device_type')
            if device_type:
                return device_type
            
            # Try to infer from measurements or other fields
            if 'measurements' in message:
                measurements = message['measurements']
                
                # Check for smart breaker specific measurements
                if any(key in measurements for key in ['voltage', 'current', 'power', 'breaker_status']):
                    return 'smart_breaker'
                
                # Check for smart meter specific measurements
                if any(key in measurements for key in ['energy', 'demand', 'power_factor']):
                    return 'smart_meter'
                
                # Check for environmental sensor specific measurements
                if any(key in measurements for key in ['temperature', 'humidity', 'pressure']):
                    return 'environmental_sensor'
            
            # Default fallback
            return 'unknown'
            
        except Exception as e:
            self.logger.error("Error determining device type", error=str(e))
            return 'unknown'
    
    def enrich_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich raw message with device metadata and context"""
        try:
            device_type = self.determine_device_type(message)
            
            # Try to get FDI package first
            fdi_package = self.get_fdi_package(device_type)
            
            if fdi_package:
                # Use FDI package for device metadata
                device_metadata = self.get_device_metadata_from_fdi(fdi_package)
                self.logger.info(f"Using FDI package for device type {device_type}", 
                               package_id=fdi_package.get('package_id'))
            else:
                # Fallback to static device registry
                device_metadata = self.fallback_device_registry.get('device_types', {}).get(device_type, {})
                if device_metadata:
                    self.logger.info(f"Using fallback device registry for device type {device_type}")
                else:
                    # Create minimal metadata for unknown device types
                    device_metadata = {
                        'device_type': device_type,
                        'device_type_name': 'Unknown Device Type',
                        'device_type_description': 'Device type not found in FDI packages or registry',
                        'device_category': 'unknown',
                        'capabilities': [],
                        'data_format': 'json',
                        'update_frequency': 'unknown',
                        'retention_policy': 'unknown'
                    }
                    self.logger.warning(f"Device type {device_type} not found in FDI packages or fallback registry")
            
            # Query app registry for applications interested in this device type
            try:
                registered_applications = self.query_app_registry(device_type)
            except Exception as e:
                self.logger.warning("App registry query failed, using empty list", error=str(e))
                registered_applications = []
            
            # Create enriched message
            enriched_message = message.copy()
            
            # Add device type metadata
            enriched_message['device_metadata'] = device_metadata
                
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
                'enrichment_version': '2.0.0',
                'device_type_detected': device_type,
                'fdi_package_used': fdi_package is not None,
                'app_registry_integration': True
            }
            
            # Add data quality indicators
            enriched_message['data_quality'] = {
                'timestamp_valid': 'timestamp' in message,
                'measurements_complete': self.validate_measurements(message, device_metadata),
                'enrichment_success': True,
                'fdi_package_available': fdi_package is not None
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
                'enrichment_version': '2.0.0',
                'error': True
            }
            return message
    
    def validate_measurements(self, message: Dict[str, Any], device_metadata: Dict[str, Any]) -> bool:
        """Validate that message contains expected measurements for device type"""
        try:
            if 'measurements' not in message:
                return False
            
            measurements = message['measurements']
            measurement_metadata = device_metadata.get('measurement_metadata', {})
            
            if not measurement_metadata:
                # If no measurement metadata available, consider it valid
                return True
            
            # Check for required measurements
            required_keys = list(measurement_metadata.keys())
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
        self.logger.info("Starting message processing loop with FDI package manager integration")
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
                    
                    # Send enriched message to general topic
                    self.producer.send(
                        'iot.enriched',
                        key=device_id,
                        value=enriched_message
                    )
                    
                    # Also send to device-type specific topic for application isolation
                    device_type = enriched_message.get('device_metadata', {}).get('device_type', 'unknown')
                    device_topic = f'iot.{device_type}.enriched'
                    
                    self.producer.send(
                        device_topic,
                        key=device_id,
                        value=enriched_message
                    )
                    
                    self.logger.info("Message routed to topics", 
                                   general_topic='iot.enriched',
                                   device_topic=device_topic,
                                   device_type=device_type)
                    
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
    print("🚀 Starting IoT Enrichment Service with FDI Package Manager Integration...")
    
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
