"""
Core Blog Application

This is the main Flask application file for the Core Blog system.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template
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
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, config.DB_FILENAME),
        POSTS_DIR=os.path.join(os.path.dirname(__file__), config.POSTS_DIRECTORY),
        POSTS_PER_PAGE=config.POSTS_PER_PAGE
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
    
    # Register the database functions
    init_db_app(app)
    
    # Initialize database if it doesn't exist
    with app.app_context():
        init_db()

    # Create a posts directory if it doesn't exist
    posts_dir = app.config['POSTS_DIR']
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)

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
            'github_url': config.GITHUB_URL,
            'background_color': config.BACKGROUND_COLOR,
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