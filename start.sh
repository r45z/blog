#!/bin/bash

# Production startup script for CoreBlog
# This script runs the application in production mode

set -e  # Exit immediately if a command exits with a non-zero status

# Set up logging
LOGDIR="logs"
LOGFILE="$LOGDIR/app.log"

# Create logs directory if it doesn't exist
if [ ! -d "$LOGDIR" ]; then
    echo "Creating logs directory..."
    mkdir -p "$LOGDIR"
fi

echo "--------------------------------------------"
echo "Starting CoreBlog at $(date)"
echo "--------------------------------------------"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "WARNING: Virtual environment not found. Creating one..."
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

# Start Flask server for production
echo "Starting production server with Flask..."
export FLASK_APP=app:create_app
export FLASK_ENV=production
export PYTHONDONTWRITEBYTECODE=1

echo "Visit http://localhost:5001 in your browser"
echo "Press CTRL+C to stop the server"
python -m flask run --host=0.0.0.0 --port=5001 