"""
Migration: Add email, token, status to project_invite table

This migration adds new columns to support enhanced invitation system:
- email: Store invitee email address
- token: Unique token for invitation acceptance URL
- status: Track invitation status (pending, accepted, cancelled)

Usage:
    from app import db
    from app.migrations.add_invite_fields import upgrade, downgrade

    # Apply migration
    upgrade(db)

    # Rollback migration
    downgrade(db)
"""
from sqlalchemy import text


def upgrade(db):
    """Apply migration - add new columns to project_invite table"""
    print("Running migration: add_invite_fields")

    try:
        # Add email column
        db.session.execute(text('''
            ALTER TABLE project_invite
            ADD COLUMN email VARCHAR(200);
        '''))
        print("✓ Added email column")

        # Add token column
        db.session.execute(text('''
            ALTER TABLE project_invite
            ADD COLUMN token VARCHAR(64);
        '''))
        print("✓ Added token column")

        # Add status column with default value
        db.session.execute(text('''
            ALTER TABLE project_invite
            ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
        '''))
        print("✓ Added status column")

        # Create indexes for better query performance
        db.session.execute(text('''
            CREATE INDEX IF NOT EXISTS idx_invite_token ON project_invite(token);
        '''))
        print("✓ Created index on token")

        db.session.execute(text('''
            CREATE INDEX IF NOT EXISTS idx_invite_email ON project_invite(email);
        '''))
        print("✓ Created index on email")

        db.session.commit()
        print("✅ Migration completed successfully!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Migration failed: {e}")
        raise


def downgrade(db):
    """Rollback migration - remove added columns"""
    print("Rolling back migration: add_invite_fields")

    try:
        # Drop indexes first
        db.session.execute(text('DROP INDEX IF EXISTS idx_invite_token'))
        print("✓ Dropped index on token")

        db.session.execute(text('DROP INDEX IF EXISTS idx_invite_email'))
        print("✓ Dropped index on email")

        # Drop columns
        # Note: SQLite doesn't support DROP COLUMN directly, so we need to recreate table
        # For production with PostgreSQL/MySQL, you can use:
        # db.session.execute(text('ALTER TABLE project_invite DROP COLUMN status'))
        # db.session.execute(text('ALTER TABLE project_invite DROP COLUMN token'))
        # db.session.execute(text('ALTER TABLE project_invite DROP COLUMN email'))

        print("⚠️  Note: SQLite doesn't support DROP COLUMN.")
        print("    For full rollback, you need to manually recreate the table.")
        print("    Or use PostgreSQL/MySQL in production.")

        db.session.commit()
        print("✅ Rollback completed!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Rollback failed: {e}")
        raise


if __name__ == '__main__':
    print("This migration file should be run from the Flask app context.")
    print("Example:")
    print("  from app import create_app, db")
    print("  from app.migrations.add_invite_fields import upgrade")
    print("  ")
    print("  app = create_app()")
    print("  with app.app_context():")
    print("      upgrade(db)")
