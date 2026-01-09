#!/usr/bin/env python3
"""
Test script for AI Financial Assistant Bot API
ทดสอบ Bot API endpoints ก่อน deploy
"""
import os
import sys
import hmac
import hashlib
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.project import Project, ProjectSettings
from app.models.category import Category


def create_test_data():
    """สร้าง test user, project และ categories"""
    
    # Check if test user exists
    test_user = User.query.filter_by(line_user_id='test-line-user-123').first()
    
    if not test_user:
        print("📝 Creating test user...")
        test_user = User(
            line_user_id='test-line-user-123',
            display_name='Test User (Bot)',
            email='test@example.com'
        )
        db.session.add(test_user)
        db.session.flush()
        
        # Create project
        print("📁 Creating test project...")
        project = Project(
            name='สมุดทดสอบ Bot',
            owner_user_id=test_user.id
        )
        db.session.add(project)
        db.session.flush()
        
        # Update user's current project
        test_user.current_project_id = project.id
        
        # Create project settings
        settings = ProjectSettings(
            project_id=project.id
        )
        settings.insight_enabled = True
        settings.insight_max_days = 30
        settings.insight_max_records = 100
        settings.insight_fields_level = 'minimal'
        db.session.add(settings)
        
        # Create default categories
        print("🏷️ Creating categories...")
        default_categories = [
            ('expense', 'อาหาร', 'food', '🍔', '#ef4444'),
            ('expense', 'เดินทาง', 'transport', '🚗', '#f59e0b'),
            ('expense', 'ช้อปปิ้ง', 'shopping', '🛍️', '#8b5cf6'),
            ('expense', 'บันเทิง', 'entertainment', '🎬', '#ec4899'),
            ('expense', 'สุขภาพ', 'health', '💊', '#10b981'),
            ('expense', 'บิล/ค่าใช้จ่าย', 'bills', '📄', '#6366f1'),
            ('income', 'เงินเดือน', 'salary', '💰', '#22c55e'),
            ('income', 'โบนัส', 'bonus', '🎁', '#eab308'),
            ('income', 'อื่นๆ', 'other_income', '📥', '#14b8a6'),
        ]
        
        for idx, (type, name_th, name_en, icon, color) in enumerate(default_categories):
            cat = Category(
                project_id=project.id,
                type=type,
                name_th=name_th,
                name_en=name_en,
                icon=icon,
                color=color,
                sort_order=idx
            )
            db.session.add(cat)
        
        db.session.commit()
        print("✅ Test data created successfully!")
        
    else:
        print("✅ Test user already exists")
        project = Project.query.get(test_user.current_project_id)
    
    return test_user, project


def test_context_resolve(app, test_user):
    """ทดสอบ /api/v1/bot/context/resolve"""
    print("\n" + "="*50)
    print("📋 Testing: /api/v1/bot/context/resolve")
    print("="*50)
    
    with app.test_client() as client:
        # Generate HMAC signature
        bot_id = app.config.get('BOTPRESS_BOT_ID', 'botpress-prod')
        bot_secret = app.config.get('BOT_HMAC_SECRET', 'test-secret')
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        payload = {'line_user_id': test_user.line_user_id}
        body = json.dumps(payload)
        
        message = f"{bot_id}:{timestamp}:{body}"
        signature = hmac.new(
            bot_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-BOT-ID': bot_id,
            'X-BOT-TS': timestamp,
            'X-BOT-HMAC': signature
        }
        
        response = client.post(
            '/api/v1/bot/context/resolve',
            data=body,
            headers=headers,
            content_type='application/json'
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json, indent=2, ensure_ascii=False)}")
        
        return response.status_code == 200


def test_create_transaction(app, test_user, category_id):
    """ทดสอบ /api/v1/bot/transactions/create"""
    print("\n" + "="*50)
    print("💰 Testing: /api/v1/bot/transactions/create")
    print("="*50)
    
    with app.test_client() as client:
        # Generate HMAC signature
        bot_id = app.config.get('BOTPRESS_BOT_ID', 'botpress-prod')
        bot_secret = app.config.get('BOT_HMAC_SECRET', 'test-secret')
        timestamp = str(int(datetime.utcnow().timestamp()))
        event_id = f"test-event-{datetime.utcnow().timestamp()}"
        
        payload = {
            'line_user_id': test_user.line_user_id,
            'type': 'expense',
            'category_id': category_id,
            'amount': 350,
            'note': 'กินข้าวกับเพื่อน (ทดสอบ Bot)',
            'event_id': event_id
        }
        body = json.dumps(payload)
        
        message = f"{bot_id}:{timestamp}:{body}"
        signature = hmac.new(
            bot_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-BOT-ID': bot_id,
            'X-BOT-TS': timestamp,
            'X-BOT-HMAC': signature,
            'X-Idempotency-Key': event_id
        }
        
        response = client.post(
            '/api/v1/bot/transactions/create',
            data=body,
            headers=headers,
            content_type='application/json'
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json, indent=2, ensure_ascii=False)}")
        
        return response.status_code == 201


def test_insights_export(app, test_user):
    """ทดสอบ /api/v1/bot/insights/export"""
    print("\n" + "="*50)
    print("📊 Testing: /api/v1/bot/insights/export")
    print("="*50)
    
    with app.test_client() as client:
        # Generate HMAC signature
        bot_id = app.config.get('BOTPRESS_BOT_ID', 'botpress-prod')
        bot_secret = app.config.get('BOT_HMAC_SECRET', 'test-secret')
        timestamp = str(int(datetime.utcnow().timestamp()))
        event_id = f"test-insight-{datetime.utcnow().timestamp()}"
        
        payload = {
            'line_user_id': test_user.line_user_id,
            'max_days': 30,
            'fields_level': 'standard',
            'event_id': event_id
        }
        body = json.dumps(payload)
        
        message = f"{bot_id}:{timestamp}:{body}"
        signature = hmac.new(
            bot_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-BOT-ID': bot_id,
            'X-BOT-TS': timestamp,
            'X-BOT-HMAC': signature,
            'X-Idempotency-Key': event_id
        }
        
        response = client.post(
            '/api/v1/bot/insights/export',
            data=body,
            headers=headers,
            content_type='application/json'
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json, indent=2, ensure_ascii=False)}")
        
        return response.status_code == 200


def main():
    print("🚀 AI Financial Assistant Bot API Test")
    print("="*50)
    
    app = create_app()
    
    with app.app_context():
        # Create test data
        test_user, project = create_test_data()
        
        # Get food category
        food_category = Category.query.filter_by(
            project_id=project.id,
            name_en='food'
        ).first()
        
        if not food_category:
            print("❌ Food category not found!")
            return
        
        print(f"\n📌 Test User: {test_user.display_name}")
        print(f"📌 LINE ID: {test_user.line_user_id}")
        print(f"📌 Project: {project.name}")
        print(f"📌 Food Category ID: {food_category.id}")
        
        # Run tests
        results = []
        
        # Test 1: Context Resolve
        results.append(('Context Resolve', test_context_resolve(app, test_user)))
        
        # Test 2: Create Transaction
        results.append(('Create Transaction', test_create_transaction(app, test_user, food_category.id)))
        
        # Test 3: Insights Export
        results.append(('Insights Export', test_insights_export(app, test_user)))
        
        # Summary
        print("\n" + "="*50)
        print("📋 Test Results Summary")
        print("="*50)
        for name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {name}: {status}")
        
        all_passed = all(r[1] for r in results)
        print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️ Some tests failed"))


if __name__ == '__main__':
    main()
