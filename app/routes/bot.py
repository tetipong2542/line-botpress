"""
Botpress integration routes - Bot API endpoints with HMAC security
"""
from flask import Blueprint, request, jsonify, g
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

    if not line_user_id:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'line_user_id is required'
            }
        }), 400

    # Find user
    user = User.query.filter_by(line_user_id=line_user_id).first()

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


@bp.route('/transactions/create', methods=['POST'])
@require_bot_auth(require_idempotency=True)
def create_transaction():
    """
    Create transaction via bot (with idempotency)
    Supports both category_id and category_name
    """
    from app.models.category import Category
    
    data = request.json

    line_user_id = data.get('line_user_id')
    type = data.get('type')
    category_id = data.get('category_id')
    category_name = data.get('category_name')  # Support category name
    amount = data.get('amount')
    note = data.get('note')
    occurred_at = data.get('occurred_at')

    # Find user first (needed for category lookup)
    user = User.query.filter_by(line_user_id=line_user_id).first()

    if not user or not user.current_project_id:
        return jsonify({
            'error': {
                'code': 'USER_NO_PROJECT',
                'message': 'User has no active project. Please login via web first.'
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
