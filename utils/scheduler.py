"""
Scheduler module for handling periodic post updates
"""
import os
import logging
from datetime import datetime
from flask import current_app
from flask_apscheduler import APScheduler
from utils.db import get_db
from utils.markdown_parser import read_markdown_file

# Configure logging
logger = logging.getLogger(__name__)

# Create scheduler
scheduler = APScheduler()

def update_posts_from_files():
    """
    Background job that checks for changes in the posts directory and updates the database.
    This function is called periodically by the scheduler.
    """
    with scheduler.app.app_context():
        try:
            logger.info("Running scheduled post update check")
            posts_dir = current_app.config['POSTS_DIR']
            
            # Get the list of post files and their stats
            md_files = []
            for filename in os.listdir(posts_dir):
                if filename.endswith('.md') and filename != 'about.md':
                    file_path = os.path.join(posts_dir, filename)
                    stat = os.stat(file_path)
                    md_files.append({
                        'filename': filename,
                        'path': file_path,
                        'mtime': stat.st_mtime,
                        'size': stat.st_size
                    })
            
            # Get existing posts from the database
            db = get_db()
            db_posts = db.execute("SELECT id, file, title, date FROM posts").fetchall()
            db_post_files = [post[1] for post in db_posts]
            
            # Check for new or modified files
            for file_info in md_files:
                filename = file_info['filename']
                file_path = file_info['path']
                
                content = read_markdown_file(file_path)
                if not content:
                    logger.warning(f"Empty or unreadable file: {file_path}")
                    continue
                
                # Extract title from markdown - always extract from content
                title = None
                for line in content.splitlines():
                    if line.startswith('# '):
                        title = line.lstrip('#').strip()
                        break
                
                if not title:
                    logger.warning(f"Could not extract title from {file_path}, using filename")
                    title = os.path.splitext(filename)[0].replace('-', ' ').title()
                
                # Use file modification time for date
                date = datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d')
                
                if filename in db_post_files:
                    # Update existing post
                    post = next(post for post in db_posts if post[1] == filename)
                    post_id, _, old_title, old_date = post
                    
                    # Always update title to ensure it's current
                    logger.info(f"Updating post in database: {filename} (ID: {post_id}) - Title: '{old_title}' -> '{title}'")
                    db.execute(
                        "UPDATE posts SET title = ?, date = ? WHERE id = ?",
                        [title, date, post_id]
                    )
                else:
                    # Add new post
                    logger.info(f"Adding new post to database: {filename}")
                    
                    # Get the next ID
                    max_id_result = db.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM posts").fetchone()
                    next_id = max_id_result[0] if max_id_result else 1
                    
                    db.execute(
                        "INSERT INTO posts (id, file, title, date) VALUES (?, ?, ?, ?)",
                        [next_id, filename, title, date]
                    )
            
            # Check for deleted files
            for post in db_posts:
                post_id, filename, _, _ = post
                file_path = os.path.join(posts_dir, filename)
                
                # If file doesn't exist in the filesystem and it's not about.md
                if filename != 'about.md' and not os.path.exists(file_path):
                    logger.info(f"Removing deleted post from database: {filename} (ID: {post_id})")
                    db.execute("DELETE FROM posts WHERE id = ?", [post_id])
                    
            logger.info("Post update check completed")
        except Exception as e:
            logger.error(f"Error in scheduled post update: {e}")

def init_scheduler(app):
    """Initialize the scheduler with the Flask app"""
    # Configure the scheduler
    app.config.setdefault('SCHEDULER_API_ENABLED', False)  # Disable API
    app.config.setdefault('POSTS_CHECK_INTERVAL', 60)  # seconds
    
    # Initialize scheduler
    scheduler.init_app(app)
    scheduler.app = app
    
    # Add job to check for post updates
    scheduler.add_job(
        id='update_posts_job',
        func=update_posts_from_files,
        trigger='interval',
        seconds=app.config['POSTS_CHECK_INTERVAL'],
        max_instances=1
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info(f"Post update scheduler started (interval: {app.config['POSTS_CHECK_INTERVAL']} seconds)")
    
    # Force an immediate post update
    with app.app_context():
        update_posts_from_files() 