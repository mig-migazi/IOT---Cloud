#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app
from src.models import db

# Create the Flask app
app = create_app()

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
