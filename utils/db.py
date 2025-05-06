import duckdb
import os
import sys
import logging
import click
from flask import current_app, g
from flask.cli import with_appcontext
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    """Get a database connection"""
    if 'db' not in g:
        logger.info("Creating new database connection")
        
        try:
            # Use Flask app config if in app context
            if hasattr(current_app, '_get_current_object'):
                db_path = get_db_path_from_app()
            else:
                # Fallback for standalone usage
                db_path = get_db_path_from_config()
            
            # Make sure data directory exists
            data_dir = os.path.dirname(db_path)
            if not os.path.exists(data_dir):
                logger.info(f"Creating data directory: {data_dir}")
                os.makedirs(data_dir)
                
            logger.info(f"Connecting to database at: {db_path}")
            g.db = duckdb.connect(db_path)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    return g.db

def get_db_path_from_app():
    """Get database path from Flask app config"""
    logger.info("Using Flask app context for database path")
    # Check if we're using the instance path or a custom path
    if os.path.isabs(current_app.config['DATABASE']):
        db_path = current_app.config['DATABASE']
    else:
        db_path = os.path.join(current_app.instance_path, current_app.config['DATABASE'])
    logger.info(f"Database path from Flask config: {db_path}")
    return db_path

def get_db_path_from_config():
    """Get database path from config module"""
    logger.info("Not in Flask context, using direct config import")
    # Add parent directory to path for imports
    if 'config' not in sys.modules:
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    import config
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          config.DATA_DIRECTORY, config.DB_FILENAME)
    logger.info(f"Database path from config module: {db_path}")
    return db_path

@contextmanager
def get_db_connection():
    """Context manager for database connections outside of Flask context"""
    db_path = get_db_path_from_config()
    conn = None
    try:
        conn = duckdb.connect(db_path)
        yield conn
    finally:
        if conn:
            conn.close()

def close_db(e=None):
    """Close the database connection"""
    db = g.pop('db', None)
    if db is not None:
        logger.info("Closing database connection")
        db.close()

def init_db():
    """Initialize the database with required tables if they don't exist"""
    try:
        logger.info("Initializing database tables")
        db = get_db()
        
        # Create posts table
        logger.info("Creating posts table if it doesn't exist")
        db.execute("""
        CREATE TABLE IF NOT EXISTS posts (
          id INTEGER PRIMARY KEY,
          file TEXT,
          title TEXT,
          date TEXT
        )
        """)
        
        # First check if subscribers table exists
        table_exists = False
        try:
            db.execute("SELECT COUNT(*) FROM subscribers")
            table_exists = True
        except:
            pass
            
        if table_exists:
            # Table exists, check for unique constraint
            try:
                # Creating a temp table with unique constraint
                db.execute("""
                CREATE TABLE IF NOT EXISTS tmp_subscribers (
                  email TEXT NOT NULL UNIQUE,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Copy unique entries to the new table
                db.execute("""
                INSERT INTO tmp_subscribers (email, timestamp)
                SELECT DISTINCT email, MIN(timestamp) 
                FROM subscribers
                GROUP BY email
                """)
                
                # Get counts for logs
                old_count = db.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
                new_count = db.execute("SELECT COUNT(*) FROM tmp_subscribers").fetchone()[0]
                
                # Replace old table with new one
                db.execute("DROP TABLE subscribers")
                db.execute("ALTER TABLE tmp_subscribers RENAME TO subscribers")
                
                if old_count != new_count:
                    logger.info(f"Removed {old_count - new_count} duplicate subscriber email(s)")
            except Exception as e:
                logger.error(f"Error adding unique constraint to subscribers table: {e}")
        else:
            # Create subscribers table with unique constraint
            logger.info("Creating subscribers table if it doesn't exist")
            db.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
              email TEXT NOT NULL UNIQUE,
              timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        
        # Check if tables were created by running a test query
        test_posts = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        test_subscribers = db.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
        logger.info(f"Database tables initialized: posts count={test_posts}, subscribers count={test_subscribers}")
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """Register database functions with the Flask app"""
    logger.info("Registering database hooks with Flask app")
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    logger.info("Database hooks registered successfully")

def get_posts(limit=5, offset=0):
    """Get posts with pagination"""
    try:
        logger.info(f"Getting posts with limit={limit}, offset={offset}")
        db = get_db()
        posts = db.execute("""
        SELECT id, file, title, date 
        FROM posts 
        ORDER BY date DESC 
        LIMIT ? OFFSET ?
        """, [limit, offset]).fetchall()
        logger.info(f"Retrieved {len(posts)} posts from database")
        return posts
    except Exception as e:
        logger.error(f"Error retrieving posts: {e}")
        return []

def add_post(file, title, date):
    """Add a new post to the database"""
    try:
        logger.info(f"Adding post to database: file={file}, title={title}, date={date}")
        db = get_db()
        db.execute("""
        INSERT INTO posts (file, title, date)
        VALUES (?, ?, ?)
        """, [file, title, date])
        logger.info(f"Added post: {title}")
    except Exception as e:
        logger.error(f"Error adding post: {e}")
        raise

def add_subscriber(email):
    """Add a new subscriber to the database"""
    try:
        logger.info(f"Adding subscriber to database: {email}")
        db = get_db()
        
        # Check if email already exists
        existing = db.execute("SELECT COUNT(*) FROM subscribers WHERE email = ?", [email]).fetchone()[0]
        if existing > 0:
            logger.info(f"Email already subscribed: {email}")
            return {'status': 'already_exists', 'message': 'This email is already subscribed to our newsletter.'}
            
        # Add new subscriber
        db.execute("""
        INSERT INTO subscribers (email)
        VALUES (?)
        """, [email])
        logger.info(f"Added subscriber: {email}")
        return {'status': 'success', 'message': 'Thank you for subscribing!'}
    except Exception as e:
        # If it's a unique constraint violation, return duplicate status
        if "UNIQUE constraint failed" in str(e):
            logger.info(f"Email already subscribed (caught constraint): {email}")
            return {'status': 'already_exists', 'message': 'This email is already subscribed to our newsletter.'}
        
        # Other error
        logger.error(f"Error adding subscriber: {e}")
        raise 