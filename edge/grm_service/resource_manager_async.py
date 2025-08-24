"""
Async Resource Manager for Edge Core
Manages resource operations using Edge Core WebSocket client
"""
import json
import math
import random
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
from .edge_core_client import EdgeCoreClient, ResourceConfig


class AsyncResourceManager:
    """Async resource manager for Edge Core operations"""
    
    def __init__(self, edge_core_client: EdgeCoreClient):
        self.edge_core_client = edge_core_client
        self.local_resources: List[ResourceConfig] = []
        
        logger.info("Async Resource Manager initialized")
    
    def load_local_resources(self, file_path: str = "resources.json") -> bool:
        """
        Load resources from local JSON file
        
        Args:
            file_path: Path to resources JSON file
            
        Returns:
            True if loading successful, False otherwise
        """
        try:
            resource_file = Path(file_path)
            if not resource_file.exists():
                logger.error(f"Resource file not found: {file_path}")
                return False
            
            with open(resource_file, 'r') as f:
                resources_data = json.load(f)
            
            self.local_resources = []
            
            for resource_data in resources_data:
                # Handle different value types
                value = resource_data.get("value", 0.0)
                resource_type = resource_data.get("resource_type", "float")
                
                # Convert value based on type
                if resource_type == "float":
                    value = float(value)
                elif resource_type == "integer":
                    value = float(int(value))
                elif resource_type == "string":
                    # For strings, we'll use a hash value or 0.0
                    value = 0.0  # Placeholder for string values
                elif resource_type == "boolean":
                    value = float(bool(value))
                else:
                    value = float(value)
                
                resource = ResourceConfig(
                    object_id=resource_data.get("object_id", 0),
                    object_instance_id=resource_data.get("object_instance_id", 0),
                    resource_id=resource_data.get("resource_id", 0),
                    resource_name=resource_data.get("resource_name"),
                    operations=resource_data.get("operations", 3),  # READ | WRITE
                    resource_type=resource_type,
                    value=value,
                    periodic_update=resource_data.get("periodic_update", True)
                )
                self.local_resources.append(resource)
            
            logger.info(f"Loaded {len(self.local_resources)} resources from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load resources from {file_path}: {e}")
            return False
    
    def validate_local_resources(self) -> bool:
        """
        Validate loaded local resources
        
        Returns:
            True if all resources are valid, False otherwise
        """
        if not self.local_resources:
            logger.warning("No local resources loaded")
            return False
        
        for i, resource in enumerate(self.local_resources):
            if not resource.resource_name:
                logger.error(f"Resource {i} missing resource_name")
                return False
            
            if resource.resource_type not in ["float", "integer", "string", "boolean"]:
                logger.error(f"Resource {i} has invalid type: {resource.resource_type}")
                return False
        
        logger.info(f"Validated {len(self.local_resources)} local resources")
        return True
    
    async def sync_resources(self, file_path: str = "resources.json") -> Dict[str, Any]:
        """
        Synchronize local resources with Edge Core
        
        Args:
            file_path: Path to resources JSON file
            
        Returns:
            Dictionary with sync results
        """
        results = {
            "registered": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Load local resources
            if not self.load_local_resources(file_path):
                results["errors"].append("Failed to load local resources")
                results["failed"] += 1
                return results
            
            # Validate resources
            if not self.validate_local_resources():
                results["errors"].append("Failed to validate local resources")
                results["failed"] += 1
                return results
            
            # Add all resources to Edge Core
            if self.local_resources:
                try:
                    result = await self.edge_core_client.add_resource(self.local_resources)
                    if result:
                        results["registered"] = len(self.local_resources)
                        logger.info(f"Successfully registered {len(self.local_resources)} resources")
                    else:
                        results["failed"] = len(self.local_resources)
                        results["errors"].append("Failed to add resources to Edge Core")
                        logger.error("Failed to add resources to Edge Core")
                except Exception as e:
                    results["failed"] = len(self.local_resources)
                    results["errors"].append(f"Exception during resource addition: {e}")
                    logger.error(f"Exception during resource addition: {e}")
            
            return results
            
        except Exception as e:
            results["errors"].append(f"Sync failed: {e}")
            results["failed"] += 1
            logger.error(f"Resource sync failed: {e}")
            return results
    
    async def register_single_resource(self, resource: ResourceConfig) -> bool:
        """
        Register a single resource with Edge Core
        
        Args:
            resource: Resource to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            result = await self.edge_core_client.add_resource([resource])
            if result:
                logger.info(f"Successfully registered resource: {resource.resource_name}")
                return True
            else:
                logger.error(f"Failed to register resource: {resource.resource_name}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during resource registration: {e}")
            return False
    
    async def update_single_resource(self, resource: ResourceConfig) -> bool:
        """
        Update a single resource value in Edge Core
        
        Args:
            resource: Resource with updated value
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            result = await self.edge_core_client.update_resource_value([resource])
            if result:
                logger.info(f"Successfully updated resource: {resource.resource_name}")
                return True
            else:
                logger.error(f"Failed to update resource: {resource.resource_name}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during resource update: {e}")
            return False
    
    async def delete_single_resource(self, object_id: int, object_instance_id: int, resource_id: int) -> bool:
        """
        Delete a single resource from Edge Core
        
        Args:
            object_id: Object ID
            object_instance_id: Object instance ID
            resource_id: Resource ID
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            result = await self.edge_core_client.delete_resource(object_id, object_instance_id, resource_id)
            if result:
                logger.info(f"Successfully deleted resource: object_id={object_id}, instance_id={object_instance_id}, resource_id={resource_id}")
                return True
            else:
                logger.error(f"Failed to delete resource: object_id={object_id}, instance_id={object_instance_id}, resource_id={resource_id}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during resource deletion: {e}")
            return False
    
    def get_local_resources(self) -> List[ResourceConfig]:
        """
        Get all loaded local resources
        
        Returns:
            List of local resources
        """
        return self.local_resources.copy()
    
    def find_resource(self, object_id: int, object_instance_id: int, resource_id: int) -> Optional[ResourceConfig]:
        """
        Find a resource by its identifiers
        
        Args:
            object_id: Object ID
            object_instance_id: Object instance ID
            resource_id: Resource ID
            
        Returns:
            Resource if found, None otherwise
        """
        for resource in self.local_resources:
            if (resource.object_id == object_id and 
                resource.object_instance_id == object_instance_id and 
                resource.resource_id == resource_id):
                return resource
        return None
    
    def update_local_resource_value(self, object_id: int, object_instance_id: int, resource_id: int, value: float) -> bool:
        """
        Update a local resource value
        
        Args:
            object_id: Object ID
            object_instance_id: Object instance ID
            resource_id: Resource ID
            value: New value
            
        Returns:
            True if update successful, False otherwise
        """
        resource = self.find_resource(object_id, object_instance_id, resource_id)
        if resource:
            resource.value = value
            logger.debug(f"Updated local resource value: {resource.resource_name} = {value}")
            return True
        else:
            logger.warning(f"Resource not found for update: object_id={object_id}, instance_id={object_instance_id}, resource_id={resource_id}")
            return False
    
    def generate_simulated_values(self) -> List[ResourceConfig]:
        """
        Generate simulated values for resources with periodic_update=True
        
        Returns:
            List of resources with updated simulated values
        """
        updated_resources = []
        
        for resource in self.local_resources:
            # Only update resources that have periodic_update=True
            if resource.periodic_update:
                # Create a copy of the resource with simulated value
                simulated_resource = ResourceConfig(
                    object_id=resource.object_id,
                    object_instance_id=resource.object_instance_id,
                    resource_id=resource.resource_id,
                    resource_name=resource.resource_name,
                    operations=resource.operations,
                    resource_type=resource.resource_type,
                    value=self._generate_simulated_value(resource),
                    periodic_update=resource.periodic_update
                )
                updated_resources.append(simulated_resource)
                logger.debug(f"Including resource '{resource.resource_name}' for periodic update")
            else:
                logger.debug(f"Skipping resource '{resource.resource_name}' (periodic_update=False)")
        
        return updated_resources
    
    def _generate_simulated_value(self, resource: ResourceConfig) -> float:
        """
        Generate a simulated value based on resource type and name
        
        Args:
            resource: Resource to generate value for
            
        Returns:
            Simulated value
        """
        base_time = time.time()
        
        if resource.resource_name == "temperature":
            # Temperature: 68-86°F (20-30°C equivalent) with some variation
            base_temp = 77.0  # 25°C = 77°F
            variation = 9.0 * math.sin(base_time / 60)  # 60-second cycle (5°C = 9°F)
            noise = random.uniform(-2.0, 2.0)  # ±2°F noise
            return base_temp + variation + noise
            
        elif resource.resource_name == "humidity":
            # Humidity: 40-80% with some variation
            base_humidity = 60.0
            variation = 20.0 * math.sin(base_time / 120)  # 120-second cycle
            noise = random.uniform(-2.0, 2.0)
            return max(40.0, min(80.0, base_humidity + variation + noise))
            
        elif resource.resource_name == "device_type":
            # Device type: keep as 0.0 (string placeholder)
            return 0.0
            
        else:
            # Default: random value between 0-100
            return random.uniform(0.0, 100.0)
    
    async def update_all_resources(self) -> Dict[str, Any]:
        """
        Update all resources with simulated values
        
        Returns:
            Dictionary with update results
        """
        results = {
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Generate simulated values
            updated_resources = self.generate_simulated_values()
            
            if updated_resources:
                # Update resources in Edge Core
                result = await self.edge_core_client.update_resource_value(updated_resources)
                if result:
                    results["updated"] = len(updated_resources)
                    logger.info(f"Successfully updated {len(updated_resources)} resources with simulated values")
                    
                    # Update local resource values
                    for updated_resource in updated_resources:
                        self.update_local_resource_value(
                            updated_resource.object_id,
                            updated_resource.object_instance_id,
                            updated_resource.resource_id,
                            updated_resource.value
                        )
                else:
                    results["failed"] = len(updated_resources)
                    results["errors"].append("Failed to update resources in Edge Core")
                    logger.error("Failed to update resources in Edge Core")
            
            return results
            
        except Exception as e:
            results["errors"].append(f"Resource update failed: {e}")
            results["failed"] += 1
            logger.error(f"Resource update failed: {e}")
            return results
