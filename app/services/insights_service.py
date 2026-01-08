"""
Insights Service
Smart insights, alerts, and recommendations for financial management
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
from app import db
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.recurring_rule import RecurringRule
from app.utils.helpers import satang_to_baht, get_month_range


class InsightsService:
    """Service for smart financial insights and alerts"""

    @staticmethod
    def get_budget_alerts(project_id, month_yyyymm=None):
        """
        Get budget alerts for current or specified month
        
        Returns alerts when budget usage reaches thresholds:
        - 75% (warning)
        - 85% (danger)
        - 95% (critical)
        - 100%+ (over budget)
        
        Returns:
            list: [
                {
                    'type': 'error' | 'warning' | 'info',
                    'category': 'Category Name',
                    'category_icon': '🍔',
                    'message': 'Alert message',
                    'percentage': 85,
                    'spent': 8500,
                    'limit': 10000,
                    'remaining': 1500,
                    'days_left': 15
                }
            ]
        """
        if not month_yyyymm:
            month_yyyymm = datetime.now().strftime('%Y-%m')
        
        year, month = map(int, month_yyyymm.split('-'))
        start_date, end_date = get_month_range(year, month)
        
        # Calculate days left in month
        today = datetime.now()
        days_left = (end_date - today).days
        
        alerts = []
        
        # Get all budgets for the month
        budgets = Budget.query.filter_by(
            project_id=project_id,
            month_yyyymm=month_yyyymm
        ).all()
        
        for budget in budgets:
            # Get spending for this category
            spent = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.project_id == project_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == 'expense',
                Transaction.occurred_at >= start_date,
                Transaction.occurred_at < end_date,
                Transaction.deleted_at.is_(None)
            ).scalar() or 0
            
            if budget.limit_amount == 0:
                continue
                
            percentage = int((spent / budget.limit_amount) * 100)
            remaining = budget.limit_amount - spent
            
            alert = None
            
            # Critical: Over budget
            if percentage >= 100:
                alert = {
                    'type': 'error',
                    'icon': '🔴',
                    'title': 'เกินงบประมาณ!',
                    'category': budget.category.name_th if budget.category else 'ไม่ระบุ',
                    'category_icon': budget.category.icon if budget.category else '📁',
                    'message': f'ใช้ไปแล้ว {percentage}% เกินงบ ฿{satang_to_baht(abs(remaining)):,.0f}',
                    'percentage': percentage,
                    'spent': spent,
                    'limit': budget.limit_amount,
                    'remaining': remaining,
                    'days_left': days_left
                }
            # Danger: 85-99%
            elif percentage >= 85:
                alert = {
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': 'ใกล้เกินงบ',
                    'category': budget.category.name_th if budget.category else 'ไม่ระบุ',
                    'category_icon': budget.category.icon if budget.category else '📁',
                    'message': f'ใช้ไป {percentage}% เหลือ ฿{satang_to_baht(remaining):,.0f} ({days_left} วัน)',
                    'percentage': percentage,
                    'spent': spent,
                    'limit': budget.limit_amount,
                    'remaining': remaining,
                    'days_left': days_left
                }
            # Warning: 75-84%
            elif percentage >= 75:
                alert = {
                    'type': 'info',
                    'icon': '💡',
                    'title': 'ควรระวัง',
                    'category': budget.category.name_th if budget.category else 'ไม่ระบุ',
                    'category_icon': budget.category.icon if budget.category else '📁',
                    'message': f'ใช้ไป {percentage}% เหลือ ฿{satang_to_baht(remaining):,.0f}',
                    'percentage': percentage,
                    'spent': spent,
                    'limit': budget.limit_amount,
                    'remaining': remaining,
                    'days_left': days_left
                }
            
            if alert:
                alerts.append(alert)
        
        # Sort by percentage (highest first)
        alerts.sort(key=lambda x: x['percentage'], reverse=True)
        
        return alerts

    @staticmethod
    def get_spending_trends(project_id):
        """
        Get spending trends comparing current week with previous week
        
        Returns:
            {
                'current_week': {
                    'total': 5000,
                    'start_date': '2026-01-06',
                    'end_date': '2026-01-12'
                },
                'previous_week': {
                    'total': 4500,
                    'start_date': '2025-12-30',
                    'end_date': '2026-01-05'
                },
                'change': {
                    'amount': 500,
                    'percentage': 11.1,
                    'direction': 'up' | 'down' | 'same'
                },
                'top_categories': [
                    {
                        'category': 'อาหาร',
                        'icon': '🍔',
                        'current': 1800,
                        'previous': 1500,
                        'change_percentage': 20
                    }
                ]
            }
        """
        today = datetime.now()
        
        # Current week (Monday to Sunday)
        current_week_start = today - timedelta(days=today.weekday())
        current_week_start = current_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        current_week_end = current_week_start + timedelta(days=7)
        
        # Previous week
        previous_week_start = current_week_start - timedelta(days=7)
        previous_week_end = current_week_start
        
        # Current week total
        current_total = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= current_week_start,
            Transaction.occurred_at < current_week_end,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0
        
        # Previous week total
        previous_total = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= previous_week_start,
            Transaction.occurred_at < previous_week_end,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0
        
        # Calculate change
        change_amount = current_total - previous_total
        change_percentage = 0
        if previous_total > 0:
            change_percentage = (change_amount / previous_total) * 100
        
        direction = 'same'
        if change_percentage > 5:
            direction = 'up'
        elif change_percentage < -5:
            direction = 'down'
        
        # Get top categories for current week
        top_categories_query = db.session.query(
            Category.name_th,
            Category.icon,
            func.sum(Transaction.amount).label('total')
        ).join(
            Transaction, Transaction.category_id == Category.id
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= current_week_start,
            Transaction.occurred_at < current_week_end,
            Transaction.deleted_at.is_(None)
        ).group_by(
            Category.id
        ).order_by(
            desc('total')
        ).limit(3).all()
        
        top_categories = []
        for cat_name, cat_icon, cat_total in top_categories_query:
            # Get previous week total for this category
            cat_previous = db.session.query(
                func.sum(Transaction.amount)
            ).join(
                Category, Transaction.category_id == Category.id
            ).filter(
                Transaction.project_id == project_id,
                Category.name_th == cat_name,
                Transaction.type == 'expense',
                Transaction.occurred_at >= previous_week_start,
                Transaction.occurred_at < previous_week_end,
                Transaction.deleted_at.is_(None)
            ).scalar() or 0
            
            cat_change = 0
            if cat_previous > 0:
                cat_change = ((cat_total - cat_previous) / cat_previous) * 100
            elif cat_total > 0:
                cat_change = 100
            
            top_categories.append({
                'category': cat_name,
                'icon': cat_icon or '📁',
                'current': cat_total,
                'previous': cat_previous,
                'change_percentage': round(cat_change, 1)
            })
        
        return {
            'current_week': {
                'total': current_total,
                'start_date': current_week_start.strftime('%Y-%m-%d'),
                'end_date': (current_week_end - timedelta(days=1)).strftime('%Y-%m-%d')
            },
            'previous_week': {
                'total': previous_total,
                'start_date': previous_week_start.strftime('%Y-%m-%d'),
                'end_date': (previous_week_end - timedelta(days=1)).strftime('%Y-%m-%d')
            },
            'change': {
                'amount': change_amount,
                'percentage': round(change_percentage, 1),
                'direction': direction
            },
            'top_categories': top_categories
        }

    @staticmethod
    def get_recurring_reminders(project_id, days_ahead=7):
        """
        Get upcoming recurring transactions that need attention
        
        Args:
            project_id: Project ID
            days_ahead: Look ahead this many days (default: 7)
        
        Returns:
            list: [
                {
                    'id': 'rec_xxx',
                    'category': 'Netflix',
                    'icon': '📺',
                    'amount': 29900,
                    'type': 'expense',
                    'next_run_date': '2026-01-15',
                    'days_until': 3
                }
            ]
        """
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        # Get active recurring rules with upcoming dates
        rules = RecurringRule.query.filter(
            RecurringRule.project_id == project_id,
            RecurringRule.is_active == True,
            RecurringRule.next_run_date.isnot(None),
            RecurringRule.next_run_date >= today,
            RecurringRule.next_run_date <= future_date
        ).order_by(RecurringRule.next_run_date).all()
        
        reminders = []
        for rule in rules:
            if rule.next_run_date:
                days_until = (rule.next_run_date - today).days
                
                reminders.append({
                    'id': rule.id,
                    'category': rule.category.name_th if rule.category else 'ไม่ระบุ',
                    'icon': rule.category.icon if rule.category else '📁',
                    'amount': rule.amount,
                    'type': rule.type,
                    'next_run_date': rule.next_run_date.strftime('%d/%m/%Y'),
                    'days_until': days_until,
                    'note': rule.note
                })
        
        return reminders

    @staticmethod
    def get_smart_recommendations(project_id, month_yyyymm=None):
        """
        Generate smart recommendations based on spending patterns
        
        Returns:
            list: [
                {
                    'type': 'budget_warning' | 'savings' | 'trend',
                    'title': 'Recommendation title',
                    'message': 'Detailed recommendation',
                    'action': 'Suggested action',
                    'priority': 'high' | 'medium' | 'low'
                }
            ]
        """
        if not month_yyyymm:
            month_yyyymm = datetime.now().strftime('%Y-%m')
        
        recommendations = []
        
        # Get budget alerts to generate recommendations
        alerts = InsightsService.get_budget_alerts(project_id, month_yyyymm)
        
        for alert in alerts:
            if alert['type'] == 'error':  # Over budget
                recommendations.append({
                    'type': 'budget_warning',
                    'icon': '⚠️',
                    'title': f'งบ "{alert["category"]}" เกินแล้ว',
                    'message': f'คุณใช้จ่ายเกินงบไป ฿{satang_to_baht(abs(alert["remaining"])):,.0f}',
                    'action': 'ลองลดรายจ่ายในหมวดนี้ หรือปรับงบให้สูงขึ้น',
                    'priority': 'high'
                })
            elif alert['type'] == 'warning' and alert['days_left'] > 0:
                # Calculate daily budget remaining
                daily_budget = alert['remaining'] / alert['days_left'] if alert['days_left'] > 0 else 0
                recommendations.append({
                    'type': 'budget_warning',
                    'icon': '💡',
                    'title': f'งบ "{alert["category"]}" ใกล้หมด',
                    'message': f'เหลือ ฿{satang_to_baht(alert["remaining"]):,.0f} สำหรับ {alert["days_left"]} วัน',
                    'action': f'ควรใช้ไม่เกิน ฿{satang_to_baht(daily_budget):,.0f}/วัน',
                    'priority': 'medium'
                })
        
        # Check spending trends
        trends = InsightsService.get_spending_trends(project_id)
        if trends['change']['direction'] == 'up' and trends['change']['percentage'] > 20:
            recommendations.append({
                'type': 'trend',
                'icon': '📈',
                'title': 'รายจ่ายสูงขึ้นกว่าปกติ',
                'message': f'สัปดาห์นี้ใช้เพิ่มขึ้น {abs(trends["change"]["percentage"]):.0f}%',
                'action': 'ลองตรวจสอบรายจ่ายที่ไม่จำเป็น',
                'priority': 'medium'
            })
        elif trends['change']['direction'] == 'down' and trends['change']['percentage'] < -15:
            recommendations.append({
                'type': 'savings',
                'icon': '💰',
                'title': 'ออมได้ดีมาก!',
                'message': f'สัปดาห์นี้ใช้น้อยลง {abs(trends["change"]["percentage"]):.0f}%',
                'action': 'เก็บเงินที่เหลือเข้าออมดีไหม?',
                'priority': 'low'
            })
        
        return recommendations
