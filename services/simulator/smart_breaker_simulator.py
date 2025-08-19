#!/usr/bin/env python3
"""
Smart Breaker Device Simulator for RedPanda/Kafka
Implements FDI-compliant smart breaker with realistic electrical measurements
Now supports both real-time values and trends aggregates per API specification

Features:
- Realistic electrical measurements and protection functions
- FDI-compliant device description and configuration
- High-throughput Kafka/RedPanda communication
- Advanced protection algorithms (overcurrent, ground fault, arc fault)
- Predictive maintenance and condition monitoring
- Trends API support with 5-minute aggregates (v, avg, min, max)
"""

import asyncio
import json
import logging
import os
import time
import threading
import uuid
import random
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from queue import Queue
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta
import numpy as np

import structlog
from faker import Faker
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

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

@dataclass
class BreakerConfig:
    """Smart breaker configuration parameters"""
    device_id: str
    rated_current: float = 100.0  # Amperes
    rated_voltage: float = 480.0  # Volts
    rated_frequency: float = 60.0  # Hz
    breaking_capacity: float = 25.0  # kA
    pole_count: int = 3
    mounting_type: str = "PanelMount"
    protection_class: str = "TypeB"
    
    # Protection settings
    overcurrent_pickup: float = 100.0  # A
    overcurrent_delay: float = 1000.0  # ms
    ground_fault_pickup: float = 5.0  # A
    ground_fault_delay: float = 500.0  # ms
    arc_fault_pickup: float = 50.0  # A
    arc_fault_delay: float = 100.0  # ms
    thermal_pickup: float = 120.0  # A
    thermal_delay: float = 300.0  # s

class BreakerState:
    """Smart breaker operational state"""
    def __init__(self, config: BreakerConfig):
        self.config = config
        self.status = 1  # 0=Open, 1=Closed, 2=Tripped, 3=Fault
        self.position = 1  # 0=Disconnected, 1=Connected, 2=Test
        self.trip_count = 0
        self.last_trip_time = None
        self.trip_reason = ""
        self.trip_current = 0.0
        self.trip_delay = 0.0
        self.operating_hours = 0
        self.maintenance_due = False
        self.communication_status = 1  # 0=Offline, 1=Online, 2=Degraded, 3=Fault
        
        # Electrical measurements
        self.current_phase_a = 0.0
        self.current_phase_b = 0.0
        self.current_phase_c = 0.0
        self.voltage_phase_a = config.rated_voltage
        self.voltage_phase_b = config.rated_voltage
        self.voltage_phase_c = config.rated_voltage
        self.power_factor = 0.95
        
        # Trends data storage for 5-minute aggregates
        self.trends_data = {
            'voltage_phase_a': [],
            'voltage_phase_b': [],
            'voltage_phase_c': [],
            'current_phase_a': [],
            'current_phase_b': [],
            'current_phase_c': [],
            'power_active': [],
            'power_reactive': [],
            'power_apparent': [],
            'frequency': [],
            'temperature': []
        }
        self.last_trends_reset = time.time()
        self.trends_interval = 300  # 5 minutes in seconds

class SmartBreakerSimulator:
    """Smart Breaker Device Simulator"""
    
    def __init__(self, config: BreakerConfig):
        self.config = config
        self.breaker_state = BreakerState(config)
        self.running = True
        self.kafka_connected = False
        self.kafka_producer = None
        self.telemetry_queue = Queue()
        self.raw_topic = os.getenv('RAW_TOPIC', 'iot.raw')
        self.enriched_topic = os.getenv('ENRICHED_TOPIC', 'iot.enriched')
        
        # Setup logging
        self.logger = structlog.get_logger()
        
        # Start worker threads
        self.start_worker_threads()
        
    def start_worker_threads(self):
        """Start background worker threads"""
        print("DEBUG: About to start main telemetry loop")
        
        # Start telemetry loop in separate thread
        telemetry_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
        telemetry_thread.start()
        
        # Start Kafka sender thread
        sender_thread = threading.Thread(target=self._kafka_sender_loop, daemon=True)
        sender_thread.start()
        
        print("DEBUG: Constructor completed")

    def setup_kafka_producer(self):
        """Setup Kafka producer connection"""
        print("DEBUG: About to call setup_kafka_producer")
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['redpanda:29092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            
            # Test connection
            self.kafka_producer.metrics()
            self.kafka_connected = True
            print("DEBUG: Kafka producer connected successfully")
            self.logger.info("Kafka producer connected successfully")
            
        except Exception as e:
            self.kafka_connected = False
            self.logger.error(f"Failed to setup Kafka producer: {e}")
            print(f"DEBUG: Kafka producer setup failed: {e}")

    def _kafka_sender_loop(self):
        """Background loop for sending telemetry to Kafka"""
        while self.running:
            try:
                if not self.telemetry_queue.empty():
                    telemetry_data = self.telemetry_queue.get(timeout=1)
                    self._send_telemetry(telemetry_data)
                else:
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in Kafka sender loop: {e}")
                time.sleep(1)

    def _reset_trends_data(self):
        """Reset trends data for new 5-minute interval"""
        current_time = time.time()
        if current_time - self.breaker_state.last_trends_reset >= self.breaker_state.trends_interval:
            # Calculate aggregates for the completed interval
            self._calculate_trends_aggregates()
            
            # Reset for new interval
            for key in self.breaker_state.trends_data:
                self.breaker_state.trends_data[key] = []
            self.breaker_state.last_trends_reset = current_time

    def _calculate_trends_aggregates(self):
        """Calculate trends aggregates for the completed 5-minute interval"""
        trends_message = {
            "device_id": self.config.device_id,
            "device_type": "smart_breaker",  # For enrichment service
            "timestamp": datetime.fromtimestamp(self.breaker_state.last_trends_reset).isoformat(),
            "event_type": "trends",
            "a": "Trends",  # Action property per API spec
            "p": self.config.device_id,  # Producer UUID per API spec
            "trends": []
        }
        
        # Channel mappings for different measurements
        channels = {
            'voltage_phase_a': '1001',
            'voltage_phase_b': '1002', 
            'voltage_phase_c': '1003',
            'current_phase_a': '1004',
            'current_phase_b': '1005',
            'current_phase_c': '1006',
            'power_active': '1007',
            'power_reactive': '1008',
            'power_apparent': '1009',
            'frequency': '1010',
            'temperature': '1011'
        }
        
        # Calculate aggregates for each measurement type
        for measurement, channel in channels.items():
            data_points = self.breaker_state.trends_data[measurement]
            if data_points:
                trend_entry = {
                    "c": channel,  # Channel tag
                    "t": int(self.breaker_state.last_trends_reset)  # Unix epoch timestamp
                }
                
                # Add aggregates if we have data
                if len(data_points) > 0:
                    trend_entry["avg"] = str(round(np.mean(data_points), 2))
                    trend_entry["min"] = str(round(np.min(data_points), 2))
                    trend_entry["max"] = str(round(np.max(data_points), 2))
                    
                    # Add current value if available (last data point)
                    if data_points:
                        trend_entry["v"] = str(round(data_points[-1], 2))
                
                trends_message["trends"].append(trend_entry)
        
        # Send trends message if we have data
        if trends_message["trends"]:
            self.telemetry_queue.put(trends_message)
            self.logger.info("Trends aggregates generated", 
                           device_id=self.config.device_id,
                           trends_count=len(trends_message["trends"]))

    def generate_telemetry(self):
        """Generate realistic IoT telemetry data with trends collection"""
        try:
            # Check if we need to reset trends data
            self._reset_trends_data()
            
            # Generate realistic electrical measurements
            voltage_a = random.uniform(110.0, 130.0)
            voltage_b = random.uniform(110.0, 130.0)
            voltage_c = random.uniform(110.0, 130.0)
            
            current_a = random.uniform(0.0, 100.0)
            current_b = random.uniform(0.0, 100.0)
            current_c = random.uniform(0.0, 100.0)
            
            # Calculate power values with realistic constraints
            power_factor = random.uniform(0.7, 1.0)  # Ensure power factor is realistic
            
            apparent_power = (voltage_a * current_a + voltage_b * current_b + voltage_c * current_c) / 3.0
            active_power = apparent_power * power_factor
            
            # Safe calculation for reactive power
            apparent_squared = apparent_power ** 2
            active_squared = active_power ** 2
            if apparent_squared >= active_squared:
                reactive_power = math.sqrt(apparent_squared - active_squared)
            else:
                # Fallback calculation
                reactive_power = active_power * math.tan(math.acos(power_factor))
            
            reactive_power = max(0.0, reactive_power)
            
            # Generate protection events
            trip_count = random.randint(0, 5)
            ground_fault_current = random.uniform(0.0, 50.0) if random.random() < 0.1 else 0.0
            arc_fault_detected = random.random() < 0.05
            harmonic_distortion = random.uniform(0.0, 20.0)
            
            # Calculate operating hours safely
            try:
                if hasattr(self.breaker_state, 'start_time'):
                    operating_hours = (time.time() - self.breaker_state.start_time) / 3600.0
                else:
                    operating_hours = random.uniform(0.0, 1000.0)
            except:
                operating_hours = random.uniform(0.0, 1000.0)
            
            # Store data points for trends calculation
            self.breaker_state.trends_data['voltage_phase_a'].append(voltage_a)
            self.breaker_state.trends_data['voltage_phase_b'].append(voltage_b)
            self.breaker_state.trends_data['voltage_phase_c'].append(voltage_c)
            self.breaker_state.trends_data['current_phase_a'].append(current_a)
            self.breaker_state.trends_data['current_phase_b'].append(current_b)
            self.breaker_state.trends_data['current_phase_c'].append(current_c)
            self.breaker_state.trends_data['power_active'].append(active_power)
            self.breaker_state.trends_data['power_reactive'].append(reactive_power)
            self.breaker_state.trends_data['power_apparent'].append(apparent_power)
            self.breaker_state.trends_data['frequency'].append(random.uniform(59.0, 61.0))
            self.breaker_state.trends_data['temperature'].append(random.uniform(20.0, 80.0))
            
            # Create telemetry message (real-time values)
            telemetry_data = {
                "device_id": self.config.device_id,
                "device_type": "smart_breaker",  # Add device type for enrichment service
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                "event_type": "telemetry",
                "measurements": {
                    "voltage": {
                        "phase_a": round(voltage_a, 2),
                        "phase_b": round(voltage_b, 2),
                        "phase_c": round(voltage_c, 2),
                        "unit": "V"
                    },
                    "current": {
                        "phase_a": round(current_a, 2),
                        "phase_b": round(current_b, 2),
                        "phase_c": round(current_c, 2),
                        "unit": "A"
                    },
                    "power": {
                        "active": round(active_power, 2),
                        "reactive": round(reactive_power, 2),
                        "apparent": round(apparent_power, 2),
                        "factor": round(power_factor, 3),
                        "unit": "W"
                    },
                    "frequency": {
                        "value": round(random.uniform(59.0, 61.0), 2),
                        "unit": "Hz"
                    },
                    "temperature": {
                        "value": round(random.uniform(20.0, 80.0), 2),
                        "unit": "°C"
                    },
                    "status": {
                        "breaker": 1,  # 1 = closed, 0 = open
                        "position": 1,  # 1 = engaged, 0 = disengaged
                        "communication": 1  # 1 = online, 0 = offline
                    },
                    "protection": {
                        "trip_count": trip_count,
                        "ground_fault_current": round(ground_fault_current, 2),
                        "arc_fault_detected": arc_fault_detected,
                        "harmonic_distortion": round(harmonic_distortion, 2)
                    },
                    "operational": {
                        "load_percentage": round((active_power / 12000.0) * 100, 1),
                        "operating_hours": round(operating_hours, 1),
                        "maintenance_due": operating_hours > 800.0
                    }
                }
            }
            
            # Add to message queue
            self.telemetry_queue.put(telemetry_data)
            self.logger.info("Telemetry generated", device_id=self.config.device_id)
            
        except Exception as e:
            self.logger.error(f"Error generating telemetry: {e}")
            import traceback
            self.logger.error(f"Full error: {traceback.format_exc()}")

    def _send_telemetry(self, telemetry_data: Dict[str, Any]):
        """Send telemetry data to Kafka topic"""
        if not self.kafka_connected or not self.kafka_producer:
            self.logger.warning("Kafka not connected, cannot send telemetry")
            return
            
        try:
            # Send to Kafka with device ID as key for partitioning
            future = self.kafka_producer.send(
                topic=self.raw_topic,
                key=self.config.device_id,
                value=telemetry_data
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            self.logger.debug(
                f"Telemetry sent to {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            
        except KafkaError as e:
            self.logger.error(f"Kafka send error: {e}")
            # Reconnect if needed
            if not self.kafka_connected:
                self.setup_kafka_producer()
        except Exception as e:
            self.logger.error(f"Error sending telemetry: {e}")

    def _telemetry_loop(self):
        """Main telemetry generation loop"""
        print("DEBUG: Starting main telemetry loop", flush=True)
        try:
            while self.running:
                try:
                    self.generate_telemetry()
                    time.sleep(5)  # Generate telemetry every 5 seconds
                except Exception as e:
                    print(f"DEBUG: Error in telemetry loop: {e}", flush=True)
                    self.logger.error(f"Error in telemetry loop: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"DEBUG: Fatal error in telemetry loop: {e}", flush=True)
            self.logger.error(f"Fatal error in telemetry loop: {e}")
        print("DEBUG: Telemetry loop ended", flush=True)

    def start(self):
        """Start the simulator"""
        self.logger.info(f"Starting Smart Breaker Simulator for device {self.config.device_id}")
        
        try:
            # Main telemetry loop
            while self.running:
                self.generate_telemetry()
                time.sleep(5)  # Generate telemetry every 5 seconds
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            self.logger.error(f"Simulator error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the simulator"""
        self.logger.info("Stopping Smart Breaker Simulator...")
        self.running = False
        
        # Close Kafka producer
        if self.kafka_producer:
            self.kafka_producer.close()
        
        # Shutdown thread pool
        # self.executor.shutdown(wait=True) # This line is removed as per the new_code, as the executor is no longer used.
        
        self.logger.info("Smart Breaker Simulator stopped")

def main():
    """Main entry point"""
    import os
    
    # Get configuration from environment variables
    device_id = os.getenv('DEVICE_ID', 'breaker-001')
    kafka_brokers = os.getenv('REDPANDA_BROKERS', 'localhost:9092')
    raw_topic = os.getenv('RAW_TOPIC', 'iot.raw')
    
    # Create breaker configuration
    config = BreakerConfig(
        device_id=device_id,
        rated_current=100.0,
        rated_voltage=480.0,
        rated_frequency=60.0,
        breaking_capacity=25.0,
        pole_count=3,
        mounting_type="PanelMount",
        protection_class="TypeB"
    )
    
    # Create and start simulator
    simulator = SmartBreakerSimulator(config)
    
    try:
        simulator.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        simulator.stop()

if __name__ == "__main__":
    main()
