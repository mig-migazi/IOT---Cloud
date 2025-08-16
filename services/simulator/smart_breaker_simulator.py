#!/usr/bin/env python3
"""
Smart Breaker Device Simulator for RedPanda/Kafka
Implements FDI-compliant smart breaker with realistic electrical measurements

Features:
- Realistic electrical measurements and protection functions
- FDI-compliant device description and configuration
- High-throughput Kafka/RedPanda communication
- Advanced protection algorithms (overcurrent, ground fault, arc fault)
- Predictive maintenance and condition monitoring
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
from typing import Dict, Any, Tuple, Optional
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
        self.frequency = config.rated_frequency
        self.temperature = 25.0
        
        # Calculated values
        self.active_power = 0.0
        self.reactive_power = 0.0
        self.apparent_power = 0.0
        self.load_percentage = 0.0
        self.harmonic_distortion = 2.5
        
        # Protection monitoring
        self.ground_fault_current = 0.0
        self.arc_fault_detected = False
        self.alarm_status = 0
        
        # Control settings
        self.remote_control_enabled = False
        self.auto_reclose_enabled = False
        self.auto_reclose_attempts = 0
        self.max_auto_reclose_attempts = 1
        
        # Timing
        self.start_time = time.time()
        self.last_protection_check = time.time()
        self.last_maintenance_check = time.time()

class SmartBreakerSimulator:
    """High-performance smart breaker simulator with Kafka/RedPanda integration"""

    def __init__(self, config: BreakerConfig, kafka_brokers: str, raw_topic: str):
        print("DEBUG: SmartBreakerSimulator constructor called", flush=True)
        self.config = config
        self.logger = logger.bind(device_id=config.device_id)
        self.fake = Faker()
        
        # Kafka configuration
        self.kafka_brokers = kafka_brokers
        self.raw_topic = raw_topic
        
        # Breaker state
        self.breaker_state = BreakerState(config)
        
        # Threading control
        self.running = True
        self.kafka_connected = False
        
        # Kafka producer for sending telemetry data
        self.kafka_producer = None
        
        # Protocol state
        self.start_time = time.time()
        
        # Message queues for high throughput
        self.telemetry_queue = Queue(maxsize=1000)
        self.command_queue = Queue(maxsize=100)
        
        # Thread pool for message processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        print("DEBUG: About to call setup_kafka_producer", flush=True)
        self.setup_kafka_producer()
        print("DEBUG: About to call start_worker_threads", flush=True)
        self.start_worker_threads()
        print("DEBUG: About to start main telemetry loop", flush=True)
        
        # Start the main telemetry loop in a separate thread
        self.main_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
        self.main_thread.start()
        
        print("DEBUG: Constructor completed", flush=True)

    def setup_kafka_producer(self):
        """Setup Kafka producer for sending telemetry data"""
        print(f"DEBUG: Setting up Kafka producer for brokers: {self.kafka_brokers}", flush=True)
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.kafka_brokers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10,
                buffer_memory=33554432,
                max_request_size=1048576,
                compression_type='gzip'
            )
            self.kafka_connected = True
            print("DEBUG: Kafka producer connected successfully", flush=True)
            self.logger.info("Kafka producer connected successfully")
        except Exception as e:
            print(f"DEBUG: Failed to connect Kafka producer: {e}", flush=True)
            self.logger.error(f"Failed to connect Kafka producer: {e}")
            self.kafka_connected = False

    def start_worker_threads(self):
        """Start worker threads for telemetry and command processing"""
        # Telemetry worker thread
        self.telemetry_thread = threading.Thread(
            target=self._telemetry_worker,
            daemon=True
        )
        self.telemetry_thread.start()
        
        # Command processing thread
        self.command_thread = threading.Thread(
            target=self._command_worker,
            daemon=True
        )
        self.command_thread.start()
        
        # Protection monitoring thread
        self.protection_thread = threading.Thread(
            target=self._protection_monitor,
            daemon=True
        )
        self.protection_thread.start()
        
        # Maintenance monitoring thread
        self.maintenance_thread = threading.Thread(
            target=self._maintenance_monitor,
            daemon=True
        )
        self.maintenance_thread.start()

    def _telemetry_worker(self):
        """Worker thread for processing telemetry data"""
        while self.running:
            try:
                if not self.telemetry_queue.empty():
                    telemetry_data = self.telemetry_queue.get()
                    self._send_telemetry(telemetry_data)
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
            except Exception as e:
                self.logger.error(f"Telemetry worker error: {e}")
                time.sleep(1)

    def _command_worker(self):
        """Worker thread for processing commands"""
        while self.running:
            try:
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    self._process_command(command)
                else:
                    time.sleep(0.01)
            except Exception as e:
                self.logger.error(f"Command worker error: {e}")
                time.sleep(1)

    def _protection_monitor(self):
        """Monitor protection functions and trip conditions"""
        while self.running:
            try:
                self._check_protection_functions()
                time.sleep(0.1)  # Check every 100ms
            except Exception as e:
                self.logger.error(f"Protection monitor error: {e}")
                time.sleep(1)

    def _maintenance_monitor(self):
        """Monitor maintenance requirements"""
        while self.running:
            try:
                self._check_maintenance_requirements()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Maintenance monitor error: {e}")
                time.sleep(60)

    def _check_protection_functions(self):
        """Check all protection functions and trip if necessary"""
        current_time = time.time()
        
        # Overcurrent protection
        max_current = max(
            self.breaker_state.current_phase_a,
            self.breaker_state.current_phase_b,
            self.breaker_state.current_phase_c
        )
        
        if max_current > self.config.overcurrent_pickup:
            if self.breaker_state.status == 1:  # Only trip if closed
                self._trip_breaker("Overcurrent", max_current, self.config.overcurrent_delay)
        
        # Ground fault protection
        if self.breaker_state.ground_fault_current > self.config.ground_fault_pickup:
            if self.breaker_state.status == 1:
                self._trip_breaker("Ground Fault", self.breaker_state.ground_fault_current, self.config.ground_fault_delay)
        
        # Arc fault protection
        if self.breaker_state.arc_fault_detected:
            if self.breaker_state.status == 1:
                self._trip_breaker("Arc Fault", max_current, self.config.arc_fault_delay)
        
        # Thermal protection
        if self.breaker_state.temperature > 80.0:  # Thermal limit
            if self.breaker_state.status == 1:
                self._trip_breaker("Thermal", max_current, self.config.thermal_delay * 1000)

    def _trip_breaker(self, reason: str, current: float, delay_ms: float):
        """Trip the breaker with specified reason and delay"""
        self.breaker_state.trip_reason = reason
        self.breaker_state.trip_current = current
        self.breaker_state.trip_delay = delay_ms
        self.breaker_state.status = 2  # Tripped
        self.breaker_state.trip_count += 1
        self.breaker_state.last_trip_time = datetime.now()
        
        self.logger.warning(f"Breaker tripped: {reason} at {current}A")
        
        # Send trip event to Kafka
        trip_event = {
            "device_id": self.config.device_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "trip",
            "trip_reason": reason,
            "trip_current": current,
            "trip_delay": delay_ms,
            "trip_count": self.breaker_state.trip_count
        }
        self.telemetry_queue.put(trip_event)

    def _check_maintenance_requirements(self):
        """Check if maintenance is due"""
        current_time = time.time()
        operating_hours = (current_time - self.breaker_state.start_time) / 3600
        
        # Update operating hours
        self.breaker_state.operating_hours = operating_hours
        
        # Check maintenance schedule (every 8760 hours = 1 year)
        if operating_hours > 8760 and not self.breaker_state.maintenance_due:
            self.breaker_state.maintenance_due = True
            self.logger.info("Maintenance due - operating hours exceeded 8760")
            
            # Send maintenance alert
            maintenance_alert = {
                "device_id": self.config.device_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": "maintenance_required",
                "operating_hours": operating_hours,
                "maintenance_type": "annual_inspection"
            }
            self.telemetry_queue.put(maintenance_alert)

    def _process_command(self, command: Dict[str, Any]):
        """Process incoming commands"""
        try:
            command_type = command.get('command_type')
            
            if command_type == 'open':
                self._open_breaker()
            elif command_type == 'close':
                self._close_breaker()
            elif command_type == 'reset':
                self._reset_breaker()
            elif command_type == 'configure':
                self._configure_breaker(command.get('parameters', {}))
            else:
                self.logger.warning(f"Unknown command type: {command_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")

    def _open_breaker(self):
        """Open the breaker"""
        if self.breaker_state.status == 1:  # Only if closed
            self.breaker_state.status = 0
            self.logger.info("Breaker opened")
            
            # Send status update
            status_update = {
                "device_id": self.config.device_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": "status_change",
                "new_status": "open",
                "previous_status": "closed"
            }
            self.telemetry_queue.put(status_update)

    def _close_breaker(self):
        """Close the breaker"""
        if self.breaker_state.status == 0:  # Only if open
            self.breaker_state.status = 1
            self.logger.info("Breaker closed")
            
            # Send status update
            status_update = {
                "device_id": self.config.device_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": "status_change",
                "new_status": "closed",
                "previous_status": "open"
            }
            self.telemetry_queue.put(status_update)

    def _reset_breaker(self):
        """Reset the breaker after a trip"""
        if self.breaker_state.status == 2:  # Only if tripped
            self.breaker_state.status = 1
            self.breaker_state.trip_reason = ""
            self.breaker_state.trip_current = 0.0
            self.logger.info("Breaker reset")
            
            # Send reset event
            reset_event = {
                "device_id": self.config.device_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": "reset",
                "previous_status": "tripped"
            }
            self.telemetry_queue.put(reset_event)

    def _configure_breaker(self, parameters: Dict[str, Any]):
        """Configure breaker parameters"""
        try:
            for key, value in parameters.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    self.logger.info(f"Updated {key} to {value}")
                else:
                    self.logger.warning(f"Unknown parameter: {key}")
                    
            # Send configuration update
            config_update = {
                "device_id": self.config.device_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": "configuration_update",
                "parameters": parameters
            }
            self.telemetry_queue.put(config_update)
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")

    def generate_telemetry(self):
        """Generate realistic IoT telemetry data"""
        try:
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
            
            # Create telemetry message
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
        self.executor.shutdown(wait=True)
        
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
    simulator = SmartBreakerSimulator(config, kafka_brokers, raw_topic)
    
    try:
        simulator.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        simulator.stop()

if __name__ == "__main__":
    main()
