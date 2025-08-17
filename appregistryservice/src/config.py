import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Use absolute path for SQLite database
    DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    DATABASE_PATH = os.path.join(DATABASE_DIR, 'app_registry.db')
    
    # Handle Docker environment with proper absolute path
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('sqlite:////'):
        # Docker absolute path - use as is
        SQLALCHEMY_DATABASE_URI = database_url
    elif database_url:
        # Regular environment variable
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Local development
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @classmethod
    def init_app(cls, app):
        # Ensure data directory exists
        os.makedirs(cls.DATABASE_DIR, exist_ok=True)
