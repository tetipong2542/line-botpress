"""
Main entry point for the Flask application
"""
import os
from app import create_app
from app.services.init_service import init_database

app = create_app()

# Auto-initialize database on first run (for Railway deployment)
with app.app_context():
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization: {e}")

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))

    # Get debug mode from environment
    debug = os.environ.get('FLASK_ENV') == 'development'

    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
