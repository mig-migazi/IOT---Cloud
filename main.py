#!/usr/bin/env python3
"""
Main entry point for Application Registry Service
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from src.models import db
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)
