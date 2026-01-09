"""
Report Template Model
Stores custom report templates for generating reports
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class ReportTemplate(db.Model):
    """Custom report templates"""

    __tablename__ = 'report_templates'

    id = db.Column(db.String(36), primary_key=True, default=generate_id)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    config = db.Column(db.Text, nullable=False)  # JSON configuration
    created_by = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = db.relationship('Project', backref='report_templates')
    creator = db.relationship('User', backref='created_report_templates')

    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'config': json.loads(self.config) if self.config else {},
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
