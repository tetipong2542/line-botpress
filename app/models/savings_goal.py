"""
Savings Goal Model
Tracks savings goals with progress tracking
"""
from datetime import datetime, date
from app import db
from app.utils.helpers import generate_id


class SavingsGoal(db.Model):
    """Savings goals for tracking progress"""

    __tablename__ = 'savings_goals'

    id = db.Column(db.String(36), primary_key=True, default=generate_id)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    target_amount = db.Column(db.Integer, nullable=False)  # satang
    current_amount = db.Column(db.Integer, default=0, nullable=False)  # satang
    target_date = db.Column(db.Date)
    category_id = db.Column(db.String(36), db.ForeignKey('category.id'))
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = db.relationship('Project', backref='savings_goals')
    category = db.relationship('Category', backref='savings_goals')

    def to_dict(self):
        """Convert to dictionary"""
        from app.utils.helpers import satang_to_baht

        progress = self.progress_percentage
        days_remaining = self.days_remaining

        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'target_amount': self.target_amount,
            'target_amount_formatted': satang_to_baht(self.target_amount),
            'current_amount': self.current_amount,
            'current_amount_formatted': satang_to_baht(self.current_amount),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'category_id': self.category_id,
            'is_active': self.is_active,
            'progress_percentage': progress,
            'days_remaining': days_remaining,
            'is_completed': self.is_completed,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.target_amount == 0:
            return 0
        return round((self.current_amount / self.target_amount * 100), 1)

    @property
    def is_completed(self):
        """Check if goal is completed"""
        return self.current_amount >= self.target_amount

    @property
    def is_overdue(self):
        """Check if goal is overdue"""
        if not self.target_date:
            return False
        return date.today() > self.target_date and not self.is_completed

    @property
    def days_remaining(self):
        """Calculate days remaining until target date"""
        if not self.target_date:
            return None
        delta = self.target_date - date.today()
        return delta.days if delta.days > 0 else 0

    def add_contribution(self, amount):
        """Add contribution to goal"""
        self.current_amount += amount
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def update_progress(self):
        """Update progress based on actual savings (income - expense)"""
        from app.models.transaction import Transaction
        from sqlalchemy import func

        # Calculate net savings since goal creation
        net_savings = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == self.project_id,
            Transaction.occurred_at >= self.created_at,
            Transaction.type == 'income'
        ).scalar() or 0

        expenses = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == self.project_id,
            Transaction.occurred_at >= self.created_at,
            Transaction.type == 'expense'
        ).scalar() or 0

        self.current_amount = net_savings - expenses
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def get_required_saving_rate(self):
        """Calculate required daily saving rate to reach goal"""
        if not self.target_date or self.is_completed:
            return None

        days_remaining = self.days_remaining
        if days_remaining <= 0:
            return None

        remaining_amount = self.target_amount - self.current_amount
        if remaining_amount <= 0:
            return 0

        return remaining_amount / days_remaining  # satang per day

    @staticmethod
    def get_active_goals(project_id):
        """Get all active goals for a project"""
        return SavingsGoal.query.filter_by(
            project_id=project_id,
            is_active=True
        ).order_by(SavingsGoal.target_date).all()

    @staticmethod
    def get_goal(goal_id, project_id):
        """Get a specific goal"""
        return SavingsGoal.query.filter_by(
            id=goal_id,
            project_id=project_id
        ).first()
