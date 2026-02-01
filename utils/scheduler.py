"""Scheduler for periodic post sync"""
import logging
from flask import Flask
from flask_apscheduler import APScheduler
from services.sync_service import sync_posts_to_db

logger = logging.getLogger(__name__)
scheduler = APScheduler()


def _run_sync() -> None:
    """Run post sync within app context"""
    with scheduler.app.app_context():
        sync_posts_to_db()


def init_scheduler(app: Flask) -> None:
    """Initialize scheduler - only runs in first worker"""
    app.config.setdefault('SCHEDULER_API_ENABLED', False)
    app.config.setdefault('POSTS_CHECK_INTERVAL', 60)
    
    scheduler.init_app(app)
    scheduler.app = app
    
    scheduler.add_job(
        id='sync_posts',
        func=_run_sync,
        trigger='interval',
        seconds=app.config['POSTS_CHECK_INTERVAL'],
        max_instances=1,
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
    
    with app.app_context():
        sync_posts_to_db()
