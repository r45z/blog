import markdown
import os
import sys
import logging
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_markdown_file(file_path):
    """Read a markdown file and return its content"""
    try:
        logger.info(f"Reading markdown file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        logger.info(f"Successfully read file: {file_path} ({len(content)} bytes)")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""

def render_markdown(content):
    """Convert markdown content to HTML"""
    try:
        logger.info(f"Rendering markdown content ({len(content)} bytes)")
        # Use Python-Markdown with extensions for code highlighting and tables
        html = markdown.markdown(
            content,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.codehilite'
            ]
        )
        logger.info(f"Successfully rendered markdown to HTML ({len(html)} bytes)")
        return html
    except Exception as e:
        logger.error(f"Error rendering markdown: {e}")
        return f"<p>Error rendering content: {e}</p>"

def get_posts_dir():
    """Get the posts directory path from Flask app or config"""
    if hasattr(current_app, '_get_current_object'):
        logger.info("Using Flask app context for posts directory")
        posts_dir = current_app.config['POSTS_DIR']
        logger.info(f"Posts directory from Flask config: {posts_dir}")
    else:
        # Fallback to config file when outside Flask context
        logger.info("Not in Flask context, using direct config import")
        # Add parent directory to path for imports
        if 'config' not in sys.modules:
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        import config
        posts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), config.POSTS_DIRECTORY)
        logger.info(f"Posts directory from config module: {posts_dir}")
    return posts_dir

def get_post_content(filename):
    """Get HTML content from a markdown post file"""
    try:
        logger.info(f"Getting post content for: {filename}")
        posts_dir = get_posts_dir()
        file_path = os.path.join(posts_dir, filename)
        logger.info(f"Full file path: {file_path}")
        
        if not os.path.exists(file_path):
            logger.warning(f"Post file not found: {file_path}")
            return None
        
        content = read_markdown_file(file_path)
        if not content:
            logger.warning(f"Empty content for file: {file_path}")
            return None
            
        html = render_markdown(content)
        return html
    except Exception as e:
        logger.error(f"Error getting post content for {filename}: {e}")
        return f"<p>Error loading post content: {e}</p>" 