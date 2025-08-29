import json
import jsonschema
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SchemaRegistry:
    """
    Schema Registry for managing JSON schemas generated from FDI packages.
    Provides versioning, validation, and schema evolution capabilities.
    """
    
    def __init__(self):
        self.schemas: Dict[str, Dict[str, Any]] = {}  # device_type -> version -> schema
        self.fdi_mappings: Dict[str, str] = {}  # device_type -> latest_fdi_version
        self.validation_history: List[Dict] = []
        
    def register_schema_from_fdi(self, fdi_package: Dict) -> str:
        """
        Generate and register JSON schema from FDI package.
        
        Args:
            fdi_package: FDI package dictionary
            
        Returns:
            str: Schema ID for the registered schema
        """
        try:
            logger.info(f"Received FDI package with keys: {list(fdi_package.keys())}")
            
            device_type = fdi_package.get('device_type')
            version = fdi_package.get('version', '1.0.0')
            
            logger.info(f"Device type: {type(device_type)}, Version: {version}")
            
            if not device_type:
                raise ValueError("FDI package must have device_type")
            
            # Check if device_type is a dictionary (nested structure)
            if isinstance(device_type, dict):
                logger.info(f"Device type is dict with keys: {list(device_type.keys())}")
                # Extract the actual device type from the nested structure
                actual_device_type = device_type.get('device_type')
                if actual_device_type:
                    device_type = actual_device_type
                    logger.info(f"Extracted device type from nested structure: {device_type}")
                else:
                    raise ValueError("Nested device_type structure is invalid")
            
            logger.info(f"About to call _fdi_to_json_schema")
            # Generate JSON schema from FDI package
            schema = self._fdi_to_json_schema(fdi_package)
            logger.info(f"Schema generated successfully")
            
            logger.info(f"About to call _register_schema")
            # Register the schema
            schema_id = self._register_schema(device_type, version, schema, fdi_package)
            logger.info(f"Schema registered with ID: {schema_id}")
            
            # Update FDI mapping
            self.fdi_mappings[device_type] = version
            
            logger.info(f"Registered schema for {device_type} v{version}")
            return schema_id
            
        except Exception as e:
            logger.error(f"Failed to register schema from FDI package: {e}")
            raise
    
    def _fdi_to_json_schema(self, fdi_package: Dict) -> Dict:
        """
        Convert FDI package to JSON schema.
        
        Args:
            fdi_package: FDI package dictionary
            
        Returns:
            Dict: JSON schema
        """
        try:
            logger.info(f"Starting _fdi_to_json_schema with package keys: {list(fdi_package.keys())}")
            
            # Handle nested FDI package structure
            device_type_info = fdi_package.get('device_type', {})
            
            # Check if device_type is a nested structure (from dataclass asdict)
            if isinstance(device_type_info, dict):
                # Extract the actual device type and parameters from the nested structure
                actual_device_type = device_type_info.get('device_type', 'unknown')
                parameters = device_type_info.get('parameters', [])
                commands = device_type_info.get('commands', [])
                version = fdi_package.get('version', '1.0.0')
                
                logger.info(f"Extracted from nested structure: device_type={actual_device_type}, version={version}, parameters={len(parameters)}")
            else:
                # Direct structure (fallback)
                actual_device_type = device_type_info
                parameters = fdi_package.get('parameters', [])
                commands = fdi_package.get('commands', [])
                version = fdi_package.get('version', '1.0.0')
                
                logger.info(f"Direct structure: device_type={actual_device_type}, version={version}, parameters={len(parameters)}")
            
            # Build schema properties from FDI parameters
            properties = {}
            required = []
            
            logger.info(f"Processing {len(parameters)} parameters")
            
            for i, param in enumerate(parameters):
                logger.info(f"Processing parameter {i} of type {type(param)}")
                
                # Handle nested parameter structure
                if isinstance(param, dict):
                    param_name = param.get('name')
                    param_type = param.get('data_type', 'string')
                    param_required = param.get('required', False)
                    param_description = param.get('description', '')
                    param_unit = param.get('unit', '')
                else:
                    logger.warning(f"Parameter {i} is not a dict: {type(param)}")
                    continue
                
                if param_name:
                    # Map FDI data types to JSON schema types
                    json_type = self._map_fdi_type_to_json(param_type)
                    
                    properties[param_name] = {
                        "type": json_type,
                        "description": param_description
                    }
                    
                    # Add unit if specified
                    if param_unit:
                        properties[param_name]["unit"] = param_unit
                    
                    # Add to required fields if marked as required
                    if param_required:
                        required.append(param_name)
            
            logger.info(f"Built properties: {properties}")
            logger.info(f"Required fields: {required}")
            
            # Build the complete schema
            schema = {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
                "metadata": {
                    "device_type": actual_device_type,
                    "fdi_version": version,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source": "fdi_package"
                }
            }
            
            logger.info(f"Generated schema: {schema}")
            return schema
            
        except Exception as e:
            logger.error(f"Error in _fdi_to_json_schema: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _map_fdi_type_to_json(self, fdi_type: str) -> str:
        """
        Map FDI data types to JSON schema types.
        
        Args:
            fdi_type: FDI data type string
            
        Returns:
            str: JSON schema type
        """
        type_mapping = {
            'float': 'number',
            'double': 'number',
            'integer': 'integer',
            'int32': 'integer',
            'int64': 'integer',
            'string': 'string',
            'boolean': 'boolean',
            'bool': 'boolean',
            'array': 'array',
            'object': 'object'
        }
        
        return type_mapping.get(fdi_type.lower(), 'string')
    
    def _register_schema(self, device_type: str, version: str, schema: Dict, fdi_package: Dict) -> str:
        """
        Register a schema in the registry.
        
        Args:
            device_type: Type of device
            version: Schema version
            schema: JSON schema
            fdi_package: Source FDI package
            
        Returns:
            str: Schema ID
        """
        try:
            logger.info(f"_register_schema: Starting with device_type={device_type}, version={version}")
            
            if device_type not in self.schemas:
                logger.info(f"_register_schema: Creating new device type entry for {device_type}")
                self.schemas[device_type] = {}
            
            logger.info(f"_register_schema: Storing schema for {device_type} v{version}")
            # Store schema with version
            self.schemas[device_type][version] = {
                'schema': schema,
                'fdi_package': fdi_package,
                'registered_at': datetime.now(timezone.utc).isoformat(),
                'schema_id': f"{device_type}_{version}"
            }
            
            logger.info(f"_register_schema: Updating latest version to {version}")
            # Update latest version
            self.schemas[device_type]['latest'] = version
            
            schema_id = f"{device_type}_{version}"
            logger.info(f"_register_schema: Successfully registered schema with ID: {schema_id}")
            return schema_id
            
        except Exception as e:
            logger.error(f"_register_schema: Error occurred: {e}")
            logger.error(f"_register_schema: Error type: {type(e)}")
            import traceback
            logger.error(f"_register_schema: Full traceback: {traceback.format_exc()}")
            raise
    
    def get_schema(self, device_type: str, version: Optional[str] = None) -> Optional[Dict]:
        """
        Get schema for device type and version.
        
        Args:
            device_type: Type of device
            version: Schema version (None for latest)
            
        Returns:
            Dict: Schema or None if not found
        """
        if device_type not in self.schemas:
            return None
        
        if version is None:
            version = self.schemas[device_type].get('latest')
        
        if version and version in self.schemas[device_type]:
            return self.schemas[device_type][version]['schema']
        
        return None
    
    def get_current_schema(self, device_type: str) -> Optional[Dict]:
        """
        Get the latest schema for a device type.
        
        Args:
            device_type: Type of device
            
        Returns:
            Dict: Latest schema or None if not found
        """
        return self.get_schema(device_type, None)
    
    def validate_message(self, message: Dict, device_type: str) -> Dict:
        """
        Validate a message against the current schema.
        
        Args:
            message: Message to validate
            device_type: Type of device
            
        Returns:
            Dict: Validation result with success status and details
        """
        try:
            schema = self.get_current_schema(device_type)
            
            if not schema:
                return {
                    'valid': False,
                    'error': f'No schema found for device type: {device_type}',
                    'device_type': device_type,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # Validate against schema
            jsonschema.validate(message, schema)
            
            # Record successful validation
            validation_record = {
                'valid': True,
                'device_type': device_type,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'schema_version': self.schemas[device_type].get('latest')
            }
            self.validation_history.append(validation_record)
            
            return validation_record
            
        except jsonschema.ValidationError as e:
            # Record validation failure
            validation_record = {
                'valid': False,
                'error': str(e),
                'device_type': device_type,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'schema_version': self.schemas[device_type].get('latest'),
                'validation_path': list(e.path),
                'validation_message': e.message
            }
            self.validation_history.append(validation_record)
            
            return validation_record
            
        except Exception as e:
            # Record unexpected error
            validation_record = {
                'valid': False,
                'error': f'Unexpected error during validation: {str(e)}',
                'device_type': device_type,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            self.validation_history.append(validation_record)
            
            return validation_record
    
    def get_schema_versions(self, device_type: str) -> List[str]:
        """
        Get all available versions for a device type.
        
        Args:
            device_type: Type of device
            
        Returns:
            List[str]: List of available versions
        """
        try:
            if device_type not in self.schemas:
                return []
            
            device_schemas = self.schemas[device_type]
            
            # Filter out non-string keys and 'latest' key
            versions = []
            for key in device_schemas.keys():
                if isinstance(key, str) and key != 'latest':
                    try:
                        # Validate that it's a valid version string
                        if '.' in key:
                            versions.append(key)
                    except:
                        continue
            
            # Sort versions safely
            try:
                return sorted(versions, key=lambda x: [int(n) for n in x.split('.')])
            except:
                # Fallback to simple string sorting
                return sorted(versions)
                
        except Exception as e:
            logger.error(f"Error getting schema versions: {e}")
            return []
    
    def compare_schemas(self, device_type: str, version1: str, version2: str) -> Dict:
        """
        Compare two schema versions for a device type.
        
        Args:
            device_type: Type of device
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Dict: Comparison result with differences
        """
        schema1 = self.get_schema(device_type, version1)
        schema2 = self.get_schema(device_type, version2)
        
        if not schema1 or not schema2:
            return {
                'error': f'One or both schemas not found: {version1}, {version2}'
            }
        
        # Simple comparison - in production, use more sophisticated diffing
        props1 = schema1.get('properties', {})
        props2 = schema2.get('properties', {})
        
        # Convert to sets for comparison (keys are strings, so they're hashable)
        props1_keys = set(props1.keys())
        props2_keys = set(props2.keys())
        
        added_fields = props2_keys - props1_keys
        removed_fields = props1_keys - props2_keys
        changed_fields = []
        
        # Check for changed fields
        for field in props1_keys & props2_keys:
            # Convert to JSON strings for comparison to avoid unhashable dict issues
            try:
                if json.dumps(props1[field], sort_keys=True) != json.dumps(props2[field], sort_keys=True):
                    changed_fields.append({
                        'field': field,
                        'old': props1[field],
                        'new': props2[field]
                    })
            except (TypeError, ValueError):
                # Fallback to simple string comparison
                if str(props1[field]) != str(props2[field]):
                    changed_fields.append({
                        'field': field,
                        'old': props1[field],
                        'new': props2[field]
                    })
        
        return {
            'device_type': device_type,
            'version1': version1,
            'version2': version2,
            'added_fields': list(added_fields),
            'removed_fields': list(removed_fields),
            'changed_fields': changed_fields,
            'breaking_changes': len(removed_fields) > 0 or any(
                'required' in change['old'] != 'required' in change['new'] 
                for change in changed_fields
            )
        }
    
    def get_validation_stats(self, device_type: Optional[str] = None) -> Dict:
        """
        Get validation statistics.
        
        Args:
            device_type: Optional device type filter
            
        Returns:
            Dict: Validation statistics
        """
        if not self.validation_history:
            return {
                'total_validations': 0,
                'success_rate': 0.0,
                'device_types': {}
            }
        
        # Filter by device type if specified
        history = self.validation_history
        if device_type:
            history = [h for h in history if h.get('device_type') == device_type]
        
        total = len(history)
        successful = len([h for h in history if h.get('valid', False)])
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        # Group by device type
        device_stats = {}
        for record in history:
            dt = record.get('device_type', 'unknown')
            if dt not in device_stats:
                device_stats[dt] = {'total': 0, 'successful': 0}
            
            device_stats[dt]['total'] += 1
            if record.get('valid', False):
                device_stats[dt]['successful'] += 1
        
        # Calculate success rates for each device type
        for dt in device_stats:
            total_dt = device_stats[dt]['total']
            successful_dt = device_stats[dt]['successful']
            device_stats[dt]['success_rate'] = (successful_dt / total_dt * 100) if total_dt > 0 else 0.0
        
        return {
            'total_validations': total,
            'success_rate': success_rate,
            'device_types': device_stats
        }
    
    def export_schema(self, device_type: str, version: str) -> Optional[Dict]:
        """
        Export a schema for external use.
        
        Args:
            device_type: Type of device
            version: Schema version
            
        Returns:
            Dict: Exported schema or None if not found
        """
        schema_data = self.schemas.get(device_type, {}).get(version)
        if not schema_data:
            return None
        
        return {
            'schema': schema_data['schema'],
            'metadata': {
                'device_type': device_type,
                'version': version,
                'exported_at': datetime.now(timezone.utc).isoformat(),
                'source': 'fdi_package'
            }
        }
    
    def get_registry_summary(self) -> Dict:
        """
        Get a summary of the entire registry.
        
        Returns:
            Dict: Registry summary
        """
        summary = {
            'total_device_types': len(self.schemas),
            'total_schemas': sum(len([k for k in v.keys() if k != 'latest']) for v in self.schemas.values()),
            'device_types': {}
        }
        
        for device_type, versions in self.schemas.items():
            latest = versions.get('latest')
            version_count = len([k for k in versions.keys() if k != 'latest'])
            
            summary['device_types'][device_type] = {
                'latest_version': latest,
                'version_count': version_count,
                'versions': [k for k in versions.keys() if k != 'latest']
            }
        
        return summary
