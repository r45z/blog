#!/bin/bash

# Development startup script for CoreBlog
# This script runs the application in development mode with hot-reloading

set -e  # Exit immediately if a command exits with a non-zero status

echo "--------------------------------------------"
echo "Starting CoreBlog - DEVELOPMENT MODE"
echo "$(date)"
echo "--------------------------------------------"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Run Flask development server
echo "Starting development server with debug mode enabled..."
export FLASK_APP=app:create_app
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONDONTWRITEBYTECODE=1  # Don't create .pyc files

# Start the Flask development server
echo "Visit http://localhost:5043 in your browser"
echo "Press CTRL+C to stop the server"
flask run --host=0.0.0.0 --port=5043
