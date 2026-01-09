"""
Botpress integration routes - Bot API endpoints with HMAC security
"""
from flask import Blueprint, request, jsonify, g, current_app
from app import db
from app.models.user import User
from app.models.project import Project, ProjectSettings
from app.services.transaction_service import TransactionService
from app.utils.security import require_bot_auth, store_idempotency_response
from app.models.transaction import Transaction
from app.models.budget import Budget
from datetime import datetime, timedelta
import json

bp = Blueprint('bot', __name__, url_prefix='/api/v1/bot')


@bp.route('/context/resolve', methods=['POST'])
@require_bot_auth()
def resolve_context():
    """
    Resolve user context (user + project + policy)
    Used by Botpress to get user information before operations
    """
    data = request.json
    line_user_id = data.get('line_user_id')
    botpress_user_id = data.get('botpress_user_id')

    if not line_user_id and not botpress_user_id:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'line_user_id or botpress_user_id is required'
            }
        }), 400

    # Try to find user by multiple methods
    user = None
    if line_user_id:
        user = User.query.filter_by(line_user_id=line_user_id).first()
    if not user and botpress_user_id:
        user = User.query.filter_by(botpress_user_id=botpress_user_id).first()

    if not user:
        return jsonify({
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found. Please login via web first.'
            }
        }), 404

    # Get current project
    project_id = user.current_project_id
    project = None
    settings = None

    if project_id:
        project = Project.query.get(project_id)
        if project:
            settings = ProjectSettings.query.filter_by(project_id=project_id).first()

    return jsonify({
        'user': user.to_dict(),
        'current_project': project.to_dict() if project else None,
        'settings': settings.to_dict() if settings else None
    })


@bp.route('/link', methods=['POST'])
@require_bot_auth()
def link_botpress_account():
    """
    Link Botpress user ID to LINE user ID
    Supports: link_code from web profile page
    """
    from flask import current_app
    import time
    
    data = request.json
    botpress_user_id = data.get('botpress_user_id')
    link_code = data.get('link_code')  # 6-digit code from web

    if not botpress_user_id:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'botpress_user_id is required'
            }
        }), 400

    # Check if botpress_user_id already linked
    existing = User.query.filter_by(botpress_user_id=botpress_user_id).first()
    if existing:
        return jsonify({
            'success': True,
            'message': f'บัญชีเชื่อมต่อแล้ว! สวัสดี {existing.display_name}',
            'user': existing.to_dict()
        })

    # If link_code provided, verify and link
    if link_code:
        # Get link code from app config/cache
        link_codes = getattr(current_app, '_link_codes', {})
        code_data = link_codes.get(link_code.upper())
        
        if code_data:
            # Check expiry (5 minutes)
            if time.time() - code_data['created_at'] < 300:
                user = User.query.get(code_data['user_id'])
                if user:
                    user.botpress_user_id = botpress_user_id
                    
                    # Ensure user has a project and current_project_id
                    from app.routes.web import get_user_project
                    project = get_user_project(user.id)
                    
                    db.session.commit()
                    
                    # Remove used code
                    del link_codes[link_code.upper()]
                    
                    return jsonify({
                        'success': True,
                        'message': f'🎉 เชื่อมต่อบัญชีสำเร็จ! สวัสดี {user.display_name} สามารถบันทึกรายรับรายจ่ายได้แล้วครับ',
                        'user': user.to_dict()
                    })
            else:
                # Code expired
                del link_codes[link_code.upper()]
                return jsonify({
                    'success': False,
                    'message': 'รหัสหมดอายุแล้ว กรุณาสร้างรหัสใหม่ที่หน้าเว็บ'
                })
        else:
            return jsonify({
                'success': False,
                'message': 'รหัสไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง'
            })

    # No link_code - provide instructions
    return jsonify({
        'success': False,
        'message': 'กรุณา:\n1. เข้าเว็บ https://line-botpress-production.up.railway.app\n2. ล็อกอินด้วย LINE\n3. ไปหน้าโปรไฟล์ กดปุ่ม "สร้างรหัสเชื่อมต่อ"\n4. พิมพ์ "เชื่อมต่อ [รหัส 6 ตัว]" ในแชทนี้',
        'link_url': 'https://line-botpress-production.up.railway.app/profile'
    })



@bp.route('/transactions/create', methods=['POST'])
@require_bot_auth(require_idempotency=True)
def create_transaction():
    """
    Create transaction via bot (with idempotency)
    Supports both category_id and category_name
    Supports botpress_user_id with auto-mapping to LINE user
    """
    from app.models.category import Category
    
    data = request.json

    line_user_id = data.get('line_user_id')  # Can be LINE ID or Botpress ID
    type = data.get('type')
    category_id = data.get('category_id')
    category_name = data.get('category_name')  # Support category name
    amount = data.get('amount')
    note = data.get('note')
    occurred_at = data.get('occurred_at')

    # Find user - try multiple methods
    user = None
    
    # Method 1: Try as LINE user ID first
    if line_user_id:
        user = User.query.filter_by(line_user_id=line_user_id).first()
    
    # Method 2: Try as Botpress user ID
    if not user and line_user_id:
        user = User.query.filter_by(botpress_user_id=line_user_id).first()
    
    # Method 3: If user found by LINE ID but no botpress mapping, auto-update
    # (This handles future cases where we know the LINE ID)

    if not user or not user.current_project_id:
        # Provide helpful error message with link instructions
        return jsonify({
            'error': {
                'code': 'USER_NO_PROJECT',
                'message': 'ยังไม่ได้เชื่อมต่อบัญชี กรุณาเข้าเว็บแล้วพิมพ์ "เชื่อมต่อ" หรือ "link" ในแชทนี้'
            }
        }), 400

    # Auto-lookup category if category_name is provided
    if not category_id and category_name:
        # Map common names to English names
        name_mapping = {
            'อาหาร': 'food', 'food': 'food', 'กินข้าว': 'food',
            'เดินทาง': 'transport', 'transport': 'transport',
            'ช้อปปิ้ง': 'shopping', 'shopping': 'shopping',
            'บันเทิง': 'entertainment', 'entertainment': 'entertainment',
            'สุขภาพ': 'health', 'health': 'health',
            'บิล': 'bills', 'bills': 'bills', 'ค่าใช้จ่าย': 'bills',
            'เงินเดือน': 'salary', 'salary': 'salary',
            'โบนัส': 'bonus', 'bonus': 'bonus',
            'อื่นๆ': 'other_income', 'other': 'other_income'
        }
        
        lookup_name = name_mapping.get(category_name.lower(), category_name.lower())
        
        # Find category by name_en or name_th
        category = Category.query.filter(
            Category.project_id == user.current_project_id,
            (Category.name_en == lookup_name) | (Category.name_th == category_name)
        ).first()
        
        if category:
            category_id = category.id
        else:
            # Use default category based on type
            default_cat = Category.query.filter(
                Category.project_id == user.current_project_id,
                Category.type == type
            ).first()
            if default_cat:
                category_id = default_cat.id

    # Validate required fields
    if not all([line_user_id, type, amount]):
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Missing required fields: line_user_id, type, amount'
            }
        }), 400
    
    if not category_id:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'No valid category found. Please provide category_id or category_name'
            }
        }), 400

    try:
        # Create transaction
        transaction = TransactionService.create_transaction(
            project_id=user.current_project_id,
            user_id=user.id,
            type=type,
            category_id=category_id,
            amount=amount,
            occurred_at=occurred_at,
            note=note
        )

        # Check budget if expense
        budget_status = None
        if type == 'expense':
            budget_status = _check_budget_status(
                user.current_project_id,
                category_id,
                transaction.occurred_at
            )

        response = {
            'success': True,
            'transaction': transaction.to_dict(include_category=True),
            'budget_status': budget_status
        }

        # Store idempotency response
        if hasattr(g, 'event_id'):
            store_idempotency_response(
                g.event_id,
                request.path,
                201,
                json.dumps(response)
            )

        return jsonify(response), 201

    except (ValueError, PermissionError) as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


@bp.route('/insights/export', methods=['POST'])
@require_bot_auth(require_idempotency=True)
def export_insights_dataset():
    """
    Export limited transaction dataset for Botpress insights (Mode B)
    """
    data = request.json

    line_user_id = data.get('line_user_id')
    max_days = data.get('max_days', 30)
    fields_level = data.get('fields_level', 'minimal')

    # Find user
    user = User.query.filter_by(line_user_id=line_user_id).first()

    if not user or not user.current_project_id:
        return jsonify({
            'error': {
                'code': 'USER_NO_PROJECT',
                'message': 'User has no active project'
            }
        }), 400

    # Get project settings
    settings = ProjectSettings.query.filter_by(project_id=user.current_project_id).first()

    if not settings or not settings.insight_enabled:
        return jsonify({
            'error': {
                'code': 'INSIGHTS_DISABLED',
                'message': 'Insights are disabled for this project'
            }
        }), 403

    # Enforce limits
    max_days = min(max_days, settings.insight_max_days)
    max_records = settings.insight_max_records

    # Query transactions
    from_date = datetime.utcnow() - timedelta(days=max_days)

    transactions = Transaction.query.filter(
        Transaction.project_id == user.current_project_id,
        Transaction.occurred_at >= from_date,
        Transaction.deleted_at.is_(None)
    ).order_by(Transaction.occurred_at.desc()).limit(max_records).all()

    # Build dataset based on fields_level
    dataset = []
    for txn in transactions:
        item = {
            'type': txn.type,
            'category_id': txn.category_id,
            'amount': txn.amount,
            'occurred_at': txn.occurred_at.isoformat()
        }

        if fields_level in ['standard', 'full']:
            item['category_name'] = txn.category.name_th if txn.category else None

        if fields_level == 'full':
            item['note'] = txn.note

        dataset.append(item)

    response = {
        'dataset': dataset,
        'metadata': {
            'count': len(dataset),
            'from_date': from_date.isoformat(),
            'fields_level': fields_level,
            'project_id': user.current_project_id
        }
    }

    # Store idempotency response
    if hasattr(g, 'event_id'):
        store_idempotency_response(
            g.event_id,
            request.path,
            200,
            json.dumps(response)
        )

    return jsonify(response)


def _check_budget_status(project_id, category_id, occurred_at):
    """Check budget status for category in month"""
    month = occurred_at.strftime('%Y-%m')

    budget = Budget.query.filter_by(
        project_id=project_id,
        category_id=category_id,
        month_yyyymm=month
    ).first()

    if not budget:
        return None

    # Calculate spent amount this month
    month_start = datetime(occurred_at.year, occurred_at.month, 1)
    if occurred_at.month == 12:
        month_end = datetime(occurred_at.year + 1, 1, 1)
    else:
        month_end = datetime(occurred_at.year, occurred_at.month + 1, 1)

    spent = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.project_id == project_id,
        Transaction.category_id == category_id,
        Transaction.type == 'expense',
        Transaction.occurred_at >= month_start,
        Transaction.occurred_at < month_end,
        Transaction.deleted_at.is_(None)
    ).scalar() or 0

    remaining = budget.limit_amount - spent
    percentage = (spent / budget.limit_amount * 100) if budget.limit_amount > 0 else 0

    return {
        'limit': budget.limit_amount,
        'spent': spent,
        'remaining': remaining,
        'percentage': round(percentage, 2),
        'is_over_budget': remaining < 0
    }


@bp.route('/summary', methods=['POST'])
@require_bot_auth()
def get_summary():
    """
    Get transaction summary for user
    Used by Botpress getSummary action
    
    Supports periods: today, this_week, this_month, last_month, custom
    """
    from app.models.category import Category
    from datetime import date
    
    data = request.json
    botpress_user_id = data.get('botpress_user_id') or data.get('line_user_id')
    period = data.get('period', 'this_month')  # today, this_week, this_month, last_month
    
    if not botpress_user_id:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'botpress_user_id is required'
            }
        }), 400
    
    # Find user
    user = User.query.filter_by(botpress_user_id=botpress_user_id).first()
    if not user:
        user = User.query.filter_by(line_user_id=botpress_user_id).first()
    
    if not user or not user.current_project_id:
        return jsonify({
            'success': False,
            'message': 'ยังไม่ได้เชื่อมต่อบัญชี กรุณาพิมพ์ "เชื่อมต่อ" เพื่อลงทะเบียน'
        }), 400
    
    # Calculate date range based on period
    today = date.today()
    
    if period == 'today':
        start_date = datetime(today.year, today.month, today.day)
        end_date = start_date + timedelta(days=1)
        period_name = 'วันนี้'
    elif period == 'this_week':
        start_date = datetime(today.year, today.month, today.day) - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
        period_name = 'สัปดาห์นี้'
    elif period == 'this_month':
        start_date = datetime(today.year, today.month, 1)
        if today.month == 12:
            end_date = datetime(today.year + 1, 1, 1)
        else:
            end_date = datetime(today.year, today.month + 1, 1)
        period_name = 'เดือนนี้'
    elif period == 'last_month':
        if today.month == 1:
            start_date = datetime(today.year - 1, 12, 1)
            end_date = datetime(today.year, 1, 1)
        else:
            start_date = datetime(today.year, today.month - 1, 1)
            end_date = datetime(today.year, today.month, 1)
        period_name = 'เดือนที่แล้ว'
    else:
        # Default to this month
        start_date = datetime(today.year, today.month, 1)
        if today.month == 12:
            end_date = datetime(today.year + 1, 1, 1)
        else:
            end_date = datetime(today.year, today.month + 1, 1)
        period_name = 'เดือนนี้'
    
    project_id = user.current_project_id
    
    # Get income summary
    income_total = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.project_id == project_id,
        Transaction.type == 'income',
        Transaction.occurred_at >= start_date,
        Transaction.occurred_at < end_date,
        Transaction.deleted_at.is_(None)
    ).scalar() or 0
    
    # Get expense summary
    expense_total = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.project_id == project_id,
        Transaction.type == 'expense',
        Transaction.occurred_at >= start_date,
        Transaction.occurred_at < end_date,
        Transaction.deleted_at.is_(None)
    ).scalar() or 0
    
    # Get top expense categories
    top_categories = db.session.query(
        Category.name_th,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction, Transaction.category_id == Category.id).filter(
        Transaction.project_id == project_id,
        Transaction.type == 'expense',
        Transaction.occurred_at >= start_date,
        Transaction.occurred_at < end_date,
        Transaction.deleted_at.is_(None)
    ).group_by(Category.id).order_by(db.desc('total')).limit(5).all()
    
    # Get transaction count
    transaction_count = Transaction.query.filter(
        Transaction.project_id == project_id,
        Transaction.occurred_at >= start_date,
        Transaction.occurred_at < end_date,
        Transaction.deleted_at.is_(None)
    ).count()
    
    # Convert satang to baht
    income_baht = income_total / 100
    expense_baht = expense_total / 100
    balance_baht = income_baht - expense_baht
    
    # Format top categories
    top_categories_formatted = []
    for cat_name, cat_total in top_categories:
        top_categories_formatted.append({
            'name': cat_name,
            'amount': cat_total / 100
        })
    
    # Build human-readable message
    message_lines = [
        f"📊 สรุป{period_name}:",
        f"",
        f"💰 รายรับ: {income_baht:,.2f} บาท",
        f"💸 รายจ่าย: {expense_baht:,.2f} บาท",
        f"📈 คงเหลือ: {balance_baht:,.2f} บาท",
        f"📝 จำนวนรายการ: {transaction_count} รายการ"
    ]
    
    if top_categories_formatted:
        message_lines.append(f"")
        message_lines.append(f"🏆 หมวดหมู่ที่ใช้จ่ายมากที่สุด:")
        for i, cat in enumerate(top_categories_formatted[:3], 1):
            message_lines.append(f"   {i}. {cat['name']}: {cat['amount']:,.2f} บาท")
    
    return jsonify({
        'success': True,
        'period': period,
        'period_name': period_name,
        'income': income_baht,
        'expense': expense_baht,
        'balance': balance_baht,
        'transaction_count': transaction_count,
        'top_categories': top_categories_formatted,
        'message': '\n'.join(message_lines)
    })


@bp.route('/query', methods=['POST'])
@require_bot_auth()
def universal_query():
    """
    Universal Query endpoint - One endpoint for all data queries
    Used by Botpress queryData action
    
    Supports query_types:
    - summary: Transaction summary (same as /summary)
    - transactions: List recent transactions
    - categories: List user's categories
    - budgets: Budget status
    """
    from app.models.category import Category
    from datetime import date
    
    data = request.json
    botpress_user_id = data.get('botpress_user_id') or data.get('line_user_id')
    query_type = data.get('query_type', 'summary')
    params = data.get('params', {})
    
    if not botpress_user_id:
        return jsonify({
            'success': False,
            'message': 'botpress_user_id is required'
        }), 400
    
    # Find user
    user = User.query.filter_by(botpress_user_id=botpress_user_id).first()
    if not user:
        user = User.query.filter_by(line_user_id=botpress_user_id).first()
    
    if not user or not user.current_project_id:
        return jsonify({
            'success': False,
            'message': 'ยังไม่ได้เชื่อมต่อบัญชี กรุณาพิมพ์ "เชื่อมต่อ" เพื่อลงทะเบียน'
        }), 400
    
    project_id = user.current_project_id
    today = date.today()
    
    # ============================================
    # QUERY TYPE: transactions
    # ============================================
    if query_type == 'transactions':
        limit = params.get('limit', 10)
        trans_type = params.get('type')  # 'income' or 'expense' or None
        
        query = Transaction.query.filter(
            Transaction.project_id == project_id,
            Transaction.deleted_at.is_(None)
        )
        
        if trans_type:
            query = query.filter(Transaction.type == trans_type)
        
        transactions = query.order_by(Transaction.occurred_at.desc()).limit(limit).all()
        
        if not transactions:
            return jsonify({
                'success': True,
                'message': '📝 ยังไม่มีรายการ\n\nลองเพิ่มรายการโดยพิมพ์ เช่น "กินข้าว 350"'
            })
        
        lines = [f"📝 รายการล่าสุด ({len(transactions)} รายการ):", ""]
        
        for t in transactions:
            cat = Category.query.get(t.category_id)
            cat_name = cat.name_th if cat else "ไม่ระบุ"
            amount = t.amount / 100
            icon = "💸" if t.type == 'expense' else "💰"
            date_str = t.occurred_at.strftime("%d/%m") if t.occurred_at else ""
            note = f" - {t.note}" if t.note else ""
            lines.append(f"{icon} {cat_name}: {amount:,.2f}฿ ({date_str}){note}")
        
        return jsonify({
            'success': True,
            'count': len(transactions),
            'message': '\n'.join(lines)
        })
    
    # ============================================
    # QUERY TYPE: categories
    # ============================================
    elif query_type == 'categories':
        cat_type = params.get('type')  # 'income' or 'expense' or None
        
        query = Category.query.filter(
            Category.project_id == project_id,
            Category.is_active == True
        )
        
        if cat_type:
            query = query.filter(Category.type == cat_type)
        
        categories = query.order_by(Category.sort_order).all()
        
        expense_cats = [c for c in categories if c.type == 'expense']
        income_cats = [c for c in categories if c.type == 'income']
        
        lines = ["📂 หมวดหมู่ของคุณ:", ""]
        
        if expense_cats:
            lines.append("💸 รายจ่าย:")
            for c in expense_cats:
                lines.append(f"   • {c.name_th}")
        
        if income_cats:
            lines.append("")
            lines.append("💰 รายรับ:")
            for c in income_cats:
                lines.append(f"   • {c.name_th}")
        
        return jsonify({
            'success': True,
            'expense_count': len(expense_cats),
            'income_count': len(income_cats),
            'message': '\n'.join(lines)
        })
    
    # ============================================
    # QUERY TYPE: budgets
    # ============================================
    elif query_type == 'budgets':
        month = params.get('month', today.strftime('%Y-%m'))
        
        budgets = Budget.query.filter_by(
            project_id=project_id,
            month_yyyymm=month
        ).all()
        
        if not budgets:
            return jsonify({
                'success': True,
                'message': '📊 ยังไม่ได้ตั้งงบประมาณ\n\nสามารถตั้งงบได้ที่เว็บ https://line-botpress-production.up.railway.app/budgets'
            })
        
        lines = [f"📊 งบประมาณ {month}:", ""]
        
        for b in budgets:
            cat = Category.query.get(b.category_id)
            cat_name = cat.name_th if cat else "ไม่ระบุ"
            limit_baht = b.limit_amount / 100
            
            # Calculate spent
            month_start = datetime(today.year, int(month.split('-')[1]), 1)
            spent = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.project_id == project_id,
                Transaction.category_id == b.category_id,
                Transaction.type == 'expense',
                Transaction.occurred_at >= month_start,
                Transaction.deleted_at.is_(None)
            ).scalar() or 0
            
            spent_baht = spent / 100
            remaining = limit_baht - spent_baht
            percent = (spent_baht / limit_baht * 100) if limit_baht > 0 else 0
            
            status = "✅" if remaining >= 0 else "❌"
            lines.append(f"{status} {cat_name}: {spent_baht:,.0f}/{limit_baht:,.0f}฿ ({percent:.0f}%)")
        
        return jsonify({
            'success': True,
            'budget_count': len(budgets),
            'message': '\n'.join(lines)
        })
    
    # ============================================
    # QUERY TYPE: goals (Savings Goals)
    # ============================================
    elif query_type == 'goals':
        from app.models.savings_goal import SavingsGoal
        
        goals = SavingsGoal.get_active_goals(project_id)
        
        if not goals:
            return jsonify({
                'success': True,
                'message': '🎯 ยังไม่มีเป้าหมายออมเงิน\n\nพิมพ์ "ตั้งเป้าออม [ชื่อ] [จำนวน] บาทใน [เดือน] เดือน"'
            })
        
        lines = ["🎯 เป้าหมายออมเงินของคุณ:", ""]
        total_progress = 0
        
        for goal in goals:
            current = goal.current_amount / 100
            target = goal.target_amount / 100
            progress = goal.progress_percentage
            total_progress += progress
            
            status = "✅" if goal.is_completed else ("⚠️" if goal.is_overdue else "🔄")
            
            lines.append(f"{status} {goal.name}")
            lines.append(f"   💰 {current:,.0f}/{target:,.0f}฿ ({progress:.0f}%)")
            
            if goal.days_remaining is not None and not goal.is_completed:
                # Calculate daily required
                remaining = target - current
                if goal.days_remaining > 0:
                    daily = remaining / goal.days_remaining
                    lines.append(f"   📅 เหลือ {goal.days_remaining} วัน (ต้องออมวันละ {daily:,.0f}฿)")
            lines.append("")
        
        avg_progress = total_progress / len(goals) if goals else 0
        lines.append(f"📊 ค่าเฉลี่ยความคืบหน้า: {avg_progress:.0f}%")
        
        return jsonify({
            'success': True,
            'goals_count': len(goals),
            'message': '\n'.join(lines)
        })
    
    # ============================================
    # QUERY TYPE: recurring
    # ============================================
    elif query_type == 'recurring':
        from app.models.recurring import RecurringRule
        
        recurring_rules = RecurringRule.query.filter(
            RecurringRule.project_id == project_id,
            RecurringRule.is_active == True
        ).order_by(RecurringRule.next_run_date).all()
        
        if not recurring_rules:
            return jsonify({
                'success': True,
                'message': '🔄 ยังไม่มีรายการประจำ\n\nพิมพ์ "เพิ่มรายการประจำ [ชื่อ] [จำนวน] บาททุกวันที่ [วัน]"'
            })
        
        lines = ["🔄 รายการประจำของคุณ:", ""]
        
        income_total = 0
        expense_total = 0
        
        for rule in recurring_rules:
            amount = rule.amount / 100
            icon = "💰" if rule.type == 'income' else "💸"
            cat_name = rule.category.name_th if rule.category else "ไม่ระบุ"
            
            if rule.type == 'income':
                income_total += amount
            else:
                expense_total += amount
            
            freq_text = {
                'daily': 'รายวัน',
                'weekly': 'รายสัปดาห์',
                'monthly': f'วันที่ {rule.day_of_month}'
            }.get(rule.freq, rule.freq)
            
            lines.append(f"{icon} {cat_name}: {amount:,.0f}฿ ({freq_text})")
            if rule.note:
                lines.append(f"   📝 {rule.note}")
        
        lines.append("")
        lines.append(f"📊 รวม: +{income_total:,.0f}฿ | -{expense_total:,.0f}฿/เดือน")
        
        return jsonify({
            'success': True,
            'count': len(recurring_rules),
            'message': '\n'.join(lines)
        })
    
    # ============================================
    # QUERY TYPE: summary (default)
    # ============================================
    else:
        # Use the same logic as /summary endpoint
        period = params.get('period', 'this_month')
        
        if period == 'today':
            start_date = datetime(today.year, today.month, today.day)
            end_date = start_date + timedelta(days=1)
            period_name = 'วันนี้'
        elif period == 'this_week':
            start_date = datetime(today.year, today.month, today.day) - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=7)
            period_name = 'สัปดาห์นี้'
        elif period == 'this_month':
            start_date = datetime(today.year, today.month, 1)
            end_date = datetime(today.year + 1, 1, 1) if today.month == 12 else datetime(today.year, today.month + 1, 1)
            period_name = 'เดือนนี้'
        elif period == 'last_month':
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1)
                end_date = datetime(today.year, 1, 1)
            else:
                start_date = datetime(today.year, today.month - 1, 1)
                end_date = datetime(today.year, today.month, 1)
            period_name = 'เดือนที่แล้ว'
        else:
            start_date = datetime(today.year, today.month, 1)
            end_date = datetime(today.year + 1, 1, 1) if today.month == 12 else datetime(today.year, today.month + 1, 1)
            period_name = 'เดือนนี้'
        
        income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'income',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0
        
        expense = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.project_id == project_id,
            Transaction.type == 'expense',
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).scalar() or 0
        
        count = Transaction.query.filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
            Transaction.deleted_at.is_(None)
        ).count()
        
        income_baht = income / 100
        expense_baht = expense / 100
        balance = income_baht - expense_baht
        
        lines = [
            f"📊 สรุป{period_name}:",
            "",
            f"💰 รายรับ: {income_baht:,.2f} บาท",
            f"💸 รายจ่าย: {expense_baht:,.2f} บาท",
            f"📈 คงเหลือ: {balance:,.2f} บาท",
            f"📝 จำนวนรายการ: {count} รายการ"
        ]
        
        return jsonify({
            'success': True,
            'income': income_baht,
            'expense': expense_baht,
            'balance': balance,
            'transaction_count': count,
            'message': '\n'.join(lines)
        })


@bp.route('/action', methods=['POST'])
@require_bot_auth()
def universal_action():
    """
    Universal Action endpoint - One endpoint for all data mutations
    Used by Botpress actionData action
    
    Supports action_types:
    - update_transaction: Update a transaction
    - delete_transaction: Delete a transaction
    - create_category: Create a new category
    - delete_category: Delete a category
    """
    from app.models.category import Category
    from app.utils.helpers import generate_id
    
    data = request.json
    botpress_user_id = data.get('botpress_user_id') or data.get('line_user_id')
    action_type = data.get('action_type')
    params = data.get('params', {})
    
    if not botpress_user_id:
        return jsonify({
            'success': False,
            'message': 'botpress_user_id is required'
        }), 400
    
    if not action_type:
        return jsonify({
            'success': False,
            'message': 'action_type is required'
        }), 400
    
    # Find user
    user = User.query.filter_by(botpress_user_id=botpress_user_id).first()
    if not user:
        user = User.query.filter_by(line_user_id=botpress_user_id).first()
    
    if not user or not user.current_project_id:
        return jsonify({
            'success': False,
            'message': 'ยังไม่ได้เชื่อมต่อบัญชี กรุณาพิมพ์ "เชื่อมต่อ" เพื่อลงทะเบียน'
        }), 400
    
    project_id = user.current_project_id
    
    # ============================================
    # ACTION: update_transaction
    # ============================================
    if action_type == 'update_transaction':
        transaction_id = params.get('transaction_id')
        
        if not transaction_id:
            # Try to find by description (last N transactions)
            keyword = params.get('keyword')
            if keyword:
                transactions = Transaction.query.filter(
                    Transaction.project_id == project_id,
                    Transaction.note.ilike(f'%{keyword}%'),
                    Transaction.deleted_at.is_(None)
                ).order_by(Transaction.occurred_at.desc()).limit(5).all()
                
                if not transactions:
                    return jsonify({
                        'success': False,
                        'message': f'ไม่พบรายการที่มี "{keyword}"'
                    })
                
                if len(transactions) > 1:
                    lines = ["พบหลายรายการ กรุณาระบุให้ชัดเจน:", ""]
                    for i, t in enumerate(transactions, 1):
                        cat = Category.query.get(t.category_id)
                        cat_name = cat.name_th if cat else "ไม่ระบุ"
                        amount = t.amount / 100
                        lines.append(f"{i}. {cat_name}: {amount:,.2f}฿ - {t.note or 'ไม่มีหมายเหตุ'}")
                    return jsonify({
                        'success': False,
                        'message': '\n'.join(lines)
                    })
                
                transaction_id = transactions[0].id
        
        transaction = Transaction.query.get(transaction_id)
        
        if not transaction or transaction.project_id != project_id:
            return jsonify({
                'success': False,
                'message': 'ไม่พบรายการ'
            })
        
        # Update fields
        updated = []
        if 'amount' in params and params['amount']:
            new_amount = params['amount']
            if new_amount < 1000000:  # Assume baht
                new_amount = int(new_amount * 100)
            transaction.amount = new_amount
            updated.append(f"จำนวน: {new_amount/100:,.2f}฿")
        
        if 'note' in params:
            transaction.note = params['note']
            updated.append(f"หมายเหตุ: {params['note']}")
        
        if 'category_name' in params:
            cat = Category.query.filter(
                Category.project_id == project_id,
                Category.name_th.ilike(f"%{params['category_name']}%")
            ).first()
            if cat:
                transaction.category_id = cat.id
                updated.append(f"หมวดหมู่: {cat.name_th}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"✅ แก้ไขรายการสำเร็จ!\n\nอัพเดท: {', '.join(updated) if updated else 'ไม่มีการเปลี่ยนแปลง'}"
        })
    
    # ============================================
    # ACTION: delete_transaction
    # ============================================
    elif action_type == 'delete_transaction':
        transaction_id = params.get('transaction_id')
        keyword = params.get('keyword')
        delete_last = params.get('delete_last', False)
        
        if delete_last:
            # Delete the most recent transaction
            transaction = Transaction.query.filter(
                Transaction.project_id == project_id,
                Transaction.deleted_at.is_(None)
            ).order_by(Transaction.occurred_at.desc()).first()
        elif keyword:
            transaction = Transaction.query.filter(
                Transaction.project_id == project_id,
                Transaction.note.ilike(f'%{keyword}%'),
                Transaction.deleted_at.is_(None)
            ).order_by(Transaction.occurred_at.desc()).first()
        elif transaction_id:
            transaction = Transaction.query.get(transaction_id)
        else:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุรายการที่ต้องการลบ เช่น "ลบรายการล่าสุด" หรือ "ลบรายการกินข้าว"'
            })
        
        if not transaction or transaction.project_id != project_id:
            return jsonify({
                'success': False,
                'message': 'ไม่พบรายการ'
            })
        
        # Get info before delete
        cat = Category.query.get(transaction.category_id)
        cat_name = cat.name_th if cat else "ไม่ระบุ"
        amount = transaction.amount / 100
        note = transaction.note or ""
        
        # Soft delete
        transaction.deleted_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"🗑️ ลบรายการสำเร็จ!\n\n{cat_name}: {amount:,.2f}฿{' - ' + note if note else ''}"
        })
    
    # ============================================
    # ACTION: create_category
    # ============================================
    elif action_type == 'create_category':
        name = params.get('name')
        cat_type = params.get('type', 'expense')  # expense or income
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุชื่อหมวดหมู่'
            })
        
        # Check if exists
        existing = Category.query.filter(
            Category.project_id == project_id,
            Category.name_th == name
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': f'หมวดหมู่ "{name}" มีอยู่แล้ว'
            })
        
        # Get max sort_order
        max_order = db.session.query(db.func.max(Category.sort_order)).filter(
            Category.project_id == project_id
        ).scalar() or 0
        
        # Create category
        category = Category(
            project_id=project_id,
            type=cat_type,
            name_th=name,
            name_en=name.lower().replace(' ', '_'),
            icon='tag',
            color='#6B7280',
            sort_order=max_order + 1
        )
        category.id = generate_id('cat')
        db.session.add(category)
        db.session.commit()
        
        icon = "💸" if cat_type == 'expense' else "💰"
        return jsonify({
            'success': True,
            'message': f"✅ สร้างหมวดหมู่สำเร็จ!\n\n{icon} {name} ({cat_type})"
        })
    
    # ============================================
    # ACTION: delete_category
    # ============================================
    elif action_type == 'delete_category':
        name = params.get('name')
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุชื่อหมวดหมู่ที่ต้องการลบ'
            })
        
        category = Category.query.filter(
            Category.project_id == project_id,
            Category.name_th.ilike(f'%{name}%')
        ).first()
        
        if not category:
            return jsonify({
                'success': False,
                'message': f'ไม่พบหมวดหมู่ "{name}"'
            })
        
        # Check if category has transactions
        trans_count = Transaction.query.filter(
            Transaction.category_id == category.id,
            Transaction.deleted_at.is_(None)
        ).count()
        
        if trans_count > 0:
            return jsonify({
                'success': False,
                'message': f'ไม่สามารถลบหมวดหมู่ "{category.name_th}" ได้ เพราะมีรายการอยู่ {trans_count} รายการ'
            })
        
        cat_name = category.name_th
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"🗑️ ลบหมวดหมู่สำเร็จ!\n\n{cat_name}"
        })
    
    # ============================================
    # ACTION: create_goal (Savings Goal)
    # ============================================
    elif action_type == 'create_goal':
        from app.models.savings_goal import SavingsGoal
        from app.utils.helpers import generate_id
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        name = params.get('name')
        target_amount = params.get('target_amount')
        months = params.get('months', 6)  # Default 6 months
        
        if not name or not target_amount:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุชื่อเป้าหมายและจำนวนเงิน เช่น "ตั้งเป้าออม ซื้อรถ 500000 บาทใน 12 เดือน"'
            })
        
        # Convert to satang
        if target_amount < 1000000:
            target_amount = int(target_amount * 100)
        
        # Calculate target date
        target_date = date.today() + relativedelta(months=int(months))
        
        goal = SavingsGoal(
            project_id=project_id,
            name=name,
            target_amount=target_amount,
            current_amount=0,
            target_date=target_date
        )
        goal.id = generate_id('goal')
        
        db.session.add(goal)
        db.session.commit()
        
        target_baht = target_amount / 100
        monthly_required = target_baht / int(months)
        
        return jsonify({
            'success': True,
            'message': f"🎯 สร้างเป้าหมายสำเร็จ!\n\n"
                      f"📌 {name}\n"
                      f"💰 เป้าหมาย: {target_baht:,.0f} บาท\n"
                      f"📅 ภายใน: {months} เดือน ({target_date.strftime('%d/%m/%Y')})\n"
                      f"💵 ต้องออมเดือนละ: {monthly_required:,.0f} บาท\n\n"
                      f"พิมพ์ \"เพิ่มเงินออม [จำนวน]\" เพื่อบันทึกความคืบหน้า"
        })
    
    # ============================================
    # ACTION: contribute_goal (Add to Savings)
    # ============================================
    elif action_type == 'contribute_goal':
        from app.models.savings_goal import SavingsGoal
        
        amount = params.get('amount')
        goal_name = params.get('goal_name')
        
        if not amount:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุจำนวนเงิน เช่น "เพิ่มเงินออม 5000"'
            })
        
        # Convert to satang
        if amount < 1000000:
            amount = int(amount * 100)
        
        # Find goal
        if goal_name:
            goal = SavingsGoal.query.filter(
                SavingsGoal.project_id == project_id,
                SavingsGoal.name.ilike(f'%{goal_name}%'),
                SavingsGoal.is_active == True
            ).first()
        else:
            # Get first active goal
            goal = SavingsGoal.query.filter(
                SavingsGoal.project_id == project_id,
                SavingsGoal.is_active == True
            ).order_by(SavingsGoal.created_at.desc()).first()
        
        if not goal:
            return jsonify({
                'success': False,
                'message': 'ยังไม่มีเป้าหมายออมเงิน\n\nพิมพ์ "ตั้งเป้าออม [ชื่อ] [จำนวน] บาทใน [เดือน] เดือน"'
            })
        
        # Add contribution
        goal.current_amount += amount
        db.session.commit()
        
        amount_baht = amount / 100
        current_baht = goal.current_amount / 100
        target_baht = goal.target_amount / 100
        progress = goal.progress_percentage
        
        # Check if completed
        if goal.is_completed:
            status = "🎉 ยินดีด้วย! บรรลุเป้าหมายแล้ว!"
        else:
            remaining = target_baht - current_baht
            status = f"📊 เหลืออีก {remaining:,.0f} บาท"
        
        return jsonify({
            'success': True,
            'message': f"✅ เพิ่มเงินออมสำเร็จ!\n\n"
                      f"📌 {goal.name}\n"
                      f"💰 เพิ่ม: {amount_baht:,.0f} บาท\n"
                      f"📊 ความคืบหน้า: {current_baht:,.0f}/{target_baht:,.0f} บาท ({progress:.0f}%)\n\n"
                      f"{status}"
        })
    
    # ============================================
    # ACTION: get_goals
    # ============================================
    elif action_type == 'get_goals':
        from app.models.savings_goal import SavingsGoal
        
        goals = SavingsGoal.get_active_goals(project_id)
        
        if not goals:
            return jsonify({
                'success': True,
                'message': '🎯 ยังไม่มีเป้าหมายออมเงิน\n\nพิมพ์ "ตั้งเป้าออม [ชื่อ] [จำนวน] บาทใน [เดือน] เดือน"'
            })
        
        lines = ["🎯 เป้าหมายออมเงินของคุณ:", ""]
        
        for i, goal in enumerate(goals, 1):
            current = goal.current_amount / 100
            target = goal.target_amount / 100
            progress = goal.progress_percentage
            
            status = "✅" if goal.is_completed else ("⚠️" if goal.is_overdue else "🔄")
            
            lines.append(f"{status} {goal.name}")
            lines.append(f"   💰 {current:,.0f}/{target:,.0f}฿ ({progress:.0f}%)")
            
            if goal.days_remaining is not None and not goal.is_completed:
                lines.append(f"   📅 เหลือ {goal.days_remaining} วัน")
            lines.append("")
        
        return jsonify({
            'success': True,
            'goals_count': len(goals),
            'message': '\n'.join(lines)
        })
    
    # ============================================
    # ACTION: create_recurring
    # ============================================
    elif action_type == 'create_recurring':
        from app.models.recurring import RecurringRule
        from app.models.category import Category
        from datetime import date
        
        # Get params
        category_name = params.get('category_name')
        amount = params.get('amount')
        day_of_month = params.get('day_of_month', 1)
        note = params.get('note', '')
        trans_type = params.get('type', 'expense')
        freq = params.get('freq', 'monthly')
        
        if not amount:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุจำนวนเงิน เช่น "เพิ่มรายการประจำ Netflix 300 บาททุกวันที่ 1"'
            })
        
        # Convert to satang
        if amount < 1000000:
            amount = int(amount * 100)
        
        # Find category
        category = None
        if category_name:
            category = Category.query.filter(
                Category.project_id == project_id,
                Category.name_th.ilike(f'%{category_name}%'),
                Category.type == trans_type
            ).first()
        
        if not category:
            # Find first category of that type
            category = Category.query.filter(
                Category.project_id == project_id,
                Category.type == trans_type
            ).first()
        
        if not category:
            return jsonify({
                'success': False,
                'message': f'ไม่พบหมวดหมู่สำหรับ {trans_type}'
            })
        
        # Create recurring rule
        try:
            recurring = RecurringRule(
                project_id=project_id,
                type=trans_type,
                category_id=category.id,
                amount=amount,
                freq=freq,
                start_date=date.today(),
                day_of_month=day_of_month,
                note=note
            )
            
            db.session.add(recurring)
            db.session.commit()
            
            current_app.logger.info(f"✅ Created recurring rule: {recurring.id} for project {project_id}")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ Error creating recurring: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'เกิดข้อผิดพลาด: {str(e)}'
            })
        
        amount_baht = amount / 100
        freq_text = {
            'daily': 'ทุกวัน',
            'weekly': 'ทุกสัปดาห์',
            'monthly': f'ทุกวันที่ {day_of_month} ของเดือน'
        }.get(freq, freq)
        
        return jsonify({
            'success': True,
            'recurring_id': recurring.id,
            'message': f"✅ สร้างรายการประจำสำเร็จ!\n\n"
                      f"📌 {category.name_th}{' - ' + note if note else ''}\n"
                      f"💰 {amount_baht:,.0f} บาท\n"
                      f"📅 {freq_text}\n"
                      f"🗓️ ครั้งถัดไป: {recurring.next_run_date.strftime('%d/%m/%Y')}"
        })
    
    # ============================================
    # ACTION: get_recurring
    # ============================================
    elif action_type == 'get_recurring':
        from app.models.recurring import RecurringRule
        
        recurring_rules = RecurringRule.query.filter(
            RecurringRule.project_id == project_id,
            RecurringRule.is_active == True
        ).order_by(RecurringRule.next_run_date).all()
        
        if not recurring_rules:
            return jsonify({
                'success': True,
                'message': '🔄 ยังไม่มีรายการประจำ\n\nพิมพ์ "เพิ่มรายการประจำ [ชื่อ] [จำนวน] บาททุกวันที่ [วัน]"'
            })
        
        lines = ["🔄 รายการประจำของคุณ:", ""]
        
        income_total = 0
        expense_total = 0
        
        for rule in recurring_rules:
            amount = rule.amount / 100
            icon = "💰" if rule.type == 'income' else "💸"
            cat_name = rule.category.name_th if rule.category else "ไม่ระบุ"
            
            if rule.type == 'income':
                income_total += amount
            else:
                expense_total += amount
            
            freq_text = {
                'daily': 'รายวัน',
                'weekly': 'รายสัปดาห์',
                'monthly': f'วันที่ {rule.day_of_month}'
            }.get(rule.freq, rule.freq)
            
            lines.append(f"{icon} {cat_name}: {amount:,.0f}฿ ({freq_text})")
            if rule.note:
                lines.append(f"   📝 {rule.note}")
        
        lines.append("")
        lines.append(f"📊 รวม: รายรับ {income_total:,.0f}฿ | รายจ่าย {expense_total:,.0f}฿/เดือน")
        
        return jsonify({
            'success': True,
            'count': len(recurring_rules),
            'message': '\n'.join(lines)
        })
    
    # ============================================
    # ACTION: delete_recurring
    # ============================================
    elif action_type == 'delete_recurring':
        from app.models.recurring import RecurringRule
        
        keyword = params.get('keyword')
        delete_all = params.get('delete_all', False)
        
        if delete_all:
            # Delete all recurring rules
            count = RecurringRule.query.filter(
                RecurringRule.project_id == project_id,
                RecurringRule.is_active == True
            ).update({'is_active': False})
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f"🗑️ ลบรายการประจำทั้งหมด {count} รายการ"
            })
        
        if not keyword:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุรายการที่ต้องการลบ เช่น "ลบรายการประจำ Netflix"'
            })
        
        # Find by note or category name
        rule = RecurringRule.query.filter(
            RecurringRule.project_id == project_id,
            RecurringRule.is_active == True
        ).join(Category, RecurringRule.category_id == Category.id).filter(
            db.or_(
                RecurringRule.note.ilike(f'%{keyword}%'),
                Category.name_th.ilike(f'%{keyword}%')
            )
        ).first()
        
        if not rule:
            return jsonify({
                'success': False,
                'message': f'ไม่พบรายการประจำ "{keyword}"'
            })
        
        cat_name = rule.category.name_th if rule.category else "ไม่ระบุ"
        amount = rule.amount / 100
        
        rule.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"🗑️ ลบรายการประจำสำเร็จ!\n\n{cat_name}: {amount:,.0f}฿{' - ' + rule.note if rule.note else ''}"
        })
    
    # ============================================
    # ACTION: update_recurring
    # ============================================
    elif action_type == 'update_recurring':
        from app.models.recurring import RecurringRule
        from app.models.category import Category
        
        keyword = params.get('keyword')
        
        if not keyword:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุรายการที่ต้องการแก้ไข เช่น "แก้ไขรายการประจำ Netflix วันที่ 2"'
            })
        
        # Find rule by keyword
        rule = RecurringRule.query.filter(
            RecurringRule.project_id == project_id,
            RecurringRule.is_active == True
        ).join(Category, RecurringRule.category_id == Category.id).filter(
            db.or_(
                RecurringRule.note.ilike(f'%{keyword}%'),
                Category.name_th.ilike(f'%{keyword}%')
            )
        ).first()
        
        if not rule:
            return jsonify({
                'success': False,
                'message': f'ไม่พบรายการประจำ "{keyword}"'
            })
        
        # Track changes
        changes = []
        
        # Update day_of_month
        if 'day_of_month' in params:
            old_day = rule.day_of_month
            rule.day_of_month = int(params['day_of_month'])
            # Recalculate next run
            from datetime import date
            rule.next_run_date = rule._calculate_next_run(date.today())
            changes.append(f"วันที่: {old_day} → {rule.day_of_month}")
        
        # Update amount
        if 'amount' in params:
            old_amount = rule.amount / 100
            new_amount = params['amount']
            if new_amount < 1000000:
                new_amount = int(new_amount * 100)
            rule.amount = new_amount
            changes.append(f"จำนวนเงิน: {old_amount:,.0f}฿ → {new_amount/100:,.0f}฿")
        
        # Update note
        if 'note' in params:
            rule.note = params['note']
            changes.append(f"โน๊ต: {params['note']}")
        
        # Update category
        if 'category_name' in params:
            category = Category.query.filter(
                Category.project_id == project_id,
                Category.name_th.ilike(f'%{params["category_name"]}%')
            ).first()
            if category:
                rule.category_id = category.id
                changes.append(f"หมวดหมู่: {category.name_th}")
        
        if not changes:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุสิ่งที่ต้องการแก้ไข เช่น วันที่, จำนวนเงิน, หมวดหมู่'
            })
        
        db.session.commit()
        
        cat_name = rule.category.name_th if rule.category else "ไม่ระบุ"
        
        return jsonify({
            'success': True,
            'message': f"✅ แก้ไขรายการประจำสำเร็จ!\n\n"
                      f"📌 {cat_name}{' - ' + rule.note if rule.note else ''}\n"
                      f"📝 เปลี่ยนแปลง:\n" + '\n'.join([f"  • {c}" for c in changes]) + "\n\n"
                      f"🗓️ ครั้งถัดไป: {rule.next_run_date.strftime('%d/%m/%Y')}"
        })
    
    # Unknown action
    else:
        return jsonify({
            'success': False,
            'message': f'ไม่รู้จัก action_type: {action_type}\n\nรองรับ: update_transaction, delete_transaction, create_category, delete_category, create_goal, contribute_goal, get_goals, create_recurring, get_recurring, delete_recurring, update_recurring'
        })


@bp.route('/analyze', methods=['POST'])
@require_bot_auth()
def analyze_finances():
    """
    AI Analytics endpoint - Smart financial analysis and advice
    Used by Botpress analyzeData action
    
    Supports analysis_types:
    - spending_analysis: Analyze spending patterns
    - prediction: Predict next month spending
    - health_score: Calculate financial health
    - advice: Get personalized advice
    - full_report: Complete analysis
    """
    from app.services.ai_analytics_service import AIAnalyticsService
    
    data = request.json
    botpress_user_id = data.get('botpress_user_id') or data.get('line_user_id')
    analysis_type = data.get('analysis_type', 'full_report')
    
    if not botpress_user_id:
        return jsonify({
            'success': False,
            'message': 'botpress_user_id is required'
        }), 400
    
    # Find user
    user = User.query.filter_by(botpress_user_id=botpress_user_id).first()
    if not user:
        user = User.query.filter_by(line_user_id=botpress_user_id).first()
    
    if not user or not user.current_project_id:
        return jsonify({
            'success': False,
            'message': 'ยังไม่ได้เชื่อมต่อบัญชี กรุณาพิมพ์ "เชื่อมต่อ" เพื่อลงทะเบียน'
        }), 400
    
    project_id = user.current_project_id
    
    try:
        # ============================================
        # Spending Analysis
        # ============================================
        if analysis_type == 'spending_analysis':
            result = AIAnalyticsService.get_spending_analysis(project_id)
            
            lines = ["📊 วิเคราะห์รายจ่าย:", ""]
            
            # Monthly trend
            if result['monthly_data']:
                for m in result['monthly_data'][-3:]:
                    lines.append(f"• {m['month']}: {m['total']:,.0f}฿")
            
            # Trend
            trend_icon = "📈" if result['trend'] == 'increasing' else ("📉" if result['trend'] == 'decreasing' else "➡️")
            trend_text = "เพิ่มขึ้น" if result['trend'] == 'increasing' else ("ลดลง" if result['trend'] == 'decreasing' else "คงที่")
            lines.append(f"\n{trend_icon} แนวโน้ม: {trend_text} {abs(result['change_percent']):.0f}%")
            
            # Top categories
            if result['category_breakdown']:
                lines.append("\n🏆 หมวดที่ใช้มากที่สุด:")
                for i, cat in enumerate(result['category_breakdown'][:3], 1):
                    lines.append(f"   {i}. {cat['name']}: {cat['amount']:,.0f}฿ ({cat['percentage']}%)")
            
            return jsonify({
                'success': True,
                'data': result,
                'message': '\n'.join(lines)
            })
        
        # ============================================
        # Prediction
        # ============================================
        elif analysis_type == 'prediction':
            result = AIAnalyticsService.predict_next_month(project_id)
            
            if result['predicted_amount'] == 0:
                return jsonify({
                    'success': True,
                    'message': '🔮 ยังไม่มีข้อมูลเพียงพอสำหรับพยากรณ์\n\nลองบันทึกรายการอย่างน้อย 1 เดือนก่อนนะครับ'
                })
            
            confidence_text = {"high": "สูง ✅", "medium": "ปานกลาง", "low": "ต่ำ"}
            
            lines = [
                "🔮 พยากรณ์รายจ่ายเดือนหน้า:",
                "",
                f"💰 คาดการณ์: {result['predicted_amount']:,.0f} บาท",
                f"📊 ช่วง: {result['range_low']:,.0f} - {result['range_high']:,.0f} บาท",
                f"📈 ความมั่นใจ: {confidence_text.get(result['confidence'], result['confidence'])}",
                f"📅 อ้างอิงจาก: {result['based_on_months']} เดือนที่ผ่านมา"
            ]
            
            return jsonify({
                'success': True,
                'data': result,
                'message': '\n'.join(lines)
            })
        
        # ============================================
        # Health Score
        # ============================================
        elif analysis_type == 'health_score':
            result = AIAnalyticsService.calculate_financial_health(project_id)
            
            lines = [
                f"💯 คะแนนสุขภาพการเงิน: {result['score']}/100 ({result['grade_text']})",
                ""
            ]
            
            if result['strengths']:
                lines.append("✅ จุดแข็ง:")
                for s in result['strengths']:
                    lines.append(f"   • {s}")
            
            if result['improvements']:
                lines.append("\n⚠️ ควรปรับปรุง:")
                for imp in result['improvements']:
                    lines.append(f"   • {imp}")
            
            return jsonify({
                'success': True,
                'data': result,
                'message': '\n'.join(lines)
            })
        
        # ============================================
        # Smart Advice
        # ============================================
        elif analysis_type == 'advice':
            result = AIAnalyticsService.get_smart_advice(project_id)
            
            lines = [
                f"💡 คำแนะนำทางการเงิน (คะแนน: {result['health_score']}/100)",
                ""
            ]
            
            for adv in result['advice']:
                lines.append(f"{adv['title']}")
                lines.append(f"   {adv['content']}")
                lines.append("")
            
            return jsonify({
                'success': True,
                'data': result,
                'message': '\n'.join(lines)
            })
        
        # ============================================
        # Full Report (default)
        # ============================================
        else:
            health = AIAnalyticsService.calculate_financial_health(project_id)
            spending = AIAnalyticsService.get_spending_analysis(project_id)
            prediction = AIAnalyticsService.predict_next_month(project_id)
            
            trend_icon = "📈" if spending['trend'] == 'increasing' else ("📉" if spending['trend'] == 'decreasing' else "➡️")
            trend_text = "เพิ่มขึ้น" if spending['trend'] == 'increasing' else ("ลดลง" if spending['trend'] == 'decreasing' else "คงที่")
            
            lines = [
                "📊 รายงานวิเคราะห์การเงิน",
                "═══════════════════",
                "",
                f"💯 สุขภาพการเงิน: {health['score']}/100 ({health['grade_text']})",
                f"💰 รายรับเดือนนี้: {health['income']:,.0f}฿",
                f"💸 รายจ่ายเดือนนี้: {health['expense']:,.0f}฿",
                f"{trend_icon} แนวโน้ม: {trend_text} {abs(spending['change_percent']):.0f}%",
            ]
            
            if prediction['predicted_amount'] > 0:
                lines.append(f"🔮 คาดการณ์เดือนหน้า: {prediction['predicted_amount']:,.0f}฿")
            
            # Top category
            if spending['category_breakdown']:
                top = spending['category_breakdown'][0]
                lines.append(f"\n🏆 หมวดใช้มากสุด: {top['name']} ({top['percentage']}%)")
            
            # Key advice
            if health['improvements']:
                lines.append(f"\n💡 แนะนำ: {health['improvements'][0]}")
            
            return jsonify({
                'success': True,
                'data': {
                    'health': health,
                    'spending': spending,
                    'prediction': prediction
                },
                'message': '\n'.join(lines)
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500


@bp.route('/smart', methods=['POST'])
def smart_message():
    """
    Smart NLP endpoint - Universal message handler using Gemini AI
    
    This is the ONLY action Botpress needs to call.
    It understands natural language and routes to appropriate functions.
    
    Request: { botpress_user_id, message, context (optional) }
    Response: { success, message, need_more_info, question }
    """
    import os
    from app.services.gemini_nlp_service import gemini_nlp
    from app.models.recurring import RecurringRule
    from app.models.category import Category
    from app.models.savings_goal import SavingsGoal
    from datetime import date
    
    # Simple API key authentication
    api_key = request.headers.get('X-Bot-Signature') or request.headers.get('X-API-Key')
    expected_key = os.environ.get('BOT_SECRET', '')
    
    # Debug logging
    current_app.logger.info(f"Smart API - Received key: {api_key[:10] if api_key else 'None'}...")
    current_app.logger.info(f"Smart API - Expected key exists: {bool(expected_key)}, len: {len(expected_key)}")
    
    # If no BOT_SECRET configured, allow for testing (log warning)
    if not expected_key:
        current_app.logger.warning("BOT_SECRET not configured! Allowing request for testing.")
    elif not api_key or api_key != expected_key:
        current_app.logger.warning(f"Smart API - Auth failed: key_match={api_key == expected_key}")
        return jsonify({
            'success': False,
            'message': 'Unauthorized: Invalid API Key'
        }), 401
    
    data = request.json
    botpress_user_id = data.get('botpress_user_id') or data.get('line_user_id')
    message = data.get('message', '').strip()
    context = data.get('context', {})  # For multi-turn conversations
    
    if not botpress_user_id:
        return jsonify({
            'success': False,
            'message': 'botpress_user_id is required'
        }), 400
    
    if not message:
        return jsonify({
            'success': False,
            'message': 'message is required'
        }), 400
    
    # Find user
    user = User.query.filter_by(botpress_user_id=botpress_user_id).first()
    if not user:
        user = User.query.filter_by(line_user_id=botpress_user_id).first()
    
    if not user or not user.current_project_id:
        return jsonify({
            'success': False,
            'message': 'ยังไม่ได้เชื่อมต่อบัญชี กรุณาพิมพ์ \"เชื่อมต่อ\" เพื่อลงทะเบียน'
        })
    
    project_id = user.current_project_id
    
    # Parse message using Gemini NLP
    parsed = gemini_nlp.parse_message(message)
    intent = parsed.get('intent', 'general')
    entities = parsed.get('entities', {})
    missing_fields = parsed.get('missing_fields', [])
    fallback_question = parsed.get('fallback_question')
    
    # Check for missing required fields
    if missing_fields and fallback_question:
        return jsonify({
            'success': True,
            'need_more_info': True,
            'missing_fields': missing_fields,
            'message': f"📝 {fallback_question}"
        })
    
    # Route based on intent
    try:
        # ========================
        # CREATE RECURRING
        # ========================
        if intent == 'create_recurring':
            amount = entities.get('amount')
            day_of_month = entities.get('day_of_month', 1)
            note = entities.get('note', '')
            category_name = entities.get('category_name', '')
            trans_type = entities.get('type', 'expense')
            
            if not amount:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '💰 กรุณาระบุจำนวนเงินด้วยค่ะ'
                })
            
            # Convert to satang
            if amount < 1000000:
                amount = int(amount * 100)
            
            # Find or create category
            category = None
            if category_name:
                category = Category.query.filter(
                    Category.project_id == project_id,
                    Category.name_th.ilike(f'%{category_name}%'),
                    Category.type == trans_type
                ).first()
            
            if not category:
                category = Category.query.filter(
                    Category.project_id == project_id,
                    Category.type == trans_type
                ).first()
            
            if not category:
                return jsonify({
                    'success': False,
                    'message': f'ไม่พบหมวดหมู่สำหรับ {trans_type}'
                })
            
            recurring = RecurringRule(
                project_id=project_id,
                type=trans_type,
                category_id=category.id,
                amount=amount,
                freq='monthly',
                start_date=date.today(),
                day_of_month=day_of_month,
                note=note or category_name
            )
            
            db.session.add(recurring)
            db.session.commit()
            
            amount_baht = amount / 100
            return jsonify({
                'success': True,
                'message': f"✅ สร้างรายการประจำสำเร็จ!\n\n"
                          f"📌 {category.name_th}{' - ' + (note or category_name) if (note or category_name) else ''}\n"
                          f"💰 {amount_baht:,.0f} บาท\n"
                          f"📅 ทุกวันที่ {day_of_month} ของเดือน\n"
                          f"🗓️ ครั้งถัดไป: {recurring.next_run_date.strftime('%d/%m/%Y')}\n\n"
                          f"ต้องการทำอะไรต่อไหมคะ?"
            })
        
        # ========================
        # GET RECURRING
        # ========================
        elif intent == 'get_recurring':
            recurring_rules = RecurringRule.query.filter(
                RecurringRule.project_id == project_id,
                RecurringRule.is_active == True
            ).order_by(RecurringRule.next_run_date).all()
            
            if not recurring_rules:
                return jsonify({
                    'success': True,
                    'message': '🔄 ยังไม่มีรายการประจำ\n\nพิมพ์ "เพิ่มรายการประจำ [ชื่อ] [จำนวน] บาททุกวันที่ [วัน]"'
                })
            
            lines = ["🔄 รายการประจำของคุณ:", ""]
            income_total = 0
            expense_total = 0
            
            for rule in recurring_rules:
                amount = rule.amount / 100
                icon = "💰" if rule.type == 'income' else "💸"
                cat_name = rule.category.name_th if rule.category else "ไม่ระบุ"
                
                if rule.type == 'income':
                    income_total += amount
                else:
                    expense_total += amount
                
                freq_text = f'วันที่ {rule.day_of_month}' if rule.freq == 'monthly' else rule.freq
                lines.append(f"{icon} {cat_name}: {amount:,.0f}฿ ({freq_text})")
                if rule.note:
                    lines.append(f"   📝 {rule.note}")
            
            lines.append("")
            lines.append(f"📊 รวม: +{income_total:,.0f}฿ | -{expense_total:,.0f}฿/เดือน")
            
            return jsonify({
                'success': True,
                'count': len(recurring_rules),
                'message': '\n'.join(lines)
            })
        
        # ========================
        # DELETE RECURRING
        # ========================
        elif intent == 'delete_recurring':
            keyword = entities.get('keyword')
            
            if not keyword:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '❓ ต้องการลบรายการประจำชื่ออะไรคะ?'
                })
            
            rule = RecurringRule.query.filter(
                RecurringRule.project_id == project_id,
                RecurringRule.is_active == True
            ).join(Category, RecurringRule.category_id == Category.id).filter(
                db.or_(
                    RecurringRule.note.ilike(f'%{keyword}%'),
                    Category.name_th.ilike(f'%{keyword}%')
                )
            ).first()
            
            if not rule:
                return jsonify({
                    'success': False,
                    'message': f'ไม่พบรายการประจำ "{keyword}"'
                })
            
            cat_name = rule.category.name_th if rule.category else "ไม่ระบุ"
            amount = rule.amount / 100
            
            rule.is_active = False
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f"🗑️ ลบรายการประจำสำเร็จ!\n\n{cat_name}: {amount:,.0f}฿{' - ' + rule.note if rule.note else ''}\n\nต้องการทำอะไรต่อไหมคะ?"
            })
        
        # ========================
        # UPDATE RECURRING
        # ========================
        elif intent == 'update_recurring':
            keyword = entities.get('keyword')
            
            if not keyword:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '❓ ต้องการแก้ไขรายการประจำชื่ออะไรคะ?'
                })
            
            rule = RecurringRule.query.filter(
                RecurringRule.project_id == project_id,
                RecurringRule.is_active == True
            ).join(Category, RecurringRule.category_id == Category.id).filter(
                db.or_(
                    RecurringRule.note.ilike(f'%{keyword}%'),
                    Category.name_th.ilike(f'%{keyword}%')
                )
            ).first()
            
            if not rule:
                return jsonify({
                    'success': False,
                    'message': f'ไม่พบรายการประจำ "{keyword}"'
                })
            
            changes = []
            
            if 'day_of_month' in entities and entities['day_of_month']:
                old_day = rule.day_of_month
                rule.day_of_month = int(entities['day_of_month'])
                rule.next_run_date = rule._calculate_next_run(date.today())
                changes.append(f"วันที่: {old_day} → {rule.day_of_month}")
            
            if 'amount' in entities and entities['amount']:
                old_amount = rule.amount / 100
                new_amount = entities['amount']
                if new_amount < 1000000:
                    new_amount = int(new_amount * 100)
                rule.amount = new_amount
                changes.append(f"จำนวนเงิน: {old_amount:,.0f}฿ → {new_amount/100:,.0f}฿")
            
            if not changes:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '❓ ต้องการแก้ไขอะไรคะ?\n• วันที่ (เช่น วันที่ 15)\n• จำนวนเงิน (เช่น 500 บาท)'
                })
            
            db.session.commit()
            cat_name = rule.category.name_th if rule.category else "ไม่ระบุ"
            
            return jsonify({
                'success': True,
                'message': f"✅ แก้ไขรายการประจำสำเร็จ!\n\n"
                          f"📌 {cat_name}{' - ' + rule.note if rule.note else ''}\n"
                          f"📝 เปลี่ยนแปลง:\n" + '\n'.join([f"  • {c}" for c in changes]) + "\n\n"
                          f"🗓️ ครั้งถัดไป: {rule.next_run_date.strftime('%d/%m/%Y')}"
            })
        
        # ========================
        # GET GOALS
        # ========================
        elif intent == 'get_goals':
            goals = SavingsGoal.query.filter_by(project_id=project_id, is_active=True).all()
            
            if not goals:
                return jsonify({
                    'success': True,
                    'message': '🎯 ยังไม่มีเป้าหมายออมเงิน\n\nพิมพ์ "ตั้งเป้าออม [ชื่อ] [จำนวน] บาทใน [X] เดือน"'
                })
            
            lines = ["🎯 เป้าหมายออมเงินของคุณ:", ""]
            
            for goal in goals:
                target = goal.target_amount / 100
                current = (goal.current_amount or 0) / 100
                progress = goal.progress_percentage or 0
                status = "✅" if goal.is_completed else "🎯"
                
                lines.append(f"{status} {goal.name}")
                lines.append(f"   💰 {current:,.0f}/{target:,.0f}฿ ({progress:.0f}%)")
                
                if goal.days_remaining is not None and not goal.is_completed:
                    lines.append(f"   📅 เหลือ {goal.days_remaining} วัน")
                lines.append("")
            
            return jsonify({
                'success': True,
                'goals_count': len(goals),
                'message': '\n'.join(lines)
            })
        
        # ========================
        # CREATE GOAL
        # ========================
        elif intent == 'create_goal':
            goal_name = entities.get('goal_name')
            target_amount = entities.get('target_amount')
            months = entities.get('months', 12)
            
            if not goal_name:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '🎯 ต้องการตั้งเป้าออมชื่ออะไรคะ?\n\nตัวอย่าง: "ตั้งเป้าออม iPhone 45000 บาท"'
                })
            
            if not target_amount:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': f'💰 เป้าหมาย "{goal_name}" ต้องออมเท่าไหร่คะ?'
                })
            
            # Convert to satang
            target_satang = int(target_amount * 100) if target_amount < 1000000 else int(target_amount)
            
            # Calculate target date
            from dateutil.relativedelta import relativedelta
            target_date = date.today() + relativedelta(months=int(months))
            
            new_goal = SavingsGoal(
                project_id=project_id,
                name=goal_name,
                target_amount=target_satang,
                current_amount=0,
                target_date=target_date,
                is_active=True
            )
            
            db.session.add(new_goal)
            db.session.commit()
            
            monthly_save = target_amount / months
            
            return jsonify({
                'success': True,
                'message': f"🎯 สร้างเป้าหมายสำเร็จ!\n\n"
                          f"📌 {goal_name}\n"
                          f"💰 เป้าหมาย: {target_amount:,.0f} บาท\n"
                          f"📅 กำหนด: {months} เดือน\n"
                          f"💡 ควรออมเดือนละ: {monthly_save:,.0f} บาท\n\n"
                          f"พิมพ์ \"เติมเงิน {goal_name} [จำนวน] บาท\" เพื่อเพิ่มเงิน"
            })
        
        # ========================
        # CONTRIBUTE TO GOAL
        # ========================
        elif intent == 'contribute_goal':
            goal_name = entities.get('goal_name')
            amount = entities.get('amount')
            
            if not goal_name and not amount:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '💰 ต้องการเติมเงินเข้าเป้าหมายไหนคะ?\n\nตัวอย่าง: "เติมเงิน iPhone 5000 บาท"'
                })
            
            # Find goal
            query = SavingsGoal.query.filter_by(project_id=project_id, is_active=True)
            
            if goal_name:
                goal = query.filter(SavingsGoal.name.ilike(f'%{goal_name}%')).first()
            else:
                goal = query.first()
            
            if not goal:
                return jsonify({
                    'success': False,
                    'message': f'❌ ไม่พบเป้าหมาย "{goal_name or ""}"\n\nพิมพ์ "เป้าหมาย" เพื่อดูรายการ'
                })
            
            if not amount:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': f'💰 ต้องการเติมเงินเข้า "{goal.name}" เท่าไหร่คะ?'
                })
            
            # Convert to satang
            amount_satang = int(amount * 100) if amount < 1000000 else int(amount)
            
            old_amount = goal.current_amount / 100
            goal.current_amount = (goal.current_amount or 0) + amount_satang
            new_amount = goal.current_amount / 100
            target = goal.target_amount / 100
            progress = goal.progress_percentage
            
            db.session.commit()
            
            status = "🎉 ยินดีด้วย! บรรลุเป้าหมายแล้ว!" if goal.is_completed else f"📊 Progress: {progress:.0f}%"
            
            return jsonify({
                'success': True,
                'message': f"💰 เติมเงินสำเร็จ!\n\n"
                          f"🎯 {goal.name}\n"
                          f"➕ เติม: {amount:,.0f} บาท\n"
                          f"💵 รวม: {new_amount:,.0f}/{target:,.0f} บาท\n\n"
                          f"{status}"
            })
        
        # ========================
        # DELETE GOAL
        # ========================
        elif intent == 'delete_goal':
            goal_name = entities.get('goal_name')
            
            if not goal_name:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '❓ ต้องการลบเป้าหมายไหนคะ?\n\nพิมพ์ "เป้าหมาย" เพื่อดูรายการ'
                })
            
            goal = SavingsGoal.query.filter(
                SavingsGoal.project_id == project_id,
                SavingsGoal.name.ilike(f'%{goal_name}%'),
                SavingsGoal.is_active == True
            ).first()
            
            if not goal:
                return jsonify({
                    'success': False,
                    'message': f'❌ ไม่พบเป้าหมาย "{goal_name}"'
                })
            
            goal_name_saved = goal.name
            current = goal.current_amount / 100
            
            goal.is_active = False
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f"🗑️ ลบเป้าหมายสำเร็จ!\n\n"
                          f"📌 {goal_name_saved}\n"
                          f"💰 ยอดสะสม: {current:,.0f} บาท\n\n"
                          f"พิมพ์ \"เป้าหมาย\" เพื่อดูเป้าหมายที่เหลือ"
            })
        
        # ========================
        # GET SUMMARY
        # ========================
        elif intent == 'get_summary':
            from app.services.ai_analytics_service import AIAnalyticsService
            
            period = entities.get('period', 'this_month')
            today = datetime.utcnow()
            
            if period == 'today':
                start_date = datetime(today.year, today.month, today.day)
            elif period == 'this_week':
                start_date = today - timedelta(days=today.weekday())
            else:
                start_date = datetime(today.year, today.month, 1)
            
            # Get transactions
            transactions = Transaction.query.filter(
                Transaction.project_id == project_id,
                Transaction.occurred_at >= start_date,
                Transaction.deleted_at.is_(None)
            ).all()
            
            income = sum(t.amount for t in transactions if t.type == 'income') / 100
            expense = sum(t.amount for t in transactions if t.type == 'expense') / 100
            balance = income - expense
            
            period_text = {
                'today': 'วันนี้',
                'this_week': 'สัปดาห์นี้',
                'this_month': 'เดือนนี้'
            }.get(period, 'เดือนนี้')
            
            return jsonify({
                'success': True,
                'message': f"📊 สรุป{period_text}\n\n"
                          f"💰 รายรับ: {income:,.0f} บาท\n"
                          f"💸 รายจ่าย: {expense:,.0f} บาท\n"
                          f"{'💚' if balance >= 0 else '❤️'} คงเหลือ: {balance:+,.0f} บาท\n"
                          f"📝 รายการ: {len(transactions)} รายการ"
            })
        
        # ========================
        # GET CATEGORIES
        # ========================
        elif intent == 'get_categories':
            categories = Category.query.filter_by(project_id=project_id).order_by(Category.type, Category.name_th).all()
            
            if not categories:
                return jsonify({
                    'success': True,
                    'message': '📁 ยังไม่มีหมวดหมู่\n\nพิมพ์ "สร้างหมวดหมู่ [ชื่อ]" เพื่อสร้างใหม่'
                })
            
            income_cats = [c for c in categories if c.type == 'income']
            expense_cats = [c for c in categories if c.type == 'expense']
            
            lines = ["📁 หมวดหมู่ของคุณ:", ""]
            
            if income_cats:
                lines.append("💰 **รายรับ:**")
                for cat in income_cats:
                    lines.append(f"  • {cat.name_th}")
            
            if expense_cats:
                lines.append("\n💸 **รายจ่าย:**")
                for cat in expense_cats:
                    lines.append(f"  • {cat.name_th}")
            
            lines.append(f"\n📊 รวม {len(categories)} หมวดหมู่")
            
            return jsonify({
                'success': True,
                'count': len(categories),
                'message': '\n'.join(lines)
            })
        
        # ========================
        # CREATE CATEGORY
        # ========================
        elif intent == 'create_category':
            category_name = entities.get('category_name')
            category_type = entities.get('type', 'expense')
            
            if not category_name:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '❓ ต้องการสร้างหมวดหมู่ชื่ออะไรคะ?'
                })
            
            # Check if exists
            existing = Category.query.filter(
                Category.project_id == project_id,
                Category.name_th.ilike(f'%{category_name}%')
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'❌ หมวดหมู่ "{category_name}" มีอยู่แล้ว'
                })
            
            new_category = Category(
                project_id=project_id,
                name_th=category_name,
                name_en=category_name,
                icon='📁',
                type=category_type
            )
            
            db.session.add(new_category)
            db.session.commit()
            
            type_text = 'รายรับ' if category_type == 'income' else 'รายจ่าย'
            
            return jsonify({
                'success': True,
                'message': f"✅ สร้างหมวดหมู่สำเร็จ!\n\n"
                          f"📁 {category_name}\n"
                          f"💰 ประเภท: {type_text}\n\n"
                          f"ต้องการทำอะไรต่อไหมคะ?"
            })
        
        # ========================
        # UPDATE CATEGORY (change type income/expense)
        # ========================
        elif intent == 'update_category':
            category_name = entities.get('category_name')
            new_type = entities.get('new_type')  # 'income' or 'expense'
            
            if not category_name:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '❓ ต้องการแก้ไขหมวดหมู่ไหนคะ? กรุณาระบุชื่อ'
                })
            
            # Find category
            category = Category.query.filter(
                Category.project_id == project_id,
                Category.name_th.ilike(f'%{category_name}%')
            ).first()
            
            if not category:
                return jsonify({
                    'success': False,
                    'message': f'❌ ไม่พบหมวดหมู่ "{category_name}"'
                })
            
            old_type = category.type
            old_type_text = 'รายรับ' if old_type == 'income' else 'รายจ่าย'
            
            # Toggle type if not specified
            if not new_type:
                new_type = 'expense' if old_type == 'income' else 'income'
            
            new_type_text = 'รายรับ' if new_type == 'income' else 'รายจ่าย'
            
            category.type = new_type
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f"✅ แก้ไขหมวดหมู่สำเร็จ!\n\n"
                          f"📁 {category.name_th}\n"
                          f"🔄 เปลี่ยน: {old_type_text} → {new_type_text}\n\n"
                          f"ต้องการทำอะไรต่อไหมคะ?"
            })
        
        # ========================
        # DELETE CATEGORY
        # ========================
        elif intent == 'delete_category':
            category_name = entities.get('category_name')
            
            if not category_name:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '❓ ต้องการลบหมวดหมู่ไหนคะ? กรุณาระบุชื่อ'
                })
            
            # Find category
            category = Category.query.filter(
                Category.project_id == project_id,
                Category.name_th.ilike(f'%{category_name}%')
            ).first()
            
            if not category:
                return jsonify({
                    'success': False,
                    'message': f'❌ ไม่พบหมวดหมู่ "{category_name}"'
                })
            
            # Check if category has transactions
            trans_count = Transaction.query.filter_by(category_id=category.id).count()
            
            if trans_count > 0:
                return jsonify({
                    'success': False,
                    'message': f'❌ ไม่สามารถลบ "{category.name_th}" เพราะมี {trans_count} รายการใช้งานอยู่'
                })
            
            cat_name = category.name_th
            db.session.delete(category)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f"🗑️ ลบหมวดหมู่ \"{cat_name}\" สำเร็จ!\n\n"
                          f"พิมพ์ \"หมวดหมู่\" เพื่อดูหมวดหมู่ที่เหลือ"
            })
        
        # ========================
        # CREATE TRANSACTION
        # ========================
        elif intent == 'create_transaction':
            amount = entities.get('amount')
            trans_type = entities.get('type', 'expense')
            category_name = entities.get('category_name', '')
            note = entities.get('note', '')
            
            if not amount:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '💰 กรุณาระบุจำนวนเงินค่ะ'
                })
            
            # Convert to satang
            if amount < 1000000:
                amount = int(amount * 100)
            
            # Find category
            category = None
            if category_name:
                category = Category.query.filter(
                    Category.project_id == project_id,
                    Category.name_th.ilike(f'%{category_name}%'),
                    Category.type == trans_type
                ).first()
            
            if not category:
                category = Category.query.filter(
                    Category.project_id == project_id,
                    Category.type == trans_type
                ).first()
            
            if not category:
                return jsonify({
                    'success': False,
                    'message': f'ไม่พบหมวดหมู่สำหรับ {trans_type}'
                })
            
            transaction = Transaction(
                project_id=project_id,
                type=trans_type,
                category_id=category.id,
                amount=amount,
                note=note or category_name,
                occurred_at=datetime.utcnow()
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            amount_baht = amount / 100
            icon = '💰' if trans_type == 'income' else '💸'
            
            return jsonify({
                'success': True,
                'message': f"{icon} บันทึกสำเร็จ!\n\n"
                          f"📁 {category.name_th}\n"
                          f"💵 {amount_baht:,.0f} บาท\n"
                          f"📝 {note or '-'}\n\n"
                          f"ต้องการบันทึกรายการเพิ่มไหมคะ?"
            })
        
        # ========================
        # GET TRANSACTIONS (ดูรายการ)
        # ========================
        elif intent == 'get_transactions':
            period = entities.get('period', 'this_month')
            today = datetime.utcnow()
            
            if period == 'today':
                start_date = datetime(today.year, today.month, today.day)
                period_text = 'วันนี้'
            elif period == 'this_week':
                start_date = today - timedelta(days=today.weekday())
                period_text = 'สัปดาห์นี้'
            else:
                start_date = datetime(today.year, today.month, 1)
                period_text = 'เดือนนี้'
            
            transactions = Transaction.query.filter(
                Transaction.project_id == project_id,
                Transaction.occurred_at >= start_date,
                Transaction.deleted_at.is_(None)
            ).order_by(Transaction.occurred_at.desc()).limit(10).all()
            
            if not transactions:
                return jsonify({
                    'success': True,
                    'message': f"📝 ยังไม่มีรายการ{period_text}\n\nพิมพ์ \"กินข้าว 350 บาท\" เพื่อบันทึกรายการใหม่"
                })
            
            lines = [f"📝 รายการ{period_text} (ล่าสุด 10):", ""]
            
            for t in transactions:
                icon = '💰' if t.type == 'income' else '💸'
                cat_name = t.category.name_th if t.category else 'ไม่ระบุ'
                amount = t.amount / 100
                date_str = t.occurred_at.strftime('%d/%m')
                lines.append(f"{icon} {date_str} | {cat_name}: {amount:,.0f}฿")
                if t.note:
                    lines.append(f"   📝 {t.note}")
            
            return jsonify({
                'success': True,
                'count': len(transactions),
                'message': '\n'.join(lines)
            })
        
        # ========================
        # DELETE TRANSACTION
        # ========================
        elif intent == 'delete_transaction':
            trans_id = entities.get('transaction_id')
            keyword = entities.get('keyword')
            
            if not trans_id and not keyword:
                return jsonify({
                    'success': True,
                    'need_more_info': True,
                    'message': '❓ ต้องการลบรายการไหนคะ? กรุณาระบุรายละเอียด\n\nพิมพ์ "รายการ" เพื่อดูรายการทั้งหมดก่อน'
                })
            
            # Find transaction
            query = Transaction.query.filter(
                Transaction.project_id == project_id,
                Transaction.deleted_at.is_(None)
            )
            
            if keyword:
                query = query.filter(Transaction.note.ilike(f'%{keyword}%'))
            
            transaction = query.order_by(Transaction.occurred_at.desc()).first()
            
            if not transaction:
                return jsonify({
                    'success': False,
                    'message': '❌ ไม่พบรายการ'
                })
            
            cat_name = transaction.category.name_th if transaction.category else 'ไม่ระบุ'
            amount = transaction.amount / 100
            
            transaction.deleted_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f"🗑️ ลบรายการสำเร็จ!\n\n"
                          f"📁 {cat_name}: {amount:,.0f} บาท\n"
                          f"📝 {transaction.note or '-'}"
            })
        
        # ========================
        # GET WEB LINK
        # ========================
        elif intent == 'get_web_link':
            # Generate web link for user
            base_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'line-botpress-production.up.railway.app')
            
            return jsonify({
                'success': True,
                'message': f"🌐 ลิงก์เว็บไซต์ของคุณ:\n\n"
                          f"📊 Dashboard:\nhttps://{base_url}/\n\n"
                          f"👤 Profile:\nhttps://{base_url}/profile\n\n"
                          f"📈 Analytics:\nhttps://{base_url}/analytics\n\n"
                          f"คลิกลิงก์เพื่อดูรายละเอียดเพิ่มเติมได้เลยค่ะ! 💜"
            })
        
        # ========================
        # GENERAL / UNKNOWN
        # ========================
        else:
            return jsonify({
                'success': True,
                'intent': intent,
                'entities': entities,
                'message': f"สวัสดีค่ะ! ฉันช่วยอะไรได้บ้าง?\n\n"
                          f"📝 รายการ: \"รายการเดือนนี้\"\n"
                          f"💰 บันทึก: \"กินข้าว 350 บาท\"\n"
                          f"🔄 ประจำ: \"รายการประจำ\"\n"
                          f"🎯 ออมเงิน: \"ตั้งเป้าออม iPhone 45000 บาท\"\n"
                          f"📁 หมวดหมู่: \"หมวดหมู่\"\n"
                          f"🌐 เว็บไซต์: \"ขอลิงก์เว็บ\"\n"
                          f"📊 สรุป: \"สรุปวันนี้\""
            })
    
    except Exception as e:
        current_app.logger.error(f"Smart endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500
