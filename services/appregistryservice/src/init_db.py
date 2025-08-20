#!/usr/bin/env python3
"""
Database initialization script - direct SQL approach to avoid circular imports
"""

import os
import sqlite3
import uuid
from datetime import datetime

def init_database():
    """Initialize the database with tables"""
    # Get database path
    db_path = '/app/data/app_registry.db'
    
    print(f"Creating database at: {db_path}")
    
    # Ensure directory exists
    os.makedirs('/app/data', exist_ok=True)
    
    # Create SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing table if it exists (to ensure correct schema)
    cursor.execute('DROP TABLE IF EXISTS applications')
    
    # Create applications table with ALL required columns
    cursor.execute('''
        CREATE TABLE applications (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            version TEXT NOT NULL,
            developer TEXT NOT NULL,
            contact_email TEXT NOT NULL,
            category TEXT,
            platform TEXT,
            devicetypes TEXT NOT NULL,
            status TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    ''')
    
    # Create some test applications
    test_apps = [
        (str(uuid.uuid4()), 'Smart Grid Monitor', 'Monitors smart grid performance', '1.0.0', 
         'IoT Solutions Inc', 'dev@iotsolutions.com', 'monitoring', 'web', 
         '["smart_breaker"]', 'active', str(uuid.uuid4()).replace('-', ''), 
         datetime.now().isoformat(), datetime.now().isoformat()),
        (str(uuid.uuid4()), 'Energy Analytics', 'Energy consumption analytics', '2.1.0', 
         'Energy Corp', 'analytics@energycorp.com', 'analytics', 'mobile', 
         '["smart_meter"]', 'active', str(uuid.uuid4()).replace('-', ''), 
         datetime.now().isoformat(), datetime.now().isoformat()),
        (str(uuid.uuid4()), 'Environmental Tracker', 'Environmental monitoring', '1.5.0', 
         'EcoTech', 'support@ecotech.com', 'monitoring', 'desktop', 
         '["environmental_sensor"]', 'active', str(uuid.uuid4()).replace('-', ''), 
         datetime.now().isoformat(), datetime.now().isoformat())
    ]
    
    for app in test_apps:
        cursor.execute('''
            INSERT OR IGNORE INTO applications 
            (id, name, description, version, developer, contact_email, category, platform, devicetypes, status, api_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', app)
    
    conn.commit()
    conn.close()
    
    print("✓ Database created successfully!")
    print("✓ Test applications added!")

if __name__ == '__main__':
    init_database()
