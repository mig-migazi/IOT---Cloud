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
from .edge_core_client import EdgeCoreClient, ResourceConfig, CloudUpdateMessage
import asyncio


class AsyncResourceManager:
    """Async resource manager for Edge Core operations with cloud update support"""
    
    def __init__(self, edge_core_client: EdgeCoreClient):
        self.edge_core_client = edge_core_client
        self.local_resources: List[ResourceConfig] = []
        
        # Cloud update handling
        self.cloud_update_stats = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "last_update_time": None
        }
        
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

    async def handle_cloud_update(self, cloud_update: CloudUpdateMessage) -> Dict[str, Any]:
        """
        Handle incoming cloud update
        
        Args:
            cloud_update: Cloud update message
            
        Returns:
            Dictionary with update results
        """
        results = {
            "processed": False,
            "updated_resources": 0,
            "failed_resources": 0,
            "errors": []
        }
        
        try:
            self.cloud_update_stats["total_updates"] += 1
            self.cloud_update_stats["last_update_time"] = time.time()
            
            logger.info(f"Processing cloud update: {cloud_update.message_type}")
            
            if cloud_update.is_resource_update():
                results = await self._handle_resource_update(cloud_update)
            elif cloud_update.is_configuration_update():
                results = await self._handle_configuration_update(cloud_update)
            elif cloud_update.is_command():
                results = await self._handle_command(cloud_update)
            else:
                results["errors"].append(f"Unknown update type: {cloud_update.message_type}")
                logger.warning(f"Unknown cloud update type: {cloud_update.message_type}")
            
            # Update statistics
            if results["processed"]:
                self.cloud_update_stats["successful_updates"] += 1
            else:
                self.cloud_update_stats["failed_updates"] += 1
            
            return results
            
        except Exception as e:
            error_msg = f"Error handling cloud update: {e}"
            results["errors"].append(error_msg)
            self.cloud_update_stats["failed_updates"] += 1
            logger.error(error_msg)
            return results
    
    async def _handle_resource_update(self, cloud_update: CloudUpdateMessage) -> Dict[str, Any]:
        """
        Handle resource update from cloud
        
        Args:
            cloud_update: Cloud update message with resource updates
            
        Returns:
            Dictionary with update results
        """
        results = {
            "processed": True,
            "updated_resources": 0,
            "failed_resources": 0,
            "errors": []
        }
        
        try:
            logger.info(f"Processing resource update for device {cloud_update.device_id}")
            
            # Process each resource update
            for resource_update in cloud_update.resource_updates:
                try:
                    success = await self._apply_resource_update(resource_update)
                    if success:
                        results["updated_resources"] += 1
                    else:
                        results["failed_resources"] += 1
                        results["errors"].append(f"Failed to update resource: {resource_update}")
                except Exception as e:
                    results["failed_resources"] += 1
                    results["errors"].append(f"Error updating resource: {e}")
                    logger.error(f"Error applying resource update: {e}")
            
            logger.info(f"Resource update completed: {results['updated_resources']} successful, "
                       f"{results['failed_resources']} failed")
            
            return results
            
        except Exception as e:
            results["processed"] = False
            results["errors"].append(f"Resource update processing failed: {e}")
            logger.error(f"Resource update processing failed: {e}")
            return results
    
    async def _handle_configuration_update(self, cloud_update: CloudUpdateMessage) -> Dict[str, Any]:
        """
        Handle configuration update from cloud
        
        Args:
            cloud_update: Cloud update message with configuration changes
            
        Returns:
            Dictionary with update results
        """
        results = {
            "processed": True,
            "updated_resources": 0,
            "failed_resources": 0,
            "errors": []
        }
        
        try:
            logger.info(f"Processing configuration update for device {cloud_update.device_id}")
            
            # Extract configuration changes
            config_changes = cloud_update.metadata.get("configuration_changes", {})
            
            # Apply configuration changes
            for change_type, change_data in config_changes.items():
                try:
                    if change_type == "add_resource":
                        success = await self._add_resource_from_cloud(change_data)
                    elif change_type == "remove_resource":
                        success = await self._remove_resource_from_cloud(change_data)
                    elif change_type == "modify_resource":
                        success = await self._modify_resource_from_cloud(change_data)
                    else:
                        logger.warning(f"Unknown configuration change type: {change_type}")
                        continue
                    
                    if success:
                        results["updated_resources"] += 1
                    else:
                        results["failed_resources"] += 1
                        results["errors"].append(f"Failed to apply {change_type}")
                        
                except Exception as e:
                    results["failed_resources"] += 1
                    results["errors"].append(f"Error applying {change_type}: {e}")
                    logger.error(f"Error applying configuration change {change_type}: {e}")
            
            logger.info(f"Configuration update completed: {results['updated_resources']} successful, "
                       f"{results['failed_resources']} failed")
            
            return results
            
        except Exception as e:
            results["processed"] = False
            results["errors"].append(f"Configuration update processing failed: {e}")
            logger.error(f"Configuration update processing failed: {e}")
            return results
    
    async def _handle_command(self, cloud_update: CloudUpdateMessage) -> Dict[str, Any]:
        """
        Handle command from cloud
        
        Args:
            cloud_update: Cloud update message with command
            
        Returns:
            Dictionary with update results
        """
        results = {
            "processed": True,
            "updated_resources": 0,
            "failed_resources": 0,
            "errors": []
        }
        
        try:
            logger.info(f"Processing command for device {cloud_update.device_id}")
            
            command = cloud_update.metadata.get("command", {})
            command_type = command.get("type")
            command_params = command.get("parameters", {})
            
            if command_type == "sync_resources":
                # Sync all resources with Edge Core
                sync_results = await self.sync_resources()
                results["updated_resources"] = sync_results.get("registered", 0)
                results["failed_resources"] = sync_results.get("failed", 0)
                results["errors"].extend(sync_results.get("errors", []))
                
            elif command_type == "update_all_resources":
                # Update all resources with simulated values
                update_results = await self.update_all_resources()
                results["updated_resources"] = update_results.get("updated", 0)
                results["failed_resources"] = update_results.get("failed", 0)
                results["errors"].extend(update_results.get("errors", []))
                
            elif command_type == "set_resource_value":
                # Set specific resource value
                object_id = command_params.get("object_id")
                instance_id = command_params.get("instance_id")
                resource_id = command_params.get("resource_id")
                value = command_params.get("value")
                
                if all(v is not None for v in [object_id, instance_id, resource_id, value]):
                    success = await self._set_resource_value(object_id, instance_id, resource_id, value)
                    if success:
                        results["updated_resources"] = 1
                    else:
                        results["failed_resources"] = 1
                        results["errors"].append("Failed to set resource value")
                else:
                    results["failed_resources"] = 1
                    results["errors"].append("Missing required parameters for set_resource_value")
                    
            else:
                results["processed"] = False
                results["errors"].append(f"Unknown command type: {command_type}")
                logger.warning(f"Unknown command type: {command_type}")
            
            logger.info(f"Command processing completed: {results['updated_resources']} successful, "
                       f"{results['failed_resources']} failed")
            
            return results
            
        except Exception as e:
            results["processed"] = False
            results["errors"].append(f"Command processing failed: {e}")
            logger.error(f"Command processing failed: {e}")
            return results
    
    async def _apply_resource_update(self, resource_update: Dict[str, Any]) -> bool:
        """
        Apply a single resource update from cloud with optimistic local update
        
        Args:
            resource_update: Resource update data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Extract resource identifiers
            object_id = resource_update.get("object_id")
            instance_id = resource_update.get("instance_id")
            resource_id = resource_update.get("resource_id")
            value = resource_update.get("value")
            
            if any(v is None for v in [object_id, instance_id, resource_id, value]):
                logger.error("Missing required fields in resource update")
                return False
            
            # Find the resource
            resource = self.find_resource(object_id, instance_id, resource_id)
            if not resource:
                logger.warning(f"Resource not found: object_id={object_id}, instance_id={instance_id}, resource_id={resource_id}")
                return False
            
            # Update the resource value locally immediately (optimistic update)
            old_value = resource.value
            resource.value = float(value)
            
            # Log the immediate local update
            logger.info(f"🔄 Resource Value Changed: {resource.resource_name} = {old_value} → {value}")
            
            # Try to update in Edge Core asynchronously (don't wait for response)
            try:
                # Start the Edge Core update as a background task
                asyncio.create_task(self._update_edge_core_async(resource))
                logger.info(f"📡 Edge Core update initiated for {resource.resource_name} (background)")
            except Exception as e:
                logger.warning(f"Failed to initiate Edge Core update for {resource.resource_name}: {e}")
                # Don't fail the cloud update if Edge Core update fails
            
            # Return success immediately since local update succeeded
            return True
            
        except Exception as e:
            logger.error(f"Error applying resource update: {e}")
            return False
    
    async def _update_edge_core_async(self, resource: ResourceConfig):
        """
        Update resource in Edge Core asynchronously (background task)
        
        Args:
            resource: Resource to update
        """
        try:
            result = await self.edge_core_client.update_resource_value([resource])
            if result:
                logger.info(f"✅ Edge Core update completed for {resource.resource_name}")
            else:
                logger.warning(f"⚠️ Edge Core update failed for {resource.resource_name}")
        except Exception as e:
            logger.warning(f"⚠️ Edge Core update error for {resource.resource_name}: {e}")
    
    async def _add_resource_from_cloud(self, resource_data: Dict[str, Any]) -> bool:
        """
        Add a new resource from cloud configuration
        
        Args:
            resource_data: Resource configuration data
            
        Returns:
            True if addition successful, False otherwise
        """
        try:
            # Create resource configuration
            resource = ResourceConfig(
                object_id=resource_data.get("object_id", 0),
                object_instance_id=resource_data.get("object_instance_id", 0),
                resource_id=resource_data.get("resource_id", 0),
                resource_name=resource_data.get("resource_name"),
                operations=resource_data.get("operations", 3),
                resource_type=resource_data.get("resource_type", "float"),
                value=float(resource_data.get("value", 0.0)),
                periodic_update=resource_data.get("periodic_update", True)
            )
            
            # Add to local resources
            self.local_resources.append(resource)
            
            # Register with Edge Core
            success = await self.register_single_resource(resource)
            
            if success:
                logger.info(f"Successfully added resource from cloud: {resource.resource_name}")
            else:
                # Remove from local resources if Edge Core registration failed
                self.local_resources.remove(resource)
                logger.error(f"Failed to register resource from cloud: {resource.resource_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding resource from cloud: {e}")
            return False
    
    async def _remove_resource_from_cloud(self, resource_data: Dict[str, Any]) -> bool:
        """
        Remove a resource based on cloud configuration
        
        Args:
            resource_data: Resource identification data
            
        Returns:
            True if removal successful, False otherwise
        """
        try:
            object_id = resource_data.get("object_id")
            instance_id = resource_data.get("instance_id")
            resource_id = resource_data.get("resource_id")
            
            if any(v is None for v in [object_id, instance_id, resource_id]):
                logger.error("Missing required fields in resource removal data")
                return False
            
            # Find and remove from local resources
            resource = self.find_resource(object_id, instance_id, resource_id)
            if not resource:
                logger.warning(f"Resource not found for removal: object_id={object_id}, instance_id={instance_id}, resource_id={resource_id}")
                return False
            
            # Remove from Edge Core
            success = await self.delete_single_resource(object_id, instance_id, resource_id)
            
            if success:
                # Remove from local resources
                self.local_resources.remove(resource)
                logger.info(f"Successfully removed resource: {resource.resource_name}")
            else:
                logger.error(f"Failed to remove resource from Edge Core: {resource.resource_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing resource from cloud: {e}")
            return False
    
    async def _modify_resource_from_cloud(self, resource_data: Dict[str, Any]) -> bool:
        """
        Modify a resource based on cloud configuration
        
        Args:
            resource_data: Resource modification data
            
        Returns:
            True if modification successful, False otherwise
        """
        try:
            object_id = resource_data.get("object_id")
            instance_id = resource_data.get("instance_id")
            resource_id = resource_data.get("resource_id")
            
            if any(v is None for v in [object_id, instance_id, resource_id]):
                logger.error("Missing required fields in resource modification data")
                return False
            
            # Find the resource
            resource = self.find_resource(object_id, instance_id, resource_id)
            if not resource:
                logger.warning(f"Resource not found for modification: object_id={object_id}, instance_id={instance_id}, resource_id={resource_id}")
                return False
            
            # Apply modifications
            if "resource_name" in resource_data:
                resource.resource_name = resource_data["resource_name"]
            if "operations" in resource_data:
                resource.operations = resource_data["operations"]
            if "resource_type" in resource_data:
                resource.resource_type = resource_data["resource_type"]
            if "periodic_update" in resource_data:
                resource.periodic_update = resource_data["periodic_update"]
            if "value" in resource_data:
                resource.value = float(resource_data["value"])
            
            # Update in Edge Core
            success = await self.update_single_resource(resource)
            
            if success:
                logger.info(f"Successfully modified resource: {resource.resource_name}")
            else:
                logger.error(f"Failed to modify resource in Edge Core: {resource.resource_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error modifying resource from cloud: {e}")
            return False
    
    async def _set_resource_value(self, object_id: int, instance_id: int, resource_id: int, value: float) -> bool:
        """
        Set a specific resource value (for command handling)
        
        Args:
            object_id: Object ID
            instance_id: Object instance ID
            resource_id: Resource ID
            value: New value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the resource
            resource = self.find_resource(object_id, instance_id, resource_id)
            if not resource:
                logger.warning(f"Resource not found: object_id={object_id}, instance_id={instance_id}, resource_id={resource_id}")
                return False
            
            # Update the value
            old_value = resource.value
            resource.value = float(value)
            
            # Update in Edge Core
            success = await self.update_single_resource(resource)
            
            if success:
                logger.info(f"Successfully set resource {resource.resource_name}: {old_value} -> {value}")
            else:
                # Revert if Edge Core update failed
                resource.value = old_value
                logger.error(f"Failed to set resource value in Edge Core: {resource.resource_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting resource value: {e}")
            return False
    
    def get_cloud_update_stats(self) -> Dict[str, Any]:
        """
        Get cloud update statistics
        
        Returns:
            Dictionary with cloud update statistics
        """
        return self.cloud_update_stats.copy()
