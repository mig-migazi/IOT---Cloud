#!/usr/bin/env python3
"""
IoT Cloud Web Dashboard
Real-time visualization of IoT data flow through RedPanda
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from flask import Flask, render_template, jsonify, request, make_response
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

app = Flask(__name__)

# Configuration
KAFKA_BROKERS = os.getenv('REDPANDA_BROKERS', 'redpanda:29092')
RAW_TOPIC = os.getenv('RAW_TOPIC', 'iot.raw')
ENRICHED_TOPIC = os.getenv('ENRICHED_TOPIC', 'iot.enriched')

# Get local timezone from system (no more hardcoded EDT!)
LOCAL_TIMEZONE_OFFSET = int(os.getenv('LOCAL_TIMEZONE_OFFSET', '0'))  # Default to UTC, let system handle conversion

def convert_to_local_time(timestamp_str: str) -> str:
    """Convert UTC timestamp string to local timezone"""
    try:
        # Parse the timestamp (handle both ISO format and other formats)
        if timestamp_str.endswith('Z'):
            # UTC format
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif '+' in timestamp_str:
            # Already has timezone info
            dt = datetime.fromisoformat(timestamp_str)
        else:
            # Assume UTC if no timezone info
            dt = datetime.fromisoformat(timestamp_str + '+00:00')
        
        # Convert to local timezone (UTC+0 for now, but properly formatted)
        local_dt = dt.replace(tzinfo=timezone.utc)
        
        # Format as readable string
        return local_dt.strftime('%Y-%m-%d %I:%M:%S %p')
    except Exception as e:
        print(f"Error converting timestamp {timestamp_str}: {e}")
        return timestamp_str  # Return original if conversion fails

# In-memory storage for recent messages (last 100)
recent_raw_messages = []
recent_enriched_messages = []
message_stats = {
    'total_raw_messages': 0,
    'total_enriched_messages': 0,
    'last_raw_message_time': None,
    'last_enriched_message_time': None,
    'devices_seen': set(),
    'message_types': {},
    'kafka_connected': False
}

class IoTDashboard:
    """IoT Dashboard with Kafka integration"""
    
    def __init__(self, kafka_brokers: str, raw_topic: str, enriched_topic: str):
        self.kafka_brokers = kafka_brokers
        self.raw_topic = raw_topic
        self.enriched_topic = enriched_topic
        self.raw_consumer = None
        self.enriched_consumer = None
        self.running = False
        self.consumer_thread = None
        
    def setup_consumers(self):
        """Setup Kafka consumers for both raw and enriched data"""
        try:
            # Raw data consumer
            self.raw_consumer = KafkaConsumer(
                self.raw_topic,
                bootstrap_servers=self.kafka_brokers,
                group_id='iot-dashboard-raw-clean-' + str(int(time.time())),
                auto_offset_reset='latest',  # Start from latest to avoid replaying old messages
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None
            )
            print(f"Raw consumer created for topic: {self.raw_topic}")
            
            # Enriched data consumer
            self.enriched_consumer = KafkaConsumer(
                self.enriched_topic,
                bootstrap_servers=self.kafka_brokers,
                group_id='iot-dashboard-enriched-clean-' + str(int(time.time())),
                auto_offset_reset='latest',  # Start from latest to avoid replaying old messages
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None
            )
            print(f"Enriched consumer created for topic: {self.enriched_topic}")
            
            print(f"Dashboard connected to {self.raw_topic} and {self.enriched_topic}")
            message_stats['kafka_connected'] = True
            return True
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}")
            message_stats['kafka_connected'] = False
            return False
    
    def start_consuming(self):
        """Start background consumer thread"""
        if self.running:
            return
        
        self.running = True
        self.consumer_thread = threading.Thread(target=self._consume_messages, daemon=True)
        self.consumer_thread.start()
        print("Started background message consumption")
    
    def stop_consuming(self):
        """Stop background consumer thread"""
        self.running = False
        if self.consumer_thread:
            self.consumer_thread.join(timeout=1)
    
    def _consume_messages(self):
        """Background thread to continuously consume messages"""
        print("Starting message consumption loop")
        raw_errors = 0
        enriched_errors = 0
        
        while self.running:
            try:
                # Consume raw messages
                if self.raw_consumer:
                    try:
                        raw_batch = self.raw_consumer.poll(timeout_ms=1000, max_records=10)
                        if raw_batch:
                            print(f"Raw batch: {len(raw_batch)} partitions, records: {sum(len(records) for records in raw_batch.values())}")
                        for tp, records in raw_batch.items():
                            for record in records:
                                try:
                                    message_data = record.value
                                    message_data['_kafka_info'] = {
                                        'topic': record.topic,
                                        'partition': record.partition,
                                        'offset': record.offset,
                                        'timestamp': record.timestamp,
                                        'message_type': 'raw'
                                    }
                                    self._add_raw_message(message_data)
                                except Exception as e:
                                    print(f"Error processing raw message: {e}")
                                    raw_errors += 1
                    except Exception as e:
                        print(f"Error polling raw consumer: {e}")
                        raw_errors += 1
                        if raw_errors > 5:
                            print("Too many raw consumer errors, reconnecting...")
                            self.setup_consumers()
                            raw_errors = 0
                
                # Consume enriched messages
                if self.enriched_consumer:
                    try:
                        enriched_batch = self.enriched_consumer.poll(timeout_ms=1000, max_records=10)
                        if enriched_batch:
                            print(f"Enriched batch: {len(enriched_batch)} partitions, records: {sum(len(records) for records in enriched_batch.values())}")
                        for tp, records in enriched_batch.items():
                            for record in records:
                                try:
                                    message_data = record.value
                                    message_data['_kafka_info'] = {
                                        'topic': record.topic,
                                        'partition': record.partition,
                                        'offset': record.offset,
                                        'timestamp': record.timestamp,
                                        'message_type': 'enriched'
                                    }
                                    self._add_enriched_message(message_data)
                                except Exception as e:
                                    print(f"Error processing enriched message: {e}")
                                    enriched_errors += 1
                    except Exception as e:
                        print(f"Error polling enriched consumer: {e}")
                        enriched_errors += 1
                        if enriched_errors > 5:
                            print("Too many enriched consumer errors, reconnecting...")
                            self.setup_consumers()
                            enriched_errors = 0
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"Error in message consumption: {e}")
                import traceback
                print(f"Full error: {traceback.format_exc()}")
                time.sleep(1)  # Wait before retrying
    
    def _add_raw_message(self, message: Dict[str, Any]):
        """Add a raw message to the recent messages list"""
        try:
            # Convert timestamp to local timezone
            timestamp = message.get('timestamp', 'no-timestamp')
            local_time = convert_to_local_time(timestamp)
            print(f"Adding raw message: {message.get('device_id', 'unknown')} at {local_time}")
            
            # Add local time to message for display
            message['local_timestamp'] = local_time
            
            recent_raw_messages.append(message)
            message_stats['total_raw_messages'] += 1
            message_stats['last_raw_message_time'] = datetime.now()
            
            # Extract device ID and message type
            device_id = message.get('device_id', 'unknown')
            event_type = message.get('event_type', 'unknown')
            
            message_stats['devices_seen'].add(device_id)
            message_stats['message_types'][event_type] = message_stats['message_types'].get(event_type, 0) + 1
            
            # Keep only the last 100 messages
            if len(recent_raw_messages) > 100:
                recent_raw_messages.pop(0)
                
            print(f"Successfully added raw message. Total: {message_stats['total_raw_messages']}")
                
        except Exception as e:
            print(f"Error adding raw message: {e}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")
            print(f"Message that failed: {message}")
    
    def _add_enriched_message(self, message: Dict[str, Any]):
        """Add an enriched message to the recent messages list"""
        try:
            # Convert timestamp to local timezone
            timestamp = message.get('timestamp', 'no-timestamp')
            local_time = convert_to_local_time(timestamp)
            print(f"Adding enriched message: {message.get('device_id', 'unknown')} at {local_time}")
            
            # Add local time to message for display
            message['local_timestamp'] = local_time
            
            recent_enriched_messages.append(message)
            message_stats['total_enriched_messages'] += 1
            message_stats['last_enriched_message_time'] = datetime.now()
            
            # Extract device ID and message type
            device_id = message.get('device_id', 'unknown')
            event_type = message.get('event_type', 'unknown')
            
            message_stats['devices_seen'].add(device_id)
            message_stats['message_types'][event_type] = message_stats['message_types'].get(event_type, 0) + 1
            
            # Keep only the last 100 messages
            if len(recent_enriched_messages) > 100:
                recent_enriched_messages.pop(0)
                
        except Exception as e:
            print(f"Error adding enriched message: {e}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")

# Initialize dashboard
dashboard = IoTDashboard(KAFKA_BROKERS, RAW_TOPIC, ENRICHED_TOPIC)

# Try to connect to Kafka on startup
if dashboard.setup_consumers():
    dashboard.start_consuming()

@app.route('/')
def index():
    """Main dashboard page with cache-busting headers"""
    response = make_response(render_template('dashboard.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/messages')
def get_messages():
    """API endpoint to get recent messages with optional time range"""
    try:
        # Get time range parameter (default to 30 minutes)
        minutes = request.args.get('minutes', 30, type=int)
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # Filter messages by time range
        raw_messages = [msg for msg in recent_raw_messages if 
                       datetime.fromisoformat(msg.get('timestamp', '').replace('Z', '+00:00')) > cutoff_time] if recent_raw_messages else []
        
        enriched_messages = [msg for msg in recent_enriched_messages if 
                           datetime.fromisoformat(msg.get('timestamp', '').replace('Z', '+00:00')) > cutoff_time] if recent_enriched_messages else []
        
        return jsonify({
            'success': True,
            'raw_messages': raw_messages[-100:],  # Limit to last 100
            'enriched_messages': enriched_messages[-100:],  # Limit to last 100
            'stats': {
                'total_raw_messages': message_stats['total_raw_messages'],
                'total_enriched_messages': message_stats['total_enriched_messages'],
                'last_raw_message_time': message_stats['last_raw_message_time'].isoformat() if message_stats['last_raw_message_time'] else None,
                'last_enriched_message_time': message_stats['last_enriched_message_time'].isoformat() if message_stats['last_enriched_message_time'] else None,
                'devices_seen': list(message_stats['devices_seen']),
                'message_types': message_stats['message_types']
            },
            'time_range_minutes': minutes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    return jsonify({
        'total_raw_messages': len(recent_raw_messages),
        'total_enriched_messages': len(recent_enriched_messages),
        'last_raw_message_time': message_stats['last_raw_message_time'].isoformat() if message_stats['last_raw_message_time'] else None,
        'last_enriched_message_time': message_stats['last_enriched_message_time'].isoformat() if message_stats['last_enriched_message_time'] else None,
        'devices_seen': list(message_stats['devices_seen']),
        'message_types': message_stats['message_types']
    })

@app.route('/api/app-registry/<device_type>')
def get_app_registry(device_type):
    """Proxy endpoint to fetch application registrations from app registry service"""
    try:
        import requests
        url = f"http://appregistryservice:5000/api/applications/by-device-type/{device_type}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch from app registry', 'status': response.status_code}), 500
    except Exception as e:
        return jsonify({'error': 'App registry service unavailable', 'message': str(e)}), 500

@app.route('/api/app-registry')
def get_all_app_registrations():
    """Proxy endpoint to fetch all application registrations"""
    try:
        import requests
        url = "http://appregistryservice:5000/api/applications"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch from app registry', 'status': response.status_code}), 500
    except Exception as e:
        return jsonify({'error': 'App registry service unavailable', 'message': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Try to connect to Kafka if not connected
        if not message_stats['kafka_connected']:
            dashboard.setup_consumers()
        
        kafka_status = message_stats['kafka_connected']
        
        return jsonify({
            'status': 'healthy' if kafka_status else 'degraded',
            'kafka_connected': kafka_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/connect')
def connect_kafka():
    """Manually connect to Kafka"""
    try:
        success = dashboard.setup_consumers()
        if success:
            dashboard.start_consuming()
        return jsonify({
            'success': success,
            'message': 'Connected to Kafka' if success else 'Failed to connect to Kafka'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
