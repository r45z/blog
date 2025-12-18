"""
Core Blog Application

This is the main Flask application file for the Core Blog system.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, send_from_directory
from utils.db import init_db, init_app as init_db_app
from utils.scheduler import init_scheduler
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(test_config=None):
    """Application factory function"""
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default configuration
    # Use data/ directory for database (consistent with standalone scripts)
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, config.DATA_DIRECTORY)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(data_dir, config.DB_FILENAME),
        POSTS_DIR=os.path.join(base_dir, config.POSTS_DIRECTORY),
        POSTS_PER_PAGE=config.POSTS_PER_PAGE,
        STATIC_DIR=os.path.join(base_dir, 'static')
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Ensure static directories exist
    static_dir = app.config['STATIC_DIR']
    images_dir = os.path.join(static_dir, 'images')
    for directory in [static_dir, images_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
    
    # Register the database functions
    init_db_app(app)
    
    # Initialize database if it doesn't exist
    with app.app_context():
        init_db()

    # Create a posts directory if it doesn't exist
    posts_dir = app.config['POSTS_DIR']
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)

    # Static file route for images
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files"""
        return send_from_directory(app.config['STATIC_DIR'], filename)

    # Register template context processor
    @app.context_processor
    def inject_config():
        """Make configuration available to all templates"""
        return {
            'blog_name': config.BLOG_NAME,
            'blog_tagline': config.BLOG_TAGLINE,
            'blog_description': config.BLOG_DESCRIPTION,
            'meta_keywords': config.META_KEYWORDS,
            'meta_author': config.META_AUTHOR,
            'instagram_handle': config.INSTAGRAM_HANDLE,
            'instagram_url': config.INSTAGRAM_URL,
            'background_color': config.BACKGROUND_COLOR,
            'text_color': config.TEXT_COLOR,
            'secondary_text_color': config.SECONDARY_TEXT_COLOR,
            'accent_color': config.ACCENT_COLOR,
            'body_font': config.BODY_FONT,
            'heading_font': config.HEADING_FONT,
            'body_font_weight': config.BODY_FONT_WEIGHT,
            'heading_font_weight': config.HEADING_FONT_WEIGHT,
            'body_font_size': config.BODY_FONT_SIZE,
            'body_line_height': config.BODY_LINE_HEIGHT,
            'body_letter_spacing': config.BODY_LETTER_SPACING,
            'heading_letter_spacing': config.HEADING_LETTER_SPACING,
            'content_max_width': config.CONTENT_MAX_WIDTH,
            'now': datetime.now()
        }

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error="Page not found", status_code=404), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error=str(e)), 500
    
    # Register routes
    from routes import register_routes
    register_routes(app)
    
    # Initialize the scheduler for post updates
    init_scheduler(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 