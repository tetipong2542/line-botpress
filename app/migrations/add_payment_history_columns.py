"""
Migration script to add Payment History Tracking columns to recurring_rule table
"""

def upgrade(db):
    """Add last_paid_date and paid_count columns to recurring_rule table"""
    from sqlalchemy import text
    
    print("Adding Payment History Tracking columns to recurring_rule...")
    
    # Check if columns already exist
    try:
        result = db.session.execute(text("PRAGMA table_info(recurring_rule)"))
        existing_columns = [row[1] for row in result.fetchall()]
        
        if 'last_paid_date' not in existing_columns:
            db.session.execute(text("""
                ALTER TABLE recurring_rule 
                ADD COLUMN last_paid_date DATE
            """))
            print("✅ Added last_paid_date column")
        else:
            print("ℹ️  last_paid_date column already exists")
        
        if 'paid_count' not in existing_columns:
            db.session.execute(text("""
                ALTER TABLE recurring_rule 
                ADD COLUMN paid_count INTEGER DEFAULT 0
            """))
            print("✅ Added paid_count column")
        else:
            print("ℹ️  paid_count column already exists")
        
        db.session.commit()
        print("✅ Payment History Tracking migration completed!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Migration error: {e}")
        raise e


def migrate():
    """Standalone migration function"""
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        upgrade(db)


if __name__ == "__main__":
    migrate()
