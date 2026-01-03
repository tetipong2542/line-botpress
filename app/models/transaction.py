"""
Transaction model - Income/Expense transactions
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class Transaction(db.Model):
    """Transaction model for income/expense records"""

    __tablename__ = 'transaction'

    id = db.Column(db.String(50), primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'), nullable=False)
    member_id = db.Column(db.String(50), db.ForeignKey('project_member.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    category_id = db.Column(db.String(50), db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount in satang (cents)
    currency = db.Column(db.String(10), nullable=False, default='THB')
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    note = db.Column(db.Text, nullable=True)
    recurring_rule_id = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    project = db.relationship('Project', back_populates='transactions')
    category = db.relationship('Category', back_populates='transactions')
    attachments = db.relationship('Attachment', back_populates='transaction', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        db.Index('idx_transaction_occurred', 'project_id', 'occurred_at'),
        db.Index('idx_transaction_category', 'category_id', 'occurred_at'),
        db.Index('idx_transaction_type', 'type', 'occurred_at'),
    )

    def __init__(self, project_id, type, category_id, amount, occurred_at=None, note=None, member_id=None):
        self.id = generate_id('txn')
        self.project_id = project_id
        self.type = type
        self.category_id = category_id
        self.amount = amount
        self.occurred_at = occurred_at or datetime.utcnow()
        self.note = note
        self.member_id = member_id

    def to_dict(self, include_category=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'member_id': self.member_id,
            'type': self.type,
            'category_id': self.category_id,
            'amount': self.amount,
            'amount_formatted': self.amount / 100.0,  # Convert satang to baht
            'currency': self.currency,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else None,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_category and self.category:
            data['category'] = self.category.to_dict()

        return data

    def __repr__(self):
        return f'<Transaction {self.type} {self.amount/100} {self.currency}>'


class Attachment(db.Model):
    """Attachment model for transaction receipts/bills"""

    __tablename__ = 'attachment'

    id = db.Column(db.String(50), primary_key=True)
    transaction_id = db.Column(db.String(50), db.ForeignKey('transaction.id'), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    sha256 = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    transaction = db.relationship('Transaction', back_populates='attachments')

    def __init__(self, transaction_id, file_path, mime_type=None, sha256=None):
        self.id = generate_id('att')
        self.transaction_id = transaction_id
        self.file_path = file_path
        self.mime_type = mime_type
        self.sha256 = sha256

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'file_path': self.file_path,
            'mime_type': self.mime_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Attachment {self.id}>'
