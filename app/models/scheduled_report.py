"""
Scheduled Report Model
Stores scheduled reports with recurrence rules
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class ScheduledReport(db.Model):
    """Scheduled reports with recurrence"""

    __tablename__ = 'scheduled_reports'

    id = db.Column(db.String(36), primary_key=True, default=generate_id)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    template_id = db.Column(db.String(36), db.ForeignKey('report_templates.id'))
    name = db.Column(db.String(255), nullable=False)
    schedule_type = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly
    schedule_config = db.Column(db.Text)  # JSON config (day_of_week, day_of_month, etc.)
    recipients = db.Column(db.Text)  # JSON array of email addresses
    last_run_at = db.Column(db.DateTime)
    next_run_at = db.Column(db.DateTime, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = db.relationship('Project', backref='scheduled_reports')
    template = db.relationship('ReportTemplate', backref='scheduled_reports')

    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'project_id': self.project_id,
            'template_id': self.template_id,
            'name': self.name,
            'schedule_type': self.schedule_type,
            'schedule_config': json.loads(self.schedule_config) if self.schedule_config else {},
            'recipients': json.loads(self.recipients) if self.recipients else [],
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def calculate_next_run(self):
        """Calculate next run time based on schedule"""
        from datetime import timedelta
        import json

        config = json.loads(self.schedule_config) if self.schedule_config else {}

        if self.schedule_type == 'daily':
            next_run = datetime.utcnow() + timedelta(days=1)
        elif self.schedule_type == 'weekly':
            day_of_week = config.get('day_of_week', 0)  # 0 = Sunday
            now = datetime.utcnow()
            days_until = (day_of_week - now.weekday() + 7) % 7
            if days_until == 0:
                days_until = 7
            next_run = now + timedelta(days=days_until)
        elif self.schedule_type == 'monthly':
            day_of_month = config.get('day_of_month', 1)
            now = datetime.utcnow()
            if now.day <= day_of_month:
                next_run = now.replace(day=day_of_month)
            else:
                # Move to next month
                if now.month == 12:
                    next_run = now.replace(year=now.year + 1, month=1, day=day_of_month)
                else:
                    next_run = now.replace(month=now.month + 1, day=day_of_month)
        else:
            next_run = datetime.utcnow() + timedelta(days=1)

        self.next_run_at = next_run
        db.session.commit()

        return next_run
