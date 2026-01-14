"""
Script to run database migrations
"""
from app import create_app, db
from app.migrations.add_invite_fields import upgrade
from app.migrations.add_advanced_analytics_tables import migrate
from app.migrations.add_payment_history_columns import upgrade as upgrade_payment_history

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
    
    # Run payment history columns migration
    try:
        upgrade_payment_history(db)
    except Exception as e:
        print(f"⚠️  payment_history_columns migration skipped: {e}")

    print("\nDone!")

