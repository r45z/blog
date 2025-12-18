"""
Database utilities for the blog
"""
import sqlite3
import os
import logging
import click
from flask import current_app, g
from flask.cli import with_appcontext

logger = logging.getLogger(__name__)


def get_db():
    """Get a database connection"""
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        
        # Ensure data directory exists
        data_dir = os.path.dirname(db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    
    return g.db


def close_db(e=None):
    """Close the database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database with required tables if they don't exist"""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            file TEXT,
            title TEXT,
            date TEXT
        )
    """)
    db.commit()
    logger.debug("Database initialized")


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    """Register database functions with the Flask app"""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
