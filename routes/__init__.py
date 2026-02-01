"""Blog routes using Flask Blueprints"""
import os
from flask import (
    Blueprint, Flask, Response, jsonify, render_template, 
    request, abort, redirect, url_for, current_app, send_from_directory
)
from services.post_service import get_posts, get_post_by_slug
from services.icon_service import get_random_icon

posts_bp = Blueprint('posts', __name__)


@posts_bp.route('/')
def home() -> str:
    """Render homepage with posts list"""
    return render_template('posts.html', posts=get_posts(limit=current_app.config['POSTS_PER_PAGE']))


@posts_bp.route('/post/<slug>')
def single_post(slug: str) -> str:
    """Render a single post by slug"""
    post = get_post_by_slug(slug)
    if not post:
        abort(404)
    return render_template('post.html', post=post)


@posts_bp.route('/about')
def about() -> Response:
    """Redirect to about post"""
    return redirect(url_for('posts.single_post', slug='about'))


@posts_bp.route('/load_posts')
def load_posts() -> Response:
    """API endpoint for infinite scroll pagination"""
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', current_app.config['POSTS_PER_PAGE'], type=int)
    return jsonify({'posts': get_posts(limit=limit, offset=offset)})


@posts_bp.route('/icon')
def random_icon() -> Response:
    """Serve a random icon from the icons folder"""
    icon = get_random_icon()
    if not icon:
        abort(404)
    icons_dir = os.path.join(current_app.config['STATIC_DIR'], 'icons')
    return send_from_directory(icons_dir, icon)


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the app"""
    app.register_blueprint(posts_bp)
