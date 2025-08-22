#!/usr/bin/env python3
"""
Smart Grid Monitor Web Client
A dedicated web application for monitoring smart breaker performance
"""

from flask import Flask, render_template, jsonify
from kafka import KafkaConsumer
import json
import threading
import time
from datetime import datetime
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

app = Flask(__name__)

# Global storage for smart breaker data
smart_breaker_data = {
    'messages': [],
    'stats': {
        'total_messages': 0,
        'last_message_time': None,
        'voltage_range': {'min': float('inf'), 'max': float('-inf')},
        'current_range': {'min': float('inf'), 'max': float('-inf')},
        'power_range': {'min': float('inf'), 'max': float('-inf')},
        'temperature_range': {'min': float('inf'), 'max': float('-inf')},
        'trends_count': 0,
        'telemetry_count': 0
    }
}

def kafka_consumer():
    """Kafka consumer for smart breaker data only"""
    try:
        consumer = KafkaConsumer(
            'iot.smart_breaker.enriched',  # Only smart breaker data
            bootstrap_servers=['redpanda:29092'],
            auto_offset_reset='latest',
            group_id='smart-grid-monitor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None
        )
        
        logger.info("Smart Grid Monitor connected to smart breaker topic")
        
        for message in consumer:
            try:
                data = message.value
                device_id = message.key or data.get('device_id', 'unknown')
                
                # Process smart breaker data
                process_smart_breaker_message(data, device_id)
                
            except Exception as e:
                logger.error("Error processing message", error=str(e))
                
    except Exception as e:
        logger.error("Kafka consumer error", error=str(e))
    finally:
        if 'consumer' in locals():
            consumer.close()

def process_smart_breaker_message(data, device_id):
    """Process smart breaker specific data"""
    try:
        # Extract measurements
        measurements = data.get('measurements', {})
        event_type = data.get('event_type', 'unknown')
        
        # Update stats
        smart_breaker_data['stats']['total_messages'] += 1
        smart_breaker_data['stats']['last_message_time'] = datetime.now().isoformat()
        
        if event_type == 'trends':
            smart_breaker_data['stats']['trends_count'] += 1
        elif event_type == 'telemetry':
            smart_breaker_data['stats']['telemetry_count'] += 1
            
            # Update measurement ranges - handle nested structure
            if 'voltage' in measurements:
                voltage_data = measurements['voltage']
                if isinstance(voltage_data, dict):
                    # Extract numeric values from nested structure
                    for phase, value in voltage_data.items():
                        if isinstance(value, (int, float)) and phase != 'unit':
                            voltage = float(value)
                            smart_breaker_data['stats']['voltage_range']['min'] = min(smart_breaker_data['stats']['voltage_range']['min'], voltage)
                            smart_breaker_data['stats']['voltage_range']['max'] = max(smart_breaker_data['stats']['voltage_range']['max'], voltage)
                elif isinstance(voltage_data, (int, float)):
                    # Handle simple numeric value
                    voltage = float(voltage_data)
                    smart_breaker_data['stats']['voltage_range']['min'] = min(smart_breaker_data['stats']['voltage_range']['min'], voltage)
                    smart_breaker_data['stats']['voltage_range']['max'] = max(smart_breaker_data['stats']['voltage_range']['max'], voltage)
                
            if 'current' in measurements:
                current_data = measurements['current']
                if isinstance(current_data, dict):
                    # Extract numeric values from nested structure
                    for phase, value in current_data.items():
                        if isinstance(value, (int, float)) and phase != 'unit':
                            current = float(value)
                            smart_breaker_data['stats']['current_range']['min'] = min(smart_breaker_data['stats']['current_range']['min'], current)
                            smart_breaker_data['stats']['current_range']['max'] = max(smart_breaker_data['stats']['current_range']['max'], current)
                elif isinstance(current_data, (int, float)):
                    # Handle simple numeric value
                    current = float(current_data)
                    smart_breaker_data['stats']['current_range']['min'] = min(smart_breaker_data['stats']['current_range']['min'], current)
                    smart_breaker_data['stats']['current_range']['max'] = max(smart_breaker_data['stats']['current_range']['max'], current)
                
            if 'power' in measurements:
                power_data = measurements['power']
                if isinstance(power_data, dict):
                    # Extract numeric values from nested structure
                    for field, value in power_data.items():
                        if isinstance(value, (int, float)) and field != 'unit':
                            power = float(value)
                            smart_breaker_data['stats']['power_range']['min'] = min(smart_breaker_data['stats']['power_range']['min'], power)
                            smart_breaker_data['stats']['power_range']['max'] = max(smart_breaker_data['stats']['power_range']['max'], power)
                elif isinstance(power_data, (int, float)):
                    # Handle simple numeric value
                    power = float(power_data)
                    smart_breaker_data['stats']['power_range']['min'] = min(smart_breaker_data['stats']['power_range']['min'], power)
                    smart_breaker_data['stats']['power_range']['max'] = max(smart_breaker_data['stats']['power_range']['max'], power)
                
            if 'temperature' in measurements:
                temp_data = measurements['temperature']
                if isinstance(temp_data, dict):
                    # Extract numeric value from nested structure
                    temp_value = temp_data.get('value')
                    if isinstance(temp_value, (int, float)):
                        temp = float(temp_value)
                        smart_breaker_data['stats']['temperature_range']['min'] = min(smart_breaker_data['stats']['temperature_range']['min'], temp)
                        smart_breaker_data['stats']['temperature_range']['max'] = max(smart_breaker_data['stats']['temperature_range']['max'], temp)
                elif isinstance(temp_data, (int, float)):
                    # Handle simple numeric value
                    temp = float(temp_data)
                    smart_breaker_data['stats']['temperature_range']['min'] = min(smart_breaker_data['stats']['temperature_range']['min'], temp)
                    smart_breaker_data['stats']['temperature_range']['max'] = max(smart_breaker_data['stats']['temperature_range']['max'], temp)
        
        # Add message to recent list (keep last 50)
        message_info = {
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'device_id': device_id,
            'event_type': event_type,
            'measurements': measurements,
            'enrichment_info': data.get('enrichment_info', {}),
            'data_quality': data.get('data_quality', {})
        }
        
        smart_breaker_data['messages'].append(message_info)
        
        # Keep only last 50 messages
        if len(smart_breaker_data['messages']) > 50:
            smart_breaker_data['messages'] = smart_breaker_data['messages'][-50:]
            
        logger.info("Smart breaker message processed", 
                   device_id=device_id,
                   event_type=event_type,
                   total_messages=smart_breaker_data['stats']['total_messages'])
                   
    except Exception as e:
        logger.error("Error processing smart breaker message", error=str(e))

@app.route('/')
def dashboard():
    """Smart Grid Monitor Dashboard"""
    return render_template('dashboard.html')

@app.route('/api/smart-breaker-data')
def get_smart_breaker_data():
    """Get smart breaker data and stats"""
    return jsonify({
        'success': True,
        'data': smart_breaker_data['messages'][-20:],  # Last 20 messages
        'stats': smart_breaker_data['stats']
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Smart Grid Monitor',
        'timestamp': datetime.now().isoformat(),
        'message_count': smart_breaker_data['stats']['total_messages']
    })

if __name__ == '__main__':
    # Start Kafka consumer in background thread
    consumer_thread = threading.Thread(target=kafka_consumer, daemon=True)
    consumer_thread.start()
    
    logger.info("Starting Smart Grid Monitor Web Client...")
    app.run(host='0.0.0.0', port=5000, debug=False)
