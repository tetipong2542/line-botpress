"""
Project models - Projects/Households and members
"""
from datetime import datetime, timedelta
from app import db
from app.utils.helpers import generate_id, generate_short_code


class Project(db.Model):
    """Project/Household model"""

    __tablename__ = 'project'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    project_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    owner_user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    owner = db.relationship('User', back_populates='owned_projects', foreign_keys=[owner_user_id])
    members = db.relationship('ProjectMember', back_populates='project', cascade='all, delete-orphan')
    categories = db.relationship('Category', back_populates='project', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', back_populates='project', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', back_populates='project', cascade='all, delete-orphan')
    recurring_rules = db.relationship('RecurringRule', back_populates='project', cascade='all, delete-orphan')
    settings = db.relationship('ProjectSettings', back_populates='project', uselist=False, cascade='all, delete-orphan')

    def __init__(self, name, owner_user_id):
        self.id = generate_id('prj')
        self.name = name
        self.project_code = generate_short_code(8)
        self.owner_user_id = owner_user_id

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'project_code': self.project_code,
            'owner_user_id': self.owner_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Project {self.name} ({self.project_code})>'


class ProjectMember(db.Model):
    """Project member model"""

    __tablename__ = 'project_member'

    id = db.Column(db.String(50), primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    joined_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='members')
    user = db.relationship('User', back_populates='memberships')

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
        db.Index('idx_project_member', 'project_id', 'user_id'),
    )

    def __init__(self, project_id, user_id, role='member'):
        self.id = generate_id('mem')
        self.project_id = project_id
        self.user_id = user_id
        self.role = role

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }

    def __repr__(self):
        return f'<ProjectMember {self.user_id} in {self.project_id}>'


class ProjectInvite(db.Model):
    """Project invitation model"""

    __tablename__ = 'project_invite'

    id = db.Column(db.String(50), primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), nullable=False)
    invite_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='member')
    expires_at = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    used_by = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)

    # New fields for enhanced invitation system
    email = db.Column(db.String(200), nullable=True, index=True)  # Email of invitee
    token = db.Column(db.String(64), unique=True, nullable=True, index=True)  # Acceptance token
    status = db.Column(db.String(20), default='pending')  # pending, accepted, cancelled

    def __init__(self, project_id, created_by, role='member', expires_days=7, email=None):
        self.id = generate_id('inv')
        self.project_id = project_id
        self.invite_code = generate_short_code(12)
        self.role = role
        self.expires_at = datetime.utcnow() + timedelta(days=expires_days)
        self.created_by = created_by

        # New fields
        self.email = email
        self.token = generate_short_code(32)  # Generate 32-char token for invitation link
        self.status = 'pending'

    def is_valid(self):
        """Check if invite is still valid"""
        return self.used_at is None and datetime.utcnow() < self.expires_at

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'invite_code': self.invite_code,
            'role': self.role,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_valid': self.is_valid(),
            # New fields
            'email': self.email,
            'token': self.token,
            'status': self.status
        }

    def __repr__(self):
        return f'<ProjectInvite {self.invite_code}>'


class ProjectSettings(db.Model):
    """Project settings model for Botpress Mode B policies"""

    __tablename__ = 'project_settings'

    id = db.Column(db.String(50), primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), unique=True, nullable=False)
    insight_enabled = db.Column(db.Boolean, nullable=False, default=True)
    insight_max_records = db.Column(db.Integer, nullable=False, default=100)
    insight_max_days = db.Column(db.Integer, nullable=False, default=30)
    insight_fields_level = db.Column(db.String(20), nullable=False, default='minimal')
    budget_alert_enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='settings')

    def __init__(self, project_id):
        self.id = generate_id('set')
        self.project_id = project_id

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'insight_enabled': self.insight_enabled,
            'insight_max_records': self.insight_max_records,
            'insight_max_days': self.insight_max_days,
            'insight_fields_level': self.insight_fields_level,
            'budget_alert_enabled': self.budget_alert_enabled
        }

    def __repr__(self):
        return f'<ProjectSettings {self.project_id}>'
