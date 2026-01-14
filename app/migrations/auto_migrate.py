"""
Smart Auto-Migration System
Automatically detects and adds missing columns to database tables.
Safe: Only ADDS columns, never deletes or modifies existing ones.
"""
from sqlalchemy import text, inspect
from app import db


def get_model_columns(model_class):
    """Get all columns from a SQLAlchemy model"""
    return {column.name: column for column in model_class.__table__.columns}


def get_db_columns(table_name):
    """Get existing columns from database table"""
    try:
        result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
        return {row[1]: {'type': row[2], 'notnull': row[3], 'default': row[4]} 
                for row in result.fetchall()}
    except Exception:
        return {}


def get_column_type_sql(column):
    """Convert SQLAlchemy column type to SQLite type"""
    type_name = str(column.type).upper()
    
    if 'INTEGER' in type_name or 'INT' in type_name:
        return 'INTEGER'
    elif 'VARCHAR' in type_name or 'STRING' in type_name or 'TEXT' in type_name:
        return 'TEXT'
    elif 'BOOLEAN' in type_name:
        return 'BOOLEAN'
    elif 'FLOAT' in type_name or 'REAL' in type_name:
        return 'REAL'
    elif 'DATE' in type_name and 'DATETIME' not in type_name:
        return 'DATE'
    elif 'DATETIME' in type_name:
        return 'DATETIME'
    else:
        return 'TEXT'


def get_default_value(column):
    """Get default value for column"""
    if column.default is not None:
        if hasattr(column.default, 'arg'):
            default = column.default.arg
            if callable(default):
                return None  # Skip callable defaults
            if isinstance(default, bool):
                return '1' if default else '0'
            if isinstance(default, (int, float)):
                return str(default)
            if isinstance(default, str):
                return f"'{default}'"
            return str(default)
    return None


def auto_migrate_table(model_class):
    """Auto-migrate a single table - add missing columns"""
    table_name = model_class.__tablename__
    
    model_cols = get_model_columns(model_class)
    db_cols = get_db_columns(table_name)
    
    if not db_cols:
        print(f"  ⚠️  Table '{table_name}' not found, skipping...")
        return 0
    
    added = 0
    for col_name, column in model_cols.items():
        if col_name not in db_cols:
            col_type = get_column_type_sql(column)
            default = get_default_value(column)
            
            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
            if default is not None:
                sql += f" DEFAULT {default}"
            
            try:
                db.session.execute(text(sql))
                print(f"  ✅ Added column: {table_name}.{col_name} ({col_type})")
                added += 1
            except Exception as e:
                print(f"  ❌ Failed to add {table_name}.{col_name}: {e}")
    
    return added


def run_auto_migration():
    """Run auto-migration for all models"""
    print("\n🔄 Running Smart Auto-Migration...")
    print("=" * 50)
    
    # Import all models
    from app.models.user import User
    from app.models.project import Project, ProjectMember
    from app.models.category import Category
    from app.models.transaction import Transaction, Attachment
    from app.models.budget import Budget
    from app.models.recurring import RecurringRule
    from app.models.bot import BotNonce, IdempotencyKey
    
    # Optional models (may not exist)
    try:
        from app.models.insight import Insight
        from app.models.notification import Notification, NotificationPreference
    except ImportError:
        Insight = None
        Notification = None
        NotificationPreference = None
    
    try:
        from app.models.loan import Loan, LoanPayment
    except ImportError:
        Loan = None
        LoanPayment = None
    
    try:
        from app.models.savings import SavingsGoal
    except ImportError:
        SavingsGoal = None
    
    # List of all models to check
    models = [
        User, Project, ProjectMember, Category, Transaction, 
        Attachment, Budget, RecurringRule, BotNonce, IdempotencyKey
    ]
    
    # Add optional models if they exist
    if Insight: models.append(Insight)
    if Notification: models.append(Notification)
    if NotificationPreference: models.append(NotificationPreference)
    if Loan: models.append(Loan)
    if LoanPayment: models.append(LoanPayment)
    if SavingsGoal: models.append(SavingsGoal)
    
    total_added = 0
    for model in models:
        if model:
            added = auto_migrate_table(model)
            total_added += added
    
    db.session.commit()
    
    print("=" * 50)
    if total_added > 0:
        print(f"✅ Auto-migration complete! Added {total_added} column(s)")
    else:
        print("✅ Database is up to date!")
    print("")
    
    return total_added


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        run_auto_migration()
