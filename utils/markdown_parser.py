"""
Markdown parsing utilities for the blog
"""
import markdown
import os
import logging
import re
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)


def extract_metadata(content: str, filepath: str = None) -> dict:
    """
    Extract title and date from markdown content.
    
    Args:
        content: The markdown content string
        filepath: Optional file path for date fallback using file mtime
    
    Returns:
        dict with 'title' and 'date' keys (values may be None)
    """
    title = None
    date = None
    
    if not content:
        return {'title': title, 'date': date}
    
    # Extract title from first H1 heading
    for line in content.splitlines():
        if line.startswith('# '):
            title = line.lstrip('#').strip()
            break
    
    # Extract date - look for YYYY-MM-DD pattern in first 500 chars
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', content[:500])
    if date_match:
        date = date_match.group(0)
    
    # Fallback to file modification time if no date found
    if not date and filepath and os.path.exists(filepath):
        date = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')
    
    return {'title': title, 'date': date}


def read_markdown_file(file_path: str) -> str:
    """Read a markdown file and return its content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""


def render_markdown(content: str, post_slug: str = None) -> str:
    """Convert markdown content to HTML with image processing"""
    try:
        # Process image paths before rendering
        processed_content = _process_image_paths(content)
        
        # Validate images exist (in Flask context only)
        try:
            if hasattr(current_app, 'config'):
                _validate_images_exist(processed_content)
        except RuntimeError:
            pass  # Not in Flask context
        
        # Render markdown to HTML
        html = markdown.markdown(
            processed_content,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.codehilite',
                'markdown.extensions.attr_list'
            ]
        )
        
        # Add responsive classes to images
        return _add_responsive_image_classes(html)
        
    except Exception as e:
        logger.error(f"Error rendering markdown: {e}")
        return f"<p>Error rendering content: {e}</p>"


def _process_image_paths(content: str) -> str:
    """Process image paths in markdown content to ensure they work correctly"""
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image_path(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        
        # Already absolute path or external URL
        if img_path.startswith('/static/') or img_path.startswith('http'):
            return f'![{alt_text}]({img_path})'
        
        # Convert relative path to /static/images/
        clean_path = img_path.lstrip('./')
        return f'![{alt_text}](/static/images/{clean_path})'
    
    return re.sub(img_pattern, replace_image_path, content)


def _validate_images_exist(content: str) -> None:
    """Check if referenced images exist in the static directory"""
    static_dir = current_app.config.get('STATIC_DIR', '')
    if not static_dir:
        return
    
    img_pattern = r'!\[([^\]]*)\]\((/static/[^)]+)\)'
    matches = re.findall(img_pattern, content)
    
    for alt_text, img_path in matches:
        relative_path = img_path[8:]  # Remove '/static/' prefix
        full_path = os.path.join(static_dir, relative_path)
        if not os.path.exists(full_path):
            logger.warning(f"Image not found: {img_path}")


def _add_responsive_image_classes(html: str) -> str:
    """Add responsive CSS classes to images in HTML"""
    img_pattern = r'<img([^>]*?)>'
    
    def add_classes(match):
        attrs = match.group(1)
        if 'class=' in attrs:
            attrs = re.sub(r'class="([^"]*)"', r'class="\1 max-w-full h-auto rounded-lg shadow-md"', attrs)
        else:
            attrs += ' class="max-w-full h-auto rounded-lg shadow-md"'
        return f'<img{attrs}>'
    
    return re.sub(img_pattern, add_classes, html)
