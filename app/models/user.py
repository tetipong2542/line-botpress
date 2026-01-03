"""
User model - LINE authenticated users
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class User(db.Model):
    """User model for LINE authenticated users"""

    __tablename__ = 'user'

    id = db.Column(db.String(50), primary_key=True)
    line_user_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(200), nullable=False)
    picture_url = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(200), nullable=True)
    current_project_id = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owned_projects = db.relationship('Project', back_populates='owner', foreign_keys='Project.owner_user_id')
    memberships = db.relationship('ProjectMember', back_populates='user')

    def __init__(self, line_user_id, display_name, picture_url=None, email=None):
        self.id = generate_id('usr')
        self.line_user_id = line_user_id
        self.display_name = display_name
        self.picture_url = picture_url
        self.email = email

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'line_user_id': self.line_user_id,
            'display_name': self.display_name,
            'picture_url': self.picture_url,
            'email': self.email,
            'current_project_id': self.current_project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<User {self.display_name} ({self.id})>'
