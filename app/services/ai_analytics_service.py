"""
AI Analytics Service - Smart financial analysis and predictions
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from sqlalchemy import func
import statistics


class AIAnalyticsService:
    """Service for AI-powered financial analytics"""
    
    @staticmethod
    def get_spending_analysis(project_id, months=3):
        """
        Analyze spending patterns over multiple months
        
        Returns:
        - Total spending per month
        - Month-over-month change
        - Category breakdown
        - Trend direction
        """
        today = datetime.now()
        
        monthly_data = []
        for i in range(months):
            month_start = (today - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                month_end = today
            else:
                month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
            
            # Get total expenses
            total = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.project_id == project_id,
                Transaction.type == 'expense',
                Transaction.occurred_at >= month_start,
                Transaction.occurred_at <= month_end,
                Transaction.deleted_at.is_(None)
            ).scalar() or 0
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%B %Y'),
                'total': total / 100  # Convert to baht
            })
        
        # Reverse to get chronological order
        monthly_data.reverse()
        
        # Calculate trend
        if len(monthly_data) >= 2:
            last_month = monthly_data[-1]['total']
            prev_month = monthly_data[-2]['total']
            if prev_month > 0:
                change_percent = ((last_month - prev_month) / prev_month) * 100
            else:
                change_percent = 0
            trend = 'increasing' if change_percent > 5 else ('decreasing' if change_percent < -5 else 'stable')
        else:
            change_percent = 0
            trend = 'stable'
        
        # Get category breakdown for current month
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        categories = db.session.query(
            Category.name_th,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction, Transaction.category_id == Category.id).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= month_start,
            Transaction.deleted_at.is_(None)
        ).group_by(Category.id).order_by(func.sum(Transaction.amount).desc()).all()
        
        total_expense = sum(c.total for c in categories) if categories else 0
        category_breakdown = []
        for cat in categories:
            percentage = (cat.total / total_expense * 100) if total_expense > 0 else 0
            category_breakdown.append({
                'name': cat.name_th,
                'amount': cat.total / 100,
                'percentage': round(percentage, 1)
            })
        
        return {
            'monthly_data': monthly_data,
            'trend': trend,
            'change_percent': round(change_percent, 1),
            'category_breakdown': category_breakdown[:5]  # Top 5
        }
    
    @staticmethod
    def predict_next_month(project_id):
        """
        Predict next month's spending using simple moving average
        """
        today = datetime.now()
        
        # Get last 3 months spending
        monthly_totals = []
        for i in range(1, 4):  # Last 3 months (not including current)
            month_start = (today - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
            
            total = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.project_id == project_id,
                Transaction.type == 'expense',
                Transaction.occurred_at >= month_start,
                Transaction.occurred_at <= month_end,
                Transaction.deleted_at.is_(None)
            ).scalar() or 0
            
            monthly_totals.append(total / 100)
        
        if not monthly_totals or all(t == 0 for t in monthly_totals):
            return {
                'predicted_amount': 0,
                'confidence': 'low',
                'based_on_months': 0
            }
        
        # Simple moving average
        avg = statistics.mean(monthly_totals)
        
        # Calculate standard deviation for confidence
        if len(monthly_totals) > 1:
            std_dev = statistics.stdev(monthly_totals)
            confidence = 'high' if std_dev < avg * 0.2 else ('medium' if std_dev < avg * 0.5 else 'low')
        else:
            confidence = 'low'
        
        return {
            'predicted_amount': round(avg, 2),
            'confidence': confidence,
            'based_on_months': len([t for t in monthly_totals if t > 0]),
            'range_low': round(avg * 0.85, 2),
            'range_high': round(avg * 1.15, 2)
        }
    
    @staticmethod
    def calculate_financial_health(project_id):
        """
        Calculate financial health score (0-100) based on multiple factors
        """
        today = datetime.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get current month data
        income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'income',
            Transaction.occurred_at >= month_start,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0
        
        expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= month_start,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0
        
        income_baht = income / 100
        expense_baht = expense / 100
        
        # Calculate scores
        scores = {}
        strengths = []
        improvements = []
        
        # 1. Savings Rate Score (0-30 points)
        if income_baht > 0:
            savings_rate = ((income_baht - expense_baht) / income_baht) * 100
            if savings_rate >= 20:
                scores['savings'] = 30
                strengths.append(f"ออมได้ {savings_rate:.0f}% ของรายได้ (ดีมาก!)")
            elif savings_rate >= 10:
                scores['savings'] = 20
                strengths.append(f"ออมได้ {savings_rate:.0f}% ของรายได้")
            elif savings_rate >= 0:
                scores['savings'] = 10
                improvements.append("พยายามออมให้ได้ 20% ของรายได้")
            else:
                scores['savings'] = 0
                improvements.append("⚠️ ใช้จ่ายเกินรายได้")
        else:
            scores['savings'] = 0
            improvements.append("ยังไม่มีข้อมูลรายรับ")
        
        # 2. Budget Discipline Score (0-25 points)
        budgets = Budget.query.filter_by(
            project_id=project_id,
            month_yyyymm=today.strftime('%Y-%m')
        ).all()
        
        if budgets:
            over_budget = 0
            for b in budgets:
                spent = db.session.query(func.sum(Transaction.amount)).filter(
                    Transaction.project_id == project_id,
                    Transaction.category_id == b.category_id,
                    Transaction.type == 'expense',
                    Transaction.occurred_at >= month_start,
                    Transaction.deleted_at.is_(None)
                ).scalar() or 0
                if spent > b.limit_amount:
                    over_budget += 1
            
            if over_budget == 0:
                scores['budget'] = 25
                strengths.append("ไม่เกินงบประมาณทุกหมวด")
            elif over_budget <= len(budgets) * 0.3:
                scores['budget'] = 15
                improvements.append(f"มี {over_budget} หมวดที่เกินงบ")
            else:
                scores['budget'] = 5
                improvements.append(f"⚠️ เกินงบหลายหมวด")
        else:
            scores['budget'] = 10
            improvements.append("ลองตั้งงบประมาณเพื่อควบคุมรายจ่าย")
        
        # 3. Consistency Score (0-25 points) - Based on transaction regularity
        trans_count = Transaction.query.filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= month_start,
            Transaction.deleted_at.is_(None)
        ).count()
        
        if trans_count >= 20:
            scores['consistency'] = 25
            strengths.append("บันทึกรายการสม่ำเสมอ")
        elif trans_count >= 10:
            scores['consistency'] = 15
        else:
            scores['consistency'] = 5
            improvements.append("บันทึกรายการให้บ่อยขึ้นเพื่อติดตามได้ดี")
        
        # 4. 50/30/20 Rule Score (0-20 points)
        if income_baht > 0 and expense_baht > 0:
            expense_ratio = (expense_baht / income_baht) * 100
            if expense_ratio <= 80:  # 80% or less on expenses = good
                scores['rule_5030'] = 20
                strengths.append("สัดส่วนรายจ่ายอยู่ในเกณฑ์ดี")
            elif expense_ratio <= 90:
                scores['rule_5030'] = 10
            else:
                scores['rule_5030'] = 0
                improvements.append("รายจ่ายสูงเกินไป ลองลด 10%")
        else:
            scores['rule_5030'] = 10
        
        # Calculate total score
        total_score = sum(scores.values())
        
        # Grade
        if total_score >= 85:
            grade = 'A'
            grade_text = 'ยอดเยี่ยม'
        elif total_score >= 70:
            grade = 'B'
            grade_text = 'ดี'
        elif total_score >= 55:
            grade = 'C'
            grade_text = 'พอใช้'
        elif total_score >= 40:
            grade = 'D'
            grade_text = 'ควรปรับปรุง'
        else:
            grade = 'F'
            grade_text = 'ต้องปรับปรุงด่วน'
        
        return {
            'score': total_score,
            'grade': grade,
            'grade_text': grade_text,
            'breakdown': scores,
            'strengths': strengths,
            'improvements': improvements,
            'income': income_baht,
            'expense': expense_baht
        }
    
    @staticmethod
    def get_smart_advice(project_id, user_occupation=None):
        """
        Generate personalized financial advice
        """
        health = AIAnalyticsService.calculate_financial_health(project_id)
        spending = AIAnalyticsService.get_spending_analysis(project_id)
        prediction = AIAnalyticsService.predict_next_month(project_id)
        
        advice = []
        
        # Based on health score
        if health['score'] < 50:
            advice.append({
                'priority': 'high',
                'title': '⚠️ ควรปรับปรุงการเงินด่วน',
                'content': 'รายจ่ายสูงกว่ารายรับ หรือออมได้น้อย ลองทบทวนรายจ่ายที่ไม่จำเป็น'
            })
        
        # Based on spending trend
        if spending['trend'] == 'increasing' and spending['change_percent'] > 20:
            advice.append({
                'priority': 'medium',
                'title': '📈 รายจ่ายเพิ่มขึ้นมาก',
                'content': f"รายจ่ายเพิ่มขึ้น {spending['change_percent']:.0f}% จากเดือนที่แล้ว ลองตรวจสอบหมวดที่ใช้มากที่สุด"
            })
        
        # Top spending category advice
        if spending['category_breakdown']:
            top_cat = spending['category_breakdown'][0]
            if top_cat['percentage'] > 40:
                advice.append({
                    'priority': 'medium',
                    'title': f"💸 หมวด '{top_cat['name']}' ใช้มากถึง {top_cat['percentage']:.0f}%",
                    'content': f"ลองหาวิธีลดค่าใช้จ่ายหมวดนี้ 10% จะประหยัดได้ {top_cat['amount']*0.1:,.0f} บาท/เดือน"
                })
        
        # 50/30/20 Rule advice
        if health['income'] > 0:
            needs_budget = health['income'] * 0.5
            wants_budget = health['income'] * 0.3
            savings_target = health['income'] * 0.2
            
            advice.append({
                'priority': 'info',
                'title': '📊 กฎ 50/30/20 สำหรับคุณ',
                'content': f"รายได้ {health['income']:,.0f}฿\n• ค่าใช้จ่ายจำเป็น: {needs_budget:,.0f}฿\n• ความต้องการ: {wants_budget:,.0f}฿\n• ออมเงิน: {savings_target:,.0f}฿"
            })
        
        # Emergency fund advice
        if health['expense'] > 0:
            emergency_fund = health['expense'] * 6
            advice.append({
                'priority': 'info',
                'title': '🛡️ เป้าหมาย Emergency Fund',
                'content': f"ควรมีเงินสำรองฉุกเฉิน 6 เดือน = {emergency_fund:,.0f} บาท"
            })
        
        # Prediction advice
        if prediction['predicted_amount'] > 0:
            advice.append({
                'priority': 'info',
                'title': '🔮 คาดการณ์เดือนหน้า',
                'content': f"คาดว่าจะใช้จ่ายประมาณ {prediction['predicted_amount']:,.0f} บาท ({prediction['range_low']:,.0f}-{prediction['range_high']:,.0f})"
            })
        
        return {
            'health_score': health['score'],
            'health_grade': health['grade'],
            'advice': advice
        }
