#!/usr/bin/env python3
"""
IoT Cloud Web Dashboard
Real-time visualization of IoT data flow through RedPanda
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

from flask import Flask, render_template, jsonify, request
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

app = Flask(__name__)

# Configuration
KAFKA_BROKERS = os.getenv('REDPANDA_BROKERS', 'redpanda:29092')
RAW_TOPIC = os.getenv('RAW_TOPIC', 'iot.raw')
ENRICHED_TOPIC = os.getenv('ENRICHED_TOPIC', 'iot.enriched')

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
                group_id='iot-dashboard-raw',
                auto_offset_reset='earliest',  # Changed from 'latest' to see existing messages
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                consumer_timeout_ms=1000
            )
            
            # Enriched data consumer
            self.enriched_consumer = KafkaConsumer(
                self.enriched_topic,
                bootstrap_servers=self.kafka_brokers,
                group_id='iot-dashboard-enriched',
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                consumer_timeout_ms=1000
            )
            
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
        while self.running:
            try:
                # Consume raw messages
                if self.raw_consumer:
                    raw_batch = self.raw_consumer.poll(timeout_ms=1000, max_records=10)
                    for tp, records in raw_batch.items():
                        for record in records:
                            message_data = record.value
                            message_data['_kafka_info'] = {
                                'topic': record.topic,
                                'partition': record.partition,
                                'offset': record.offset,
                                'timestamp': record.timestamp,
                                'message_type': 'raw'
                            }
                            self._add_raw_message(message_data)
                
                # Consume enriched messages
                if self.enriched_consumer:
                    enriched_batch = self.enriched_consumer.poll(timeout_ms=1000, max_records=10)
                    for tp, records in enriched_batch.items():
                        for record in records:
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
                print(f"Error in consumer thread: {e}")
                time.sleep(1)
    
    def _add_raw_message(self, message: Dict[str, Any]):
        """Add raw message to storage"""
        global recent_raw_messages
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        
        # Add to recent messages (keep last 50)
        recent_raw_messages.insert(0, message)
        recent_raw_messages = recent_raw_messages[:50]
        
        # Update statistics
        message_stats['total_raw_messages'] += 1
        message_stats['last_raw_message_time'] = datetime.now()
        
        device_id = message.get('device_id', 'unknown')
        message_stats['devices_seen'].add(device_id)
        
        event_type = message.get('event_type', 'telemetry')
        message_stats['message_types'][event_type] = message_stats['message_types'].get(event_type, 0) + 1
    
    def _add_enriched_message(self, message: Dict[str, Any]):
        """Add enriched message to storage"""
        global recent_enriched_messages
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        
        # Add to recent messages (keep last 50)
        recent_enriched_messages.insert(0, message)
        recent_enriched_messages = recent_enriched_messages[:50]
        
        # Update statistics
        message_stats['total_enriched_messages'] += 1
        message_stats['last_enriched_message_time'] = datetime.now()
        
        device_id = message.get('device_id', 'unknown')
        message_stats['devices_seen'].add(device_id)
        
        event_type = message.get('event_type', 'telemetry')
        message_stats['message_types'][event_type] = message_stats['message_types'].get(event_type, 0) + 1

# Global dashboard instance
dashboard = IoTDashboard(KAFKA_BROKERS, RAW_TOPIC, ENRICHED_TOPIC)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/messages')
def get_messages():
    """API endpoint to get recent messages"""
    try:
        return jsonify({
            'success': True,
            'raw_messages': recent_raw_messages[:20],
            'enriched_messages': recent_enriched_messages[:20],
            'stats': {
                'total_raw_messages': message_stats['total_raw_messages'],
                'total_enriched_messages': message_stats['total_enriched_messages'],
                'last_raw_message_time': message_stats['last_raw_message_time'].isoformat() if message_stats['last_raw_message_time'] else None,
                'last_enriched_message_time': message_stats['last_enriched_message_time'].isoformat() if message_stats['last_enriched_message_time'] else None,
                'devices_seen': list(message_stats['devices_seen']),
                'message_types': message_stats['message_types']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """API endpoint to get current statistics"""
    try:
        # Calculate time since last messages
        now = datetime.now()
        last_raw_ago = None
        last_enriched_ago = None
        
        if message_stats['last_raw_message_time']:
            last_raw_ago = int((now - message_stats['last_raw_message_time']).total_seconds())
        
        if message_stats['last_enriched_message_time']:
            last_enriched_ago = int((now - message_stats['last_enriched_message_time']).total_seconds())
        
        return jsonify({
            'success': True,
            'stats': {
                'total_raw_messages': message_stats['total_raw_messages'],
                'total_enriched_messages': message_stats['total_enriched_messages'],
                'last_raw_message_ago': last_raw_ago,
                'last_enriched_message_ago': last_enriched_ago,
                'devices_seen': list(message_stats['devices_seen']),
                'message_types': message_stats['message_types'],
                'kafka_connected': message_stats['kafka_connected']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    # Try to connect to Kafka on startup
    if dashboard.setup_consumers():
        dashboard.start_consuming()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
