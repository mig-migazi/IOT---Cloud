#!/usr/bin/env python3
"""
Database initialization script
Run this script to create the database tables
"""

from .app import create_app
from .models import db

def init_database():
    """Initialize the database with tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Print table information
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {', '.join(tables)}")

if __name__ == '__main__':
    init_database()
