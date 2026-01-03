"""
Insight model - AI-generated insights from Botpress
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class Insight(db.Model):
    """Insight model for storing AI-generated insights"""

    __tablename__ = 'insight'

    id = db.Column(db.String(50), primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), nullable=False)
    insight_type = db.Column(db.String(50), nullable=False)  # 'spending_pattern', 'budget_alert', 'suggestion'
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    insight_metadata = db.Column(db.Text, nullable=True)  # JSON string with additional data
    source = db.Column(db.String(50), nullable=False, default='botpress')
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        db.Index('idx_insight_project', 'project_id', 'created_at'),
    )

    def __init__(self, project_id, insight_type, title, content, insight_metadata=None, confidence=None):
        self.id = generate_id('ins')
        self.project_id = project_id
        self.insight_type = insight_type
        self.title = title
        self.content = content
        self.insight_metadata = insight_metadata
        self.confidence = confidence

    def acknowledge(self):
        """Mark insight as acknowledged"""
        self.acknowledged_at = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'insight_type': self.insight_type,
            'title': self.title,
            'content': self.content,
            'metadata': self.insight_metadata,
            'source': self.source,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }

    def __repr__(self):
        return f'<Insight {self.insight_type} - {self.title[:30]}>'
