"""
Recurring rule model - Recurring transactions
"""
from datetime import datetime, timedelta
from app import db
from app.utils.helpers import generate_id


class RecurringRule(db.Model):
    """Recurring rule model for automatic transactions"""

    __tablename__ = 'recurring_rule'

    id = db.Column(db.String(50), primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), nullable=False)
    member_id = db.Column(db.String(50), db.ForeignKey('project_member.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    category_id = db.Column(db.String(50), db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount in satang
    note = db.Column(db.Text, nullable=True)
    freq = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    day_of_week = db.Column(db.Integer, nullable=True)  # 0=Monday, 6=Sunday (for weekly)
    day_of_month = db.Column(db.Integer, nullable=True)  # 1-31 (for monthly)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # Optional end date (null = forever)
    next_run_date = db.Column(db.Date, nullable=False)
    remind_days = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='recurring_rules')
    category = db.relationship('Category', foreign_keys=[category_id], lazy='joined')

    # Indexes
    __table_args__ = (
        db.Index('idx_recurring_next_run', 'next_run_date', 'is_active'),
    )

    def __init__(self, project_id, type, category_id, amount, freq, start_date,
                 day_of_week=None, day_of_month=None, note=None, member_id=None, end_date=None):
        self.id = generate_id('rec')
        self.project_id = project_id
        self.type = type
        self.category_id = category_id
        self.amount = amount
        self.note = note
        self.freq = freq
        self.day_of_week = day_of_week
        self.day_of_month = day_of_month
        self.start_date = start_date
        self.end_date = end_date
        self.next_run_date = self._calculate_next_run(start_date)
        self.member_id = member_id

    def _calculate_next_run(self, from_date):
        """Calculate next run date based on frequency"""
        if self.freq == 'daily':
            return from_date + timedelta(days=1)
        elif self.freq == 'weekly':
            # Calculate next occurrence of day_of_week
            days_ahead = self.day_of_week - from_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return from_date + timedelta(days=days_ahead)
        elif self.freq == 'monthly':
            # Calculate next month with same day
            next_month = from_date.month + 1
            next_year = from_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1

            # Handle invalid days (e.g., Feb 31 -> Feb 28/29)
            day = min(self.day_of_month or from_date.day,
                     self._last_day_of_month(next_year, next_month))

            return datetime(next_year, next_month, day).date()

        return from_date

    def _last_day_of_month(self, year, month):
        """Get last day of month"""
        if month == 12:
            return 31
        next_month = datetime(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        return last_day.day

    def update_next_run(self):
        """Update next_run_date after execution"""
        self.next_run_date = self._calculate_next_run(self.next_run_date)

    def to_dict(self):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'project_id': self.project_id,
            'member_id': self.member_id,
            'type': self.type,
            'category_id': self.category_id,
            'amount': self.amount,
            'amount_formatted': self.amount / 100.0,
            'note': self.note,
            'freq': self.freq,
            'day_of_week': self.day_of_week,
            'day_of_month': self.day_of_month,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'next_run_date': self.next_run_date.isoformat() if self.next_run_date else None,
            'remind_days': self.remind_days,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

        # Include category data if available
        if self.category:
            result['category'] = {
                'id': self.category.id,
                'name': self.category.name_th,  # Add name alias
                'name_th': self.category.name_th,
                'name_en': self.category.name_en,
                'icon': self.category.icon,
                'color': self.category.color,  # Add color field
                'type': self.category.type
            }
        else:
            result['category'] = None

        return result

    def __repr__(self):
        return f'<RecurringRule {self.freq} {self.amount/100}>'
