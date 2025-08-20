from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Application(db.Model):
    """Model for registered applications"""
    __tablename__ = 'applications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    version = db.Column(db.String(20), nullable=True, default='1.0.0')
    developer = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50))
    platform = db.Column(db.String(50))  # web, mobile, desktop, api
    devicetypes = db.Column(db.JSON, default=list)  # array of device type strings
    status = db.Column(db.String(20), default='active')  # active, inactive, pending
    api_key = db.Column(db.String(64), unique=True, default=lambda: str(uuid.uuid4()).replace('-', ''))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': getattr(self, 'version', '1.0.0'),  # Handle missing column gracefully
            'developer': self.developer,
            'contact_email': self.contact_email,
            'category': self.category,
            'platform': self.platform,
            'devicetypes': self.devicetypes or [],
            'status': self.status,
            'api_key': self.api_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Application {self.name}>'
