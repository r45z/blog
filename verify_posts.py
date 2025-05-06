#!/usr/bin/env python3

"""
Script to verify post files and ensure they're properly formatted.
Run this script to check if your blog posts are correctly formatted for the CoreBlog system.
"""

import os
import sys
import logging
from utils.markdown_parser import read_markdown_file, render_markdown, get_posts_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("post_verifier")

def verify_post(file_path):
    """Verify a post file's content and format"""
    logger.info(f"Verifying post: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    
    # Read the file content
    content = read_markdown_file(file_path)
    if not content:
        logger.error(f"Failed to read or empty file: {file_path}")
        return False
    
    # Check if content starts with a title (# Title)
    lines = content.splitlines()
    if not lines or not lines[0].startswith('# '):
        logger.error(f"File does not start with a level 1 heading (# Title): {file_path}")
        return False
    
    # Try rendering the markdown
    try:
        html = render_markdown(content)
        if not html:
            logger.error(f"Failed to render markdown to HTML: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error rendering markdown: {e}")
        return False
    
    logger.info(f"Post verified successfully: {file_path}")
    return True

def verify_all_posts(posts_dir=None):
    """Verify all markdown files in the posts directory"""
    if posts_dir is None:
        posts_dir = get_posts_dir()
        
    logger.info(f"Verifying all posts in directory: {posts_dir}")
    
    # Check if directory exists
    if not os.path.exists(posts_dir):
        logger.error(f"Posts directory does not exist: {posts_dir}")
        return False
    
    # Get all markdown files
    markdown_files = [f for f in os.listdir(posts_dir) if f.endswith('.md')]
    logger.info(f"Found {len(markdown_files)} markdown files")
    
    if not markdown_files:
        logger.warning("No markdown files found in the posts directory")
        return False
    
    # Verify each file
    success = True
    for filename in markdown_files:
        file_path = os.path.join(posts_dir, filename)
        if not verify_post(file_path):
            success = False
    
    return success

if __name__ == "__main__":
    # Get posts directory from command line argument or use default
    posts_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    if verify_all_posts(posts_dir):
        logger.info("All posts verified successfully!")
        sys.exit(0)
    else:
        logger.error("Some posts failed verification")
        sys.exit(1) 