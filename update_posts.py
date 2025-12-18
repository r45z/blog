#!/usr/bin/env python3
"""
Script to sync posts from filesystem to database.
Run this script to manually update the blog database with all posts.

Usage:
    python update_posts.py
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run post sync within Flask app context"""
    from app import create_app
    from services.sync_service import sync_posts_to_db
    
    flask_app = create_app()
    
    with flask_app.app_context():
        if sync_posts_to_db():
            logger.info("Posts synced successfully")
            return 0
        else:
            logger.error("Post sync failed")
            return 1


if __name__ == "__main__":
    sys.exit(main())
