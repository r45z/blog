"""Blog routes"""
from flask import jsonify, render_template, request, abort, redirect, url_for, current_app
from services.post_service import get_posts, get_post_by_slug


def register_routes(app):
    @app.route('/')
    def home():
        return render_template('posts.html', posts=get_posts(limit=current_app.config['POSTS_PER_PAGE']))

    @app.route('/post/<slug>')
    def single_post(slug):
        post = get_post_by_slug(slug)
        if not post:
            abort(404)
        return render_template('post.html', post=post)

    @app.route('/about')
    def about():
        return redirect(url_for('single_post', slug='about'))

    @app.route('/load_posts')
    def load_posts():
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', current_app.config['POSTS_PER_PAGE'], type=int)
        return jsonify({'posts': get_posts(limit=limit, offset=offset)})
