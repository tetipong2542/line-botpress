"""
Budget Service
Business logic for budget management
"""
from datetime import datetime
from sqlalchemy import func, and_
from app import db
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.utils.helpers import generate_id, baht_to_satang, satang_to_baht


class BudgetService:
    """Service for budget management"""

    @staticmethod
    def create_budget(project_id, category_id, month_yyyymm, limit_amount, rollover_policy='none'):
        """
        Create a budget for a category in a specific month

        Args:
            project_id: Project ID
            category_id: Category ID
            month_yyyymm: Month in format "YYYY-MM"
            limit_amount: Budget limit in satang
            rollover_policy: 'none', 'add', 'reset'

        Returns:
            Budget object

        Raises:
            ValueError: If validation fails
        """
        # Validate category belongs to project
        category = Category.query.filter_by(
            id=category_id,
            project_id=project_id,
            deleted_at=None
        ).first()

        if not category:
            raise ValueError("Category not found or doesn't belong to project")

        # Validate month format
        try:
            datetime.strptime(month_yyyymm, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid month format. Use YYYY-MM")

        # Check if budget already exists
        existing = Budget.query.filter_by(
            project_id=project_id,
            category_id=category_id,
            month_yyyymm=month_yyyymm
        ).first()

        if existing:
            raise ValueError(f"Budget already exists for {category.name_th} in {month_yyyymm}")

        # Create budget
        budget = Budget(
            project_id=project_id,
            category_id=category_id,
            month_yyyymm=month_yyyymm,
            limit_amount=limit_amount,
            rollover_policy=rollover_policy
        )

        db.session.add(budget)
        db.session.commit()

        return budget

    @staticmethod
    def get_budgets(project_id, month_yyyymm=None):
        """
        Get budgets for a project, optionally filtered by month

        Args:
            project_id: Project ID
            month_yyyymm: Optional month filter in "YYYY-MM"

        Returns:
            List of budget dicts with spending information
        """
        query = Budget.query.filter_by(project_id=project_id)

        if month_yyyymm:
            query = query.filter_by(month_yyyymm=month_yyyymm)

        budgets = query.all()

        # Enrich with spending data
        result = []
        for budget in budgets:
            budget_dict = budget.to_dict()

            # Get category info
            category = Category.query.get(budget.category_id)
            if category:
                budget_dict['category'] = {
                    'id': category.id,
                    'name_th': category.name_th,
                    'icon': category.icon,
                    'color': category.color,
                    'type': category.type
                }

            # Calculate spending for this month
            year, month = map(int, budget.month_yyyymm.split('-'))
            start_date = datetime(year, month, 1)

            # Calculate end date (first day of next month)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            # Get total spending in this category for this month
            spent_total = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.project_id == project_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == 'expense',
                Transaction.occurred_at >= start_date,
                Transaction.occurred_at < end_date,
                Transaction.deleted_at.is_(None)
            ).scalar() or 0

            budget_dict['spent'] = spent_total
            budget_dict['spent_formatted'] = satang_to_baht(spent_total)
            budget_dict['remaining'] = budget.limit_amount - spent_total
            budget_dict['remaining_formatted'] = satang_to_baht(budget.limit_amount - spent_total)

            # Calculate percentage
            if budget.limit_amount > 0:
                usage_pct = (spent_total / budget.limit_amount) * 100
                budget_dict['usage_percentage'] = round(usage_pct, 1)
            else:
                budget_dict['usage_percentage'] = 0

            # Status flags
            budget_dict['is_over_budget'] = spent_total > budget.limit_amount
            budget_dict['is_near_limit'] = spent_total >= (budget.limit_amount * 0.8)

            result.append(budget_dict)

        # Sort by usage percentage (descending)
        result.sort(key=lambda x: x['usage_percentage'], reverse=True)

        return result

    @staticmethod
    def get_budget(budget_id, project_id):
        """Get a single budget"""
        budget = Budget.query.filter_by(
            id=budget_id,
            project_id=project_id
        ).first()

        if not budget:
            raise ValueError("Budget not found")

        # Enrich with data
        budgets = BudgetService.get_budgets(project_id, budget.month_yyyymm)
        budget_dict = next((b for b in budgets if b['id'] == budget_id), None)

        if not budget_dict:
            raise ValueError("Budget not found")

        return budget_dict

    @staticmethod
    def update_budget(budget_id, project_id, limit_amount=None, rollover_policy=None):
        """
        Update a budget

        Args:
            budget_id: Budget ID
            project_id: Project ID
            limit_amount: New limit amount in satang (optional)
            rollover_policy: New rollover policy (optional)

        Returns:
            Updated budget dict
        """
        budget = Budget.query.filter_by(
            id=budget_id,
            project_id=project_id
        ).first()

        if not budget:
            raise ValueError("Budget not found")

        # Update fields
        if limit_amount is not None:
            if limit_amount < 0:
                raise ValueError("Budget limit must be positive")
            budget.limit_amount = limit_amount

        if rollover_policy is not None:
            if rollover_policy not in ['none', 'add', 'reset']:
                raise ValueError("Invalid rollover policy")
            budget.rollover_policy = rollover_policy

        budget.updated_at = datetime.utcnow()
        db.session.commit()

        # Return enriched data
        return BudgetService.get_budget(budget_id, project_id)

    @staticmethod
    def delete_budget(budget_id, project_id):
        """
        Delete a budget

        Args:
            budget_id: Budget ID
            project_id: Project ID

        Returns:
            True if deleted
        """
        budget = Budget.query.filter_by(
            id=budget_id,
            project_id=project_id
        ).first()

        if not budget:
            raise ValueError("Budget not found")

        db.session.delete(budget)
        db.session.commit()

        return True

    @staticmethod
    def get_budget_summary(project_id, month_yyyymm):
        """
        Get budget summary for a month

        Args:
            project_id: Project ID
            month_yyyymm: Month in "YYYY-MM"

        Returns:
            dict with total budgeted, spent, remaining
        """
        budgets = BudgetService.get_budgets(project_id, month_yyyymm)

        total_budgeted = sum(b['limit_amount'] for b in budgets)
        total_spent = sum(b['spent'] for b in budgets)
        total_remaining = total_budgeted - total_spent

        return {
            'month': month_yyyymm,
            'total_budgeted': total_budgeted,
            'total_budgeted_formatted': satang_to_baht(total_budgeted),
            'total_spent': total_spent,
            'total_spent_formatted': satang_to_baht(total_spent),
            'total_remaining': total_remaining,
            'total_remaining_formatted': satang_to_baht(total_remaining),
            'usage_percentage': round((total_spent / total_budgeted * 100), 1) if total_budgeted > 0 else 0,
            'budgets_count': len(budgets),
            'over_budget_count': sum(1 for b in budgets if b['is_over_budget'])
        }

    @staticmethod
    def get_dashboard_budgets(project_id, month_yyyymm, limit=3):
        """
        Get top budgets for dashboard display
        
        Returns top N budgets sorted by:
        1. Over budget (>100%)
        2. Near limit (>80%)
        3. Highest usage
        
        Args:
            project_id: Project ID
            month_yyyymm: Month in "YYYY-MM"
            limit: Number of budgets to return (default 3)
            
        Returns:
            List of budget dicts sorted by priority
        """
        budgets = BudgetService.get_budgets(project_id, month_yyyymm)
        
        if not budgets:
            return []
        
        # Sort by priority:
        # 1. Over budget first (>100%)
        # 2. Near limit next (>80%)
        # 3. Then by usage percentage
        def sort_key(budget):
            usage = budget['usage_percentage']
            if usage > 100:
                return (0, -usage)  # Over budget - highest priority
            elif usage > 80:
                return (1, -usage)  # Near limit - medium priority
            else:
                return (2, -usage)  # Normal - sorted by usage
        
        sorted_budgets = sorted(budgets, key=sort_key)
        
        return sorted_budgets[:limit]
