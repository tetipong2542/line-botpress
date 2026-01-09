#!/usr/bin/env python3
"""
Diagnostic script for LINE Bot Integration
วิเคราะห์ปัญหา LINE Bot ไม่ตอบกลับ
"""
import os
import sys
import requests

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def check_config():
    """ตรวจสอบ configuration"""
    app = create_app()
    
    print("🔍 Checking LINE Bot Configuration...")
    print("=" * 50)
    
    issues = []
    
    # Check LINE credentials
    line_channel_id = app.config.get('LINE_CHANNEL_ID', '')
    line_channel_secret = app.config.get('LINE_CHANNEL_SECRET', '')
    line_access_token = app.config.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    
    print("\n📱 LINE Configuration:")
    if line_channel_id:
        print(f"  ✅ LINE_CHANNEL_ID: {line_channel_id[:8]}... (set)")
    else:
        print(f"  ❌ LINE_CHANNEL_ID: NOT SET")
        issues.append("LINE_CHANNEL_ID is missing")
    
    if line_channel_secret:
        print(f"  ✅ LINE_CHANNEL_SECRET: {line_channel_secret[:8]}... (set)")
    else:
        print(f"  ❌ LINE_CHANNEL_SECRET: NOT SET")
        issues.append("LINE_CHANNEL_SECRET is missing")
    
    if line_access_token:
        print(f"  ✅ LINE_CHANNEL_ACCESS_TOKEN: {line_access_token[:15]}... (set)")
    else:
        print(f"  ❌ LINE_CHANNEL_ACCESS_TOKEN: NOT SET")
        issues.append("LINE_CHANNEL_ACCESS_TOKEN is missing")
    
    # Check Botpress credentials
    botpress_webhook = app.config.get('BOTPRESS_WEBHOOK_URL', '')
    botpress_secret = app.config.get('BOTPRESS_BOT_SECRET', '')
    
    print("\n🤖 Botpress Configuration:")
    if botpress_webhook:
        print(f"  ✅ BOTPRESS_WEBHOOK_URL: {botpress_webhook}")
    else:
        print(f"  ❌ BOTPRESS_WEBHOOK_URL: NOT SET")
        issues.append("BOTPRESS_WEBHOOK_URL is missing")
    
    if botpress_secret:
        print(f"  ✅ BOTPRESS_BOT_SECRET: {botpress_secret[:8]}... (set)")
    else:
        print(f"  ⚠️ BOTPRESS_BOT_SECRET: NOT SET (may be optional)")
    
    # Check BOT_HMAC_SECRET
    hmac_secret = app.config.get('BOT_HMAC_SECRET', '')
    print("\n🔐 Security Configuration:")
    if hmac_secret and hmac_secret != 'change-this-secret-minimum-32-characters':
        print(f"  ✅ BOT_HMAC_SECRET: {hmac_secret[:8]}... (set)")
    else:
        print(f"  ⚠️ BOT_HMAC_SECRET: Using default (should change in production)")
    
    # Test Botpress webhook
    print("\n🌐 Testing Botpress Webhook Connection:")
    if botpress_webhook:
        try:
            response = requests.post(
                botpress_webhook,
                json={
                    'type': 'text',
                    'text': 'ping test',
                    'userId': 'test-diagnostic',
                    'channel': 'line'
                },
                timeout=10
            )
            print(f"  Status Code: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ Botpress webhook is reachable")
            else:
                print(f"  ⚠️ Botpress returned non-200: {response.text[:200]}")
        except requests.exceptions.Timeout:
            print(f"  ❌ Botpress webhook timeout")
            issues.append("Botpress webhook is not responding")
        except Exception as e:
            print(f"  ❌ Botpress webhook error: {str(e)}")
            issues.append(f"Botpress webhook error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 50)
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ All basic configurations look OK!")
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS TO DEBUG:")
    print("=" * 50)
    print("""
1. ตรวจสอบว่า Flask server รันอยู่หรือไม่:
   - ต้องรัน: flask run หรือ python -m flask run
   - Server ต้อง deploy บน public URL (ไม่ใช่ localhost)

2. ตรวจสอบ LINE Webhook URL:
   - ไปที่ LINE Developers Console
   - ดูว่า Webhook URL ชี้ไปที่ไหน
   - ต้องเป็น: https://your-domain.com/line/webhook

3. ตรวจสอบว่า Webhook verify passed หรือไม่:
   - กด "Verify" ใน LINE Developers Console
   - ถ้า fail = URL ไม่ถูกต้อง หรือ server ไม่รัน

4. ดู logs เมื่อส่งข้อความ:
   - Flask ต้องแสดง log เมื่อได้รับข้อความจาก LINE
""")
    
    return len(issues) == 0


if __name__ == '__main__':
    check_config()
