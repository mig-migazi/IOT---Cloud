#!/usr/bin/env python3
"""
MQTT-based Smart Breaker Simulator
Publishes IoT data to MQTT topics instead of direct Kafka connection
"""

import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt
import structlog

# Simple logging setup
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MQTTSmartBreakerSimulator:
    """MQTT-based Smart Breaker Simulator"""
    
    def __init__(self):
        # MQTT Configuration
        self.mqtt_broker = 'mqtt-broker'
        self.mqtt_port = 1883
        self.mqtt_client_id = f"smart_breaker_sim_{random.randint(1000, 9999)}"
        
        # Device Configuration
        self.device_id = "breaker-001"
        self.device_type = "smart_breaker"
        
        # MQTT Topics
        self.telemetry_topic = f"iot/{self.device_id}/raw"
        self.trends_topic = f"iot/{self.device_id}/trends"
        self.status_topic = f"iot/{self.device_id}/status"
        
        # MQTT Client
        self.mqtt_client = mqtt.Client(client_id=self.mqtt_client_id)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.mqtt_client.on_publish = self.on_mqtt_publish
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'telemetry_count': 0,
            'trends_count': 0,
            'status_count': 0,
            'burst_count': 0,
            'last_message_time': None
        }
        
        logger.info(f"MQTT Smart Breaker Simulator initialized - device_id: {self.device_id}, mqtt_broker: {self.mqtt_broker}, telemetry_topic: {self.telemetry_topic}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when MQTT client connects"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            self.stats['last_message_time'] = time.time()
        else:
            logger.error(f"Failed to connect to MQTT broker, return_code: {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback when MQTT client disconnects"""
        logger.warning(f"Disconnected from MQTT broker, return_code: {rc}")
        if rc != 0:
            logger.info("Attempting to reconnect...")
    
    def on_mqtt_publish(self, client, userdata, mid):
        """Callback when MQTT message is published"""
        logger.debug("Message published successfully", message_id=mid)
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker {self.mqtt_broker}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            logger.error("Failed to connect to MQTT broker", error=str(e))
            return False
    
    def generate_telemetry_data(self):
        """Generate realistic smart breaker telemetry data"""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "telemetry",
            "measurements": {
                "voltage": {
                    "phase_a": round(random.uniform(110.0, 130.0), 2),
                    "phase_b": round(random.uniform(110.0, 130.0), 2),
                    "phase_c": round(random.uniform(110.0, 130.0), 2),
                    "unit": "V"
                },
                "current": {
                    "phase_a": round(random.uniform(0.0, 100.0), 2),
                    "phase_b": round(random.uniform(0.0, 100.0), 2),
                    "phase_c": round(random.uniform(0.0, 100.0), 2),
                    "unit": "A"
                },
                "power": {
                    "active": round(random.uniform(5000.0, 12000.0), 2),
                    "reactive": round(random.uniform(1000.0, 3000.0), 2),
                    "apparent": round(random.uniform(5000.0, 13000.0), 2),
                    "factor": round(random.uniform(0.85, 0.98), 3),
                    "unit": "W"
                },
                "frequency": {
                    "value": round(random.uniform(59.5, 60.5), 2),
                    "unit": "Hz"
                },
                "temperature": {
                    "value": round(random.uniform(20.0, 80.0), 2),
                    "unit": "°C"
                },
                "status": {
                    "breaker": random.choice([0, 1]),
                    "position": random.choice([0, 1]),
                    "communication": 1
                },
                "protection": {
                    "trip_count": random.randint(0, 10),
                    "ground_fault_current": round(random.uniform(0.0, 5.0), 2),
                    "arc_fault_detected": random.choice([True, False])
                },
                "operational": {
                    "load_percentage": round(random.uniform(20.0, 90.0), 1),
                    "operating_hours": round(random.uniform(100.0, 1000.0), 1),
                    "maintenance_due": random.choice([True, False])
                }
            }
        }
    
    def generate_trends_data(self):
        """Generate aggregated trends data"""
        base_time = int(time.time())
        trends = []
        
        # Generate trends for different measurements
        measurements = ['voltage_phase_a', 'current_phase_a', 'power_active', 'temperature']
        
        for i, measurement in enumerate(measurements):
            base_value = random.uniform(100.0, 120.0)
            trend = {
                "c": measurement,  # Channel/measurement name
                "t": base_time - (i * 60),  # Timestamp (staggered)
                "v": str(round(base_value, 2)),  # Current value
                "avg": str(round(base_value * random.uniform(0.95, 1.05), 2)),  # Average
                "min": str(round(base_value * random.uniform(0.90, 0.98), 2)),  # Minimum
                "max": str(round(base_value * random.uniform(1.02, 1.10), 2))   # Maximum
            }
            trends.append(trend)
        
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "trends",
            "trends": trends
        }
    
    def generate_status_data(self):
        """Generate device status information"""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "timestamp": datetime.now().isoformat(),
            "event_type": "status",
            "status": {
                "online": True,
                "last_telemetry": self.stats['last_message_time'],
                "message_count": self.stats['messages_sent'],
                "uptime_hours": round(time.time() / 3600, 1),
                "firmware_version": "2.1.0",
                "hardware_revision": "A"
            }
        }
    
    def publish_message(self, topic, payload, qos=1):
        """Publish message to MQTT topic"""
        try:
            message = json.dumps(payload, default=str)
            result = self.mqtt_client.publish(topic, message, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.stats['messages_sent'] += 1
                self.stats['last_message_time'] = time.time()
                logger.info(f"Message published successfully - topic: {topic}, message_size: {len(message)}, qos: {qos}")
                return True
            else:
                logger.error("Failed to publish message", 
                           topic=topic,
                           return_code=result.rc)
                return False
                
        except Exception as e:
            logger.error("Error publishing message", topic=topic, error=str(e))
            return False
    
    def run_simulation(self):
        """Main simulation loop"""
        logger.info("Starting MQTT Smart Breaker simulation...")
        
        if not self.connect_mqtt():
            logger.error("Failed to connect to MQTT broker, exiting")
            return
        
        try:
            while True:
                try:
                    # 25% chance of burst
                    if random.random() < 0.25:
                        burst_size = random.randint(3, 6)
                        logger.info(f"💥 Generating burst of {burst_size} messages")
                        self.stats['burst_count'] += 1

                        # Send burst messages
                        for i in range(burst_size):
                            # Telemetry message
                            telemetry_data = self.generate_telemetry_data()
                            self.publish_message(self.telemetry_topic, telemetry_data)
                            self.stats['telemetry_count'] += 1
                            
                            # Small delay between burst messages
                            time.sleep(0.2)
                        
                        # Send trends message after burst
                        trends_data = self.generate_trends_data()
                        self.publish_message(self.trends_topic, trends_data)
                        self.stats['trends_count'] += 1
                        
                        # Send status update
                        status_data = self.generate_status_data()
                        self.publish_message(self.status_topic, status_data)
                        self.stats['status_count'] += 1
                        
                    else:
                        # Normal single telemetry message
                        telemetry_data = self.generate_telemetry_data()
                        self.publish_message(self.telemetry_topic, telemetry_data)
                        self.stats['telemetry_count'] += 1
                    
                    # Random wait for dynamic rates
                    wait_time = random.uniform(3, 8)
                    logger.info(f"⏳ Waiting {wait_time:.1f}s... (Total: {self.stats['messages_sent']}, Bursts: {self.stats['burst_count']})")
                    time.sleep(wait_time)
                    
                except Exception as e:
                    logger.error("Error in simulation loop", error=str(e))
                    time.sleep(2)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up...")
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        logger.info(f"✅ Simulator stopped. Final stats: {self.stats}")

def main():
    """Main entry point"""
    simulator = MQTTSmartBreakerSimulator()
    simulator.run_simulation()

if __name__ == "__main__":
    main()
