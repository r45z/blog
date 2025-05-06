"""
Posts module for handling post-related operations
"""
import os
import logging
from datetime import datetime
from flask import current_app
from utils.db import get_db, add_post
from utils.markdown_parser import get_post_content, read_markdown_file, render_markdown

# Configure logging
logger = logging.getLogger(__name__)

def get_post_list():
    """Get posts from the database or create initial entries from filesystem"""
    logger.info("Getting post list from database")
    posts_list = get_posts(limit=100)  # Get all posts
    logger.info(f"Found {len(posts_list) if posts_list else 0} posts in database")
    
    # If no posts in DB, scan the posts directory and add them
    if not posts_list:
        posts_dir = current_app.config['POSTS_DIR']
        logger.info(f"No posts found in database, scanning directory: {posts_dir}")
        for filename in os.listdir(posts_dir):
            if filename.endswith('.md') and filename != 'about.md':
                logger.info(f"Processing file: {filename}")
                file_path = os.path.join(posts_dir, filename)
                content = read_markdown_file(file_path)
                
                # Extract title from content - look for the first markdown heading
                title = None
                if content:
                    for line in content.splitlines():
                        if line.startswith('# '):
                            title = line.lstrip('#').strip()
                            break
                
                # Fallback to filename if no title found
                if not title:
                    logger.warning(f"Could not extract title from {file_path}, using filename")
                    title = os.path.splitext(filename)[0].replace('-', ' ').title()
                
                # Use file modification time as date if not available
                date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d')
                
                # Add to database
                logger.info(f"Adding post to database: {title}")
                add_post(filename, title, date)
        
        # Fetch again after populating
        posts_list = get_posts(limit=100)
        logger.info(f"After scanning, found {len(posts_list) if posts_list else 0} posts")
    
    return posts_list

def get_posts(limit=5, offset=0):
    """Get posts with pagination"""
    try:
        logger.info(f"Getting posts with limit={limit}, offset={offset}")
        db = get_db()
        posts = db.execute("""
        SELECT id, file, title, date 
        FROM posts 
        ORDER BY date DESC 
        LIMIT ? OFFSET ?
        """, [limit, offset]).fetchall()
        logger.info(f"Retrieved {len(posts)} posts from database")
        return posts
    except Exception as e:
        logger.error(f"Error retrieving posts: {e}")
        return []

def get_posts_with_content(limit=None, offset=0):
    """Get posts with their content"""
    if limit is None:
        limit = current_app.config['POSTS_PER_PAGE']
    
    logger.info(f"Getting posts with content: limit={limit}, offset={offset}")    
    posts_list = get_posts(limit=limit, offset=offset)
    logger.info(f"Found {len(posts_list) if posts_list else 0} posts")
    
    # Make sure we have posts in the database
    if not posts_list:
        logger.info("No posts found, triggering get_post_list to scan directory")
        get_post_list()
        posts_list = get_posts(limit=limit, offset=offset)
        logger.info(f"After scanning, found {len(posts_list) if posts_list else 0} posts")
        
    result = []
    
    for post in posts_list:
        logger.info(f"Processing post: {post[1]}")  # post[1] is the filename
        content = get_post_content(post[1])
        if content:
            result.append({
                'id': post[0],
                'file': post[1],
                'title': post[2],
                'date': post[3],
                'content': content
            })
        else:
            logger.warning(f"No content found for post: {post[1]}")
    
    logger.info(f"Returning {len(result)} posts with content")
    return result

def get_post_by_slug(slug):
    """Get a single post by its slug"""
    try:
        # Add .md extension to the slug to get the filename
        filename = f"{slug}.md"
        
        # Try to get the post from the database
        db = get_db()
        post_data = db.execute(
            "SELECT id, file, title, date FROM posts WHERE file = ?",
            [filename]
        ).fetchone()
        
        if not post_data:
            logger.error(f"Post not found in database: {filename}")
            return None
        
        # Get post content
        posts_dir = current_app.config['POSTS_DIR']
        file_path = os.path.join(posts_dir, filename)
        raw_content = read_markdown_file(file_path)
        
        if not raw_content:
            logger.error(f"Post content not found: {filename}")
            return None
            
        # Re-extract title from content to ensure it's fresh
        updated_title = None
        for line in raw_content.splitlines():
            if line.startswith('# '):
                updated_title = line.lstrip('#').strip()
                break
                
        # If title in file has changed from what's in database, update it
        if updated_title and updated_title != post_data[2]:
            logger.info(f"Updating post title: '{post_data[2]}' -> '{updated_title}'")
            db.execute(
                "UPDATE posts SET title = ? WHERE id = ?",
                [updated_title, post_data[0]]
            )
            # Use the updated title
            post_title = updated_title
        else:
            post_title = post_data[2]
            
        # Render the content to HTML
        content = render_markdown(raw_content)
        
        post = {
            'id': post_data[0],
            'file': post_data[1],
            'title': post_title,
            'date': post_data[3],
            'content': content
        }
        
        return post
    except Exception as e:
        logger.error(f"Error retrieving post by slug {slug}: {e}")
        return None 