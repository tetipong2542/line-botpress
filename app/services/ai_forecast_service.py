"""
AI Forecast Service - Future Financial Predictions
Provides cash flow forecasting, what-if simulation, and financial health scoring
"""
import os
import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass


class AIForecastService:
    """Service for AI-powered financial forecasting"""
    
    def __init__(self):
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def _get_user_api_key(self, user):
        """Get OpenRouter API key from user or system"""
        user_key = getattr(user, 'openrouter_api_key', None)
        if user_key:
            return user_key
        return os.environ.get('OPENROUTER_API_KEY')
    
    def _get_user_model(self, user):
        """Get selected model from user preferences"""
        model = getattr(user, 'openrouter_model', None)
        return model or 'openai/gpt-4o-mini'
    
    def _call_ai(self, api_key: str, model: str, system_prompt: str, user_message: str) -> str:
        """Call OpenRouter API"""
        if not api_key:
            return None
        try:
            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 1500,
                "temperature": 0.5
            }).encode('utf-8')
            
            req = urllib.request.Request(self.api_url, data=payload, method='POST')
            req.add_header('Authorization', f'Bearer {api_key}')
            req.add_header('Content-Type', 'application/json')
            req.add_header('HTTP-Referer', 'https://promptjod.app')
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
        except Exception as e:
            print(f"AI call error: {e}")
            return None
    
    def predict_cash_flow(self, transactions: list, months_ahead: int = 3) -> dict:
        """
        Predict future cash flow based on transaction history
        
        Args:
            transactions: List of past transactions
            months_ahead: Number of months to predict (3, 6, or 12)
        
        Returns:
            dict with monthly predictions
        """
        if not transactions:
            return {"predictions": [], "summary": "ไม่มีข้อมูลเพียงพอ"}
        
        # Calculate monthly averages
        monthly_data = {}
        for tx in transactions:
            tx_date = tx.get('date', '')
            if isinstance(tx_date, str) and len(tx_date) >= 7:
                month_key = tx_date[:7]  # YYYY-MM
            else:
                continue
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {"income": 0, "expense": 0}
            
            amount = tx.get('amount', 0)
            if tx.get('type') == 'income':
                monthly_data[month_key]["income"] += amount
            else:
                monthly_data[month_key]["expense"] += amount
        
        if not monthly_data:
            return {"predictions": [], "summary": "ไม่มีข้อมูลเพียงพอ"}
        
        # Calculate averages
        months = list(monthly_data.values())
        avg_income = sum(m["income"] for m in months) / len(months)
        avg_expense = sum(m["expense"] for m in months) / len(months)
        avg_balance = avg_income - avg_expense
        
        # Generate predictions
        predictions = []
        current_date = date.today()
        cumulative_balance = 0
        
        for i in range(1, months_ahead + 1):
            future_date = current_date + relativedelta(months=i)
            month_name = future_date.strftime("%B %Y")
            
            # Simple linear prediction with slight variance
            variance = 1 + (((i % 3) - 1) * 0.05)  # ±5% variance
            pred_income = avg_income * variance
            pred_expense = avg_expense * (2 - variance)
            pred_balance = pred_income - pred_expense
            cumulative_balance += pred_balance
            
            predictions.append({
                "month": month_name,
                "month_num": i,
                "predicted_income": round(pred_income, 2),
                "predicted_expense": round(pred_expense, 2),
                "predicted_balance": round(pred_balance, 2),
                "cumulative_balance": round(cumulative_balance, 2),
                "status": "positive" if pred_balance >= 0 else "negative"
            })
        
        # Calculate trend
        if avg_balance > 0:
            trend = "increasing"
            trend_message = f"คาดว่าจะมีเงินเหลือเฉลี่ย ฿{avg_balance:,.0f}/เดือน"
        else:
            trend = "decreasing"
            trend_message = f"คาดว่าจะขาดทุนเฉลี่ย ฿{abs(avg_balance):,.0f}/เดือน"
        
        return {
            "predictions": predictions,
            "averages": {
                "income": round(avg_income, 2),
                "expense": round(avg_expense, 2),
                "balance": round(avg_balance, 2)
            },
            "trend": trend,
            "trend_message": trend_message,
            "summary": f"พยากรณ์ {months_ahead} เดือนข้างหน้า: {trend_message}"
        }
    
    def simulate_what_if(self, transactions: list, changes: dict) -> dict:
        """
        What-if scenario simulation
        
        Args:
            transactions: Current transaction history
            changes: Dict with category changes, e.g. {"อาหาร": -20, "เดินทาง": -10}
                     Values are percentage changes (-20 = reduce by 20%)
        
        Returns:
            dict with simulation results
        """
        if not transactions:
            return {"error": "No data"}
        
        # Calculate current totals
        category_totals = {}
        total_income = 0
        total_expense = 0
        
        for tx in transactions:
            amount = tx.get('amount', 0)
            category = tx.get('category_name', 'Other')
            
            if tx.get('type') == 'income':
                total_income += amount
            else:
                total_expense += amount
                category_totals[category] = category_totals.get(category, 0) + amount
        
        # Apply changes
        new_expense = 0
        savings_per_category = {}
        
        for cat, amount in category_totals.items():
            change_pct = changes.get(cat, 0)
            new_amount = amount * (1 + change_pct / 100)
            new_expense += new_amount
            if change_pct != 0:
                savings_per_category[cat] = {
                    "original": amount,
                    "new": new_amount,
                    "saved": amount - new_amount,
                    "change_pct": change_pct
                }
        
        # Calculate impact
        original_balance = total_income - total_expense
        new_balance = total_income - new_expense
        monthly_savings = new_balance - original_balance
        annual_savings = monthly_savings * 12
        
        return {
            "original": {
                "income": total_income,
                "expense": total_expense,
                "balance": original_balance
            },
            "simulated": {
                "income": total_income,
                "expense": round(new_expense, 2),
                "balance": round(new_balance, 2)
            },
            "impact": {
                "monthly_savings": round(monthly_savings, 2),
                "annual_savings": round(annual_savings, 2),
                "expense_reduction": round(total_expense - new_expense, 2)
            },
            "by_category": savings_per_category,
            "summary": f"หากปรับตามนี้ จะประหยัดได้ ฿{monthly_savings:,.0f}/เดือน (฿{annual_savings:,.0f}/ปี)"
        }
    
    def calculate_goal_timeline(self, goal_target: float, current_amount: float,
                                monthly_savings: float) -> dict:
        """
        Calculate timeline to reach a goal
        
        Returns:
            dict with timeline prediction
        """
        remaining = goal_target - current_amount
        
        if remaining <= 0:
            return {
                "achieved": True,
                "months_remaining": 0,
                "target_date": date.today().isoformat(),
                "message": "เป้าหมายสำเร็จแล้ว!"
            }
        
        if monthly_savings <= 0:
            return {
                "achieved": False,
                "months_remaining": -1,
                "target_date": None,
                "message": "ไม่สามารถคำนวณได้ (ไม่มีเงินออมรายเดือน)"
            }
        
        months_needed = remaining / monthly_savings
        target_date = date.today() + relativedelta(months=int(months_needed) + 1)
        
        return {
            "achieved": False,
            "months_remaining": round(months_needed, 1),
            "target_date": target_date.isoformat(),
            "completion_date": target_date.strftime("%B %Y"),
            "progress_pct": round(current_amount / goal_target * 100, 1),
            "monthly_required": round(remaining / max(months_needed, 1), 2),
            "message": f"จะถึงเป้าหมายใน {months_needed:.0f} เดือน ({target_date.strftime('%B %Y')})"
        }
    
    def calculate_financial_health_score(self, transactions: list, budgets: list = None,
                                          goals: list = None) -> dict:
        """
        Calculate financial health score (0-100)
        
        Factors:
        - Savings rate (25 points)
        - Budget adherence (25 points)
        - Emergency fund (25 points)
        - Goal progress (25 points)
        """
        score = 0
        breakdown = []
        
        # Calculate basic stats
        total_income = sum(tx.get('amount', 0) for tx in transactions if tx.get('type') == 'income')
        total_expense = sum(tx.get('amount', 0) for tx in transactions if tx.get('type') == 'expense')
        
        # 1. Savings Rate (25 points)
        if total_income > 0:
            savings_rate = (total_income - total_expense) / total_income * 100
            if savings_rate >= 20:
                savings_score = 25
            elif savings_rate >= 10:
                savings_score = 20
            elif savings_rate >= 0:
                savings_score = 15
            else:
                savings_score = max(0, 10 + savings_rate / 10)
        else:
            savings_rate = 0
            savings_score = 0
        
        score += savings_score
        breakdown.append({
            "category": "อัตราการออม",
            "score": round(savings_score, 1),
            "max": 25,
            "detail": f"{savings_rate:.1f}%",
            "status": "good" if savings_score >= 20 else "warning" if savings_score >= 10 else "poor"
        })
        
        # 2. Budget Adherence (25 points)
        if budgets:
            over_budget_count = 0
            total_budgets = len(budgets)
            for b in budgets:
                used = b.get('used', 0)
                limit = b.get('limit', 1)
                if limit > 0 and used > limit:
                    over_budget_count += 1
            
            adherence_rate = (total_budgets - over_budget_count) / total_budgets * 100
            budget_score = adherence_rate / 100 * 25
        else:
            budget_score = 15  # Neutral if no budgets set
            adherence_rate = 0
        
        score += budget_score
        breakdown.append({
            "category": "การปฏิบัติตามงบ",
            "score": round(budget_score, 1),
            "max": 25,
            "detail": f"{adherence_rate:.0f}%" if budgets else "ไม่มีงบที่ตั้งไว้",
            "status": "good" if budget_score >= 20 else "warning" if budget_score >= 10 else "poor"
        })
        
        # 3. Emergency Fund (25 points) - Based on savings capacity
        if total_income > 0:
            monthly_expenses = total_expense
            months_of_expenses = (total_income - total_expense) * 6 / max(monthly_expenses, 1)  # 6 months accumulation
            if months_of_expenses >= 6:
                emergency_score = 25
            elif months_of_expenses >= 3:
                emergency_score = 20
            elif months_of_expenses >= 1:
                emergency_score = 12
            else:
                emergency_score = 5
        else:
            emergency_score = 5
        
        score += emergency_score
        breakdown.append({
            "category": "กองทุนฉุกเฉิน",
            "score": round(emergency_score, 1),
            "max": 25,
            "detail": "มีศักยภาพ" if emergency_score >= 20 else "ปานกลาง" if emergency_score >= 10 else "ต้องปรับปรุง",
            "status": "good" if emergency_score >= 20 else "warning" if emergency_score >= 10 else "poor"
        })
        
        # 4. Goal Progress (25 points)
        if goals:
            total_progress = 0
            for g in goals:
                target = g.get('target', 1)
                current = g.get('current', 0)
                if target > 0:
                    total_progress += min(current / target, 1)
            
            avg_progress = total_progress / len(goals)
            goal_score = avg_progress * 25
        else:
            goal_score = 12.5  # Neutral if no goals
        
        score += goal_score
        breakdown.append({
            "category": "ความคืบหน้าเป้าหมาย",
            "score": round(goal_score, 1),
            "max": 25,
            "detail": f"{goal_score/25*100:.0f}%" if goals else "ไม่มีเป้าหมาย",
            "status": "good" if goal_score >= 20 else "warning" if goal_score >= 10 else "poor"
        })
        
        # Overall health status
        if score >= 80:
            status = "excellent"
            message = "สุขภาพการเงินดีเยี่ยม!"
        elif score >= 60:
            status = "good"
            message = "สุขภาพการเงินดี"
        elif score >= 40:
            status = "fair"
            message = "สุขภาพการเงินพอใช้"
        else:
            status = "poor"
            message = "ต้องปรับปรุงสุขภาพการเงิน"
        
        return {
            "score": round(score, 1),
            "max_score": 100,
            "status": status,
            "message": message,
            "breakdown": breakdown,
            "recommendations": self._generate_health_recommendations(breakdown)
        }
    
    def _generate_health_recommendations(self, breakdown: list) -> list:
        """Generate recommendations based on health breakdown"""
        recommendations = []
        
        for item in breakdown:
            if item["status"] == "poor":
                if item["category"] == "อัตราการออม":
                    recommendations.append("พยายามลดรายจ่ายที่ไม่จำเป็นเพื่อเพิ่มอัตราการออม")
                elif item["category"] == "การปฏิบัติตามงบ":
                    recommendations.append("ตรวจสอบและปรับงบประมาณให้ตรงกับความเป็นจริง")
                elif item["category"] == "กองทุนฉุกเฉิน":
                    recommendations.append("สะสมเงินฉุกเฉินให้เพียงพอสำหรับ 3-6 เดือน")
                elif item["category"] == "ความคืบหน้าเป้าหมาย":
                    recommendations.append("ตั้งเป้าหมายการออมที่ชัดเจนและเป็นไปได้จริง")
        
        if not recommendations:
            recommendations.append("รักษาพฤติกรรมการเงินที่ดีเช่นนี้ต่อไป!")
        
        return recommendations[:3]


# Singleton instance
ai_forecast = AIForecastService()
