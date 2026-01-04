"""
Analytics Service
Provides analytics and reporting functionality for financial data
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc, extract
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.utils.helpers import satang_to_baht, get_month_range


class AnalyticsService:
    """Service for analytics and reporting"""

    @staticmethod
    def get_monthly_summary(project_id, month_str):
        """
        Get income, expense, and balance summary for a specific month

        Args:
            project_id: Project ID
            month_str: Month in format "YYYY-MM" (e.g. "2026-01")

        Returns:
            dict: {
                "summary": {
                    "month": "2026-01",
                    "income": {
                        "total": 50000,  # satang
                        "formatted": 500.00,  # baht
                        "count": 5
                    },
                    "expense": {
                        "total": 35000,
                        "formatted": 350.00,
                        "count": 25
                    },
                    "balance": {
                        "total": 15000,
                        "formatted": 150.00
                    }
                }
            }
        """
        # Parse month
        year, month = map(int, month_str.split('-'))
        start_date, end_date = get_month_range(year, month)

        # Query income total
        income_total = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'income',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        # Query income count
        income_count = db.session.query(
            func.count(Transaction.id)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'income',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        # Query expense total
        expense_total = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        # Query expense count
        expense_count = db.session.query(
            func.count(Transaction.id)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        # Calculate balance
        balance = income_total - expense_total

        return {
            "summary": {
                "month": month_str,
                "income": {
                    "total": income_total,
                    "formatted": satang_to_baht(income_total),
                    "count": income_count
                },
                "expense": {
                    "total": expense_total,
                    "formatted": satang_to_baht(expense_total),
                    "count": expense_count
                },
                "balance": {
                    "total": balance,
                    "formatted": satang_to_baht(balance)
                }
            }
        }

    @staticmethod
    def get_category_breakdown(project_id, month_str, type='expense'):
        """
        Get breakdown by category with budget comparison

        Args:
            project_id: Project ID
            month_str: Month in format "YYYY-MM"
            type: 'expense' or 'income'

        Returns:
            dict: {
                "categories": [
                    {
                        "category_id": "cat_xxx",
                        "category_name": "เดินทาง",
                        "category_icon": "car",
                        "category_color": "#F59E0B",
                        "type": "expense",
                        "total": 12000,
                        "formatted": 120.00,
                        "count": 8,
                        "percentage": 34.3,
                        "budget": {  # Optional - only if budget exists
                            "limit": 15000,
                            "formatted": 150.00,
                            "remaining": 3000,
                            "usage_percentage": 80.0
                        }
                    }
                ]
            }
        """
        # Parse month
        year, month = map(int, month_str.split('-'))
        start_date, end_date = get_month_range(year, month)
        month_yyyymm = month_str

        # Query category breakdown with LEFT JOIN to Budget
        results = db.session.query(
            Category.id,
            Category.name_th,
            Category.icon,
            Category.color,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count'),
            Budget.limit_amount
        ).join(
            Transaction,
            Transaction.category_id == Category.id
        ).outerjoin(
            Budget,
            and_(
                Budget.category_id == Category.id,
                Budget.month_yyyymm == month_yyyymm
            )
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == type,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            Category.id,
            Category.name_th,
            Category.icon,
            Category.color,
            Budget.limit_amount
        ).order_by(
            desc('total')
        ).all()

        # Calculate total for percentage
        grand_total = sum(r.total for r in results) if results else 0

        # Format results
        categories = []
        for r in results:
            cat = {
                "category_id": r.id,
                "category_name": r.name_th,
                "category_icon": r.icon,
                "category_color": r.color,
                "type": type,
                "total": r.total,
                "formatted": satang_to_baht(r.total),
                "count": r.count,
                "percentage": round((r.total / grand_total * 100), 1) if grand_total > 0 else 0
            }

            # Add budget info if exists
            if r.limit_amount:
                remaining = r.limit_amount - r.total
                cat["budget"] = {
                    "limit": r.limit_amount,
                    "formatted": satang_to_baht(r.limit_amount),
                    "remaining": remaining,
                    "usage_percentage": round((r.total / r.limit_amount * 100), 1)
                }

            categories.append(cat)

        return {"categories": categories}

    @staticmethod
    def get_trends(project_id, months=6):
        """
        Get income/expense trends for last N months

        Args:
            project_id: Project ID
            months: Number of months to analyze (default: 6)

        Returns:
            dict: {
                "trends": [
                    {
                        "month": "2025-08",
                        "month_label": "ส.ค. 2025",
                        "income": 45000,
                        "expense": 32000,
                        "balance": 13000
                    }
                ],
                "change": {
                    "income_change_percentage": 11.1,
                    "expense_change_percentage": 9.4
                }
            }
        """
        # Calculate date range
        today = datetime.now()
        start_month = today - timedelta(days=30 * months)

        # Query transactions grouped by month and type
        results = db.session.query(
            extract('year', Transaction.occurred_at).label('year'),
            extract('month', Transaction.occurred_at).label('month'),
            Transaction.type,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_month,
            Transaction.deleted_at.is_(None)
        ).group_by(
            'year',
            'month',
            Transaction.type
        ).order_by(
            'year',
            'month'
        ).all()

        # Process results into monthly data
        monthly_data = {}
        for r in results:
            month_key = f"{int(r.year)}-{str(int(r.month)).zfill(2)}"
            if month_key not in monthly_data:
                monthly_data[month_key] = {"income": 0, "expense": 0}

            if r.type == 'income':
                monthly_data[month_key]["income"] = r.total
            else:
                monthly_data[month_key]["expense"] = r.total

        # Format trends array
        thai_months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                       "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

        trends = []
        for month_key in sorted(monthly_data.keys()):
            year, month = month_key.split('-')
            month_idx = int(month) - 1
            income = monthly_data[month_key]["income"]
            expense = monthly_data[month_key]["expense"]

            trends.append({
                "month": month_key,
                "month_label": f"{thai_months[month_idx]} {int(year) + 543}",  # Convert to Buddhist year
                "income": income,
                "expense": expense,
                "balance": income - expense
            })

        # Calculate month-over-month change
        change = {}
        if len(trends) >= 2:
            prev = trends[-2]
            curr = trends[-1]

            if prev["income"] > 0:
                change["income_change_percentage"] = round(
                    ((curr["income"] - prev["income"]) / prev["income"] * 100), 1
                )

            if prev["expense"] > 0:
                change["expense_change_percentage"] = round(
                    ((curr["expense"] - prev["expense"]) / prev["expense"] * 100), 1
                )

        return {
            "trends": trends,
            "change": change
        }
