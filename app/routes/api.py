"""
Core API routes - CRUD operations for web and bot
"""
from flask import Blueprint, request, jsonify, session
from app.services.transaction_service import TransactionService
from app.models.user import User
from app.models.project import Project, ProjectMember, ProjectInvite, ProjectSettings
from app.models.category import Category
from app.models.budget import Budget
from app import db
from app.utils.helpers import generate_id, baht_to_satang

bp = Blueprint('api', __name__, url_prefix='/api/v1')


def get_current_user():
    """Get current user from session"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def require_auth():
    """Require authentication"""
    user = get_current_user()
    if not user:
        return jsonify({
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required'
            }
        }), 401
    return None


# Projects
@bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects for current user"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    # Get owned projects
    owned = Project.query.filter_by(owner_user_id=user.id, deleted_at=None).all()

    # Get member projects
    memberships = ProjectMember.query.filter_by(user_id=user.id).all()
    member_projects = [m.project for m in memberships if not m.project.deleted_at]

    projects = owned + member_projects

    return jsonify({
        'projects': [p.to_dict() for p in projects]
    })


@bp.route('/projects', methods=['POST'])
def create_project():
    """Create new project"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    if not data.get('name'):
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Project name is required'
            }
        }), 400

    project = Project(name=data['name'], owner_user_id=user.id)
    db.session.add(project)

    # Create default settings
    settings = ProjectSettings(project_id=project.id)
    db.session.add(settings)

    # Create default categories
    default_categories = [
        ('expense', 'อาหาร', 'food', '🍜', '#FF6B6B'),
        ('expense', 'เดินทาง', 'transport', '🚗', '#4ECDC4'),
        ('expense', 'ช้อปปิ้ง', 'shopping', '🛍️', '#FFE66D'),
        ('income', 'เงินเดือน', 'salary', '💰', '#95E1D3'),
        ('income', 'รายได้อื่นๆ', 'other_income', '💵', '#A8E6CF')
    ]

    for i, (type, name_th, name_en, icon, color) in enumerate(default_categories):
        cat = Category(
            project_id=project.id,
            type=type,
            name_th=name_th,
            name_en=name_en,
            icon=icon,
            color=color,
            sort_order=i
        )
        db.session.add(cat)

    db.session.commit()

    return jsonify({
        'project': project.to_dict()
    }), 201


# Transactions
@bp.route('/projects/<project_id>/transactions', methods=['GET'])
def get_transactions(project_id):
    """Get transactions for project"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    # Build filters from query params
    filters = {
        'type': request.args.get('type'),
        'category_id': request.args.get('category_id'),
        'from_date': request.args.get('from'),
        'to_date': request.args.get('to'),
        'page': int(request.args.get('page', 1)),
        'per_page': int(request.args.get('per_page', 50))
    }

    try:
        pagination = TransactionService.get_transactions(project_id, user.id, filters)

        return jsonify({
            'transactions': [t.to_dict(include_category=True) for t in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/transactions', methods=['POST'])
def create_transaction(project_id):
    """Create new transaction"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        transaction = TransactionService.create_transaction(
            project_id=project_id,
            user_id=user.id,
            type=data.get('type'),
            category_id=data.get('category_id'),
            amount=data.get('amount'),
            occurred_at=data.get('occurred_at'),
            note=data.get('note'),
            member_id=data.get('member_id')
        )

        return jsonify({
            'transaction': transaction.to_dict(include_category=True)
        }), 201

    except (ValueError, PermissionError) as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


# Categories
@bp.route('/projects/<project_id>/categories', methods=['GET'])
def get_categories(project_id):
    """Get categories for project"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    type_filter = request.args.get('type')

    query = Category.query.filter_by(project_id=project_id, is_active=True)

    if type_filter:
        query = query.filter_by(type=type_filter)

    categories = query.order_by(Category.sort_order).all()

    return jsonify({
        'categories': [c.to_dict() for c in categories]
    })


# Budgets
@bp.route('/projects/<project_id>/budgets', methods=['GET'])
def get_budgets(project_id):
    """Get budgets for project"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    month = request.args.get('month')  # YYYY-MM format

    if not month:
        from datetime import datetime
        month = datetime.utcnow().strftime('%Y-%m')

    budgets = Budget.query.filter_by(
        project_id=project_id,
        month_yyyymm=month
    ).all()

    return jsonify({
        'budgets': [b.to_dict() for b in budgets],
        'month': month
    })


@bp.route('/projects/<project_id>/budgets/<category_id>', methods=['PUT'])
def upsert_budget(project_id, category_id):
    """Create or update budget for category"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data = request.json
    month = request.args.get('month')

    if not month:
        from datetime import datetime
        month = datetime.utcnow().strftime('%Y-%m')

    # Check if budget exists
    budget = Budget.query.filter_by(
        project_id=project_id,
        category_id=category_id,
        month_yyyymm=month
    ).first()

    amount = data.get('limit_amount')
    if isinstance(amount, float):
        amount = baht_to_satang(amount)

    if budget:
        # Update existing
        budget.limit_amount = amount
        budget.rollover_policy = data.get('rollover_policy', budget.rollover_policy)
    else:
        # Create new
        budget = Budget(
            project_id=project_id,
            category_id=category_id,
            month_yyyymm=month,
            limit_amount=amount,
            rollover_policy=data.get('rollover_policy', 'none')
        )
        db.session.add(budget)

    db.session.commit()

    return jsonify({
        'budget': budget.to_dict()
    })
