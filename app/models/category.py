"""
Category model - Income/Expense categories
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class Category(db.Model):
    """Category model for income/expense classification"""

    __tablename__ = 'category'

    id = db.Column(db.String(50), primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    name_th = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='categories')
    transactions = db.relationship('Transaction', back_populates='category')
    budgets = db.relationship('Budget', back_populates='category')

    # Indexes
    __table_args__ = (
        db.Index('idx_category_project_type', 'project_id', 'type'),
    )

    def __init__(self, project_id, type, name_th, name_en=None, icon=None, color=None, sort_order=0):
        self.id = generate_id('cat')
        self.project_id = project_id
        self.type = type
        self.name_th = name_th
        self.name_en = name_en
        self.icon = icon
        self.color = color
        self.sort_order = sort_order

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'type': self.type,
            'name_th': self.name_th,
            'name_en': self.name_en,
            'icon': self.icon,
            'color': self.color,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Category {self.name_th} ({self.type})>'
