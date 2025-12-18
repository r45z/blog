"""
Post service - handles all post-related operations
"""
import os
import logging
from flask import current_app
from utils.db import get_db
from utils.markdown_parser import read_markdown_file, render_markdown, extract_metadata

logger = logging.getLogger(__name__)


def get_posts(limit: int = 10, offset: int = 0) -> list[dict]:
    """
    Get posts with pagination.
    
    Args:
        limit: Maximum number of posts to return
        offset: Number of posts to skip
    
    Returns:
        List of post dictionaries with id, file, title, date
    """
    try:
        db = get_db()
        rows = db.execute("""
            SELECT id, file, title, date 
            FROM posts 
            ORDER BY date DESC 
            LIMIT ? OFFSET ?
        """, [limit, offset]).fetchall()
        
        return [
            {'id': row[0], 'file': row[1], 'title': row[2], 'date': row[3]}
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error retrieving posts: {e}")
        return []


def get_post_by_slug(slug: str) -> dict | None:
    """
    Get a single post by its slug (filename without .md extension).
    
    Args:
        slug: The post slug (filename without .md)
    
    Returns:
        Post dictionary with id, file, title, date, content or None if not found
    """
    try:
        filename = f"{slug}.md"
        
        db = get_db()
        row = db.execute(
            "SELECT id, file, title, date FROM posts WHERE file = ?",
            [filename]
        ).fetchone()
        
        if not row:
            logger.debug(f"Post not found in database: {filename}")
            return None
        
        # Get post content from file
        posts_dir = current_app.config['POSTS_DIR']
        file_path = os.path.join(posts_dir, filename)
        raw_content = read_markdown_file(file_path)
        
        if not raw_content:
            logger.error(f"Post content not found: {filename}")
            return None
        
        # Extract fresh metadata and update title if changed
        metadata = extract_metadata(raw_content, file_path)
        title = metadata['title'] or row[2]
        
        if metadata['title'] and metadata['title'] != row[2]:
            logger.info(f"Updating post title: '{row[2]}' -> '{metadata['title']}'")
            db.execute("UPDATE posts SET title = ? WHERE id = ?", [metadata['title'], row[0]])
            db.commit()
        
        # Render content to HTML
        content = render_markdown(raw_content)
        
        return {
            'id': row[0],
            'file': row[1],
            'title': title,
            'date': row[3],
            'content': content
        }
    except Exception as e:
        logger.error(f"Error retrieving post by slug {slug}: {e}")
        return None


def get_post_count() -> int:
    """
    Get total number of posts.
    
    Returns:
        Total count of posts in database
    """
    try:
        db = get_db()
        result = db.execute("SELECT COUNT(*) FROM posts").fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting post count: {e}")
        return 0
