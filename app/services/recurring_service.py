"""
Recurring transaction service - Business logic for recurring rules
"""
from datetime import datetime, date
from app import db
from app.models.recurring import RecurringRule
from app.models.category import Category
from app.models.project import Project, ProjectMember
from app.models.transaction import Transaction
from app.utils.validators import (
    validate_transaction_type,
    validate_amount,
    validate_frequency,
    validate_recurring_day
)
from app.utils.helpers import baht_to_satang


class RecurringService:
    """Service for recurring transaction operations"""

    @staticmethod
    def create_recurring_rule(project_id, user_id, type, category_id, amount, freq,
                             start_date, day_of_week=None, day_of_month=None,
                             note=None, member_id=None, remind_days=0):
        """
        Create a new recurring transaction rule

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            type: Transaction type ('income' or 'expense')
            category_id: Category ID
            amount: Amount (in satang or baht - will be converted)
            freq: Frequency ('daily', 'weekly', 'monthly')
            start_date: Start date (date object or ISO string)
            day_of_week: Day of week (0-6) for weekly
            day_of_month: Day of month (1-31) for monthly
            note: Optional note
            member_id: Optional member ID
            remind_days: Days before to remind (default: 0)

        Returns:
            RecurringRule object

        Raises:
            ValueError: If validation fails
            PermissionError: If user doesn't have access
        """
        # Check user has access to project
        if not RecurringService._check_project_access(project_id, user_id):
            raise PermissionError("User doesn't have access to this project")

        # Validate inputs
        type = validate_transaction_type(type)
        freq = validate_frequency(freq)

        # Validate day based on frequency
        day_of_week, day_of_month = validate_recurring_day(freq, day_of_week, day_of_month)

        # Check category exists and belongs to project
        category = Category.query.get(category_id)
        if not category or category.project_id != project_id:
            raise ValueError("Invalid category for this project")

        # Validate category type matches transaction type
        if category.type != type:
            raise ValueError(f"Category type mismatch: category is {category.type}, transaction is {type}")

        # Convert amount to satang (handle both int and float from JSON)
        # Frontend always sends in Baht, so convert to satang
        if isinstance(amount, (int, float)):
            amount = baht_to_satang(amount)
        amount = validate_amount(amount)

        # Parse start_date
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()

        # Create recurring rule
        recurring_rule = RecurringRule(
            project_id=project_id,
            type=type,
            category_id=category_id,
            amount=amount,
            freq=freq,
            start_date=start_date,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            note=note,
            member_id=member_id
        )
        recurring_rule.remind_days = remind_days

        db.session.add(recurring_rule)
        db.session.commit()

        return recurring_rule

    @staticmethod
    def get_recurring_rules(project_id, user_id, active_only=True):
        """
        Get recurring rules for project

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            active_only: Only return active rules (default: True)

        Returns:
            List of RecurringRule objects with category data
        """
        from sqlalchemy.orm import joinedload
        
        # Check access
        if not RecurringService._check_project_access(project_id, user_id):
            raise PermissionError("User doesn't have access to this project")

        query = RecurringRule.query.filter_by(project_id=project_id).options(
            joinedload(RecurringRule.category)  # Eager load category data
        )

        if active_only:
            query = query.filter_by(is_active=True)

        # Order by next run date
        return query.order_by(RecurringRule.next_run_date).all()

    @staticmethod
    def get_recurring_rule(recurring_id, user_id):
        """
        Get a single recurring rule by ID

        Args:
            recurring_id: RecurringRule ID
            user_id: User ID (for permission check)

        Returns:
            RecurringRule object

        Raises:
            ValueError: If rule not found
            PermissionError: If user doesn't have access
        """
        recurring_rule = RecurringRule.query.get(recurring_id)

        if not recurring_rule:
            raise ValueError("Recurring rule not found")

        # Check access
        if not RecurringService._check_project_access(recurring_rule.project_id, user_id):
            raise PermissionError("User doesn't have access to this recurring rule")

        return recurring_rule

    @staticmethod
    def update_recurring_rule(recurring_id, user_id, updates):
        """
        Update a recurring rule

        Args:
            recurring_id: RecurringRule ID
            user_id: User ID (for permission check)
            updates: Dictionary of fields to update

        Returns:
            Updated RecurringRule object
        """
        recurring_rule = RecurringRule.query.get(recurring_id)

        if not recurring_rule:
            raise ValueError("Recurring rule not found")

        # Check access
        if not RecurringService._check_project_access(recurring_rule.project_id, user_id):
            raise PermissionError("User doesn't have access to this recurring rule")

        # Track if we need to recalculate next_run_date
        needs_recalc = False

        # Update fields
        if 'amount' in updates:
            amount = updates['amount']
            # Convert amount to satang (handle both int and float from JSON)
            # If amount < 10000, treat as Baht and convert to satang
            # If amount >= 10000, assume already in satang
            if isinstance(amount, (int, float)) and amount < 10000:
                amount = baht_to_satang(amount)
            recurring_rule.amount = validate_amount(amount)

        if 'type' in updates:
            recurring_rule.type = validate_transaction_type(updates['type'])

        if 'category_id' in updates:
            category = Category.query.get(updates['category_id'])
            if not category or category.project_id != recurring_rule.project_id:
                raise ValueError("Invalid category for this project")
            recurring_rule.category_id = updates['category_id']

        if 'freq' in updates:
            recurring_rule.freq = validate_frequency(updates['freq'])
            needs_recalc = True

        if 'day_of_week' in updates:
            recurring_rule.day_of_week = updates['day_of_week']
            needs_recalc = True

        if 'day_of_month' in updates:
            recurring_rule.day_of_month = updates['day_of_month']
            needs_recalc = True

        if 'start_date' in updates:
            start_date = updates['start_date']
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
            recurring_rule.start_date = start_date
            needs_recalc = True

        if 'note' in updates:
            recurring_rule.note = updates['note']

        if 'remind_days' in updates:
            recurring_rule.remind_days = int(updates['remind_days'])

        if 'is_active' in updates:
            recurring_rule.is_active = bool(updates['is_active'])

        # Recalculate next_run_date if frequency or day changed
        if needs_recalc:
            recurring_rule.next_run_date = recurring_rule._calculate_next_run(recurring_rule.start_date)

        db.session.commit()

        return recurring_rule

    @staticmethod
    def delete_recurring_rule(recurring_id, user_id):
        """
        Delete (deactivate) a recurring rule

        Args:
            recurring_id: RecurringRule ID
            user_id: User ID (for permission check)

        Returns:
            True if successful
        """
        recurring_rule = RecurringRule.query.get(recurring_id)

        if not recurring_rule:
            raise ValueError("Recurring rule not found")

        # Check access
        if not RecurringService._check_project_access(recurring_rule.project_id, user_id):
            raise PermissionError("User doesn't have access to this recurring rule")

        # Soft delete - set is_active to False
        recurring_rule.is_active = False
        db.session.commit()

        return True

    @staticmethod
    def execute_recurring_rule(recurring_id, user_id):
        """
        Manually execute a recurring rule (create transaction and update next_run_date)

        Args:
            recurring_id: RecurringRule ID
            user_id: User ID (for permission check)

        Returns:
            Created Transaction object
        """
        recurring_rule = RecurringRule.query.get(recurring_id)

        if not recurring_rule or not recurring_rule.is_active:
            raise ValueError("Recurring rule not found or inactive")

        # Check access
        if not RecurringService._check_project_access(recurring_rule.project_id, user_id):
            raise PermissionError("User doesn't have access to this recurring rule")

        # Create transaction
        transaction = Transaction(
            project_id=recurring_rule.project_id,
            type=recurring_rule.type,
            category_id=recurring_rule.category_id,
            amount=recurring_rule.amount,
            occurred_at=datetime.utcnow(),
            note=recurring_rule.note,
            member_id=recurring_rule.member_id
        )
        transaction.recurring_rule_id = recurring_rule.id

        db.session.add(transaction)

        # Update next run date
        recurring_rule.update_next_run()

        db.session.commit()

        return transaction

    @staticmethod
    def _check_project_access(project_id, user_id):
        """
        Check if user has access to project

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            bool: True if user has access
        """
        # Check if user is owner
        project = Project.query.get(project_id)
        if project and project.owner_user_id == user_id:
            return True

        # Check if user is member
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()

        return member is not None
