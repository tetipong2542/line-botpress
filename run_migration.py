"""
Script to run database migrations
"""
from app import create_app, db
from app.migrations.add_invite_fields import upgrade

app = create_app()

with app.app_context():
    print("Starting database migration...")
    upgrade(db)
    print("\nDone!")
