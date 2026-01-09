"""
Run advanced analytics migration with Flask app context
"""
from app import create_app, db
from app.migrations.add_advanced_analytics_tables import migrate

if __name__ == '__main__':
    print("Creating Flask app...")
    app = create_app()

    print("Running migration...")
    with app.app_context():
        migrate()

    print("Migration completed successfully!")
