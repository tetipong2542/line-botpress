"""
Loan Model - สินเชื่อ/ผ่อนชำระ
"""
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from app import db
from app.utils.helpers import generate_id


class Loan(db.Model):
    """Loan model for tracking loans and installment payments"""

    __tablename__ = 'loans'

    id = db.Column(db.String(36), primary_key=True)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # ชื่อสินเชื่อ
    principal = db.Column(db.Integer, nullable=False)  # ยอดเงินต้น (satang)
    interest_rate = db.Column(db.Float, nullable=False)  # ดอกเบี้ยต่อปี (%)
    interest_type = db.Column(db.String(20), nullable=False, default='reducing')  # 'reducing' | 'flat'
    term_months = db.Column(db.Integer, nullable=False)  # ระยะเวลาผ่อน (เดือน)
    start_date = db.Column(db.Date, nullable=False)
    monthly_payment = db.Column(db.Integer, nullable=False)  # ค่างวด (satang, คำนวณอัตโนมัติ)
    total_interest = db.Column(db.Integer, nullable=False)  # ดอกเบี้ยรวมตลอดสัญญา (satang)
    paid_installments = db.Column(db.Integer, default=0, nullable=False)  # จำนวนงวดที่ชำระแล้ว
    paid_principal = db.Column(db.Integer, default=0, nullable=False)  # เงินต้นที่ชำระแล้ว (satang)
    paid_interest = db.Column(db.Integer, default=0, nullable=False)  # ดอกเบี้ยที่ชำระแล้ว (satang)
    note = db.Column(db.Text, nullable=True)  # หมายเหตุ
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = db.relationship('Project', backref='loans')
    payments = db.relationship('LoanPayment', back_populates='loan', lazy='dynamic',
                               order_by='LoanPayment.installment_number')

    def __init__(self, project_id, name, principal, interest_rate, term_months, start_date,
                 interest_type='reducing', note=None):
        self.id = generate_id('loan')
        self.project_id = project_id
        self.name = name
        self.principal = principal
        self.interest_rate = interest_rate
        self.interest_type = interest_type
        self.term_months = term_months
        self.start_date = start_date
        self.note = note
        
        # Calculate monthly payment and total interest
        monthly_payment, total_interest = self.calculate_payment(
            principal, interest_rate, term_months, interest_type
        )
        self.monthly_payment = monthly_payment
        self.total_interest = total_interest

    @staticmethod
    def calculate_payment(principal, interest_rate, term_months, interest_type='reducing'):
        """
        Calculate monthly payment and total interest
        
        Args:
            principal: ยอดเงินต้น (satang)
            interest_rate: อัตราดอกเบี้ยต่อปี (%)
            term_months: ระยะเวลา (เดือน)
            interest_type: 'reducing' (ลดต้นลดดอก) หรือ 'flat' (คงที่)
        
        Returns:
            tuple: (monthly_payment, total_interest) in satang
        """
        if term_months <= 0:
            return 0, 0
            
        monthly_rate = (interest_rate / 100) / 12
        
        if interest_type == 'flat':
            # Flat Rate: ดอกเบี้ยคิดจากเงินต้นตลอดสัญญา
            total_interest = int(principal * (interest_rate / 100) * (term_months / 12))
            total_amount = principal + total_interest
            monthly_payment = int(total_amount / term_months)
        else:
            # Reducing Balance (ลดต้นลดดอก): PMT formula
            if monthly_rate == 0:
                # ดอกเบี้ย 0%
                monthly_payment = int(principal / term_months)
                total_interest = 0
            else:
                # PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
                rate_factor = (1 + monthly_rate) ** term_months
                monthly_payment = int(principal * monthly_rate * rate_factor / (rate_factor - 1))
                total_interest = int((monthly_payment * term_months) - principal)
        
        return monthly_payment, total_interest

    @property
    def remaining_balance(self):
        """ยอดเงินต้นคงเหลือ (satang)"""
        return self.principal - self.paid_principal

    @property
    def remaining_installments(self):
        """จำนวนงวดคงเหลือ"""
        return self.term_months - self.paid_installments

    @property
    def progress_percentage(self):
        """เปอร์เซ็นต์ที่ชำระแล้ว"""
        if self.term_months == 0:
            return 0
        return round((self.paid_installments / self.term_months) * 100, 1)

    @property
    def is_completed(self):
        """ตรวจสอบว่าปิดสินเชื่อแล้วหรือยัง"""
        return self.paid_installments >= self.term_months

    @property
    def next_payment_date(self):
        """วันครบกำหนดงวดถัดไป"""
        if self.is_completed:
            return None
        next_installment = self.paid_installments + 1
        return self.start_date + relativedelta(months=next_installment - 1)

    @property
    def next_installment_number(self):
        """หมายเลขงวดถัดไป"""
        if self.is_completed:
            return None
        return self.paid_installments + 1

    def get_amortization_schedule(self):
        """
        สร้างตารางผ่อนชำระ (Amortization Schedule)
        
        Returns:
            list of dict: ตารางผ่อนชำระทุกงวด
        """
        schedule = []
        balance = self.principal
        monthly_rate = (self.interest_rate / 100) / 12
        payment_date = self.start_date
        
        for i in range(1, self.term_months + 1):
            if self.interest_type == 'flat':
                # Flat Rate: ดอกเบี้ยเท่ากันทุกงวด
                interest_payment = int(self.total_interest / self.term_months)
                principal_payment = int(self.principal / self.term_months)
                # ปรับงวดสุดท้ายให้ลงตัว
                if i == self.term_months:
                    principal_payment = balance
            else:
                # Reducing Balance
                interest_payment = int(balance * monthly_rate)
                principal_payment = self.monthly_payment - interest_payment
                # ปรับงวดสุดท้ายให้ลงตัว
                if i == self.term_months:
                    principal_payment = balance
            
            balance = max(0, balance - principal_payment)
            
            schedule.append({
                'installment': i,
                'payment_date': payment_date.isoformat(),
                'principal': principal_payment,
                'interest': interest_payment,
                'total': principal_payment + interest_payment,
                'remaining_balance': balance,
                'is_paid': i <= self.paid_installments,
                # Formatted values (baht)
                'principal_formatted': principal_payment / 100,
                'interest_formatted': interest_payment / 100,
                'total_formatted': (principal_payment + interest_payment) / 100,
                'remaining_balance_formatted': balance / 100
            })
            
            payment_date = payment_date + relativedelta(months=1)
        
        return schedule

    def record_payment(self, principal_paid=None, interest_paid=None):
        """
        บันทึกการชำระงวด
        
        Args:
            principal_paid: เงินต้นที่ชำระ (satang) - ถ้าไม่ระบุจะคำนวณจาก schedule
            interest_paid: ดอกเบี้ยที่ชำระ (satang) - ถ้าไม่ระบุจะคำนวณจาก schedule
        
        Returns:
            dict: ข้อมูลงวดที่ชำระ
        """
        if self.is_completed:
            raise ValueError("สินเชื่อนี้ปิดแล้ว")
        
        schedule = self.get_amortization_schedule()
        current_installment = schedule[self.paid_installments]
        
        if principal_paid is None:
            principal_paid = current_installment['principal']
        if interest_paid is None:
            interest_paid = current_installment['interest']
        
        self.paid_installments += 1
        self.paid_principal += principal_paid
        self.paid_interest += interest_paid
        self.updated_at = datetime.utcnow()
        
        return {
            'installment_number': self.paid_installments,
            'principal_paid': principal_paid,
            'interest_paid': interest_paid,
            'total_paid': principal_paid + interest_paid,
            'remaining_balance': self.remaining_balance
        }

    def to_dict(self):
        """Convert to dictionary"""
        from app.utils.helpers import satang_to_baht
        
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'principal': self.principal,
            'principal_formatted': satang_to_baht(self.principal),
            'interest_rate': self.interest_rate,
            'interest_type': self.interest_type,
            'interest_type_label': 'ลดต้นลดดอก' if self.interest_type == 'reducing' else 'Flat Rate',
            'term_months': self.term_months,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'monthly_payment': self.monthly_payment,
            'monthly_payment_formatted': satang_to_baht(self.monthly_payment),
            'total_interest': self.total_interest,
            'total_interest_formatted': satang_to_baht(self.total_interest),
            'total_amount': self.principal + self.total_interest,
            'total_amount_formatted': satang_to_baht(self.principal + self.total_interest),
            'paid_installments': self.paid_installments,
            'paid_principal': self.paid_principal,
            'paid_principal_formatted': satang_to_baht(self.paid_principal),
            'paid_interest': self.paid_interest,
            'paid_interest_formatted': satang_to_baht(self.paid_interest),
            'remaining_balance': self.remaining_balance,
            'remaining_balance_formatted': satang_to_baht(self.remaining_balance),
            'remaining_installments': self.remaining_installments,
            'progress_percentage': self.progress_percentage,
            'is_completed': self.is_completed,
            'next_payment_date': self.next_payment_date.isoformat() if self.next_payment_date else None,
            'next_installment_number': self.next_installment_number,
            'note': self.note,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_active_loans(project_id):
        """Get all active loans for a project"""
        return Loan.query.filter_by(
            project_id=project_id,
            is_active=True
        ).order_by(Loan.start_date.desc()).all()

    @staticmethod
    def get_loan(loan_id, project_id):
        """Get a specific loan"""
        return Loan.query.filter_by(
            id=loan_id,
            project_id=project_id
        ).first()

    @staticmethod
    def get_summary(project_id):
        """Get loans summary for dashboard"""
        from sqlalchemy import func
        
        loans = Loan.query.filter_by(
            project_id=project_id,
            is_active=True
        ).all()
        
        total_balance = sum(loan.remaining_balance for loan in loans)
        total_loans = len(loans)
        
        # Find next payment
        upcoming_payments = []
        for loan in loans:
            if loan.next_payment_date and not loan.is_completed:
                upcoming_payments.append({
                    'loan_id': loan.id,
                    'loan_name': loan.name,
                    'payment_date': loan.next_payment_date,
                    'amount': loan.monthly_payment
                })
        
        # Sort by date
        upcoming_payments.sort(key=lambda x: x['payment_date'])
        next_payment = upcoming_payments[0] if upcoming_payments else None
        
        return {
            'total_loans': total_loans,
            'total_balance': total_balance,
            'total_balance_formatted': total_balance / 100,
            'next_payment': next_payment
        }

    def __repr__(self):
        return f'<Loan {self.name} {self.principal/100}>'
