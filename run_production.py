#!/usr/bin/env python3
"""
Production script for Blog application
Runs the Flask app using Gunicorn
"""
import os
import sys
from app import create_app

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask application
application = create_app()

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5001, debug=False) 