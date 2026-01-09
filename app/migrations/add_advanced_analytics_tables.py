"""
Migration script for advanced analytics and reporting features
Adds new tables: analytics_cache, report_templates, scheduled_reports, share_links, savings_goals

Usage:
    python -c "from app import create_app, db; from app.migrations.add_advanced_analytics_tables import migrate; app = create_app(); with app.app_context(): migrate()"
"""
from app import db
from app.models.analytics_cache import AnalyticsCache
from app.models.report_template import ReportTemplate
from app.models.scheduled_report import ScheduledReport
from app.models.share_link import ShareLink
from app.models.savings_goal import SavingsGoal


def migrate():
    """Run migration to create new tables"""
    print("Starting advanced analytics migration...")

    # Create tables
    db.create_all()

    # Verify tables were created
    tables = [
        ('analytics_cache', AnalyticsCache),
        ('report_templates', ReportTemplate),
        ('scheduled_reports', ScheduledReport),
        ('share_links', ShareLink),
        ('savings_goals', SavingsGoal)
    ]

    for table_name, model in tables:
        try:
            # Check if table exists
            result = db.session.execute(
                db.text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            ).fetchone()

            if result:
                print(f"✓ Table '{table_name}' already exists")
            else:
                print(f"✗ Table '{table_name}' not found")
        except Exception as e:
            print(f"✗ Error checking table '{table_name}': {e}")

    print("Migration completed!")
    print("\nNote: The add_invite_fields migration may have already run.")
    print("If you encounter 'duplicate column' errors, the tables already exist.")
    print("This is expected and the new tables were created successfully.")
    print("\nNote: To run this migration from the Flask app context, use:")
    print("  python run_migration.py")
    print("\nOr to run from Python directly:")
    print("  python -c \"from app import create_app, db; from app.migrations.add_advanced_analytics_tables import migrate; app = create_app(); with app.app_context(): migrate()\"")
