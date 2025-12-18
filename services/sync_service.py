"""
Sync service - handles syncing posts from filesystem to database
"""
import os
import logging
from flask import current_app
from utils.db import get_db
from utils.markdown_parser import read_markdown_file, extract_metadata

logger = logging.getLogger(__name__)

# Files to exclude from regular posts
EXCLUDED_FILES = {'about.md'}


def sync_posts_to_db(posts_dir: str = None) -> bool:
    """
    Sync all markdown files in posts directory to database.
    Adds new posts, updates existing ones, and removes deleted ones.
    
    Args:
        posts_dir: Optional path to posts directory (defaults to app config)
    
    Returns:
        True if sync completed successfully, False otherwise
    """
    try:
        if posts_dir is None:
            posts_dir = current_app.config['POSTS_DIR']
        
        logger.debug(f"Syncing posts from: {posts_dir}")
        
        if not os.path.exists(posts_dir):
            logger.error(f"Posts directory does not exist: {posts_dir}")
            return False
        
        # Get all markdown files
        all_md_files = {f for f in os.listdir(posts_dir) if f.endswith('.md')}
        files_to_sync = all_md_files - EXCLUDED_FILES
        
        db = get_db()
        
        # Get existing posts from database
        db_posts = {row[1]: row for row in db.execute(
            "SELECT id, file, title, date FROM posts"
        ).fetchall()}
        
        # Add or update posts
        for filename in files_to_sync:
            filepath = os.path.join(posts_dir, filename)
            _add_or_update_post(filepath, filename, db, db_posts.get(filename))
        
        # Remove deleted posts
        _remove_deleted_posts(db, db_posts, all_md_files, posts_dir)
        
        logger.debug("Post sync completed")
        return True
        
    except Exception as e:
        logger.error(f"Error syncing posts: {e}")
        return False


def _add_or_update_post(filepath: str, filename: str, db, existing_row) -> bool:
    """
    Add a new post or update an existing one in the database.
    
    Args:
        filepath: Full path to the markdown file
        filename: Just the filename (e.g. 'my-post.md')
        db: Database connection
        existing_row: Existing database row tuple or None
    
    Returns:
        True if operation succeeded
    """
    try:
        content = read_markdown_file(filepath)
        if not content:
            logger.warning(f"Empty or unreadable file: {filepath}")
            return False
        
        # Extract metadata
        metadata = extract_metadata(content, filepath)
        title = metadata['title']
        date = metadata['date']
        
        # Fallback title to filename if not found
        if not title:
            logger.warning(f"No title found in {filepath}, using filename")
            title = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ').title()
        
        if existing_row:
            # Update existing post
            post_id = existing_row[0]
            db.execute(
                "UPDATE posts SET title = ?, date = ? WHERE id = ?",
                [title, date, post_id]
            )
        else:
            # Add new post
            max_id = db.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM posts").fetchone()[0]
            db.execute(
                "INSERT INTO posts (id, file, title, date) VALUES (?, ?, ?, ?)",
                [max_id, filename, title, date]
            )
        
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error adding/updating post {filename}: {e}")
        return False


def _remove_deleted_posts(db, db_posts: dict, existing_files: set, posts_dir: str) -> None:
    """
    Remove posts from database that no longer exist as files.
    
    Args:
        db: Database connection
        db_posts: Dict of filename -> db row for existing posts
        existing_files: Set of filenames that exist in filesystem
        posts_dir: Path to posts directory
    """
    for filename, row in db_posts.items():
        filepath = os.path.join(posts_dir, filename)
        if filename not in existing_files or not os.path.exists(filepath):
            post_id = row[0]
            logger.info(f"Removing deleted post: {filename} (ID: {post_id})")
            db.execute("DELETE FROM posts WHERE id = ?", [post_id])
            db.commit()
