#!/bin/bash

# Development startup script for Gengar's Blog
# This script runs the application in development mode with hot-reloading

set -e  # Exit immediately if a command exits with a non-zero status

echo "--------------------------------------------"
echo "Starting Gengar's Blog - DEVELOPMENT MODE"
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

# Ensure database is properly initialized
echo "Running diagnostic check..."
python debug_blog.py || { echo "WARNING: Diagnostic check had issues, but continuing..."; }

# Check if posts are properly formatted
echo "Verifying post files..."
python verify_posts.py || { echo "WARNING: Post verification had issues"; }

# Run Flask development server
echo "Starting development server with debug mode enabled..."
export FLASK_APP=app:create_app
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONDONTWRITEBYTECODE=1  # Don't create .pyc files

# Start the Flask development server
echo "Visit http://localhost:5000 in your browser"
echo "Press CTRL+C to stop the server"
flask run --host=0.0.0.0 --port=5000 