#!/usr/bin/env python3
"""
Script to verify post files are properly formatted.
Usage: python verify_posts.py [posts_directory]
"""
import os
import sys
import logging
from utils.markdown_parser import read_markdown_file, render_markdown, extract_metadata

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_POSTS_DIR = "posts"


def verify_post(file_path: str) -> bool:
    """Verify a post file's content and format"""
    logger.info(f"Verifying: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    
    content = read_markdown_file(file_path)
    if not content:
        logger.error(f"Empty or unreadable: {file_path}")
        return False
    
    # Check for title heading
    metadata = extract_metadata(content, file_path)
    if not metadata['title']:
        logger.error(f"No title (# heading) found: {file_path}")
        return False
    
    # Try rendering
    try:
        html = render_markdown(content)
        if not html:
            logger.error(f"Failed to render: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Render error in {file_path}: {e}")
        return False
    
    logger.info(f"OK: {metadata['title']}")
    return True


def main():
    """Verify all markdown files in posts directory"""
    posts_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_POSTS_DIR
    
    if not os.path.exists(posts_dir):
        logger.error(f"Directory not found: {posts_dir}")
        return 1
    
    md_files = [f for f in os.listdir(posts_dir) if f.endswith('.md')]
    if not md_files:
        logger.warning("No markdown files found")
        return 1
    
    logger.info(f"Found {len(md_files)} markdown files")
    
    failed = []
    for filename in md_files:
        if not verify_post(os.path.join(posts_dir, filename)):
            failed.append(filename)
    
    if failed:
        logger.error(f"Failed: {', '.join(failed)}")
        return 1
    
    logger.info("All posts verified successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
