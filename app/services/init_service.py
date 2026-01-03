"""
Initialization service - Database initialization and default data
"""
from app import db
from app.models.user import User
from app.models.project import Project, ProjectSettings
from app.models.category import Category


def initialize_database():
    """Initialize database with tables"""
    db.create_all()
    print("Database tables created successfully!")


def create_admin_user():
    """Create admin user (for testing)"""
    # This is just a placeholder - in production, users are created via LINE Login
    print("Users are created via LINE Login OAuth2")
    print("Please login via /auth/line/login")
