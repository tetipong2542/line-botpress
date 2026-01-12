"""
Quick Template Model
Stores user-defined quick add templates for fast transaction entry
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class QuickTemplate(db.Model):
    """
    Quick template for 1-tap transaction creation
    
    Attributes:
        id: Unique identifier
        project_id: Associated project
        user_id: User who created the template (optional, None = system-generated)
        name: Display name (e.g., "☕ กาแฟเช้า")
        icon: Emoji icon
        category_id: Default category
        amount: Default amount in satang
        note: Default note text
        type: 'expense' or 'income'
        is_auto_generated: True if AI-generated from frequent transactions
        usage_count: Number of times this template was used
        last_used_at: Last time this template was used
        sort_order: Display order
        is_active: Whether template is active
    """
    
    __tablename__ = 'quick_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_id)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default='📝')
    category_id = db.Column(db.String(36), db.ForeignKey('category.id'), nullable=True)
    amount = db.Column(db.Integer, nullable=False)  # in satang
    note = db.Column(db.String(500), nullable=True)
    type = db.Column(db.String(10), default='expense')  # expense or income
    
    is_auto_generated = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('quick_templates', lazy='dynamic'))
    category = db.relationship('Category', backref=db.backref('quick_templates', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('quick_templates', lazy='dynamic'))
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        from app.utils.helpers import satang_to_baht
        
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'name': self.name,
            'icon': self.icon,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'amount': self.amount,
            'amount_formatted': satang_to_baht(self.amount),
            'note': self.note,
            'type': self.type,
            'is_auto_generated': self.is_auto_generated,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def increment_usage(self):
        """Increment usage count and update last_used_at"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    @classmethod
    def get_active_templates(cls, project_id, limit=10):
        """Get active templates ordered by usage"""
        return cls.query.filter_by(
            project_id=project_id,
            is_active=True
        ).order_by(
            cls.sort_order.asc(),
            cls.usage_count.desc()
        ).limit(limit).all()
    
    @classmethod
    def generate_from_frequent_transactions(cls, project_id, limit=5):
        """
        Auto-generate templates from most frequent transactions
        Returns list of suggested templates (not saved to DB)
        """
        from sqlalchemy import func
        from app.models.transaction import Transaction
        from app.models.category import Category
        
        # Get most common note + category + amount combinations
        frequent = db.session.query(
            Transaction.note,
            Transaction.category_id,
            func.round(func.avg(Transaction.amount)).label('avg_amount'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.note.isnot(None),
            Transaction.note != '',
            Transaction.deleted_at.is_(None)
        ).group_by(
            Transaction.note,
            Transaction.category_id
        ).having(
            func.count(Transaction.id) >= 3  # At least 3 occurrences
        ).order_by(
            func.count(Transaction.id).desc()
        ).limit(limit).all()
        
        templates = []
        for f in frequent:
            if not f.note:
                continue
                
            # Get category info
            category = Category.query.get(f.category_id) if f.category_id else None
            icon = category.icon if category else '📝'
            
            templates.append({
                'name': f"{icon} {f.note[:20]}",
                'icon': icon,
                'category_id': f.category_id,
                'amount': int(f.avg_amount),
                'note': f.note,
                'type': 'expense',
                'is_auto_generated': True,
                'suggested': True,
                'frequency': f.count
            })
        
        return templates
