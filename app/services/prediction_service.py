"""
Prediction Service
Provides predictive analytics and forecasting capabilities
"""
from datetime import datetime, timedelta
from sqlalchemy import func, extract, desc
from app import db
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.savings_goal import SavingsGoal
from app.models.recurring import RecurringRule
from app.utils.helpers import satang_to_baht
import statistics


class PredictionService:
    """Service for predictive analytics"""

    @staticmethod
    def get_spending_forecast(project_id, days=30):
        """
        Get spending forecast using linear regression

        Args:
            project_id: Project ID
            days: Number of days to forecast

        Returns:
            dict: {
                "forecast": [
                    {"date": "2025-01-10", "predicted": 1167, "lower_bound": 1000, "upper_bound": 1333}
                ],
                "summary": {
                    "total_predicted": 35000,
                    "daily_average": 1167,
                    "confidence": 0.85
                }
            }
        """
        # Get historical daily spending for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        daily_data = db.session.query(
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

        # Extract amounts
        amounts = [d.total for d in daily_data if d.total]

        if len(amounts) < 7:
            # Not enough data for reliable forecast
            avg_daily = statistics.mean(amounts) if amounts else 0
            return {
                "forecast": [],
                "summary": {
                    "total_predicted": avg_daily * days,
                    "daily_average": avg_daily,
                    "confidence": 0.5,
                    "message": "ข้อมูลไม่เพียงพอสำหรับการคาดการณ์ที่แม่นยำ"
                }
            }

        # Simple linear regression
        x = list(range(len(amounts)))
        y = amounts

        # Calculate slope and intercept
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n if n > 0 else 0

        # Calculate forecast
        forecast = []
        current_date = datetime.now().date()

        for i in range(1, days + 1):
            predicted = slope * (len(amounts) + i - 1) + intercept
            predicted = max(0, predicted)  # Don't predict negative spending

            # Calculate confidence bounds (simplified)
            std_dev = statistics.stdev(y) if len(y) > 1 else 0
            lower_bound = max(0, predicted - 1.96 * std_dev)
            upper_bound = predicted + 1.96 * std_dev

            forecast_date = current_date + timedelta(days=i)

            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted": predicted,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            })

        # Calculate summary
        total_predicted = sum(f["predicted"] for f in forecast)
        avg_daily = total_predicted / days if days > 0 else 0

        # Calculate confidence based on data variance
        if len(y) > 1:
            variance = statistics.variance(y)
            mean = statistics.mean(y)
            cv = (variance ** 0.5 / mean) if mean > 0 else 1
            confidence = max(0.5, min(0.95, 1 - cv))
        else:
            confidence = 0.5

        return {
            "forecast": forecast,
            "summary": {
                "total_predicted": total_predicted,
                "daily_average": avg_daily,
                "confidence": round(confidence, 2),
                "total_predicted_formatted": satang_to_baht(total_predicted),
                "daily_average_formatted": satang_to_baht(avg_daily)
            }
        }

    @staticmethod
    def get_budget_projection(project_id, month_str):
        """
        Get budget projection for a month

        Args:
            project_id: Project ID
            month_str: Month in format "YYYY-MM"

        Returns:
            dict: {
                "budgets": [
                    {
                        "category_id": "cat_xxx",
                        "category_name": "อาหาร",
                        "limit": 15000,
                        "spent": 12000,
                        "remaining": 3000,
                        "days_remaining": 15,
                        "daily_allowance": 200,
                        "projected_over_budget": False,
                        "projected_remaining": 0
                    }
                ],
                "overall": {
                    "total_budget": 50000,
                    "total_spent": 35000,
                    "total_remaining": 15000,
                    "days_remaining": 15,
                    "daily_allowance": 1000
                }
            }
        """
        year, month = map(int, month_str.split('-'))

        # Get current date
        today = datetime.now().date()

        # Calculate month end date
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # Calculate days remaining
        if today <= month_end:
            days_remaining = (month_end - today).days
        else:
            days_remaining = 0

        # Get budgets for this month
        budgets = db.session.query(
            Budget.id,
            Budget.category_id,
            Budget.limit_amount
        ).filter(
            Budget.project_id == project_id,
            Budget.month_yyyymm == month_str
        ).all()

        budget_projections = []

        for budget in budgets:
            # Get actual spending
            spent = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.project_id == project_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == 'expense',
                extract('year', Transaction.occurred_at) == year,
                extract('month', Transaction.occurred_at) == month,
                Transaction.deleted_at.is_(None)
            ).scalar() or 0

            remaining = budget.limit_amount - spent
            daily_allowance = remaining / days_remaining if days_remaining > 0 else 0

            # Project if current rate continues
            if days_remaining > 0 and spent > 0:
                days_passed = (today - datetime(year, month, 1).date()).days
                daily_rate = spent / days_passed if days_passed > 0 else 0
                projected_spending = spent + (daily_rate * days_remaining)
                projected_over_budget = projected_spending > budget.limit_amount
                projected_remaining = budget.limit_amount - projected_spending
            else:
                daily_rate = 0
                projected_over_budget = False
                projected_remaining = remaining

            budget_projections.append({
                "budget_id": budget.id,
                "category_id": budget.category_id,
                "limit": budget.limit_amount,
                "spent": spent,
                "remaining": remaining,
                "days_remaining": days_remaining,
                "daily_allowance": daily_allowance,
                "daily_rate": daily_rate,
                "projected_over_budget": projected_over_budget,
                "projected_remaining": projected_remaining,
                "limit_formatted": satang_to_baht(budget.limit_amount),
                "spent_formatted": satang_to_baht(spent),
                "remaining_formatted": satang_to_baht(remaining),
                "daily_allowance_formatted": satang_to_baht(daily_allowance)
            })

        # Calculate overall totals
        total_budget = sum(b.limit_amount for b in budgets)
        total_spent = sum(b["spent"] for b in budget_projections)
        total_remaining = total_budget - total_spent
        overall_daily_allowance = total_remaining / days_remaining if days_remaining > 0 else 0

        return {
            "budgets": budget_projections,
            "overall": {
                "total_budget": total_budget,
                "total_spent": total_spent,
                "total_remaining": total_remaining,
                "days_remaining": days_remaining,
                "daily_allowance": overall_daily_allowance,
                "total_budget_formatted": satang_to_baht(total_budget),
                "total_spent_formatted": satang_to_baht(total_spent),
                "total_remaining_formatted": satang_to_baht(total_remaining),
                "daily_allowance_formatted": satang_to_baht(overall_daily_allowance)
            }
        }

    @staticmethod
    def get_savings_goal_tracking(project_id):
        """
        Get savings goal tracking with predictions

        Returns:
            dict: {
                "goals": [
                    {
                        "goal_id": "goal_xxx",
                        "name": "ฉุกชิ้นรถ",
                        "target": 500000,
                        "current": 200000,
                        "progress": 40.0,
                        "days_remaining": 180,
                        "required_daily": 1667,
                        "on_track": True,
                        "estimated_completion": "2025-06-01"
                    }
                ]
            }
        """
        goals = SavingsGoal.get_active_goals(project_id)

        goal_tracking = []

        for goal in goals:
            # Update progress
            goal.update_progress()

            # Get required saving rate
            required_daily = goal.get_required_saving_rate()

            # Calculate if on track
            if required_daily is not None:
                # Get current saving rate
                from datetime import timedelta
                days_since_start = (datetime.now().date() - goal.created_at.date()).days
                if days_since_start > 0:
                    current_daily_rate = goal.current_amount / days_since_start
                    on_track = current_daily_rate >= required_daily
                else:
                    on_track = True

                # Estimate completion date
                if required_daily > 0:
                    remaining_amount = goal.target_amount - goal.current_amount
                    days_to_complete = remaining_amount / required_daily
                    estimated_completion = (datetime.now().date() + timedelta(days=days_to_complete)).isoformat()
                else:
                    estimated_completion = None
            else:
                on_track = goal.is_completed
                estimated_completion = None

            goal_tracking.append({
                "goal_id": goal.id,
                "name": goal.name,
                "target": goal.target_amount,
                "current": goal.current_amount,
                "progress": goal.progress_percentage,
                "days_remaining": goal.days_remaining,
                "required_daily": required_daily,
                "on_track": on_track,
                "estimated_completion": estimated_completion,
                "is_completed": goal.is_completed,
                "is_overdue": goal.is_overdue,
                "target_formatted": satang_to_baht(goal.target_amount),
                "current_formatted": satang_to_baht(goal.current_amount),
                "required_daily_formatted": satang_to_baht(required_daily) if required_daily else None
            })

        return {"goals": goal_tracking}

    @staticmethod
    def get_recurring_predictions(project_id):
        """
        Get recurring expense predictions

        Returns:
            dict: {
                "recurring": [
                    {
                        "rule_id": "rule_xxx",
                        "name": "ค่าเช่าบ้าน",
                        "amount": 15000,
                        "frequency": "monthly",
                        "next_occurrence": "2025-01-15",
                        "monthly_total": 15000
                    }
                ],
                "total_monthly_recurring": 50000
            }
        """
        rules = db.session.query(RecurringRule).filter(
            RecurringRule.project_id == project_id,
            RecurringRule.is_active == True
        ).all()

        recurring_predictions = []

        for rule in rules:
            # Calculate monthly total based on frequency
            amount = rule.amount
            freq = rule.frequency

            if freq == 'daily':
                monthly_total = amount * 30
            elif freq == 'weekly':
                monthly_total = amount * 4
            else:  # monthly
                monthly_total = amount

            # Get next occurrence
            next_occurrence = rule.get_next_occurrence()

            recurring_predictions.append({
                "rule_id": rule.id,
                "name": rule.note or f"{rule.category.name_th if rule.category else 'รายการ'}",
                "amount": amount,
                "frequency": freq,
                "next_occurrence": next_occurrence.isoformat() if next_occurrence else None,
                "monthly_total": monthly_total,
                "amount_formatted": satang_to_baht(amount),
                "monthly_total_formatted": satang_to_baht(monthly_total)
            })

        total_monthly = sum(r["monthly_total"] for r in recurring_predictions)

        return {
            "recurring": recurring_predictions,
            "total_monthly_recurring": total_monthly,
            "total_monthly_recurring_formatted": satang_to_baht(total_monthly)
        }

    @staticmethod
    def get_income_trend_projection(project_id, months=6):
        """
        Get income trend projection

        Args:
            project_id: Project ID
            months: Number of months to analyze and project

        Returns:
            dict: {
                "historical": [
                    {"month": "2025-08", "income": 50000}
                ],
                "projection": [
                    {"month": "2025-09", "projected": 52000}
                ],
                "trend": "increasing",
                "stability": "stable"
            }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)

        # Query monthly income
        results = db.session.query(
            extract('year', Transaction.occurred_at).label('year'),
            extract('month', Transaction.occurred_at).label('month'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'income',
            Transaction.occurred_at >= start_date,
            Transaction.deleted_at.is_(None)
        ).group_by(
            'year',
            'month'
        ).order_by(
            'year',
            'month'
        ).all()

        # Process historical data
        historical = []
        for r in results:
            month_key = f"{int(r.year)}-{str(int(r.month)).zfill(2)}"
            historical.append({
                "month": month_key,
                "income": r.total
            })

        # Simple projection (last 3 months average)
        if len(historical) >= 3:
            recent_avg = statistics.mean(h["income"] for h in historical[-3:])
            projection = []

            for i in range(1, 4):  # Project 3 months ahead
                # Simple trend analysis
                if len(historical) >= 2:
                    growth_rate = (historical[-1]["income"] - historical[-2]["income"]) / historical[-2]["income"]
                    projected = historical[-1]["income"] * (1 + growth_rate)
                else:
                    projected = recent_avg

                projected_date = datetime.now() + timedelta(days=30 * i)
                month_key = f"{projected_date.year}-{str(projected_date.month).zfill(2)}"

                projection.append({
                    "month": month_key,
                    "projected": max(0, projected)
                })
        else:
            projection = []

        # Determine trend
        if len(historical) >= 2:
            if historical[-1]["income"] > historical[-2]["income"]:
                trend = "increasing"
            elif historical[-1]["income"] < historical[-2]["income"]:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Determine stability
        if len(historical) >= 3:
            variance = statistics.variance(h["income"] for h in historical)
            mean = statistics.mean(h["income"] for h in historical)
            cv = (variance ** 0.5 / mean) if mean > 0 else 1

            if cv < 0.1:
                stability = "very_stable"
            elif cv < 0.2:
                stability = "stable"
            elif cv < 0.3:
                stability = "moderate"
            else:
                stability = "volatile"
        else:
            stability = "unknown"

        return {
            "historical": historical,
            "projection": projection,
            "trend": trend,
            "stability": stability
        }
