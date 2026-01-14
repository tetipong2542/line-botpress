"""
Loan Payment Model - บันทึกการชำระสินเชื่อ
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class LoanPayment(db.Model):
    """Loan payment record for tracking installment payments"""

    __tablename__ = 'loan_payments'

    id = db.Column(db.String(36), primary_key=True)
    loan_id = db.Column(db.String(36), db.ForeignKey('loans.id'), nullable=False, index=True)
    installment_number = db.Column(db.Integer, nullable=False)  # งวดที่
    payment_date = db.Column(db.Date, nullable=False)  # วันที่ชำระ
    due_date = db.Column(db.Date, nullable=True)  # วันครบกำหนด
    principal_paid = db.Column(db.Integer, nullable=False)  # เงินต้นที่ชำระ (satang)
    interest_paid = db.Column(db.Integer, nullable=False)  # ดอกเบี้ยที่ชำระ (satang)
    total_paid = db.Column(db.Integer, nullable=False)  # รวมที่ชำระ (satang)
    remaining_balance = db.Column(db.Integer, nullable=False)  # ยอดคงเหลือหลังชำระ (satang)
    note = db.Column(db.Text, nullable=True)  # หมายเหตุ
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    loan = db.relationship('Loan', back_populates='payments')

    def __init__(self, loan_id, installment_number, payment_date, principal_paid,
                 interest_paid, remaining_balance, due_date=None, note=None):
        self.id = generate_id('lpay')
        self.loan_id = loan_id
        self.installment_number = installment_number
        self.payment_date = payment_date
        self.due_date = due_date
        self.principal_paid = principal_paid
        self.interest_paid = interest_paid
        self.total_paid = principal_paid + interest_paid
        self.remaining_balance = remaining_balance
        self.note = note

    def to_dict(self):
        """Convert to dictionary"""
        from app.utils.helpers import satang_to_baht
        
        return {
            'id': self.id,
            'loan_id': self.loan_id,
            'installment_number': self.installment_number,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'principal_paid': self.principal_paid,
            'principal_paid_formatted': satang_to_baht(self.principal_paid),
            'interest_paid': self.interest_paid,
            'interest_paid_formatted': satang_to_baht(self.interest_paid),
            'total_paid': self.total_paid,
            'total_paid_formatted': satang_to_baht(self.total_paid),
            'remaining_balance': self.remaining_balance,
            'remaining_balance_formatted': satang_to_baht(self.remaining_balance),
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def get_payments_for_loan(loan_id):
        """Get all payments for a loan"""
        return LoanPayment.query.filter_by(
            loan_id=loan_id
        ).order_by(LoanPayment.installment_number).all()

    def __repr__(self):
        return f'<LoanPayment #{self.installment_number} {self.total_paid/100}>'
