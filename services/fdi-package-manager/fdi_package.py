#!/usr/bin/env python3
"""
FDI Package Implementation
Defines the structure and methods for FDI (Field Device Integration) packages
"""

import json
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger()

@dataclass
class FDIDeviceParameter:
    """FDI Device Parameter definition"""
    name: str
    description: str
    data_type: str
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    valid_values: Optional[List[Any]] = None
    default_value: Optional[Any] = None
    access_level: str = "read_write"  # read_only, read_write, write_only
    category: str = "measurement"  # measurement, configuration, status, command

@dataclass
class FDIDeviceCommand:
    """FDI Device Command definition"""
    name: str
    description: str
    parameters: List[FDIDeviceParameter]
    return_type: str
    timeout_seconds: int = 30
    requires_confirmation: bool = False

@dataclass
class FDIDeviceType:
    """FDI Device Type definition"""
    device_type: str
    name: str
    description: str
    category: str
    manufacturer: str
    model: str
    version: str
    capabilities: List[str]
    parameters: List[FDIDeviceParameter]
    commands: List[FDIDeviceCommand]
    data_format: str = "json"
    update_frequency: str = "5_seconds"
    retention_policy: str = "30_days"

class FDIPackage:
    """FDI Package for device integration"""
    
    def __init__(self, device_type: FDIDeviceType):
        self.device_type = device_type
        self.package_id = self._generate_package_id()
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.version = "1.0.0"
        self.schema_version = "1.0"
        self.metadata = {}
        
    def _generate_package_id(self) -> str:
        """Generate unique package ID based on device type and timestamp"""
        base = f"{self.device_type.device_type}_{self.device_type.manufacturer}_{self.device_type.model}"
        timestamp = str(int(time.time()))
        return hashlib.md5(f"{base}_{timestamp}".encode()).hexdigest()[:16]
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the package"""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert package to dictionary"""
        return {
            "package_id": self.package_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "device_type": asdict(self.device_type),
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert package to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def validate(self) -> bool:
        """Validate the FDI package structure"""
        try:
            # Check required fields
            if not self.device_type.device_type:
                logger.error("Device type is required")
                return False
                
            if not self.device_type.parameters:
                logger.error("At least one parameter is required")
                return False
                
            # Validate parameters
            for param in self.device_type.parameters:
                if not param.name or not param.data_type:
                    logger.error(f"Parameter {param.name} missing required fields")
                    return False
                    
            # Validate commands
            for cmd in self.device_type.commands:
                if not cmd.name:
                    logger.error(f"Command {cmd.name} missing required fields")
                    return False
                # Parameters can be empty for commands that don't need them
                    
            logger.info("FDI package validation successful", package_id=self.package_id)
            return True
            
        except Exception as e:
            logger.error("FDI package validation failed", error=str(e))
            return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FDIPackage':
        """Create FDI package from dictionary"""
        # Reconstruct device type
        device_type_data = data.get('device_type', {})
        
        # Reconstruct parameters
        parameters = []
        for param_data in device_type_data.get('parameters', []):
            param = FDIDeviceParameter(**param_data)
            parameters.append(param)
            
        # Reconstruct commands
        commands = []
        for cmd_data in device_type_data.get('commands', []):
            cmd_params = []
            for param_data in cmd_data.get('parameters', []):
                param = FDIDeviceParameter(**param_data)
                cmd_params.append(param)
            
            cmd = FDIDeviceCommand(
                name=cmd_data['name'],
                description=cmd_data['description'],
                parameters=cmd_params,
                return_type=cmd_data['return_type'],
                timeout_seconds=cmd_data.get('timeout_seconds', 30),
                requires_confirmation=cmd_data.get('requires_confirmation', False)
            )
            commands.append(cmd)
        
        # Create device type
        device_type = FDIDeviceType(
            device_type=device_type_data['device_type'],
            name=device_type_data['name'],
            description=device_type_data['description'],
            category=device_type_data['category'],
            manufacturer=device_type_data['manufacturer'],
            model=device_type_data['model'],
            version=device_type_data['version'],
            capabilities=device_type_data['capabilities'],
            parameters=parameters,
            commands=commands,
            data_format=device_type_data.get('data_format', 'json'),
            update_frequency=device_type_data.get('update_frequency', '5_seconds'),
            retention_policy=device_type_data.get('retention_policy', '30_days')
        )
        
        # Create package
        package = cls(device_type)
        package.package_id = data.get('package_id', package.package_id)
        package.created_at = data.get('created_at', package.created_at)
        package.version = data.get('version', package.version)
        package.schema_version = data.get('schema_version', package.schema_version)
        package.metadata = data.get('metadata', {})
        
        return package

def create_smart_breaker_fdi_package() -> FDIPackage:
    """Create FDI package for smart breaker simulator"""
    
    # Define parameters
    parameters = [
        # Voltage parameters
        FDIDeviceParameter(
            name="voltage_phase_a",
            description="Phase A voltage",
            data_type="float",
            unit="V",
            min_value=110.0,
            max_value=130.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="voltage_phase_b",
            description="Phase B voltage",
            data_type="float",
            unit="V",
            min_value=110.0,
            max_value=130.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="voltage_phase_c",
            description="Phase C voltage",
            data_type="float",
            unit="V",
            min_value=110.0,
            max_value=130.0,
            category="measurement"
        ),
        
        # Current parameters
        FDIDeviceParameter(
            name="current_phase_a",
            description="Phase A current",
            data_type="float",
            unit="A",
            min_value=0.0,
            max_value=100.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="current_phase_b",
            description="Phase B current",
            data_type="float",
            unit="A",
            min_value=0.0,
            max_value=100.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="current_phase_c",
            description="Phase C current",
            data_type="float",
            unit="A",
            min_value=0.0,
            max_value=100.0,
            category="measurement"
        ),
        
        # Power parameters
        FDIDeviceParameter(
            name="power_active",
            description="Active power",
            data_type="float",
            unit="W",
            min_value=0.0,
            max_value=12000.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="power_reactive",
            description="Reactive power",
            data_type="float",
            unit="VAR",
            min_value=0.0,
            max_value=8000.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="power_apparent",
            description="Apparent power",
            data_type="float",
            unit="VA",
            min_value=0.0,
            max_value=15000.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="power_factor",
            description="Power factor",
            data_type="float",
            min_value=0.7,
            max_value=1.0,
            category="measurement"
        ),
        
        # Other measurements
        FDIDeviceParameter(
            name="frequency",
            description="AC frequency",
            data_type="float",
            unit="Hz",
            min_value=59.0,
            max_value=61.0,
            category="measurement"
        ),
        FDIDeviceParameter(
            name="temperature",
            description="Operating temperature",
            data_type="float",
            unit="°C",
            min_value=20.0,
            max_value=80.0,
            category="measurement"
        ),
        
        # Status parameters
        FDIDeviceParameter(
            name="breaker_status",
            description="Breaker state (0=open, 1=closed)",
            data_type="integer",
            valid_values=[0, 1],
            category="status"
        ),
        FDIDeviceParameter(
            name="position",
            description="Mechanical position",
            data_type="integer",
            valid_values=[0, 1],
            category="status"
        ),
        FDIDeviceParameter(
            name="communication_status",
            description="Communication status",
            data_type="integer",
            valid_values=[0, 1],
            category="status"
        ),
        
        # Configuration parameters
        FDIDeviceParameter(
            name="trip_current_threshold",
            description="Trip current threshold",
            data_type="float",
            unit="A",
            min_value=50.0,
            max_value=200.0,
            default_value=100.0,
            category="configuration"
        ),
        FDIDeviceParameter(
            name="voltage_threshold",
            description="Voltage threshold for protection",
            data_type="float",
            unit="V",
            min_value=100.0,
            max_value=140.0,
            default_value=120.0,
            category="configuration"
        )
    ]
    
    # Define commands
    commands = [
        FDIDeviceCommand(
            name="trip_breaker",
            description="Trip the circuit breaker",
            parameters=[],
            return_type="boolean"
        ),
        FDIDeviceCommand(
            name="reset_breaker",
            description="Reset the circuit breaker",
            parameters=[],
            return_type="boolean"
        ),
        FDIDeviceCommand(
            name="set_trip_threshold",
            description="Set trip current threshold",
            parameters=[
                FDIDeviceParameter(
                    name="threshold",
                    description="New trip threshold value",
                    data_type="float",
                    unit="A",
                    min_value=50.0,
                    max_value=200.0,
                    category="configuration"
                )
            ],
            return_type="boolean"
        ),
        FDIDeviceCommand(
            name="get_diagnostics",
            description="Get device diagnostics information",
            parameters=[],
            return_type="object"
        )
    ]
    
    # Create device type
    device_type = FDIDeviceType(
        device_type="smart_breaker",
        name="Smart Circuit Breaker",
        description="Intelligent circuit breaker with monitoring and protection capabilities",
        category="electrical_protection",
        manufacturer="ElectroCorp",
        model="SB-2000",
        version="2.1.0",
        capabilities=[
            "voltage_monitoring",
            "current_monitoring",
            "power_monitoring",
            "frequency_monitoring",
            "temperature_monitoring",
            "status_monitoring",
            "protection_monitoring",
            "operational_monitoring",
            "remote_control",
            "diagnostics"
        ],
        parameters=parameters,
        commands=commands,
        data_format="json",
        update_frequency="5_seconds",
        retention_policy="30_days"
    )
    
    # Create and return package
    package = FDIPackage(device_type)
    package.add_metadata("simulator_type", "smart_breaker")
    package.add_metadata("protocol", "MQTT")
    package.add_metadata("topic_pattern", "iot/+/raw")
    
    return package
