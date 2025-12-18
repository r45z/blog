"""
Routes module for the blog
"""
import logging
from flask import jsonify, render_template, request, abort, redirect, url_for, current_app
from services.post_service import get_posts, get_post_by_slug

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all application routes"""
    
    @app.route('/')
    def home():
        """Home page - display posts"""
        posts = get_posts(limit=current_app.config['POSTS_PER_PAGE'])
        return render_template('posts.html', posts=posts)

    @app.route('/post/<slug>')
    def single_post(slug):
        """Display a single post"""
        post = get_post_by_slug(slug)
        if not post:
            abort(404)
        return render_template('post.html', post=post)

    @app.route('/about')
    def about():
        """About page - redirect to about post"""
        return redirect(url_for('single_post', slug='about'))

    @app.route('/load_posts')
    def load_posts():
        """API endpoint for loading more posts (infinite scroll)"""
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', current_app.config['POSTS_PER_PAGE'], type=int)
        posts = get_posts(limit=limit, offset=offset)
        return jsonify({'posts': posts})
