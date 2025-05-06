#!/usr/bin/env python3

"""
Script to scan posts directory and update the database with all markdown posts.
Run this script to ensure your blog database is updated with all posts.

Usage:
    python update_posts.py [posts_directory]
"""

import os
import sys
import logging
from datetime import datetime
import re
from flask import Flask
from utils.db import get_db
from utils.markdown_parser import read_markdown_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("post_updater")

# Files to exclude from regular posts
EXCLUDED_FILES = ['about.md']

def create_flask_app():
    """Create Flask app for correct DB access"""
    import app
    return app.create_app()

def get_posts_dir(flask_app):
    """Get the posts directory from Flask app config"""
    posts_dir = flask_app.config['POSTS_DIR']
    logger.info(f"Posts directory from Flask config: {posts_dir}")
    return posts_dir

def extract_title(content):
    """Extract title from markdown content (first heading)"""
    if not content:
        return None
    
    lines = content.splitlines()
    if not lines:
        return None
    
    # Find the first line that starts with # (markdown heading)
    for line in lines:
        if line.startswith('# '):
            return line.lstrip('#').strip()
    
    # If no title found, return None and let the caller handle it
    return None

def extract_date(content, filepath):
    """Extract date from markdown content or use file modification date as fallback"""
    # First try to find a date in the content with format YYYY-MM-DD
    if content:
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        date_matches = re.findall(date_pattern, content[:500])  # Look only in first 500 chars
        if date_matches:
            return date_matches[0]
    
    # Fallback to file modification time
    return datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')

def update_post(filepath, db):
    """Update or add a single post to the database"""
    filename = os.path.basename(filepath)
    logger.info(f"Updating post: {filename}")
    
    # Read the file content
    content = read_markdown_file(filepath)
    if not content:
        logger.error(f"Failed to read or empty file: {filepath}")
        return False
    
    # Extract title and date
    title = extract_title(content)
    if not title:
        logger.warning(f"Could not extract title from {filepath}, using filename")
        title = os.path.splitext(filename)[0].replace('-', ' ').title()
    
    date = extract_date(content, filepath)
    logger.info(f"Extracted metadata: title='{title}', date='{date}'")
    
    # Check if post already exists in database
    result = db.execute("SELECT id, title FROM posts WHERE file = ?", [filename]).fetchone()
    
    if result:
        # Update existing post
        post_id = result[0]
        old_title = result[1]
        logger.info(f"Updating existing post with ID {post_id} - Title: '{old_title}' -> '{title}'")
        db.execute(
            "UPDATE posts SET title = ?, date = ? WHERE id = ?",
            [title, date, post_id]
        )
    else:
        # Add new post with auto-incrementing ID
        logger.info(f"Adding new post: {title}")
        try:
            # Get the next ID value
            max_id_result = db.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM posts").fetchone()
            next_id = max_id_result[0] if max_id_result else 1
            
            db.execute(
                "INSERT INTO posts (id, file, title, date) VALUES (?, ?, ?, ?)",
                [next_id, filename, title, date]
            )
        except Exception as e:
            logger.error(f"Error adding post to database: {e}")
            return False
    
    return True

def remove_deleted_posts(db, existing_files, posts_dir):
    """Remove posts from database that no longer exist as files"""
    db_posts = db.execute("SELECT id, file FROM posts").fetchall()
    
    # Check each post in the database
    for post_id, post_file in db_posts:
        # If the file doesn't exist in the filesystem
        file_path = os.path.join(posts_dir, post_file)
        if post_file not in existing_files or not os.path.exists(file_path):
            logger.info(f"Removing deleted post from database: {post_file} (ID: {post_id})")
            db.execute("DELETE FROM posts WHERE id = ?", [post_id])
            
    # Return True if any posts were deleted
    return True

def update_all_posts(posts_dir=None):
    """Update all markdown files in the posts directory to the database"""
    # Create Flask app and use its application context
    flask_app = create_flask_app()
    
    with flask_app.app_context():
        if posts_dir is None:
            posts_dir = get_posts_dir(flask_app)
            
        logger.info(f"Updating all posts in directory: {posts_dir}")
        
        # Check if directory exists
        if not os.path.exists(posts_dir):
            logger.error(f"Posts directory does not exist: {posts_dir}")
            return False
        
        # Get all markdown files, excluding specific files
        all_markdown_files = [f for f in os.listdir(posts_dir) if f.endswith('.md')]
        markdown_files = [f for f in all_markdown_files if f not in EXCLUDED_FILES]
        
        logger.info(f"Found {len(all_markdown_files)} markdown files, processing {len(markdown_files)} (excluding {', '.join(EXCLUDED_FILES)})")
        
        # Open database connection through Flask context
        db = get_db()
        
        # Start a transaction
        db.execute("BEGIN TRANSACTION")
        
        success = True
        try:
            # Update each file
            for filename in markdown_files:
                file_path = os.path.join(posts_dir, filename)
                if not update_post(file_path, db):
                    success = False
                    raise Exception(f"Failed to update post: {filename}")
                else:
                    logger.info(f"Successfully updated post: {filename}")
            
            # Remove posts from database that don't exist as files
            # Include excluded files in the existence check so they don't get deleted
            remove_deleted_posts(db, all_markdown_files, posts_dir)
            
            # Commit the transaction if all operations succeeded
            logger.info("Committing changes to database")
            db.execute("COMMIT")
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            # Only try to rollback if we're in a transaction
            try:
                logger.warning("Rolling back changes")
                db.execute("ROLLBACK")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
            success = False
    
    return success

if __name__ == "__main__":
    # Get posts directory from command line argument or use default
    posts_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    if update_all_posts(posts_dir):
        logger.info("All posts updated successfully!")
        sys.exit(0)
    else:
        logger.error("Some posts failed to update")
        sys.exit(1) 