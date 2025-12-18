"""Sync service - syncs posts from filesystem to database"""
import os
import logging
from flask import current_app
from utils.db import get_db
from utils.markdown_parser import read_markdown_file, extract_metadata

logger = logging.getLogger(__name__)
EXCLUDED_FILES = {'about.md'}


def sync_posts_to_db(posts_dir: str = None) -> bool:
    """Sync markdown files to database"""
    try:
        if posts_dir is None:
            posts_dir = current_app.config['POSTS_DIR']
        
        if not os.path.exists(posts_dir):
            return False
        
        all_md_files = {f for f in os.listdir(posts_dir) if f.endswith('.md')}
        files_to_sync = all_md_files - EXCLUDED_FILES
        
        db = get_db()
        db_posts = {row[1]: row for row in db.execute(
            "SELECT id, file, title, date FROM posts"
        ).fetchall()}
        
        for filename in files_to_sync:
            _add_or_update_post(os.path.join(posts_dir, filename), filename, db, db_posts.get(filename))
        
        _remove_deleted_posts(db, db_posts, all_md_files, posts_dir)
        return True
        
    except Exception as e:
        logger.error(f"Error syncing posts: {e}")
        return False


def _add_or_update_post(filepath: str, filename: str, db, existing_row) -> bool:
    try:
        content = read_markdown_file(filepath)
        if not content:
            return False
        
        metadata = extract_metadata(content, filepath)
        title = metadata['title'] or os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ').title()
        date = metadata['date']
        
        if existing_row:
            db.execute("UPDATE posts SET title = ?, date = ? WHERE id = ?", [title, date, existing_row[0]])
        else:
            max_id = db.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM posts").fetchone()[0]
            db.execute("INSERT INTO posts (id, file, title, date) VALUES (?, ?, ?, ?)", [max_id, filename, title, date])
        
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating post {filename}: {e}")
        return False


def _remove_deleted_posts(db, db_posts: dict, existing_files: set, posts_dir: str) -> None:
    for filename, row in db_posts.items():
        if filename not in existing_files or not os.path.exists(os.path.join(posts_dir, filename)):
            db.execute("DELETE FROM posts WHERE id = ?", [row[0]])
            db.commit()
