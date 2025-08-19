#!/usr/bin/env python3
"""
Production-ready application runner
"""

from .app import create_app
from .models import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=5000)
