#!/bin/bash

# Production startup script for Gengar's Blog
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
echo "Starting Gengar's Blog at $(date)"
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

# Ensure database is properly initialized
echo "Running diagnostic check..."
python debug_blog.py || { echo "ERROR: Diagnostic check failed"; exit 1; }

# Check if posts are properly formatted
echo "Verifying post files..."
python verify_posts.py || { echo "WARNING: Post verification had issues"; }

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Start Gunicorn server for production
echo "Starting production server with Gunicorn..."
echo "Logs will be written to $LOGFILE"
gunicorn --workers=3 --bind=0.0.0.0:5000 \
         --log-file="$LOGFILE" --log-level=info \
         --access-logfile="$LOGDIR/access.log" \
         --capture-output \
         --timeout=30 \
         "app:create_app()" 