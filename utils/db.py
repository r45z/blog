"""Database utilities"""
import sqlite3
import os
import click
from flask import Flask, current_app, g
from flask.cli import with_appcontext


def get_db() -> sqlite3.Connection:
    """Get database connection from Flask g object"""
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e: Exception | None = None) -> None:
    """Close database connection"""
    db = g.pop('db', None)
    if db:
        db.close()


def init_db() -> None:
    """Initialize database schema"""
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


@click.command('init-db')
@with_appcontext
def init_db_command() -> None:
    """CLI command to initialize database"""
    init_db()
    click.echo('Initialized the database.')


def init_app(app: Flask) -> None:
    """Register database functions with Flask app"""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
