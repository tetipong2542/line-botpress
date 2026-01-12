"""
Flask application factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


def run_auto_migrations():
    """
    Run pending migrations automatically on app start
    This ensures new columns are added without manual intervention
    """
    from sqlalchemy import inspect, text
    
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        # Migration: Add botpress_user_id if not exists
        if 'botpress_user_id' not in columns:
            print("📝 Auto-migration: Adding 'botpress_user_id' column...")
            # SQLite doesn't support UNIQUE in ALTER TABLE, add column without it
            db.session.execute(text(
                "ALTER TABLE user ADD COLUMN botpress_user_id VARCHAR(100)"
            ))
            db.session.commit()
            print("✅ Auto-migration: 'botpress_user_id' column added!")
            
            # Create unique index (this enforces uniqueness)
            try:
                db.session.execute(text(
                    "CREATE UNIQUE INDEX idx_user_botpress_user_id ON user(botpress_user_id)"
                ))
                db.session.commit()
                print("✅ Auto-migration: Unique index created")
            except Exception:
                pass  # Index may already exist
        
        # Migration: Add gemini_api_key if not exists
        if 'gemini_api_key' not in columns:
            print("📝 Auto-migration: Adding 'gemini_api_key' column...")
            db.session.execute(text(
                "ALTER TABLE user ADD COLUMN gemini_api_key VARCHAR(200)"
            ))
            db.session.commit()
            print("✅ Auto-migration: 'gemini_api_key' column added!")
        
        # Migration: Add openrouter_api_key if not exists
        if 'openrouter_api_key' not in columns:
            print("📝 Auto-migration: Adding 'openrouter_api_key' column...")
            db.session.execute(text(
                "ALTER TABLE user ADD COLUMN openrouter_api_key VARCHAR(200)"
            ))
            db.session.commit()
            print("✅ Auto-migration: 'openrouter_api_key' column added!")
        
        # Migration: Add openrouter_model if not exists
        if 'openrouter_model' not in columns:
            print("📝 Auto-migration: Adding 'openrouter_model' column...")
            db.session.execute(text(
                "ALTER TABLE user ADD COLUMN openrouter_model VARCHAR(100) DEFAULT 'google/gemini-2.0-flash-exp:free'"
            ))
            db.session.commit()
            print("✅ Auto-migration: 'openrouter_model' column added!")
                
    except Exception as e:
        print(f"⚠️ Auto-migration check: {e}")


def create_app(config_name=None):
    """
    Create and configure the Flask application

    Args:
        config_name: Configuration name (development, production, testing)

    Returns:
        Flask application instance
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    from app.config import config
    app.config.from_object(config[config_name])

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models (for migrations to work)
    with app.app_context():
        from app.models import user, project, category, transaction, budget, recurring
        
        # Auto-run pending migrations
        run_auto_migrations()

    # Register blueprints
    from app.routes import auth, api, bot, line as line_routes, web

    app.register_blueprint(web.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(bot.bp)
    app.register_blueprint(line_routes.bp)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

    return app


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500


def register_commands(app):
    """Register CLI commands"""

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database with default data"""
        from app.services.init_service import initialize_database
        initialize_database()
        print('Database initialized successfully!')

    @app.cli.command('create-admin')
    def create_admin():
        """Create admin user"""
        from app.services.init_service import create_admin_user
        create_admin_user()
        print('Admin user created successfully!')
