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
        
        # Debug logging
        print(f"📊 Analytics query: month={month_str}, start_date={start_date}, end_date={end_date}, project_id={project_id}")

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
        
        # Debug logging
        print(f"📊 Results: income={income_count} transactions (total={income_total}), "
              f"expense={expense_count} transactions (total={expense_total})")

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

    @staticmethod
    def get_daily_averages(project_id, start_date, end_date):
        """
        Get daily average spending/income for a date range

        Args:
            project_id: Project ID
            start_date: Start date (datetime or string YYYY-MM-DD)
            end_date: End date (datetime or string YYYY-MM-DD)

        Returns:
            dict: {
                "daily_averages": {
                    "income_avg": 50000,  # satang
                    "expense_avg": 35000,
                    "net_avg": 15000,
                    "income_avg_formatted": 500.00,
                    "expense_avg_formatted": 350.00,
                    "net_avg_formatted": 150.00
                },
                "weekday_vs_weekend": {
                    "weekday_avg": 40000,
                    "weekend_avg": 45000,
                    "weekday_avg_formatted": 400.00,
                    "weekend_avg_formatted": 450.00
                },
                "days_in_period": 30
            }
        """
        from datetime import datetime

        # Parse dates if strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Calculate days in period
        days_in_period = (end_date - start_date).days + 1

        # Query totals
        income_total = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'income',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        expense_total = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        # Calculate daily averages
        income_avg = income_total / days_in_period if days_in_period > 0 else 0
        expense_avg = expense_total / days_in_period if days_in_period > 0 else 0
        net_avg = income_avg - expense_avg

        # Query weekday vs weekend
        weekday_expense = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            extract('dow', Transaction.occurred_at).in_([1, 2, 3, 4, 5]),  # Monday=1, Friday=5
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        weekend_expense = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            extract('dow', Transaction.occurred_at).in_([0, 6]),  # Sunday=0, Saturday=6
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        # Calculate weekday/weekend averages (assuming 5 weekdays, 2 weekend days)
        weekday_avg = weekday_expense / 5 if days_in_period > 0 else 0
        weekend_avg = weekend_expense / 2 if days_in_period > 0 else 0

        return {
            "daily_averages": {
                "income_avg": income_avg,
                "expense_avg": expense_avg,
                "net_avg": net_avg,
                "income_avg_formatted": satang_to_baht(income_avg),
                "expense_avg_formatted": satang_to_baht(expense_avg),
                "net_avg_formatted": satang_to_baht(net_avg)
            },
            "weekday_vs_weekend": {
                "weekday_avg": weekday_avg,
                "weekend_avg": weekend_avg,
                "weekday_avg_formatted": satang_to_baht(weekday_avg),
                "weekend_avg_formatted": satang_to_baht(weekend_avg)
            },
            "days_in_period": days_in_period
        }

    @staticmethod
    def get_spending_velocity(project_id, days=30):
        """
        Get spending velocity (rate of spending over time)

        Args:
            project_id: Project ID
            days: Number of days to analyze

        Returns:
            dict: {
                "velocity": {
                    "daily_rate": 1167,  # satang/day
                    "weekly_rate": 8167,
                    "monthly_rate": 35000,
                    "daily_rate_formatted": 11.67,
                    "weekly_rate_formatted": 81.67,
                    "monthly_rate_formatted": 350.00
                },
                "acceleration": {
                    "value": -500,  # satang/day² (negative = slowing down)
                    "direction": "decreasing",
                    "trend": "slowing_down"
                },
                "forecast": {
                    "next_7_days": 8167,
                    "next_30_days": 35000,
                    "next_7_days_formatted": 81.67,
                    "next_30_days_formatted": 350.00
                }
            }
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get daily spending data
        daily_spending = db.session.query(
            func.date(Transaction.occurred_at).label('date'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            func.date(Transaction.occurred_at)
        ).order_by(
            func.date(Transaction.occurred_at)
        ).all()

        # Calculate total and average
        total_spending = sum(d.total for d in daily_spending if d.total)
        avg_daily = total_spending / days if days > 0 else 0

        # Calculate acceleration (change in spending rate)
        acceleration = 0
        trend = "stable"
        if len(daily_spending) >= 2:
            # Compare first half vs second half
            mid_point = len(daily_spending) // 2
            first_half_avg = sum(d.total for d in daily_spending[:mid_point]) / mid_point if mid_point > 0 else 0
            second_half_avg = sum(d.total for d in daily_spending[mid_point:]) / (len(daily_spending) - mid_point) if len(daily_spending) > mid_point else 0
            acceleration = (second_half_avg - first_half_avg) / (days / 2)

            if acceleration > 100:
                trend = "speeding_up"
            elif acceleration < -100:
                trend = "slowing_down"
            else:
                trend = "stable"

        return {
            "velocity": {
                "daily_rate": avg_daily,
                "weekly_rate": avg_daily * 7,
                "monthly_rate": avg_daily * 30,
                "daily_rate_formatted": satang_to_baht(avg_daily),
                "weekly_rate_formatted": satang_to_baht(avg_daily * 7),
                "monthly_rate_formatted": satang_to_baht(avg_daily * 30)
            },
            "acceleration": {
                "value": acceleration,
                "direction": "increasing" if acceleration > 0 else "decreasing",
                "trend": trend
            },
            "forecast": {
                "next_7_days": avg_daily * 7,
                "next_30_days": avg_daily * 30,
                "next_7_days_formatted": satang_to_baht(avg_daily * 7),
                "next_30_days_formatted": satang_to_baht(avg_daily * 30)
            }
        }

    @staticmethod
    def get_savings_rate(project_id, months=6):
        """
        Get savings rate over a period

        Args:
            project_id: Project ID
            months: Number of months to analyze

        Returns:
            dict: {
                "savings_rate": {
                    "overall_rate": 30.0,  # percentage
                    "monthly_rates": [
                        {"month": "2025-08", "rate": 25.0},
                        {"month": "2025-09", "rate": 35.0}
                    ]
                },
                "comparison": {
                    "vs_previous_period": 5.0,
                    "trend": "improving"
                }
            }
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)

        # Query monthly income and expense
        monthly_data = db.session.query(
            extract('year', Transaction.occurred_at).label('year'),
            extract('month', Transaction.occurred_at).label('month'),
            Transaction.type,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            'year',
            'month',
            Transaction.type
        ).order_by(
            'year',
            'month'
        ).all()

        # Process monthly data
        monthly_rates = []
        monthly_totals = {}

        for r in monthly_data:
            month_key = f"{int(r.year)}-{str(int(r.month)).zfill(2)}"
            if month_key not in monthly_totals:
                monthly_totals[month_key] = {'income': 0, 'expense': 0}

            if r.type == 'income':
                monthly_totals[month_key]['income'] = r.total
            else:
                monthly_totals[month_key]['expense'] = r.total

        # Calculate monthly rates
        for month_key in sorted(monthly_totals.keys()):
            income = monthly_totals[month_key]['income']
            expense = monthly_totals[month_key]['expense']
            rate = ((income - expense) / income * 100) if income > 0 else 0
            monthly_rates.append({
                "month": month_key,
                "rate": round(rate, 1)
            })

        # Calculate overall rate
        total_income = sum(m['income'] for m in monthly_totals.values())
        total_expense = sum(m['expense'] for m in monthly_totals.values())
        overall_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0

        # Calculate trend
        trend = "stable"
        vs_previous = 0
        if len(monthly_rates) >= 2:
            recent_rate = monthly_rates[-1]['rate']
            previous_rate = monthly_rates[-2]['rate']
            vs_previous = recent_rate - previous_rate
            if vs_previous > 5:
                trend = "improving"
            elif vs_previous < -5:
                trend = "declining"

        return {
            "savings_rate": {
                "overall_rate": round(overall_rate, 1),
                "monthly_rates": monthly_rates
            },
            "comparison": {
                "vs_previous_period": round(vs_previous, 1),
                "trend": trend
            }
        }

    @staticmethod
    def get_financial_health_score(project_id, months=3):
        """
        Calculate financial health score based on multiple factors

        Args:
            project_id: Project ID
            months: Number of months to analyze

        Returns:
            dict: {
                "score": 75,
                "grade": "B",
                "factors": {
                    "budget_adherence": {"score": 80, "weight": 30},
                    "savings_consistency": {"score": 70, "weight": 25},
                    "spending_stability": {"score": 75, "weight": 25},
                    "income_diversity": {"score": 80, "weight": 20}
                },
                "recommendations": ["Increase savings rate", "Review budget categories"]
            }
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)

        # Factor 1: Budget Adherence (30%)
        # Calculate percentage of categories within budget
        budgets = db.session.query(Budget).filter(
            Budget.project_id == project_id,
            Budget.month_yyyymm >= start_date.strftime('%Y-%m'),
            Budget.month_yyyymm <= end_date.strftime('%Y-%m')
        ).all()

        within_budget = 0
        total_budgets = len(budgets)

        for budget in budgets:
            # Get actual spending for this category/month
            actual = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.project_id == project_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == 'expense',
                extract('year', Transaction.occurred_at) == int(budget.month_yyyymm[:4]),
                extract('month', Transaction.occurred_at) == int(budget.month_yyyymm[5:7]),
                Transaction.deleted_at.is_(None)
            ).scalar() or 0

            if actual <= budget.limit_amount:
                within_budget += 1

        budget_score = (within_budget / total_budgets * 100) if total_budgets > 0 else 50

        # Factor 2: Savings Consistency (25%)
        savings_data = AnalyticsService.get_savings_rate(project_id, months)
        monthly_rates = savings_data['savings_rate']['monthly_rates']

        if monthly_rates:
            avg_savings = sum(m['rate'] for m in monthly_rates) / len(monthly_rates)
            # Calculate variance
            variance = sum((m['rate'] - avg_savings) ** 2 for m in monthly_rates) / len(monthly_rates)
            consistency_score = max(0, 100 - variance / 10)  # Lower variance = higher score
        else:
            consistency_score = 50

        # Factor 3: Spending Stability (25%)
        # Calculate coefficient of variation of daily spending
        daily_spending = db.session.query(
            func.date(Transaction.occurred_at).label('date'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            func.date(Transaction.occurred_at)
        ).all()

        if daily_spending:
            amounts = [d.total for d in daily_spending if d.total]
            if amounts:
                avg = sum(amounts) / len(amounts)
                std_dev = (sum((x - avg) ** 2 for x in amounts) / len(amounts)) ** 0.5
                cv = (std_dev / avg * 100) if avg > 0 else 100
                stability_score = max(0, 100 - cv)  # Lower CV = higher score
            else:
                stability_score = 50
        else:
            stability_score = 50

        # Factor 4: Income Diversity (20%)
        # Count unique income categories
        income_categories = db.session.query(
            func.count(func.distinct(Transaction.category_id))
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'income',
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0

        diversity_score = min(100, income_categories * 25)  # 4+ categories = 100%

        # Calculate weighted score
        factors = {
            "budget_adherence": {"score": round(budget_score), "weight": 30},
            "savings_consistency": {"score": round(consistency_score), "weight": 25},
            "spending_stability": {"score": round(stability_score), "weight": 25},
            "income_diversity": {"score": round(diversity_score), "weight": 20}
        }

        total_score = sum(f['score'] * f['weight'] / 100 for f in factors.values())

        # Determine grade
        if total_score >= 90:
            grade = "A"
        elif total_score >= 80:
            grade = "B+"
        elif total_score >= 70:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        else:
            grade = "D"

        # Generate recommendations
        recommendations = []
        if budget_score < 70:
            recommendations.append("ปรับปรุงการควบคุมงบประมาณให้ดีขึ้น")
        if consistency_score < 70:
            recommendations.append("สร้างความสม่ำเสมอในการออมเงิน")
        if stability_score < 70:
            recommendations.append("ลดความผันผวนในการใช้จ่าย")
        if diversity_score < 50:
            recommendations.append("พัฒนาแหล่งรายได้หลากหลายขึ้น")

        return {
            "score": round(total_score),
            "grade": grade,
            "factors": factors,
            "recommendations": recommendations
        }

    @staticmethod
    def get_category_growth_rates(project_id, months=6):
        """
        Get category growth rates over time

        Args:
            project_id: Project ID
            months: Number of months to analyze

        Returns:
            dict: {
                "categories": [
                    {
                        "category_id": "cat_xxx",
                        "category_name": "อาหาร",
                        "category_icon": "food",
                        "category_color": "#FF6B6B",
                        "current_month": 12000,
                        "previous_month": 10000,
                        "growth_rate": 20.0,
                        "trend": "up",
                        "monthly_data": [
                            {"month": "2025-08", "amount": 10000},
                            {"month": "2025-09", "amount": 12000}
                        ]
                    }
                ]
            }
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)

        # Query category spending by month
        results = db.session.query(
            Category.id,
            Category.name_th,
            Category.icon,
            Category.color,
            extract('year', Transaction.occurred_at).label('year'),
            extract('month', Transaction.occurred_at).label('month'),
            func.sum(Transaction.amount).label('total')
        ).join(
            Transaction,
            Transaction.category_id == Category.id
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            Category.id,
            Category.name_th,
            Category.icon,
            Category.color,
            'year',
            'month'
        ).order_by(
            Category.id,
            'year',
            'month'
        ).all()

        # Process results
        category_data = {}
        for r in results:
            cat_id = r.id
            month_key = f"{int(r.year)}-{str(int(r.month)).zfill(2)}"

            if cat_id not in category_data:
                category_data[cat_id] = {
                    "category_id": cat_id,
                    "category_name": r.name_th,
                    "category_icon": r.icon,
                    "category_color": r.color,
                    "monthly_data": []
                }

            category_data[cat_id]["monthly_data"].append({
                "month": month_key,
                "amount": r.total
            })

        # Calculate growth rates
        categories = []
        for cat_id, data in category_data.items():
            monthly_data = sorted(data["monthly_data"], key=lambda x: x["month"])

            if len(monthly_data) >= 2:
                current_month = monthly_data[-1]["amount"]
                previous_month = monthly_data[-2]["amount"]
                growth_rate = ((current_month - previous_month) / previous_month * 100) if previous_month > 0 else 0

                trend = "up" if growth_rate > 0 else ("down" if growth_rate < 0 else "stable")
            else:
                current_month = monthly_data[-1]["amount"] if monthly_data else 0
                previous_month = 0
                growth_rate = 0
                trend = "stable"

            categories.append({
                **data,
                "current_month": current_month,
                "previous_month": previous_month,
                "growth_rate": round(growth_rate, 1),
                "trend": trend
            })

        return {"categories": categories}

    @staticmethod
    def get_seasonal_patterns(project_id, years=2):
        """
        Analyze seasonal spending patterns

        Args:
            project_id: Project ID
            years: Number of years to analyze

        Returns:
            dict: {
                "patterns": [
                    {
                        "month": 1,
                        "month_name": "มกราคม",
                        "avg_spending": 45000,
                        "avg_income": 50000,
                        "years_analyzed": 2,
                        "trend": "high"  # high, average, low
                    }
                ],
                "insights": [
                    "การใช้จ่ายสูงสุดในเดือนธันวาคม",
                    "รายรับสูงสุดในเดือนมกราคม"
                ]
            }
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)

        # Query monthly totals
        monthly_totals = db.session.query(
            extract('month', Transaction.occurred_at).label('month'),
            Transaction.type,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            'month',
            Transaction.type
        ).all()

        # Process by month
        month_data = {}
        for r in monthly_totals:
            month_num = int(r.month)
            if month_num not in month_data:
                month_data[month_num] = {'expense': 0, 'income': 0, 'expense_count': 0, 'income_count': 0}

            if r.type == 'income':
                month_data[month_num]['income'] = r.total
                month_data[month_num]['income_count'] = r.count
            else:
                month_data[month_num]['expense'] = r.total
                month_data[month_num]['expense_count'] = r.count

        # Calculate averages
        patterns = []
        thai_months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                     "ก.ค.", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]

        for month_num in range(1, 13):
            if month_num in month_data:
                avg_spending = month_data[month_num]['expense'] / years
                avg_income = month_data[month_num]['income'] / years
                years_with_data = 1 if month_data[month_num]['expense_count'] > 0 else 0
            else:
                avg_spending = 0
                avg_income = 0
                years_with_data = 0

            # Determine trend
            all_avg_spending = [m['expense'] / years for m in month_data.values() if m['expense'] > 0]
            if all_avg_spending:
                overall_avg = sum(all_avg_spending) / len(all_avg_spending)
                if avg_spending > overall_avg * 1.2:
                    trend = "high"
                elif avg_spending < overall_avg * 0.8:
                    trend = "low"
                else:
                    trend = "average"
            else:
                trend = "average"

            patterns.append({
                "month": month_num,
                "month_name": thai_months[month_num - 1],
                "avg_spending": avg_spending,
                "avg_income": avg_income,
                "years_analyzed": years_with_data,
                "trend": trend
            })

        # Generate insights
        insights = []
        sorted_by_spending = sorted(patterns, key=lambda x: x['avg_spending'], reverse=True)
        if sorted_by_spending and sorted_by_spending[0]['avg_spending'] > 0:
            insights.append(f"การใช้จ่ายสูงสุดในเดือน{sorted_by_spending[0]['month_name']}")

        sorted_by_income = sorted(patterns, key=lambda x: x['avg_income'], reverse=True)
        if sorted_by_income and sorted_by_income[0]['avg_income'] > 0:
            insights.append(f"รายรับสูงสุดในเดือน{sorted_by_income[0]['month_name']}")

        return {
            "patterns": patterns,
            "insights": insights
        }

    @staticmethod
    def get_heatmap_data(project_id, days=30):
        """
        Get spending heatmap data (day of week vs time of day)

        Args:
            project_id: Project ID
            days: Number of days to analyze

        Returns:
            dict: {
                "heatmap": [
                    {
                        "day_of_week": 0,  # Sunday=0
                        "hour": 14,
                        "total": 5000,
                        "count": 5,
                        "avg": 1000
                    }
                ],
                "max_total": 10000
            }
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query spending by day of week and hour
        results = db.session.query(
            extract('dow', Transaction.occurred_at).label('day_of_week'),
            extract('hour', Transaction.occurred_at).label('hour'),
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            'day_of_week',
            'hour'
        ).all()

        # Process results
        heatmap = []
        max_total = 0

        for r in results:
            total = r.total or 0
            count = r.count or 0
            avg = total / count if count > 0 else 0

            heatmap.append({
                "day_of_week": int(r.day_of_week),
                "hour": int(r.hour),
                "total": total,
                "count": count,
                "avg": avg
            })

            if total > max_total:
                max_total = total

        return {
            "heatmap": heatmap,
            "max_total": max_total
        }

    @staticmethod
    def get_scatter_data(project_id, days=30):
        """
        Get scatter plot data (amount vs frequency)

        Args:
            project_id: Project ID
            days: Number of days to analyze

        Returns:
            dict: {
                "scatter": [
                    {
                        "category_id": "cat_xxx",
                        "category_name": "อาหาร",
                        "category_icon": "food",
                        "category_color": "#FF6B6B",
                        "amount": 12000,
                        "count": 25,
                        "avg_amount": 480
                    }
                ]
            }
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query category totals and counts
        results = db.session.query(
            Category.id,
            Category.name_th,
            Category.icon,
            Category.color,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).join(
            Transaction,
            Transaction.category_id == Category.id
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            Category.id,
            Category.name_th,
            Category.icon,
            Category.color
        ).order_by(
            desc('total')
        ).all()

        scatter = []
        for r in results:
            total = r.total or 0
            count = r.count or 0
            avg_amount = total / count if count > 0 else 0

            scatter.append({
                "category_id": r.id,
                "category_name": r.name_th,
                "category_icon": r.icon,
                "category_color": r.color,
                "amount": total,
                "count": count,
                "avg_amount": avg_amount
            })

        return {"scatter": scatter}

    @staticmethod
    def compare_periods(project_id, period1_start, period1_end, period2_start, period2_end):
        """
        Compare two date ranges

        Args:
            project_id: Project ID
            period1_start: Start date for period 1 (YYYY-MM-DD)
            period1_end: End date for period 1 (YYYY-MM-DD)
            period2_start: Start date for period 2 (YYYY-MM-DD)
            period2_end: End date for period 2 (YYYY-MM-DD)

        Returns:
            dict: {
                "period1": {
                    "income": 50000,
                    "expense": 35000,
                    "balance": 15000
                },
                "period2": {
                    "income": 45000,
                    "expense": 30000,
                    "balance": 15000
                },
                "comparison": {
                    "income_change": 5000,
                    "income_change_pct": 11.1,
                    "expense_change": 5000,
                    "expense_change_pct": 16.7,
                    "balance_change": 0,
                    "balance_change_pct": 0
                }
            }
        """
        def get_period_totals(start_date, end_date):
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

            return {
                "income": income,
                "expense": expense,
                "balance": income - expense
            }

        period1 = get_period_totals(period1_start, period1_end)
        period2 = get_period_totals(period2_start, period2_end)

        # Calculate comparison
        def calc_change(p1, p2):
            if p2 == 0:
                return {"amount": p1, "percentage": 100 if p1 > 0 else 0}
            diff = p1 - p2
            return {
                "amount": diff,
                "percentage": round((diff / p2 * 100), 1)
            }

        comparison = {
            "income_change": calc_change(period1["income"], period2["income"]),
            "expense_change": calc_change(period1["expense"], period2["expense"]),
            "balance_change": calc_change(period1["balance"], period2["balance"])
        }

        return {
            "period1": period1,
            "period2": period2,
            "comparison": comparison
        }

    @staticmethod
    def get_amount_suggestions(project_id, category_id=None, type='expense'):
        """
        Get smart amount suggestions based on spending history
        
        Args:
            project_id: Project ID
            category_id: Optional category ID for category-specific suggestions
            type: 'expense' or 'income'
        
        Returns:
            dict: {
                "suggestions": {
                    "avg_amount": 15000,  # satang
                    "avg_formatted": 150.00,  # baht
                    "min_amount": 5000,
                    "max_amount": 35000,
                    "typical_range": "50-350 บาท",
                    "quick_amounts": [5000, 10000, 15000, 20000, 50000],  # satang
                    "quick_amounts_formatted": [50, 100, 150, 200, 500],  # baht
                },
                "recent_transactions": [
                    {"amount": 15000, "formatted": 150.00, "note": "กาแฟ", "date": "2026-01-11"},
                ],
                "category_hint": "ปกติคุณใช้ 50-350 บาท"
            }
        """
        from datetime import timedelta
        from sqlalchemy import func
        
        # Get transactions from last 90 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Build base query
        base_query = Transaction.query.filter(
            Transaction.project_id == project_id,
            Transaction.type == type,
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        )
        
        # Add category filter if provided
        if category_id:
            base_query = base_query.filter(Transaction.category_id == category_id)
        
        # Get statistics
        stats = db.session.query(
            func.avg(Transaction.amount).label('avg'),
            func.min(Transaction.amount).label('min'),
            func.max(Transaction.amount).label('max'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == type,
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        )
        
        if category_id:
            stats = stats.filter(Transaction.category_id == category_id)
        
        stats_result = stats.first()
        
        # Get recent transactions (last 5)
        recent = base_query.order_by(Transaction.occurred_at.desc()).limit(5).all()
        
        # Calculate suggestions
        avg_amount = int(stats_result.avg) if stats_result.avg else 0
        min_amount = int(stats_result.min) if stats_result.min else 0
        max_amount = int(stats_result.max) if stats_result.max else 0
        count = stats_result.count or 0
        
        # Generate quick amounts based on distribution
        if count > 0:
            # Calculate percentiles for quick amounts
            amounts_query = db.session.query(Transaction.amount).filter(
                Transaction.project_id == project_id,
                Transaction.type == type,
                Transaction.occurred_at >= start_date,
                Transaction.deleted_at.is_(None)
            )
            if category_id:
                amounts_query = amounts_query.filter(Transaction.category_id == category_id)
            
            amounts = [a[0] for a in amounts_query.all()]
            amounts.sort()
            
            # Get percentiles (10th, 25th, 50th, 75th, 90th)
            if len(amounts) >= 5:
                n = len(amounts)
                quick_amounts = [
                    amounts[int(n * 0.1)],
                    amounts[int(n * 0.25)],
                    amounts[int(n * 0.5)],
                    amounts[int(n * 0.75)],
                    amounts[int(n * 0.9)]
                ]
                # Round to nice numbers
                quick_amounts = [round(a / 5000) * 5000 for a in quick_amounts]  # Round to nearest 50 baht
                quick_amounts = list(dict.fromkeys(quick_amounts))  # Remove duplicates
            else:
                # Default quick amounts
                quick_amounts = [5000, 10000, 15000, 20000, 50000]
        else:
            # Default quick amounts when no history
            quick_amounts = [5000, 10000, 15000, 20000, 50000]
        
        # Ensure we have at least 5 amounts
        default_amounts = [5000, 10000, 15000, 20000, 50000]
        while len(quick_amounts) < 5:
            for da in default_amounts:
                if da not in quick_amounts:
                    quick_amounts.append(da)
                    break
        quick_amounts = sorted(quick_amounts[:5])
        
        # Create category hint
        if count > 0:
            min_baht = satang_to_baht(min_amount)
            max_baht = satang_to_baht(max_amount)
            category_hint = f"ปกติคุณใช้ {int(min_baht)}-{int(max_baht)} บาท"
        else:
            category_hint = None
        
        # Format recent transactions
        recent_transactions = []
        for t in recent:
            recent_transactions.append({
                "amount": t.amount,
                "formatted": satang_to_baht(t.amount),
                "note": t.note or "",
                "date": t.occurred_at.strftime('%Y-%m-%d') if t.occurred_at else None
            })
        
        return {
            "suggestions": {
                "avg_amount": avg_amount,
                "avg_formatted": satang_to_baht(avg_amount),
                "min_amount": min_amount,
                "max_amount": max_amount,
                "typical_range": f"{int(satang_to_baht(min_amount))}-{int(satang_to_baht(max_amount))} บาท" if count > 0 else None,
                "quick_amounts": quick_amounts,
                "quick_amounts_formatted": [satang_to_baht(a) for a in quick_amounts],
                "transaction_count": count
            },
            "recent_transactions": recent_transactions,
            "category_hint": category_hint
        }

