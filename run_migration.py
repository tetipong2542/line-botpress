"""
Script to run database migrations
"""
from app import create_app, db
from app.migrations.add_invite_fields import upgrade
from app.migrations.add_advanced_analytics_tables import migrate

app = create_app()

with app.app_context():
    print("Starting database migration...")

    # Run add_invite_fields migration first (may fail if already run)
    try:
        upgrade(db)
    except Exception as e:
        print(f"⚠️  add_invite_fields migration skipped: {e}")

    # Run advanced analytics migration
    migrate()
    print("\nDone!")
