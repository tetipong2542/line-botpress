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
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
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
        
        # Check for budget management (ตั้งงบ/งบประมาณ)
        if any(x in message_lower for x in ['ตั้งงบ', 'งบประมาณ', 'budget', 'งบ']):
            if any(x in message_lower for x in ['ดู', 'แสดง', 'เท่าไหร่']):
                result['intent'] = 'get_budget'
            elif any(x in message_lower for x in ['ลบ', 'ยกเลิก']):
                result['intent'] = 'delete_budget'
                # Extract category
                cat_match = re.search(r'(?:ลบงบ|ยกเลิกงบ)\s*(\S+)', message)
                if cat_match:
                    result['entities']['category_name'] = cat_match.group(1)
            elif any(x in message_lower for x in ['แก้', 'เปลี่ยน', 'อัพเดท']):
                result['intent'] = 'update_budget'
                # Extract amount
                amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
                if amount_match:
                    result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
                # Extract category
                cat_match = re.search(r'(?:แก้งบ|เปลี่ยนงบ|อัพเดทงบ)\s*(\S+)', message)
                if cat_match:
                    cat_name = cat_match.group(1)
                    if not cat_name.isdigit() and 'บาท' not in cat_name and 'เป็น' not in cat_name:
                        result['entities']['category_name'] = cat_name
            else:
                result['intent'] = 'set_budget'
                # Extract amount first
                amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
                if amount_match:
                    result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
                # Extract category (word after ตั้งงบ or งบ, excluding numbers)
                cat_match = re.search(r'(?:ตั้งงบ|งบ)\s*(\S+)', message)
                if cat_match:
                    cat_name = cat_match.group(1)
                    if not cat_name.isdigit() and 'บาท' not in cat_name:
                        result['entities']['category_name'] = cat_name
            return result
        
        # Check for help command
        if any(x in message_lower for x in ['ช่วยเหลือ', 'help', 'คำสั่ง', 'ทำอะไรได้']):
            result['intent'] = 'get_help'
            return result
        
        # Check for resume recurring (เปิด Netflix) - before recurring check
        if any(x in message_lower for x in ['เปิด', 'resume', 'เริ่ม']) and 'ประจำ' not in message_lower and 'เว็บ' not in message_lower:
            result['intent'] = 'resume_recurring'
            words = message.split()
            for i, w in enumerate(words):
                if any(kw in w for kw in ['เปิด', 'resume', 'เริ่ม']) and i + 1 < len(words):
                    result['entities']['keyword'] = words[i + 1]
                    break
            return result
        
        # Check for pause recurring (หยุด/พัก Netflix) - before recurring check
        if any(x in message_lower for x in ['หยุด', 'พัก', 'pause']) and 'ประจำ' not in message_lower:
            result['intent'] = 'pause_recurring'
            words = message.split()
            for i, w in enumerate(words):
                if any(kw in w for kw in ['หยุด', 'พัก', 'pause']) and i + 1 < len(words):
                    result['entities']['keyword'] = words[i + 1]
                    break
            return result
        
        # Check for withdraw goal (ถอนเงิน xxx บาท)
        if any(x in message_lower for x in ['ถอนเงิน', 'ถอน', 'withdraw']) and 'ออม' not in message_lower:
            result['intent'] = 'withdraw_goal'
            # Extract goal name
            words = message.split()
            for i, w in enumerate(words):
                if any(kw in w for kw in ['ถอน', 'จาก']) and i + 1 < len(words):
                    result['entities']['goal_name'] = words[i + 1]
                    break
            # Extract amount
            amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
            if amount_match:
                result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
            return result
        
        # Check for update transaction (แก้ไขรายการที่ 1)
        if any(x in message_lower for x in ['แก้ไขรายการ', 'แก้รายการ', 'เปลี่ยนรายการ']) and 'ประจำ' not in message_lower:
            result['intent'] = 'update_transaction'
            # Check for index
            num_match = re.search(r'ที่\s*(\d+)|รายการ\s*(\d+)', message)
            if num_match:
                result['entities']['index'] = int(num_match.group(1) or num_match.group(2))
            # Extract amount
            amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
            if amount_match:
                result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
            return result
        
        # Check for delete all (need clarification: recurring or regular?)
        if 'ลบรายการทั้งหมด' in message_lower or ('ลบ' in message_lower and 'ทั้งหมด' in message_lower):
            if 'ประจำ' in message_lower:
                result['intent'] = 'delete_recurring'
                result['entities']['delete_all'] = True
            elif 'เดือน' in message_lower:
                result['intent'] = 'delete_all_transactions'
            else:
                result['intent'] = 'delete_all_confirm'
            return result
        
        # Check for recurring patterns
        if 'รายการประจำ' in message or 'ประจำ' in message_lower:
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
                
                # Check for index (ลบรายการประจำที่ 1)
                num_match = re.search(r'ที่\s*(\d+)|ประจำ\s*(\d+)', message)
                if num_match:
                    result['entities']['index'] = int(num_match.group(1) or num_match.group(2))
                
                # Check for "ทั้งหมด"
                if 'ทั้งหมด' in message_lower:
                    result['entities']['delete_all'] = True
                
                # Extract keyword
                if 'index' not in result['entities'] and 'delete_all' not in result['entities']:
                    words = message.split()
                    for i, w in enumerate(words):
                        if 'ประจำ' in w and i + 1 < len(words):
                            next_word = words[i + 1]
                            if not next_word.isdigit() and next_word not in ['ที่', 'ทั้งหมด']:
                                result['entities']['keyword'] = next_word
                                break
            elif any(x in message_lower for x in ['หยุด', 'pause', 'พัก']):
                result['intent'] = 'pause_recurring'
                # Extract keyword
                words = message.split()
                for i, w in enumerate(words):
                    if any(kw in w for kw in ['หยุด', 'พัก']) and i + 1 < len(words):
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
            elif 'ปี' in message_lower or 'year' in message_lower:
                result['entities']['period'] = 'this_year'
            elif 'เดือนที่แล้ว' in message_lower or 'เดือนก่อน' in message_lower:
                result['entities']['period'] = 'last_month'
            else:
                result['entities']['period'] = 'this_month'
        
        # Check for categories
        elif any(x in message_lower for x in ['หมวดหมู่', 'category', 'categories']):
            # Extract category name helper
            def extract_category_name(msg, keywords):
                words = msg.split()
                for i, w in enumerate(words):
                    if any(kw in w for kw in keywords) and i + 1 < len(words):
                        return words[i + 1]
                return None
            
            if any(x in message_lower for x in ['ลบ', 'delete']):
                result['intent'] = 'delete_category'
                result['entities']['category_name'] = extract_category_name(message, ['หมวดหมู่', 'ลบ'])
            elif any(x in message_lower for x in ['แก้ไข', 'เปลี่ยน', 'update']):
                result['intent'] = 'update_category'
                result['entities']['category_name'] = extract_category_name(message, ['หมวดหมู่', 'แก้ไข', 'เปลี่ยน'])
                # Check for type change
                if 'รายรับ' in message_lower:
                    result['entities']['new_type'] = 'income'
                elif 'รายจ่าย' in message_lower:
                    result['entities']['new_type'] = 'expense'
            elif any(x in message_lower for x in ['สร้าง', 'เพิ่ม']):
                result['intent'] = 'create_category'
                result['entities']['category_name'] = extract_category_name(message, ['หมวดหมู่'])
                # Check for type
                if 'รายรับ' in message_lower:
                    result['entities']['type'] = 'income'
            else:
                result['intent'] = 'get_categories'
        
        # Check for goals
        elif any(x in message_lower for x in ['เป้าหมาย', 'ออม', 'goal']):
            if any(x in message_lower for x in ['ลบ', 'ยกเลิก', 'delete']):
                result['intent'] = 'delete_goal'
                # Extract goal name
                words = message.split()
                for i, w in enumerate(words):
                    if any(kw in w for kw in ['เป้าหมาย', 'ออม', 'ลบ']) and i + 1 < len(words):
                        result['entities']['goal_name'] = words[i + 1]
                        break
            elif any(x in message_lower for x in ['ตั้ง', 'สร้าง', 'create']):
                result['intent'] = 'create_goal'
                # Extract goal name and amount
                words = message.split()
                for i, w in enumerate(words):
                    if any(kw in w for kw in ['ออม', 'เป้า', 'ตั้ง']) and i + 1 < len(words):
                        result['entities']['goal_name'] = words[i + 1]
                        break
                # Extract amount
                amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
                if amount_match:
                    result['entities']['target_amount'] = float(amount_match.group(1).replace(',', ''))
                # Extract months
                months_match = re.search(r'(\d+)\s*เดือน', message)
                if months_match:
                    result['entities']['months'] = int(months_match.group(1))
            elif any(x in message_lower for x in ['เติม', 'เพิ่ม', 'add']):
                result['intent'] = 'contribute_goal'
                # Extract goal name
                words = message.split()
                for i, w in enumerate(words):
                    if any(kw in w for kw in ['เติม', 'เพิ่ม']) and i + 1 < len(words):
                        result['entities']['goal_name'] = words[i + 1]
                        break
                # Extract amount
                amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
                if amount_match:
                    result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
            elif any(x in message_lower for x in ['แก้ไข', 'เปลี่ยน', 'อัพเดท']):
                result['intent'] = 'update_goal'
                # Extract goal name (first non-keyword word)
                name_match = re.search(r'(?:แก้ไข|เปลี่ยน|อัพเดท)(?:เป้าหมาย)?\s*(\S+)', message)
                if name_match:
                    result['entities']['goal_name'] = name_match.group(1)
                # Extract new target
                amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
                if amount_match:
                    result['entities']['target_amount'] = float(amount_match.group(1).replace(',', ''))
            elif any(x in message_lower for x in ['ลบ', 'ยกเลิก']):
                result['intent'] = 'delete_goal'
                # Extract goal name
                name_match = re.search(r'(?:ลบ|ยกเลิก)(?:เป้าหมาย)?\s*(\S+)', message)
                if name_match:
                    result['entities']['goal_name'] = name_match.group(1)
            else:
                result['intent'] = 'get_goals'
        
        # Check for web link / profile
        elif any(x in message_lower for x in ['เว็บ', 'website', 'ลิงก์', 'link', 'profile', 'โปรไฟล์', 'dashboard', 'หน้าเว็บ']):
            result['intent'] = 'get_web_link'
        
        # Check for delete transaction FIRST (ลบรายการ, ลบรายการล่าสุด, ลบรายการที่ 1)
        elif any(x in message_lower for x in ['ลบรายการ']) and 'ประจำ' not in message_lower:
            result['intent'] = 'delete_transaction'
            
            # Check for "ล่าสุด" - delete latest
            if 'ล่าสุด' in message_lower:
                result['entities']['delete_latest'] = True
            
            # Check for number (ลบรายการที่ 1, ลบรายการ 2)
            num_match = re.search(r'ที่\s*(\d+)|รายการ\s*(\d+)', message)
            if num_match:
                result['entities']['index'] = int(num_match.group(1) or num_match.group(2))
            
            # Extract keyword after ลบรายการ (if not number)
            if 'delete_latest' not in result['entities'] and 'index' not in result['entities']:
                words = message.split()
                for i, w in enumerate(words):
                    if 'รายการ' in w and i + 1 < len(words):
                        next_word = words[i + 1]
                        if not next_word.isdigit() and next_word not in ['ที่', 'ล่าสุด', 'ทั้งหมด']:
                            result['entities']['keyword'] = next_word
                            break
        
        # Check for transactions list (ดูรายการ, แสดงรายการ, รายการเดือนนี้) - NO ลบ
        elif any(x in message_lower for x in ['แสดงรายการ', 'ดูรายการ', 'รายการทั้งหมด', 'รายการล่าสุด', 'รายการวันนี้', 'รายการเดือน', 'มีรายการอะไร', 'รายการการเงิน']) and 'ลบ' not in message_lower:
            result['intent'] = 'get_transactions'
            if 'วันนี้' in message_lower:
                result['entities']['period'] = 'today'
            elif 'สัปดาห์' in message_lower:
                result['entities']['period'] = 'this_week'
            else:
                result['entities']['period'] = 'this_month'
        
        # Check for contribute goal (เติมเงิน xxx บาท)
        elif any(x in message_lower for x in ['เติมเงิน', 'เพิ่มเงิน']) and re.search(r'\d+\s*บาท', message):
            result['intent'] = 'contribute_goal'
            # Extract goal name
            words = message.split()
            for i, w in enumerate(words):
                if any(kw in w for kw in ['เติมเงิน', 'เพิ่มเงิน']) and i + 1 < len(words):
                    result['entities']['goal_name'] = words[i + 1]
                    break
            # Extract amount
            amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
            if amount_match:
                result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
        
        # Check for transaction creation (มี บาท แต่ไม่ใช่คำถาม และไม่ใช่ออม/เติม)
        elif re.search(r'(\d+(?:,\d+)?)\s*บาท', message) and 'อะไร' not in message_lower and 'ออม' not in message_lower:
            result['intent'] = 'create_transaction'
            amount_match = re.search(r'(\d+(?:,\d+)?)\s*บาท', message)
            if amount_match:
                result['entities']['amount'] = float(amount_match.group(1).replace(',', ''))
            result['entities']['type'] = 'income' if any(x in message_lower for x in ['รับ', 'เงินเดือน', 'ได้']) else 'expense'
            # Extract note (words before บาท)
            note_match = re.match(r'^(.+?)\s*\d+', message)
            if note_match:
                result['entities']['note'] = note_match.group(1).strip()
        
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
