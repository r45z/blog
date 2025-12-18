"""Post service - handles post operations"""
import os
import logging
from flask import current_app
from utils.db import get_db
from utils.markdown_parser import read_markdown_file, render_markdown, extract_metadata

logger = logging.getLogger(__name__)


def get_posts(limit: int = 10, offset: int = 0) -> list[dict]:
    """Get posts with pagination"""
    try:
        db = get_db()
        rows = db.execute(
            "SELECT id, file, title, date FROM posts ORDER BY date DESC LIMIT ? OFFSET ?",
            [limit, offset]
        ).fetchall()
        return [{'id': r[0], 'file': r[1], 'title': r[2], 'date': r[3]} for r in rows]
    except Exception as e:
        logger.error(f"Error retrieving posts: {e}")
        return []


def get_post_by_slug(slug: str) -> dict | None:
    """Get a single post by slug (filename without .md)"""
    try:
        filename = f"{slug}.md"
        db = get_db()
        row = db.execute(
            "SELECT id, file, title, date FROM posts WHERE file = ?", [filename]
        ).fetchone()
        
        if not row:
            return None
        
        posts_dir = current_app.config['POSTS_DIR']
        raw_content = read_markdown_file(os.path.join(posts_dir, filename))
        
        if not raw_content:
            logger.error(f"Post content not found: {filename}")
            return None
        
        metadata = extract_metadata(raw_content, os.path.join(posts_dir, filename))
        title = metadata['title'] or row[2]
        
        if metadata['title'] and metadata['title'] != row[2]:
            db.execute("UPDATE posts SET title = ? WHERE id = ?", [metadata['title'], row[0]])
            db.commit()
        
        return {
            'id': row[0], 'file': row[1], 'title': title,
            'date': row[3], 'content': render_markdown(raw_content)
        }
    except Exception as e:
        logger.error(f"Error retrieving post {slug}: {e}")
        return None


def get_post_count() -> int:
    """Get total number of posts"""
    try:
        return get_db().execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    except Exception:
        return 0
