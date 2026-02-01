"""Markdown parsing utilities"""
import markdown
import os
import logging
import re
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)


def extract_metadata(content: str, filepath: str | None = None) -> dict[str, str | None]:
    """Extract title and date from markdown content"""
    title: str | None = None
    date: str | None = None
    
    if not content:
        return {'title': title, 'date': date}
    
    for line in content.splitlines():
        if line.startswith('# '):
            title = line.lstrip('#').strip()
            break
    
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', content[:500])
    if date_match:
        date = date_match.group(0)
    elif filepath and os.path.exists(filepath):
        date = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')
    
    return {'title': title, 'date': date}


def read_markdown_file(file_path: str) -> str:
    """Read markdown file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return ""


def render_markdown(content: str, post_slug: str | None = None) -> str:
    """Convert markdown to HTML"""
    try:
        processed = _process_image_paths(content)
        
        try:
            if hasattr(current_app, 'config'):
                _validate_images_exist(processed)
        except RuntimeError:
            pass
        
        html = markdown.markdown(processed, extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.codehilite',
            'markdown.extensions.attr_list'
        ])
        
        return _add_responsive_image_classes(html)
    except Exception as e:
        logger.error(f"Error rendering markdown: {e}")
        return "<p>Error rendering content</p>"


def _process_image_paths(content: str) -> str:
    """Convert relative image paths to static paths"""
    def replace_path(match: re.Match) -> str:
        alt, path = match.group(1), match.group(2)
        if path.startswith('/static/') or path.startswith('http'):
            return f'![{alt}]({path})'
        return f'![{alt}](/static/images/{path.lstrip("./")})'
    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_path, content)


def _validate_images_exist(content: str) -> None:
    """Log warnings for missing images"""
    static_dir = current_app.config.get('STATIC_DIR', '')
    if not static_dir:
        return
    for _, path in re.findall(r'!\[([^\]]*)\]\((/static/[^)]+)\)', content):
        full_path = os.path.join(static_dir, path[8:])
        if not os.path.exists(full_path):
            logger.warning(f"Image not found: {path}")


def _add_responsive_image_classes(html: str) -> str:
    """Add responsive CSS classes to images"""
    def add_classes(match: re.Match) -> str:
        attrs = match.group(1)
        if 'class=' in attrs:
            return re.sub(r'class="([^"]*)"', r'class="\1 max-w-full h-auto rounded-lg shadow-md"', f'<img{attrs}>')
        return f'<img{attrs} class="max-w-full h-auto rounded-lg shadow-md">'
    return re.sub(r'<img([^>]*?)>', add_classes, html)
