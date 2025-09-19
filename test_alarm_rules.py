#!/usr/bin/env python3
"""
Test script to verify alarm rules work with simulator data
"""

import json
import random
from datetime import datetime

def generate_test_telemetry():
    """Generate test telemetry data that should trigger alarms"""
    return {
        "device_id": "breaker-001",
        "device_type": "smart_breaker",
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

def generate_alarm_test_cases():
    """Generate test cases that should trigger specific alarms"""
    test_cases = []
    
    # Test case 1: High voltage alarm
    test_cases.append({
        "name": "High Voltage Phase A",
        "data": {
            "device_id": "breaker-001",
            "device_type": "smart_breaker",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "telemetry",
            "measurements": {
                "voltage": {"phase_a": 130.5, "phase_b": 120.0, "phase_c": 119.0},
                "temperature": {"value": 45.0},
                "current": {"phase_a": 50.0, "phase_b": 45.0, "phase_c": 48.0},
                "power": {"active": 8000.0, "factor": 0.92},
                "frequency": {"value": 60.0},
                "protection": {"trip_count": 2, "ground_fault_current": 0.5, "arc_fault_detected": False},
                "operational": {"load_percentage": 70.0, "maintenance_due": False}
            }
        },
        "expected_alarms": ["High Voltage Phase A"]
    })
    
    # Test case 2: High temperature alarm
    test_cases.append({
        "name": "High Temperature",
        "data": {
            "device_id": "breaker-001",
            "device_type": "smart_breaker",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "telemetry",
            "measurements": {
                "voltage": {"phase_a": 120.0, "phase_b": 121.0, "phase_c": 119.5},
                "temperature": {"value": 78.5},
                "current": {"phase_a": 60.0, "phase_b": 58.0, "phase_c": 62.0},
                "power": {"active": 9000.0, "factor": 0.88},
                "frequency": {"value": 59.8},
                "protection": {"trip_count": 1, "ground_fault_current": 0.2, "arc_fault_detected": False},
                "operational": {"load_percentage": 75.0, "maintenance_due": False}
            }
        },
        "expected_alarms": ["High Temperature"]
    })
    
    # Test case 3: Ground fault alarm
    test_cases.append({
        "name": "Ground Fault Detected",
        "data": {
            "device_id": "breaker-001",
            "device_type": "smart_breaker",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "telemetry",
            "measurements": {
                "voltage": {"phase_a": 118.0, "phase_b": 120.0, "phase_c": 119.0},
                "temperature": {"value": 35.0},
                "current": {"phase_a": 45.0, "phase_b": 47.0, "phase_c": 46.0},
                "power": {"active": 7000.0, "factor": 0.90},
                "frequency": {"value": 60.1},
                "protection": {"trip_count": 0, "ground_fault_current": 4.2, "arc_fault_detected": False},
                "operational": {"load_percentage": 60.0, "maintenance_due": False}
            }
        },
        "expected_alarms": ["Ground Fault Detected"]
    })
    
    # Test case 4: Multiple alarms
    test_cases.append({
        "name": "Multiple Alarms",
        "data": {
            "device_id": "breaker-001",
            "device_type": "smart_breaker",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "telemetry",
            "measurements": {
                "voltage": {"phase_a": 128.0, "phase_b": 130.5, "phase_c": 129.0},
                "temperature": {"value": 82.0},
                "current": {"phase_a": 95.0, "phase_b": 92.0, "phase_c": 98.0},
                "power": {"active": 11500.0, "factor": 0.82},
                "frequency": {"value": 59.2},
                "protection": {"trip_count": 9, "ground_fault_current": 3.5, "arc_fault_detected": True},
                "operational": {"load_percentage": 88.0, "maintenance_due": True}
            }
        },
        "expected_alarms": [
            "High Voltage Phase A", "High Voltage Phase B", "High Voltage Phase C",
            "Critical Temperature", "High Current Phase A", "High Current Phase B", 
            "High Current Phase C", "High Active Power", "Low Power Factor",
            "Frequency Out of Range", "Ground Fault Detected", "Arc Fault Detected",
            "High Trip Count", "High Load Percentage", "Maintenance Due"
        ]
    })
    
    return test_cases

def print_test_summary():
    """Print a summary of the alarm rules"""
    print("🚨 ALARM RULES SUMMARY")
    print("=" * 50)
    
    rules = [
        ("VOLTAGE ALARMS", [
            "High Voltage Phase A (>125V) - HIGH severity",
            "Low Voltage Phase A (<115V) - HIGH severity", 
            "High Voltage Phase B (>125V) - HIGH severity",
            "Low Voltage Phase B (<115V) - HIGH severity",
            "High Voltage Phase C (>125V) - HIGH severity",
            "Low Voltage Phase C (<115V) - HIGH severity"
        ]),
        ("TEMPERATURE ALARMS", [
            "High Temperature (>75°C) - HIGH severity",
            "Critical Temperature (>80°C) - CRITICAL severity"
        ]),
        ("CURRENT ALARMS", [
            "High Current Phase A (>90A) - MEDIUM severity",
            "High Current Phase B (>90A) - MEDIUM severity", 
            "High Current Phase C (>90A) - MEDIUM severity"
        ]),
        ("POWER ALARMS", [
            "High Active Power (>11000W) - MEDIUM severity",
            "Low Power Factor (<0.85) - MEDIUM severity"
        ]),
        ("FREQUENCY ALARMS", [
            "Frequency Out of Range (59.5-60.5 Hz) - MEDIUM severity"
        ]),
        ("PROTECTION ALARMS", [
            "Ground Fault Detected (>3A) - CRITICAL severity",
            "Arc Fault Detected - CRITICAL severity",
            "High Trip Count (>8) - LOW severity"
        ]),
        ("OPERATIONAL ALARMS", [
            "High Load Percentage (>85%) - MEDIUM severity",
            "Maintenance Due - LOW severity"
        ])
    ]
    
    for category, rule_list in rules:
        print(f"\n📊 {category}")
        print("-" * 30)
        for rule in rule_list:
            print(f"  • {rule}")
    
    print(f"\n🎯 TOTAL RULES: 19")
    print(f"🔴 CRITICAL: 3 rules")
    print(f"🟠 HIGH: 8 rules") 
    print(f"🟡 MEDIUM: 6 rules")
    print(f"🟢 LOW: 2 rules")

if __name__ == "__main__":
    print_test_summary()
    
    print("\n" + "=" * 50)
    print("🧪 TEST CASES")
    print("=" * 50)
    
    test_cases = generate_alarm_test_cases()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        print("📤 Input Data:")
        print(json.dumps(test_case['data'], indent=2))
        print(f"\n🎯 Expected Alarms: {', '.join(test_case['expected_alarms'])}")
        print(f"📊 Expected Count: {len(test_case['expected_alarms'])} alarms")
    
    print(f"\n✅ Generated {len(test_cases)} test cases")
    print("\n💡 To test with real data:")
    print("   1. Start the simulator: docker-compose up smart-breaker-simulator")
    print("   2. Start the alarm processor: docker-compose up alarm-processor") 
    print("   3. Monitor alarms: docker-compose logs alarm-processor")
    print("   4. Check alarm topic: kafka-console-consumer --bootstrap-server localhost:9092 --topic iot.alarms")
