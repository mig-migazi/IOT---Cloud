from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from marshmallow import ValidationError
from .config import Config
from .models import db, Application
from .schemas import ApplicationRegistrationSchema, ApplicationUpdateSchema, ApplicationResponseSchema

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize configuration
    Config.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    CORS(app)
    
    # Initialize schemas
    registration_schema = ApplicationRegistrationSchema()
    update_schema = ApplicationUpdateSchema()
    response_schema = ApplicationResponseSchema()
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'service': 'Application Registry Service'})
    
    @app.route('/api/applications', methods=['POST'])
    def register_application():
        """Register a new application"""
        try:
            # Validate input data
            data = registration_schema.load(request.json)
            
            # Check if application with same name already exists
            existing_app = Application.query.filter_by(name=data['name']).first()
            if existing_app:
                return jsonify({
                    'error': 'Application with this name already exists',
                    'code': 'DUPLICATE_NAME'
                }), 409
            
            # Create new application
            app_instance = Application(**data)
            db.session.add(app_instance)
            db.session.commit()
            
            return jsonify({
                'message': 'Application registered successfully',
                'application': response_schema.dump(app_instance.to_dict())
            }), 201
            
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @app.route('/api/applications', methods=['GET'])
    def get_applications():
        """Get all registered applications"""
        try:
            # Query parameters for filtering
            status = request.args.get('status')
            platform = request.args.get('platform')
            category = request.args.get('category')
            
            query = Application.query
            
            if status:
                query = query.filter_by(status=status)
            if platform:
                query = query.filter_by(platform=platform)
            if category:
                query = query.filter_by(category=category)
            
            applications = query.all()
            
            return jsonify({
                'applications': [response_schema.dump(app.to_dict()) for app in applications],
                'count': len(applications)
            })
            
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @app.route('/api/applications/<app_id>', methods=['GET'])
    def get_application(app_id):
        """Get a specific application by ID"""
        try:
            app_instance = Application.query.get(app_id)
            if not app_instance:
                return jsonify({
                    'error': 'Application not found'
                }), 404
            
            return jsonify({
                'application': response_schema.dump(app_instance.to_dict())
            })
            
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @app.route('/api/applications/<app_id>', methods=['PUT'])
    def update_application(app_id):
        """Update an existing application"""
        try:
            app_instance = Application.query.get(app_id)
            if not app_instance:
                return jsonify({
                    'error': 'Application not found'
                }), 404
            
            # Validate input data
            data = update_schema.load(request.json)
            
            # Check if name is being changed and if it conflicts
            if 'name' in data and data['name'] != app_instance.name:
                existing_app = Application.query.filter_by(name=data['name']).first()
                if existing_app:
                    return jsonify({
                        'error': 'Application with this name already exists',
                        'code': 'DUPLICATE_NAME'
                    }), 409
            
            # Update application
            for key, value in data.items():
                setattr(app_instance, key, value)
            
            db.session.commit()
            
            return jsonify({
                'message': 'Application updated successfully',
                'application': response_schema.dump(app_instance.to_dict())
            })
            
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @app.route('/api/applications/<app_id>', methods=['DELETE'])
    def delete_application(app_id):
        """Delete an application"""
        try:
            app_instance = Application.query.get(app_id)
            if not app_instance:
                return jsonify({
                    'error': 'Application not found'
                }), 404
            
            db.session.delete(app_instance)
            db.session.commit()
            
            return jsonify({
                'message': 'Application deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @app.route('/api/applications/<app_id>/regenerate-key', methods=['POST'])
    def regenerate_api_key(app_id):
        """Regenerate API key for an application"""
        try:
            app_instance = Application.query.get(app_id)
            if not app_instance:
                return jsonify({
                    'error': 'Application not found'
                }), 404
            
            # Generate new API key
            import uuid
            app_instance.api_key = str(uuid.uuid4()).replace('-', '')
            db.session.commit()
            
            return jsonify({
                'message': 'API key regenerated successfully',
                'api_key': app_instance.api_key
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method not allowed'}), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)
