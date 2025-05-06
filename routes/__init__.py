"""
Routes module for the blog
"""

import os
from flask import jsonify, render_template, request, abort, current_app
import logging
from utils.db import get_db, add_subscriber
from utils.markdown_parser import read_markdown_file, render_markdown
from utils.posts import get_posts, get_post_by_slug

# Configure logging
logger = logging.getLogger(__name__)

def register_routes(app):
    """Register all application routes"""
    @app.route('/')
    def home():
        """Home page - display posts"""
        logger.info("Home page requested")
        
        # Get posts from database without content
        db = get_db()
        posts_data = db.execute("""
        SELECT id, file, title, date 
        FROM posts 
        ORDER BY date DESC 
        LIMIT ?
        """, [current_app.config['POSTS_PER_PAGE']]).fetchall()
        
        posts = []
        for post in posts_data:
            posts.append({
                'id': post[0],
                'file': post[1],
                'title': post[2],
                'date': post[3]
            })
        
        logger.info(f"Rendering home page with {len(posts)} posts")
        return render_template('posts.html', posts=posts)

    @app.route('/post/<slug>')
    def single_post(slug):
        """Display a single post"""
        logger.info(f"Post page requested for slug: {slug}")
        
        post = get_post_by_slug(slug)
        if not post:
            abort(404)
        
        logger.info(f"Rendering post page for: {post['title']}")
        return render_template('post.html', post=post)

    @app.route('/about')
    def about():
        """About page"""
        posts_dir = current_app.config['POSTS_DIR']
        about_path = os.path.join(posts_dir, 'about.md')
        if os.path.exists(about_path):
            content = read_markdown_file(about_path)
            html_content = render_markdown(content)
        else:
            html_content = "<p>About page content not found.</p>"
        
        return render_template('about.html', content=html_content, image_path=None)

    @app.route('/newsletter')
    def newsletter():
        """Newsletter subscription page"""
        return render_template('newsletter.html')

    @app.route('/load_posts')
    def load_posts():
        """API endpoint for loading more posts (AJAX)"""
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', current_app.config['POSTS_PER_PAGE'], type=int)
        
        # Get posts from database without content
        db = get_db()
        posts_data = db.execute("""
        SELECT id, file, title, date 
        FROM posts 
        ORDER BY date DESC 
        LIMIT ? OFFSET ?
        """, [limit, offset]).fetchall()
        
        posts = []
        for post in posts_data:
            posts.append({
                'id': post[0],
                'file': post[1],
                'title': post[2],
                'date': post[3]
            })
        
        return jsonify({
            'posts': posts
        })
        
    @app.route('/subscribe', methods=['POST'])
    def subscribe():
        """Handle newsletter subscriptions"""
        email = request.form.get('email', '').strip()
        
        # Simple validation
        if not email or '@' not in email:
            return jsonify({'success': False, 'message': 'Please enter a valid email address'}), 400
        
        try:
            # Add to database and get result
            result = add_subscriber(email)
            
            if result['status'] == 'already_exists':
                # Email is already subscribed - return a 409 Conflict with a message
                return jsonify({
                    'success': False, 
                    'message': result['message'],
                    'status': 'duplicate'
                }), 409
            
            # Success case
            return jsonify({
                'success': True, 
                'message': result['message']
            })
            
        except Exception as e:
            logger.error(f"Error adding subscriber: {e}")
            return jsonify({'success': False, 'message': 'There was an error. Please try again later.'}), 500 