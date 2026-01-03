"""
Budget model - Budget envelopes per category
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class Budget(db.Model):
    """Budget model for category budget limits"""

    __tablename__ = 'budget'

    id = db.Column(db.String(50), primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), nullable=False)
    category_id = db.Column(db.String(50), db.ForeignKey('category.id'), nullable=False)
    month_yyyymm = db.Column(db.String(7), nullable=False)  # Format: "2025-01"
    limit_amount = db.Column(db.Integer, nullable=False)  # Amount in satang
    rollover_policy = db.Column(db.String(20), nullable=False, default='none')  # 'none', 'add', 'reset'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='budgets')
    category = db.relationship('Category', back_populates='budgets')

    # Unique constraint and indexes
    __table_args__ = (
        db.UniqueConstraint('project_id', 'category_id', 'month_yyyymm', name='uq_budget_month'),
        db.Index('idx_budget_month', 'project_id', 'month_yyyymm'),
    )

    def __init__(self, project_id, category_id, month_yyyymm, limit_amount, rollover_policy='none'):
        self.id = generate_id('bdg')
        self.project_id = project_id
        self.category_id = category_id
        self.month_yyyymm = month_yyyymm
        self.limit_amount = limit_amount
        self.rollover_policy = rollover_policy

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'category_id': self.category_id,
            'month_yyyymm': self.month_yyyymm,
            'limit_amount': self.limit_amount,
            'limit_amount_formatted': self.limit_amount / 100.0,
            'rollover_policy': self.rollover_policy,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Budget {self.month_yyyymm} {self.limit_amount/100}>'
