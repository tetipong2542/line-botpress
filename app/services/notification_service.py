"""
Notification Service - Handle user notifications
"""
from datetime import datetime, timedelta
from app import db
from app.models.notification import Notification, NotificationPreference
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.recurring import RecurringRule
from sqlalchemy import func


class NotificationService:
    """Service for managing user notifications"""

    @staticmethod
    def get_or_create_preference(user_id):
        """Get or create notification preference for user"""
        preference = NotificationPreference.query.filter_by(user_id=user_id).first()
        if not preference:
            preference = NotificationPreference(user_id=user_id)
            db.session.add(preference)
            db.session.commit()
        return preference

    @staticmethod
    def create_notification(user_id, type, title, message, project_id=None, data=None):
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            project_id=project_id,
            data=data
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def get_user_notifications(user_id, unread_only=False, limit=50):
        """Get notifications for user"""
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return [n.to_dict() for in notifications]

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark notification as read"""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.mark_as_read()
            return True
        return False

    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for user"""
        notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        for notification in notifications:
            notification.is_read = True
        db.session.commit()
        return len(notifications)

    @staticmethod
    def check_budget_alerts(project_id, month_yyyymm=None):
        """Check budget thresholds and create alerts if needed"""
        if not month_yyyymm:
            month_yyyymm = datetime.now().strftime('%Y-%m')

        # Get all budgets for this project and month
        budgets = Budget.query.filter_by(
            project_id=project_id,
            month_yyyymm=month_yyyymm
        ).all()

        alerts_created = []

        for budget in budgets:
            # Get owner's notification preference
            preference = NotificationService.get_or_create_preference(budget.project.owner_user_id)

            if not preference.budget_alerts:
                continue

            # Calculate spending for this category
            from app.models.transaction import Transaction
            start_date = datetime.strptime(f"{month_yyyymm}-01", '%Y-%m-%d')
            if month_yyyymm.endswith('12'):
                end_date = datetime.strptime(f"{int(month_yyyymm[:4]) + 1}-01-01", '%Y-%m-%d')
            else:
                end_date = datetime.strptime(f"{month_yyyymm[:4]}-{int(month_yyyymm[5:]) + 1:02d}-01", '%Y-%m-%d')

            transactions = Transaction.query.filter(
                Transaction.project_id == project_id,
                Transaction.category_id == budget.category_id,
                Transaction.occurred_at >= start_date,
                Transaction.occurred_at < end_date,
                Transaction.type == 'expense'
            ).all()

            total_spent = sum(t.amount for t in transactions)
            usage_percentage = (total_spent / budget.limit_amount) * 100 if budget.limit_amount > 0 else 0

            # Check if threshold exceeded
            if usage_percentage >= preference.budget_threshold:
                # Check if alert already created for this budget today
                existing_alert = Notification.query.filter_by(
                    user_id=budget.project.owner_user_id,
                    type='budget_alert',
                    project_id=project_id
                ).filter(
                    Notification.data['budget_id'].astext == budget.id
                ).filter(
                    Notification.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                ).first()

                if not existing_alert:
                    category = budget.category
                    alert_title = f"แจ้งเตือนงบประมาณ: {category.name_th}"
                    alert_message = f"คุณใช้ไป {usage_percentage:.0f}% ของงบประมาณหมวดหมู่ '{category.name_th}' (฿{total_spent/100:.2f} / ฿{budget.limit_amount/100:.2f})"

                    notification = NotificationService.create_notification(
                        user_id=budget.project.owner_user_id,
                        type='budget_alert',
                        title=alert_title,
                        message=alert_message,
                        project_id=project_id,
                        data={
                            'budget_id': budget.id,
                            'category_id': budget.category_id,
                            'usage_percentage': round(usage_percentage, 2),
                            'spent': total_spent,
                            'limit': budget.limit_amount
                        }
                    )
                    alerts_created.append(notification.to_dict())

        return alerts_created

    @staticmethod
    def check_recurring_reminders():
        """Check for recurring transactions due soon"""
        tomorrow = datetime.now().date() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%d')  # Day of month

        # Get recurring rules that run on this day
        recurring_rules = RecurringRule.query.filter(
            RecurringRule.is_active == True,
            RecurringRule.frequency == 'monthly',
            func.extract('day', RecurringRule.next_run_date) == int(tomorrow_str)
        ).all()

        reminders_created = []

        for rule in recurring_rules:
            preference = NotificationService.get_or_create_preference(rule.project.owner_user_id)

            if not preference.recurring_reminders:
                continue

            # Check if reminder already created today
            existing_reminder = Notification.query.filter_by(
                user_id=rule.project.owner_user_id,
                type='recurring_reminder',
                project_id=rule.project_id
            ).filter(
                Notification.data['recurring_rule_id'].astext == rule.id
            ).filter(
                Notification.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).first()

            if not existing_reminder:
                category = rule.category
                reminder_title = f"รายการประจำพรุ่งนี้: {category.name_th}"
                reminder_message = f"รายการ '{rule.note or category.name_th}' จะครบกำหนดพรุ่งนี้ (฿{rule.amount/100:.2f})"

                notification = NotificationService.create_notification(
                    user_id=rule.project.owner_user_id,
                    type='recurring_reminder',
                    title=reminder_title,
                    message=reminder_message,
                    project_id=rule.project_id,
                    data={
                        'recurring_rule_id': rule.id,
                        'category_id': rule.category_id,
                        'amount': rule.amount,
                        'next_run_date': rule.next_run_date.isoformat() if rule.next_run_date else None
                    }
                )
                reminders_created.append(notification.to_dict())

        return reminders_created

    @staticmethod
    def update_preference(user_id, preferences_data):
        """Update user notification preferences"""
        preference = NotificationService.get_or_create_preference(user_id)

        updatable_fields = [
            'budget_alerts',
            'budget_threshold',
            'recurring_reminders',
            'reminder_days_before',
            'weekly_summary',
            'weekly_summary_day',
            'insights',
            'line_notifications'
        ]

        for field in updatable_fields:
            if field in preferences_data:
                setattr(preference, field, preferences_data[field])

        preference.updated_at = datetime.utcnow()
        db.session.commit()

        return preference.to_dict()

    @staticmethod
    def delete_old_notifications(days=30):
        """Delete notifications older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        old_notifications = Notification.query.filter(
            Notification.is_read == True,
            Notification.created_at < cutoff_date
        ).all()

        count = len(old_notifications)
        for notification in old_notifications:
            db.session.delete(notification)

        db.session.commit()
        return count
