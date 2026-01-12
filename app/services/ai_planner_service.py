"""
AI Planner Service - One-Click Financial Planning with AI
Uses OpenRouter API for intelligent financial planning
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


class AIPlannerService:
    """Service for AI-powered financial planning"""
    
    def __init__(self):
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def _get_user_api_key(self, user):
        """Get OpenRouter API key from user or system"""
        user_key = getattr(user, 'openrouter_api_key', None)
        if user_key:
            return user_key
        # Fallback to system key
        return os.environ.get('OPENROUTER_API_KEY')
    
    def _get_user_model(self, user):
        """Get selected model from user preferences"""
        model = getattr(user, 'openrouter_model', None)
        return model or 'openai/gpt-4o-mini'
    
    def _call_ai(self, api_key: str, model: str, system_prompt: str, user_message: str) -> str:
        """Call OpenRouter API with given prompts"""
        if not api_key:
            return None
        
        try:
            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
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
    
    def generate_monthly_plan(self, user, transactions: list, categories: list, 
                               current_budgets: list = None, goals: list = None) -> dict:
        """
        Generate a complete monthly financial plan using AI
        
        Args:
            user: User object with API key
            transactions: List of past transactions [{amount, category, date, type}]
            categories: Available categories [{id, name, icon}]
            current_budgets: Existing budgets [{category_id, amount}]
            goals: Savings goals [{name, target, current}]
        
        Returns:
            dict with monthly plan including budgets, savings suggestions, alerts
        """
        api_key = self._get_user_api_key(user)
        model = self._get_user_model(user)
        
        if not api_key:
            return self._fallback_plan(transactions, categories)
        
        # Prepare transaction summary for AI
        summary = self._summarize_transactions(transactions)
        
        system_prompt = """คุณคือที่ปรึกษาการเงินส่วนบุคคล AI ภาษาไทย วิเคราะห์ข้อมูลการใช้จ่ายและสร้างแผนการเงินรายเดือน

ตอบกลับเป็น JSON เท่านั้น (ห้ามใช้ markdown):
{
    "monthly_plan": {
        "budgets": [
            {"category": "หมวดหมู่", "amount": 5000, "reason": "เหตุผลภาษาไทย"}
        ],
        "savings_target": 5000,
        "savings_percentage": 20,
        "allocation_rule": "50/30/20"
    },
    "recurring_detected": [
        {"name": "ชื่อรายจ่าย", "amount": 350, "frequency": "รายเดือน", "next_date": "2026-02-01"}
    ],
    "alerts": [
        "คำเตือนสำคัญ เช่น ใช้เงินเกินงบ"
    ],
    "tips": [
        "คำแนะนำประหยัดเงินภาษาไทย"
    ],
    "summary": "สรุปภาพรวมสถานการณ์การเงินของคุณ 2-3 ประโยคภาษาไทย"
}

หมายเหตุสำคัญ:
- ตอบเป็นภาษาไทยทั้งหมด
- ให้คำแนะนำที่เป็นประโยชน์และปฏิบัติได้จริง
- budget ควรสมจริงตามพฤติกรรมการใช้จ่าย"""

        user_message = f"""วิเคราะห์ข้อมูลการเงินและสร้างแผนรายเดือน:

สรุปรายการ (3 เดือนล่าสุด):
{json.dumps(summary, ensure_ascii=False, indent=2)}

หมวดหมู่ที่มี:
{json.dumps([c.get('name') for c in categories[:15]], ensure_ascii=False)}

เป้าหมายการออม:
{json.dumps(goals or [], ensure_ascii=False)}

สร้างแผนงบประมาณรายเดือนที่สมจริงตามข้อมูลนี้ โปรดตอบเป็นภาษาไทยทั้งหมด"""

        ai_response = self._call_ai(api_key, model, system_prompt, user_message)
        
        if ai_response:
            try:
                # Clean response
                cleaned = ai_response.strip()
                if cleaned.startswith('```'):
                    cleaned = cleaned.split('\n', 1)[1].rsplit('```', 1)[0]
                return json.loads(cleaned)
            except:
                pass
        
        return self._fallback_plan(transactions, categories)
    
    def _summarize_transactions(self, transactions: list) -> dict:
        """Summarize transactions for AI analysis"""
        if not transactions:
            return {"total_income": 0, "total_expense": 0, "categories": {}}
        
        total_income = 0
        total_expense = 0
        categories = {}
        
        for tx in transactions:
            amount = tx.get('amount', 0)
            tx_type = tx.get('type', 'expense')
            category = tx.get('category_name', 'Unknown')
            
            if tx_type == 'income':
                total_income += amount
            else:
                total_expense += amount
                categories[category] = categories.get(category, 0) + amount
        
        # Sort categories by amount
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": dict(sorted_cats[:10]),
            "transaction_count": len(transactions)
        }
    
    def _fallback_plan(self, transactions: list, categories: list) -> dict:
        """Generate a basic plan without AI"""
        summary = self._summarize_transactions(transactions)
        income = summary.get('total_income', 0)
        expense = summary.get('total_expense', 0)
        
        # 50/30/20 rule
        needs_budget = income * 0.5
        wants_budget = income * 0.3
        savings_budget = income * 0.2
        
        budgets = []
        top_cats = summary.get('top_categories', {})
        for cat_name, amount in list(top_cats.items())[:5]:
            budgets.append({
                "category": cat_name,
                "amount": int(amount * 1.1),  # 10% buffer
                "reason": "Based on past spending"
            })
        
        return {
            "monthly_plan": {
                "budgets": budgets,
                "savings_target": int(savings_budget),
                "savings_percentage": 20,
                "allocation_rule": "50/30/20"
            },
            "recurring_detected": [],
            "alerts": [
                "ยังไม่ได้เชื่อมต่อ AI - แผนนี้เป็นแผนพื้นฐาน"
            ] if not budgets else [],
            "tips": [
                "บันทึกรายรับ-รายจ่ายทุกวันเพื่อข้อมูลที่แม่นยำขึ้น",
                "ตั้งงบประมาณตามหลัก 50/30/20"
            ],
            "summary": f"รายรับ: ฿{income:,.0f} | รายจ่าย: ฿{expense:,.0f} | คงเหลือ: ฿{income-expense:,.0f}"
        }
    
    def detect_recurring_expenses(self, user, transactions: list) -> list:
        """
        Detect recurring expenses from transaction history
        
        Returns:
            List of recurring expenses with frequency and next expected date
        """
        api_key = self._get_user_api_key(user)
        model = self._get_user_model(user)
        
        if not api_key or len(transactions) < 10:
            return self._fallback_recurring(transactions)
        
        # Prepare data - group by note/description
        tx_notes = [{"note": tx.get('note', ''), "amount": tx.get('amount', 0), 
                     "date": str(tx.get('date', ''))} for tx in transactions[:100]]
        
        system_prompt = """วิเคราะห์รายการและระบุรายจ่ายประจำ (recurring expenses)

ตอบเป็น JSON เท่านั้น:
{
    "recurring": [
        {
            "name": "ชื่อรายจ่าย",
            "amount": 500,
            "frequency": "รายเดือน|รายสัปดาห์|รายปี",
            "confidence": 0.95,
            "next_date": "2026-02-15",
            "category_suggestion": "หมวดหมู่ที่แนะนำ"
        }
    ]
}

ตอบเป็นภาษาไทยทั้งหมด"""

        user_message = f"Find recurring patterns in these transactions:\n{json.dumps(tx_notes, ensure_ascii=False)}"
        
        ai_response = self._call_ai(api_key, model, system_prompt, user_message)
        
        if ai_response:
            try:
                cleaned = ai_response.strip()
                if cleaned.startswith('```'):
                    cleaned = cleaned.split('\n', 1)[1].rsplit('```', 1)[0]
                result = json.loads(cleaned)
                return result.get('recurring', [])
            except:
                pass
        
        return self._fallback_recurring(transactions)
    
    def _fallback_recurring(self, transactions: list) -> list:
        """Basic recurring detection without AI"""
        recurring = []
        note_counts = {}
        
        for tx in transactions:
            note = tx.get('note', '').lower().strip()
            if len(note) > 3:
                if note not in note_counts:
                    note_counts[note] = {"count": 0, "amounts": [], "dates": []}
                note_counts[note]["count"] += 1
                note_counts[note]["amounts"].append(tx.get('amount', 0))
                note_counts[note]["dates"].append(tx.get('date'))
        
        for note, data in note_counts.items():
            if data["count"] >= 2:
                avg_amount = sum(data["amounts"]) / len(data["amounts"])
                recurring.append({
                    "name": note.title(),
                    "amount": int(avg_amount),
                    "frequency": "monthly",
                    "confidence": min(0.5 + (data["count"] * 0.1), 0.95),
                    "next_date": (date.today() + timedelta(days=30)).isoformat()
                })
        
        return sorted(recurring, key=lambda x: x["confidence"], reverse=True)[:10]
    
    def estimate_taxes(self, user, annual_income: float, deductions: dict = None) -> dict:
        """
        Estimate annual tax based on Thai tax brackets
        
        Args:
            user: User object
            annual_income: Total annual income
            deductions: Optional deductions {personal, insurance, etc}
        
        Returns:
            dict with tax estimation and breakdown
        """
        api_key = self._get_user_api_key(user)
        model = self._get_user_model(user)
        
        # Thai tax brackets 2026
        brackets = [
            (0, 150000, 0),
            (150001, 300000, 0.05),
            (300001, 500000, 0.10),
            (500001, 750000, 0.15),
            (750001, 1000000, 0.20),
            (1000001, 2000000, 0.25),
            (2000001, 5000000, 0.30),
            (5000001, float('inf'), 0.35)
        ]
        
        # Apply standard deductions
        base_deduction = 60000  # Personal deduction
        expenses_deduction = min(annual_income * 0.5, 100000)  # 50% max 100k
        
        total_deductions = base_deduction + expenses_deduction
        if deductions:
            total_deductions += sum(deductions.values())
        
        taxable_income = max(0, annual_income - total_deductions)
        
        # Calculate tax
        tax = 0
        remaining = taxable_income
        tax_breakdown = []
        
        for low, high, rate in brackets:
            if remaining <= 0:
                break
            bracket_income = min(remaining, high - low)
            bracket_tax = bracket_income * rate
            tax += bracket_tax
            if bracket_tax > 0:
                tax_breakdown.append({
                    "bracket": f"{low:,}-{high:,}" if high != float('inf') else f"{low:,}+",
                    "rate": f"{rate*100:.0f}%",
                    "income": bracket_income,
                    "tax": bracket_tax
                })
            remaining -= bracket_income
        
        result = {
            "annual_income": annual_income,
            "total_deductions": total_deductions,
            "taxable_income": taxable_income,
            "estimated_tax": tax,
            "effective_rate": (tax / annual_income * 100) if annual_income > 0 else 0,
            "breakdown": tax_breakdown,
            "monthly_tax_reserve": tax / 12,
            "tips": []
        }
        
        # AI enhancement for tips
        if api_key and tax > 0:
            system_prompt = "You are a Thai tax advisor. Give 3 short tips to reduce tax legally. JSON: {\"tips\": [\"tip1\", \"tip2\", \"tip3\"]}"
            user_msg = f"Annual income: {annual_income:,.0f} THB, Current tax: {tax:,.0f} THB"
            
            ai_response = self._call_ai(api_key, model, system_prompt, user_msg)
            if ai_response:
                try:
                    cleaned = ai_response.strip()
                    if cleaned.startswith('```'):
                        cleaned = cleaned.split('\n', 1)[1].rsplit('```', 1)[0]
                    tips_data = json.loads(cleaned)
                    result["tips"] = tips_data.get("tips", [])
                except:
                    pass
        
            result["tips"] = [
                "พิจารณาลงทุน SSF/RMF เพื่อลดหย่อนภาษี",
                "เก็บใบเสร็จค่ารักษาพยาบาลและประกันเพื่อลดหย่อน",
                "บริจาคให้มูลนิธิที่จดทะเบียนเพื่อลดหย่อนภาษี"
            ]
        
        return result


# Singleton instance
ai_planner = AIPlannerService()
