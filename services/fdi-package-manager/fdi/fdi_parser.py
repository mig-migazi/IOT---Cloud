#!/usr/bin/env python3
"""
FDI XML Parser
Parses FDI (Field Device Integration) XML files and converts them to our internal format
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()

class FDIParser:
    """Parser for FDI XML device profiles"""
    
    def __init__(self):
        self.namespace = "http://www.opcfoundation.org/FDI/2011/Device"
    
    def parse_fdi_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse an FDI XML file and return structured data"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Parse the FDI document
            fdi_data = {
                'device_identity': self._parse_device_identity(root),
                'device_type': self._parse_device_type(root),
                'capabilities': self._parse_device_capabilities(root),
                'configuration': self._parse_device_configuration(root),
                'documentation': self._parse_device_documentation(root)
            }
            
            logger.info("FDI file parsed successfully", file_path=file_path)
            return fdi_data
            
        except Exception as e:
            logger.error("Failed to parse FDI file", file_path=file_path, error=str(e))
            return None
    
    def _parse_device_identity(self, root: ET.Element) -> Dict[str, Any]:
        """Parse device identity section"""
        try:
            identity = root.find(f'.//{{{self.namespace}}}DeviceIdentity')
            if identity is None:
                return {}
            
            return {
                'device_type': self._get_text(identity, 'DeviceType'),
                'device_revision': self._get_text(identity, 'DeviceRevision'),
                'device_revision_date': self._get_text(identity, 'DeviceRevisionDate'),
                'device_manufacturer': self._get_text(identity, 'DeviceManufacturer'),
                'device_model': self._get_text(identity, 'DeviceModel'),
                'device_serial_number': self._get_text(identity, 'DeviceSerialNumber'),
                'device_version': self._get_text(identity, 'DeviceVersion'),
                'device_description': self._get_text(identity, 'DeviceDescription')
            }
            
        except Exception as e:
            logger.error("Failed to parse device identity", error=str(e))
            return {}
    
    def _parse_device_type(self, root: ET.Element) -> Dict[str, Any]:
        """Parse device type section"""
        try:
            device_type = root.find(f'.//{{{self.namespace}}}DeviceType')
            if device_type is None:
                return {}
            
            return {
                'device_type_name': self._get_text(device_type, 'DeviceTypeName'),
                'device_type_description': self._get_text(device_type, 'DeviceTypeDescription'),
                'device_type_class': self._get_text(device_type, 'DeviceTypeClass'),
                'device_type_category': self._get_text(device_type, 'DeviceTypeCategory')
            }
            
        except Exception as e:
            logger.error("Failed to parse device type", error=str(e))
            return {}
    
    def _parse_device_capabilities(self, root: ET.Element) -> Dict[str, Any]:
        """Parse device capabilities section"""
        try:
            capabilities = root.find(f'.//{{{self.namespace}}}DeviceCapabilities')
            if capabilities is None:
                return {}
            
            return {
                'communication_protocols': self._parse_communication_protocols(capabilities),
                'device_functions': self._parse_device_functions(capabilities),
                'device_commands': self._parse_device_commands(capabilities),
                'device_alarms': self._parse_device_alarms(capabilities),
                'device_events': self._parse_device_events(capabilities)
            }
            
        except Exception as e:
            logger.error("Failed to parse device capabilities", error=str(e))
            return {}
    
    def _parse_communication_protocols(self, capabilities: ET.Element) -> List[Dict[str, Any]]:
        """Parse communication protocols"""
        try:
            protocols = []
            protocols_elem = capabilities.find(f'.//{{{self.namespace}}}CommunicationProtocols')
            
            if protocols_elem is None:
                return protocols
            
            for protocol in protocols_elem.findall(f'.//{{{self.namespace}}}Protocol'):
                protocol_data = {
                    'name': protocol.get('name', ''),
                    'version': protocol.get('version', ''),
                    'transport': protocol.get('transport', ''),
                    'object_model': self._parse_object_model(protocol)
                }
                protocols.append(protocol_data)
            
            return protocols
            
        except Exception as e:
            logger.error("Failed to parse communication protocols", error=str(e))
            return []
    
    def _parse_object_model(self, protocol: ET.Element) -> Dict[str, Any]:
        """Parse object model for a protocol"""
        try:
            object_model = protocol.find(f'.//{{{self.namespace}}}ObjectModel')
            if object_model is None:
                return {}
            
            objects = []
            for obj in object_model.findall(f'.//{{{self.namespace}}}Object'):
                obj_data = {
                    'id': obj.get('ID', ''),
                    'name': obj.get('name', ''),
                    'instances': self._parse_instances(obj)
                }
                objects.append(obj_data)
            
            return {'objects': objects}
            
        except Exception as e:
            logger.error("Failed to parse object model", error=str(e))
            return {}
    
    def _parse_instances(self, obj: ET.Element) -> List[Dict[str, Any]]:
        """Parse instances for an object"""
        try:
            instances = []
            for instance in obj.findall(f'.//{{{self.namespace}}}Instance'):
                instance_data = {
                    'id': instance.get('ID', ''),
                    'resources': self._parse_resources(instance)
                }
                instances.append(instance_data)
            
            return instances
            
        except Exception as e:
            logger.error("Failed to parse instances", error=str(e))
            return []
    
    def _parse_resources(self, instance: ET.Element) -> List[Dict[str, Any]]:
        """Parse resources for an instance"""
        try:
            resources = []
            for resource in instance.findall(f'.//{{{self.namespace}}}Resource'):
                resource_data = {
                    'id': resource.get('ID', ''),
                    'name': resource.get('name', ''),
                    'type': resource.get('type', ''),
                    'mandatory': resource.get('mandatory', 'false') == 'true',
                    'units': resource.get('units', ''),
                    'range': resource.get('range', ''),
                    'access': resource.get('access', ''),
                    'value_maps': self._parse_value_maps(resource)
                }
                resources.append(resource_data)
            
            return resources
            
        except Exception as e:
            logger.error("Failed to parse resources", error=str(e))
            return []
    
    def _parse_value_maps(self, resource: ET.Element) -> List[Dict[str, Any]]:
        """Parse value maps for a resource"""
        try:
            value_maps = []
            value_maps_elem = resource.find(f'.//{{{self.namespace}}}ValueMap')
            
            if value_maps_elem is None:
                return value_maps
            
            for value in value_maps_elem.findall(f'.//{{{self.namespace}}}Value'):
                value_data = {
                    'id': value.get('ID', ''),
                    'name': value.get('name', '')
                }
                value_maps.append(value_data)
            
            return value_maps
            
        except Exception as e:
            logger.error("Failed to parse value maps", error=str(e))
            return []
    
    def _parse_device_functions(self, capabilities: ET.Element) -> List[Dict[str, Any]]:
        """Parse device functions"""
        try:
            functions = []
            functions_elem = capabilities.find(f'.//{{{self.namespace}}}DeviceFunctions')
            
            if functions_elem is None:
                return functions
            
            for function in functions_elem.findall(f'.//{{{self.namespace}}}Function'):
                function_data = {
                    'name': function.get('name', ''),
                    'description': function.get('description', ''),
                    'parameters': self._parse_function_parameters(function)
                }
                functions.append(function_data)
            
            return functions
            
        except Exception as e:
            logger.error("Failed to parse device functions", error=str(e))
            return []
    
    def _parse_function_parameters(self, function: ET.Element) -> List[Dict[str, Any]]:
        """Parse parameters for a function"""
        try:
            parameters = []
            for param in function.findall(f'.//{{{self.namespace}}}Parameter'):
                param_data = {
                    'name': param.get('name', ''),
                    'type': param.get('type', ''),
                    'units': param.get('units', ''),
                    'default': param.get('default', ''),
                    'range': param.get('range', ''),
                    'valid_values': param.get('valid_values', ''),
                    'description': param.get('description', ''),
                    'optional': param.get('optional', 'false') == 'true'
                }
                parameters.append(param_data)
            
            return parameters
            
        except Exception as e:
            logger.error("Failed to parse function parameters", error=str(e))
            return []
    
    def _parse_device_commands(self, capabilities: ET.Element) -> List[Dict[str, Any]]:
        """Parse device commands"""
        try:
            commands = []
            commands_elem = capabilities.find(f'.//{{{self.namespace}}}DeviceCommands')
            
            if commands_elem is None:
                return commands
            
            for command in commands_elem.findall(f'.//{{{self.namespace}}}Command'):
                command_data = {
                    'name': command.get('name', ''),
                    'description': command.get('description', ''),
                    'parameters': self._parse_function_parameters(command),
                    'response': self._parse_command_response(command)
                }
                commands.append(command_data)
            
            return commands
            
        except Exception as e:
            logger.error("Failed to parse device commands", error=str(e))
            return []
    
    def _parse_command_response(self, command: ET.Element) -> Dict[str, Any]:
        """Parse response for a command"""
        try:
            response = command.find(f'.//{{{self.namespace}}}Response')
            if response is None:
                return {}
            
            return {
                'type': response.get('type', ''),
                'description': response.get('description', '')
            }
            
        except Exception as e:
            logger.error("Failed to parse command response", error=str(e))
            return {}
    
    def _parse_device_alarms(self, capabilities: ET.Element) -> List[Dict[str, Any]]:
        """Parse device alarms"""
        try:
            alarms = []
            alarms_elem = capabilities.find(f'.//{{{self.namespace}}}DeviceAlarms')
            
            if alarms_elem is None:
                return alarms
            
            for alarm in alarms_elem.findall(f'.//{{{self.namespace}}}Alarm'):
                alarm_data = {
                    'name': alarm.get('name', ''),
                    'severity': alarm.get('severity', ''),
                    'description': alarm.get('description', ''),
                    'condition': self._get_text(alarm, 'Condition'),
                    'action': self._get_text(alarm, 'Action')
                }
                alarms.append(alarm_data)
            
            return alarms
            
        except Exception as e:
            logger.error("Failed to parse device alarms", error=str(e))
            return []
    
    def _parse_device_events(self, capabilities: ET.Element) -> List[Dict[str, Any]]:
        """Parse device events"""
        try:
            events = []
            events_elem = capabilities.find(f'.//{{{self.namespace}}}DeviceEvents')
            
            if events_elem is None:
                return events
            
            for event in events_elem.findall(f'.//{{{self.namespace}}}Event'):
                event_data = {
                    'name': event.get('name', ''),
                    'description': event.get('description', ''),
                    'parameters': self._parse_function_parameters(event)
                }
                events.append(event_data)
            
            return events
            
        except Exception as e:
            logger.error("Failed to parse device events", error=str(e))
            return []
    
    def _parse_device_configuration(self, root: ET.Element) -> Dict[str, Any]:
        """Parse device configuration section"""
        try:
            config = root.find(f'.//{{{self.namespace}}}DeviceConfiguration')
            if config is None:
                return {}
            
            return {
                'default_settings': self._parse_default_settings(config),
                'configuration_profiles': self._parse_configuration_profiles(config)
            }
            
        except Exception as e:
            logger.error("Failed to parse device configuration", error=str(e))
            return {}
    
    def _parse_default_settings(self, config: ET.Element) -> List[Dict[str, Any]]:
        """Parse default settings"""
        try:
            settings = []
            default_settings = config.find(f'.//{{{self.namespace}}}DefaultSettings')
            
            if default_settings is None:
                return settings
            
            for setting in default_settings.findall(f'.//{{{self.namespace}}}Setting'):
                setting_data = {
                    'name': setting.get('name', ''),
                    'value': setting.get('value', ''),
                    'units': setting.get('units', '')
                }
                settings.append(setting_data)
            
            return settings
            
        except Exception as e:
            logger.error("Failed to parse default settings", error=str(e))
            return []
    
    def _parse_configuration_profiles(self, config: ET.Element) -> List[Dict[str, Any]]:
        """Parse configuration profiles"""
        try:
            profiles = []
            profiles_elem = config.find(f'.//{{{self.namespace}}}ConfigurationProfiles')
            
            if profiles_elem is None:
                return profiles
            
            for profile in profiles_elem.findall(f'.//{{{self.namespace}}}Profile'):
                profile_data = {
                    'name': profile.get('name', ''),
                    'description': profile.get('description', ''),
                    'settings': self._parse_profile_settings(profile)
                }
                profiles.append(profile_data)
            
            return profiles
            
        except Exception as e:
            logger.error("Failed to parse configuration profiles", error=str(e))
            return []
    
    def _parse_profile_settings(self, profile: ET.Element) -> List[Dict[str, Any]]:
        """Parse settings for a profile"""
        try:
            settings = []
            for setting in profile.findall(f'.//{{{self.namespace}}}Setting'):
                setting_data = {
                    'name': setting.get('name', ''),
                    'value': setting.get('value', ''),
                    'units': setting.get('units', '')
                }
                settings.append(setting_data)
            
            return settings
            
        except Exception as e:
            logger.error("Failed to parse profile settings", error=str(e))
            return []
    
    def _parse_device_documentation(self, root: ET.Element) -> Dict[str, Any]:
        """Parse device documentation section"""
        try:
            docs = root.find(f'.//{{{self.namespace}}}DeviceDocumentation')
            if docs is None:
                return {}
            
            return {
                'manuals': self._parse_documentation_items(docs, 'Manual'),
                'data_sheets': self._parse_documentation_items(docs, 'DataSheet')
            }
            
        except Exception as e:
            logger.error("Failed to parse device documentation", error=str(e))
            return {}
    
    def _parse_documentation_items(self, docs: ET.Element, item_type: str) -> List[Dict[str, Any]]:
        """Parse documentation items (manuals or data sheets)"""
        try:
            items = []
            for item in docs.findall(f'.//{{{self.namespace}}}{item_type}'):
                item_data = {
                    'name': item.get('name', ''),
                    'version': item.get('version', ''),
                    'language': item.get('language', ''),
                    'format': item.get('format', '')
                }
                items.append(item_data)
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to parse {item_type.lower()}s", error=str(e))
            return []
    
    def _get_text(self, parent: ET.Element, tag_name: str) -> str:
        """Get text content of a child tag"""
        try:
            child = parent.find(f'.//{{{self.namespace}}}{tag_name}')
            return child.text if child is not None else ''
        except Exception:
            return ''

def parse_fdi_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Convenience function to parse an FDI file"""
    parser = FDIParser()
    return parser.parse_fdi_file(file_path)
