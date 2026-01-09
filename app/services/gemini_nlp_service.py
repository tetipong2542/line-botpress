"""
Gemini NLP Service - Smart natural language processing for chatbot
Uses Google Gemini API to understand user intent and extract entities
"""
import os
import json
import re
from datetime import datetime, date

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiNLPService:
    """Service for NLP processing using Gemini API"""
    
    SYSTEM_PROMPT = """คุณเป็น NLP Parser สำหรับแอปบันทึกรายรับรายจ่าย
    
วิเคราะห์ข้อความและ return JSON ตามรูปแบบนี้เท่านั้น:

{
  "intent": "create_transaction|create_recurring|update_recurring|delete_recurring|get_recurring|create_goal|contribute_goal|get_goals|get_summary|get_transactions|analyze|general",
  "entities": {
    "amount": null หรือ ตัวเลข,
    "category_name": null หรือ string,
    "type": "income|expense" หรือ null,
    "note": null หรือ string,
    "day_of_month": null หรือ 1-31,
    "keyword": null หรือ string (สำหรับค้นหา/ลบ),
    "period": "today|this_week|this_month|last_month" หรือ null,
    "goal_name": null หรือ string,
    "target_amount": null หรือ ตัวเลข,
    "months": null หรือ ตัวเลข
  },
  "missing_fields": ["field1", "field2"] หรือ [],
  "fallback_question": null หรือ string (คำถามถ้าข้อมูลไม่ครบ),
  "confidence": 0.0-1.0
}

กฎ:
1. ถ้าไม่มี amount สำหรับ transaction → missing_fields: ["amount"], fallback_question: "กรุณาระบุจำนวนเงินด้วยค่ะ"
2. ถ้าไม่มี day_of_month สำหรับ recurring → missing_fields: ["day_of_month"], fallback_question: "ทุกวันที่เท่าไหร่ของเดือน? (1-31)"
3. ถ้าไม่มี amount สำหรับ recurring → missing_fields: ["amount"]
4. intent "general" สำหรับคำถามทั่วไปที่ไม่เกี่ยวกับการเงิน
5. ถ้าเป็นคำสั่งลบ → ต้องมี keyword

ตัวอย่าง:
- "กินข้าว 350" → intent: create_transaction, type: expense, amount: 350, category_name: "อาหาร"
- "เพิ่มรายการประจำ Netflix 300 บาททุกวันที่ 1" → intent: create_recurring, amount: 300, day_of_month: 1, note: "Netflix"
- "เพิ่มรายการประจำ Netflix" → intent: create_recurring, missing_fields: ["amount", "day_of_month"], fallback_question: "กรุณาระบุจำนวนเงินและวันที่"
- "รายการประจำ" → intent: get_recurring
- "สรุป" → intent: get_summary
- "ลบรายการประจำ Netflix" → intent: delete_recurring, keyword: "Netflix"
"""

    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.model = None
        
        if GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def is_available(self):
        """Check if Gemini is properly configured"""
        return GEMINI_AVAILABLE and self.api_key and self.model
    
    def parse_message(self, message: str) -> dict:
        """
        Parse user message using Gemini AI
        
        Returns:
            dict with intent, entities, missing_fields, fallback_question
        """
        if not self.is_available():
            # Fallback to simple regex parsing
            return self._simple_parse(message)
        
        try:
            prompt = f"{self.SYSTEM_PROMPT}\n\nข้อความ: {message}\n\nJSON:"
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 500,
                }
            )
            
            # Extract JSON from response
            text = response.text.strip()
            
            # Find JSON block
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(text)
            return result
            
        except Exception as e:
            print(f"Gemini parse error: {e}")
            return self._simple_parse(message)
    
    def _simple_parse(self, message: str) -> dict:
        """Simple regex-based parsing as fallback"""
        message_lower = message.lower()
        
        result = {
            'intent': 'general',
            'entities': {},
            'missing_fields': [],
            'fallback_question': None,
            'confidence': 0.5
        }
        
        # Check for recurring patterns
        if 'รายการประจำ' in message:
            if any(x in message_lower for x in ['เพิ่ม', 'สร้าง', 'ตั้ง']):
                result['intent'] = 'create_recurring'
                # Extract amount
                amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
                if amount_match:
                    result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
                else:
                    result['missing_fields'].append('amount')
                
                # Extract day
                day_match = re.search(r'วันที่\s*(\d{1,2})', message)
                if day_match:
                    result['entities']['day_of_month'] = int(day_match.group(1))
                else:
                    result['missing_fields'].append('day_of_month')
                
                if result['missing_fields']:
                    result['fallback_question'] = self._generate_fallback_question(result['missing_fields'])
                    
            elif any(x in message_lower for x in ['ลบ', 'ยกเลิก']):
                result['intent'] = 'delete_recurring'
                # Extract keyword
                words = message.split()
                for i, w in enumerate(words):
                    if 'ประจำ' in w and i + 1 < len(words):
                        result['entities']['keyword'] = words[i + 1]
                        break
            elif any(x in message_lower for x in ['แก้ไข', 'เปลี่ยน', 'อัพเดท']):
                result['intent'] = 'update_recurring'
            else:
                result['intent'] = 'get_recurring'
        
        # Check for summary
        elif any(x in message_lower for x in ['สรุป', 'รายงาน', 'ยอด']):
            result['intent'] = 'get_summary'
            if 'วันนี้' in message_lower:
                result['entities']['period'] = 'today'
            elif 'สัปดาห์' in message_lower:
                result['entities']['period'] = 'this_week'
        
        # Check for goals
        elif any(x in message_lower for x in ['เป้าหมาย', 'ออม']):
            if any(x in message_lower for x in ['ตั้ง', 'สร้าง']):
                result['intent'] = 'create_goal'
            elif any(x in message_lower for x in ['เพิ่ม']):
                result['intent'] = 'contribute_goal'
            else:
                result['intent'] = 'get_goals'
        
        # Check for transaction
        elif re.search(r'(\d+(?:,\d+)?)\s*บาท', message):
            result['intent'] = 'create_transaction'
            amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
            if amount_match:
                result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
            result['entities']['type'] = 'income' if any(x in message_lower for x in ['รับ', 'เงินเดือน', 'ได้']) else 'expense'
        
        return result
    
    def _generate_fallback_question(self, missing_fields: list) -> str:
        """Generate fallback question based on missing fields"""
        questions = []
        
        if 'amount' in missing_fields:
            questions.append("จำนวนเงินเท่าไหร่?")
        if 'day_of_month' in missing_fields:
            questions.append("ทุกวันที่เท่าไหร่ของเดือน? (1-31)")
        if 'category_name' in missing_fields:
            questions.append("หมวดหมู่อะไร?")
        if 'goal_name' in missing_fields:
            questions.append("ชื่อเป้าหมายอะไร?")
        if 'target_amount' in missing_fields:
            questions.append("เป้าหมายเท่าไหร่?")
        
        if questions:
            return "กรุณาระบุ:\n" + "\n".join([f"• {q}" for q in questions])
        return None


# Singleton instance
gemini_nlp = GeminiNLPService()
