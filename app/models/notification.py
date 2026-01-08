"""
Notification model - User notifications and alerts
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class Notification(db.Model):
    """Notification model for user alerts"""

    __tablename__ = 'notification'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # 'budget_alert', 'recurring_reminder', 'insight', 'system'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.JSON, nullable=True)  # Additional data (budget_id, category_id, etc.)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    sent_via_line = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='notifications')
    project = db.relationship('Project', backref='notifications')

    # Indexes
    __table_args__ = (
        db.Index('idx_notification_user', 'user_id', 'is_read'),
        db.Index('idx_notification_created', 'created_at'),
    )

    def __init__(self, user_id, type, title, message, project_id=None, data=None):
        self.id = generate_id('notif')
        self.user_id = user_id
        self.project_id = project_id
        self.type = type
        self.title = title
        self.message = message
        self.data = data

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'sent_via_line': self.sent_via_line,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Notification {self.type}: {self.title}>'


class NotificationPreference(db.Model):
    """User notification preferences"""

    __tablename__ = 'notification_preference'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False, unique=True)
    budget_alerts = db.Column(db.Boolean, nullable=False, default=True)
    budget_threshold = db.Column(db.Integer, nullable=False, default=80)  # Alert at 80% of budget
    recurring_reminders = db.Column(db.Boolean, nullable=False, default=True)
    reminder_days_before = db.Column(db.Integer, nullable=False, default=1)  # Remind 1 day before
    weekly_summary = db.Column(db.Boolean, nullable=False, default=True)
    weekly_summary_day = db.Column(db.Integer, nullable=False, default=0)  # 0 = Sunday
    insights = db.Column(db.Boolean, nullable=False, default=True)
    line_notifications = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='notification_preference')

    def __init__(self, user_id):
        self.id = generate_id('npref')
        self.user_id = user_id

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'budget_alerts': self.budget_alerts,
            'budget_threshold': self.budget_threshold,
            'recurring_reminders': self.recurring_reminders,
            'reminder_days_before': self.reminder_days_before,
            'weekly_summary': self.weekly_summary,
            'weekly_summary_day': self.weekly_summary_day,
            'insights': self.insights,
            'line_notifications': self.line_notifications,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<NotificationPreference user_id={self.user_id}>'
