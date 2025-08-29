#!/usr/bin/env python3
"""
Schema Registry Service
Provides REST API for managing JSON schemas generated from FDI packages.
"""

from flask import Flask, request, jsonify
from schema_registry import SchemaRegistry
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize schema registry
schema_registry = SchemaRegistry()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'service': 'Schema Registry',
        'status': 'healthy',
        'timestamp': '2025-08-28T15:00:00Z'
    })

@app.route('/api/schemas', methods=['GET'])
def get_schemas():
    """Get all schemas in the registry"""
    try:
        summary = schema_registry.get_registry_summary()
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error getting schemas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schemas/<device_type>', methods=['GET'])
def get_device_schemas(device_type):
    """Get schemas for a specific device type"""
    try:
        versions = schema_registry.get_schema_versions(device_type)
        schemas = {}
        
        for version in versions:
            schema_data = schema_registry.schemas[device_type][version]
            schemas[version] = {
                'schema': schema_data['schema'],
                'registered_at': schema_data['registered_at'],
                'schema_id': schema_data['schema_id']
            }
        
        return jsonify({
            'success': True,
            'device_type': device_type,
            'data': {
                'versions': versions,
                'latest': schema_registry.schemas[device_type].get('latest'),
                'schemas': schemas
            }
        })
    except Exception as e:
        logger.error(f"Error getting device schemas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schemas/<device_type>/<version>', methods=['GET'])
def get_schema(device_type, version):
    """Get a specific schema version"""
    try:
        schema = schema_registry.get_schema(device_type, version)
        if not schema:
            return jsonify({'error': 'Schema not found'}), 404
        
        schema_data = schema_registry.schemas[device_type][version]
        return jsonify({
            'success': True,
            'data': {
                'schema': schema,
                'metadata': {
                    'device_type': device_type,
                    'version': version,
                    'registered_at': schema_data['registered_at'],
                    'schema_id': schema_data['schema_id']
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schemas/<device_type>/latest', methods=['GET'])
def get_latest_schema(device_type):
    """Get the latest schema for a device type"""
    try:
        schema = schema_registry.get_current_schema(device_type)
        if not schema:
            return jsonify({'error': 'Schema not found'}), 404
        
        latest_version = schema_registry.schemas[device_type].get('latest')
        schema_data = schema_registry.schemas[device_type][latest_version]
        
        return jsonify({
            'success': True,
            'data': {
                'schema': schema,
                'metadata': {
                    'device_type': device_type,
                    'version': latest_version,
                    'registered_at': schema_data['registered_at'],
                    'schema_id': schema_data['schema_id']
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting latest schema: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schemas/register', methods=['POST'])
def register_schema():
    """Register a new schema from FDI package"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        schema_id = schema_registry.register_schema_from_fdi(data)
        
        return jsonify({
            'success': True,
            'data': {
                'schema_id': schema_id,
                'message': 'Schema registered successfully'
            }
        })
    except Exception as e:
        logger.error(f"Error registering schema: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schemas/validate', methods=['POST'])
def validate_message():
    """Validate a message against a schema"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', {})
        device_type = data.get('device_type')
        
        if not device_type:
            return jsonify({'error': 'device_type is required'}), 400
        
        validation_result = schema_registry.validate_message(message, device_type)
        
        return jsonify({
            'success': True,
            'data': validation_result
        })
    except Exception as e:
        logger.error(f"Error validating message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schemas/<device_type>/compare', methods=['GET'])
def compare_schemas(device_type):
    """Compare two schema versions"""
    try:
        version1 = request.args.get('v1')
        version2 = request.args.get('v2')
        
        if not version1 or not version2:
            return jsonify({'error': 'Both v1 and v2 parameters are required'}), 400
        
        comparison = schema_registry.compare_schemas(device_type, version1, version2)
        
        if 'error' in comparison:
            return jsonify({'error': comparison['error']}), 404
        
        return jsonify({
            'success': True,
            'data': comparison
        })
    except Exception as e:
        logger.error(f"Error comparing schemas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schemas/stats', methods=['GET'])
def get_validation_stats():
    """Get validation statistics"""
    try:
        device_type = request.args.get('device_type')
        stats = schema_registry.get_validation_stats(device_type)
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting validation stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schemas/<device_type>/<version>/export', methods=['GET'])
def export_schema(device_type, version):
    """Export a schema"""
    try:
        exported = schema_registry.export_schema(device_type, version)
        if not exported:
            return jsonify({'error': 'Schema not found'}), 404
        
        return jsonify({
            'success': True,
            'data': exported
        })
    except Exception as e:
        logger.error(f"Error exporting schema: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Schema Registry Service...")
    app.run(host='0.0.0.0', port=5000, debug=True)
