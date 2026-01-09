"""
Migration: Add botpress_user_id column to user table
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db


def run_migration():
    """Add botpress_user_id column to user table"""
    app = create_app()
    
    with app.app_context():
        # Check if column exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'botpress_user_id' in columns:
            print("✅ Column 'botpress_user_id' already exists")
            return True
        
        print("📝 Adding 'botpress_user_id' column to user table...")
        
        # Add column
        try:
            db.session.execute(db.text(
                "ALTER TABLE user ADD COLUMN botpress_user_id VARCHAR(100) UNIQUE"
            ))
            db.session.commit()
            print("✅ Migration completed successfully!")
            
            # Create index
            try:
                db.session.execute(db.text(
                    "CREATE INDEX idx_user_botpress_user_id ON user(botpress_user_id)"
                ))
                db.session.commit()
                print("✅ Index created")
            except Exception as e:
                print(f"⚠️ Index may already exist: {e}")
            
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            return False


if __name__ == '__main__':
    run_migration()
