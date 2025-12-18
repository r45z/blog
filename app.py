"""Flask blog application"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, send_from_directory
from utils.db import init_db, init_app as init_db_app
from utils.scheduler import init_scheduler
import config

# Silence noisy loggers
logging.getLogger('apscheduler').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def create_app(test_config=None):
    """Application factory"""
    app = Flask(__name__, instance_relative_config=True)
    
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
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    
    # Ensure directories exist
    for directory in [app.instance_path, app.config['STATIC_DIR'], 
                      os.path.join(app.config['STATIC_DIR'], 'images'),
                      app.config['POSTS_DIR']]:
        os.makedirs(directory, exist_ok=True)
    
    init_db_app(app)
    
    with app.app_context():
        init_db()

    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(app.config['STATIC_DIR'], filename)

    @app.context_processor
    def inject_config():
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

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error="Page not found", status_code=404), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error=str(e)), 500
    
    from routes import register_routes
    register_routes(app)
    
    init_scheduler(app)
    
    return app


if __name__ == '__main__':
    create_app().run(debug=True)
