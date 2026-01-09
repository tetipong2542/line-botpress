"""
Aggregation Service
Provides data aggregation for different time periods
"""
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract, desc
from app import db
from app.models.transaction import Transaction
from app.utils.helpers import satang_to_baht


class AggregationService:
    """Service for data aggregation"""

    @staticmethod
    def get_weekly_summaries(project_id, weeks=12):
        """
        Get week-by-week summaries

        Args:
            project_id: Project ID
            weeks: Number of weeks to analyze

        Returns:
            dict: {
                "summaries": [
                    {
                        "week_start": "2025-01-06",
                        "week_end": "2025-01-12",
                        "week_number": 2,
                        "income": 50000,
                        "expense": 35000,
                        "balance": 15000,
                        "transaction_count": 30
                    }
                ],
                "comparison": {
                    "vs_previous_week": {
                        "income_change": 5000,
                        "expense_change": -2000,
                        "balance_change": 7000
                    }
                }
            }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)

        # Query weekly data (group by week number)
        results = db.session.query(
            extract('year', Transaction.occurred_at).label('year'),
            extract('week', Transaction.occurred_at).label('week'),
            func.min(Transaction.occurred_at).label('week_start'),
            func.max(Transaction.occurred_at).label('week_end'),
            func.sum(
                func.case(
                    (Transaction.type == 'income', Transaction.amount),
                    else_=0
                )
            ).label('income'),
            func.sum(
                func.case(
                    (Transaction.type == 'expense', Transaction.amount),
                    else_=0
                )
            ).label('expense'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            'year',
            'week'
        ).order_by(
            'year',
            'week'
        ).all()

        summaries = []
        for r in results:
            balance = r.income - r.expense

            summaries.append({
                "week_start": r.week_start.date().isoformat() if r.week_start else None,
                "week_end": r.week_end.date().isoformat() if r.week_end else None,
                "week_number": int(r.week),
                "year": int(r.year),
                "income": r.income,
                "expense": r.expense,
                "balance": balance,
                "transaction_count": r.count,
                "income_formatted": satang_to_baht(r.income),
                "expense_formatted": satang_to_baht(r.expense),
                "balance_formatted": satang_to_baht(balance)
            })

        # Calculate comparison with previous week
        comparison = {}
        if len(summaries) >= 2:
            current = summaries[-1]
            previous = summaries[-2]

            comparison["vs_previous_week"] = {
                "income_change": current["income"] - previous["income"],
                "expense_change": current["expense"] - previous["expense"],
                "balance_change": current["balance"] - previous["balance"]
            }

        return {
            "summaries": summaries,
            "comparison": comparison
        }

    @staticmethod
    def get_quarterly_summaries(project_id, quarters=4):
        """
        Get quarter-by-quarter summaries

        Args:
            project_id: Project ID
            quarters: Number of quarters to analyze

        Returns:
            dict: {
                "summaries": [
                    {
                        "quarter": "Q4 2025",
                        "year": 2025,
                        "quarter_number": 4,
                        "start_date": "2025-10-01",
                        "end_date": "2025-12-31",
                        "income": 150000,
                        "expense": 120000,
                        "balance": 30000,
                        "transaction_count": 120
                    }
                ],
                "comparison": {
                    "vs_previous_quarter": {
                        "income_change": 10000,
                        "expense_change": -5000,
                        "balance_change": 15000
                    }
                }
            }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90 * quarters)

        # Query quarterly data
        results = db.session.query(
            extract('year', Transaction.occurred_at).label('year'),
            func.ceil(extract('month', Transaction.occurred_at) / 3.0).label('quarter'),
            func.min(Transaction.occurred_at).label('quarter_start'),
            func.max(Transaction.occurred_at).label('quarter_end'),
            func.sum(
                func.case(
                    (Transaction.type == 'income', Transaction.amount),
                    else_=0
                )
            ).label('income'),
            func.sum(
                func.case(
                    (Transaction.type == 'expense', Transaction.amount),
                    else_=0
                )
            ).label('expense'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            'year',
            'quarter'
        ).order_by(
            'year',
            'quarter'
        ).all()

        summaries = []
        for r in results:
            quarter_num = int(r.quarter)
            year = int(r.year)

            # Calculate quarter dates
            quarter_start_month = (quarter_num - 1) * 3 + 1
            quarter_end_month = quarter_num * 3

            quarter_start = date(year, quarter_start_month, 1)
            if quarter_end_month == 12:
                quarter_end = date(year, 12, 31)
            else:
                quarter_end = date(year, quarter_end_month + 1, 1) - timedelta(days=1)

            balance = r.income - r.expense

            summaries.append({
                "quarter": f"Q{quarter_num} {year}",
                "year": year,
                "quarter_number": quarter_num,
                "start_date": quarter_start.isoformat(),
                "end_date": quarter_end.isoformat(),
                "income": r.income,
                "expense": r.expense,
                "balance": balance,
                "transaction_count": r.count,
                "income_formatted": satang_to_baht(r.income),
                "expense_formatted": satang_to_baht(r.expense),
                "balance_formatted": satang_to_baht(balance)
            })

        # Calculate comparison with previous quarter
        comparison = {}
        if len(summaries) >= 2:
            current = summaries[-1]
            previous = summaries[-2]

            comparison["vs_previous_quarter"] = {
                "income_change": current["income"] - previous["income"],
                "expense_change": current["expense"] - previous["expense"],
                "balance_change": current["balance"] - previous["balance"]
            }

        return {
            "summaries": summaries,
            "comparison": comparison
        }

    @staticmethod
    def get_yearly_summaries(project_id, years=3):
        """
        Get year-by-year summaries

        Args:
            project_id: Project ID
            years: Number of years to analyze

        Returns:
            dict: {
                "summaries": [
                    {
                        "year": 2025,
                        "income": 600000,
                        "expense": 480000,
                        "balance": 120000,
                        "transaction_count": 480,
                        "avg_monthly_income": 50000,
                        "avg_monthly_expense": 40000,
                        "avg_monthly_balance": 10000
                    }
                ],
                "comparison": {
                    "vs_previous_year": {
                        "income_change": 50000,
                        "expense_change": -10000,
                        "balance_change": 60000,
                        "income_growth_pct": 9.1
                    }
                }
            }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)

        # Query yearly data
        results = db.session.query(
            extract('year', Transaction.occurred_at).label('year'),
            func.sum(
                func.case(
                    (Transaction.type == 'income', Transaction.amount),
                    else_=0
                )
            ).label('income'),
            func.sum(
                func.case(
                    (Transaction.type == 'expense', Transaction.amount),
                    else_=0
                )
            ).label('expense'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            'year'
        ).order_by(
            'year'
        ).all()

        summaries = []
        for r in results:
            year = int(r.year)
            balance = r.income - r.expense
            months_with_data = 12  # Assume full year

            summaries.append({
                "year": year,
                "income": r.income,
                "expense": r.expense,
                "balance": balance,
                "transaction_count": r.count,
                "avg_monthly_income": r.income / months_with_data,
                "avg_monthly_expense": r.expense / months_with_data,
                "avg_monthly_balance": balance / months_with_data,
                "income_formatted": satang_to_baht(r.income),
                "expense_formatted": satang_to_baht(r.expense),
                "balance_formatted": satang_to_baht(balance),
                "avg_monthly_income_formatted": satang_to_baht(r.income / months_with_data),
                "avg_monthly_expense_formatted": satang_to_baht(r.expense / months_with_data),
                "avg_monthly_balance_formatted": satang_to_baht(balance / months_with_data)
            })

        # Calculate comparison with previous year
        comparison = {}
        if len(summaries) >= 2:
            current = summaries[-1]
            previous = summaries[-2]

            income_change = current["income"] - previous["income"]
            expense_change = current["expense"] - previous["expense"]
            balance_change = current["balance"] - previous["balance"]

            income_growth_pct = (income_change / previous["income"] * 100) if previous["income"] > 0 else 0

            comparison["vs_previous_year"] = {
                "income_change": income_change,
                "expense_change": expense_change,
                "balance_change": balance_change,
                "income_growth_pct": round(income_growth_pct, 1)
            }

        return {
            "summaries": summaries,
            "comparison": comparison
        }

    @staticmethod
    def get_custom_period_aggregation(project_id, period_name, start_date, end_date):
        """
        Get aggregation for a custom period

        Args:
            project_id: Project ID
            period_name: Name for the period (e.g., "Summer 2025")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            dict: {
                "period": {
                    "name": "Summer 2025",
                    "start_date": "2025-06-01",
                    "end_date": "2025-08-31",
                    "days": 92
                },
                "summary": {
                    "income": 150000,
                    "expense": 120000,
                    "balance": 30000,
                    "transaction_count": 180,
                    "daily_avg_income": 1630,
                    "daily_avg_expense": 1304,
                    "daily_avg_balance": 326
                },
                "categories": [
                    {
                        "category_id": "cat_xxx",
                        "category_name": "อาหาร",
                        "total": 50000,
                        "percentage": 41.7
                    }
                ]
            }
        """
        from app.models.category import Category

        # Parse dates
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        days = (end_date - start_date).days + 1

        # Get summary
        income = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'income',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        expense = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        count = db.session.query(
            func.count(Transaction.id)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        # Get category breakdown
        category_results = db.session.query(
            Category.id,
            Category.name_th,
            Category.icon,
            Category.color,
            func.sum(Transaction.amount).label('total')
        ).join(
            Transaction,
            Transaction.category_id == Category.id
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            Category.id,
            Category.name_th,
            Category.icon,
            Category.color
        ).order_by(
            desc('total')
        ).all()

        categories = []
        for r in category_results:
            categories.append({
                "category_id": r.id,
                "category_name": r.name_th,
                "category_icon": r.icon,
                "category_color": r.color,
                "total": r.total,
                "percentage": round((r.total / expense * 100), 1) if expense > 0 else 0,
                "total_formatted": satang_to_baht(r.total)
            })

        balance = income - expense

        return {
            "period": {
                "name": period_name,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "income": income,
                "expense": expense,
                "balance": balance,
                "transaction_count": count,
                "daily_avg_income": income / days if days > 0 else 0,
                "daily_avg_expense": expense / days if days > 0 else 0,
                "daily_avg_balance": balance / days if days > 0 else 0,
                "income_formatted": satang_to_baht(income),
                "expense_formatted": satang_to_baht(expense),
                "balance_formatted": satang_to_baht(balance)
            },
            "categories": categories
        }
