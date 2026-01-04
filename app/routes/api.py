"""
Core API routes - CRUD operations for web and bot
"""
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app.services.transaction_service import TransactionService
from app.services.analytics_service import AnalyticsService
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


@bp.route('/projects/<project_id>/transactions/<transaction_id>', methods=['PUT'])
def update_transaction(project_id, transaction_id):
    """Update transaction"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        transaction = TransactionService.update_transaction(
            transaction_id=transaction_id,
            user_id=user.id,
            updates=data
        )

        return jsonify({
            'transaction': transaction.to_dict(include_category=True)
        })

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/transactions/<transaction_id>', methods=['DELETE'])
def delete_transaction(project_id, transaction_id):
    """Soft delete transaction"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        TransactionService.delete_transaction(
            transaction_id=transaction_id,
            user_id=user.id
        )

        return jsonify({
            'success': True,
            'message': 'ลบรายการเรียบร้อยแล้ว'
        })

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


# Recurring Transactions
@bp.route('/projects/<project_id>/recurring', methods=['POST'])
def create_recurring(project_id):
    """Create recurring transaction rule"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        from app.services.recurring_service import RecurringService

        recurring_rule = RecurringService.create_recurring_rule(
            project_id=project_id,
            user_id=user.id,
            type=data.get('type'),
            category_id=data.get('category_id'),
            amount=data.get('amount'),
            freq=data.get('freq'),
            start_date=data.get('start_date'),
            day_of_week=data.get('day_of_week'),
            day_of_month=data.get('day_of_month'),
            note=data.get('note'),
            member_id=data.get('member_id'),
            remind_days=data.get('remind_days', 0)
        )

        return jsonify({
            'recurring_rule': recurring_rule.to_dict()
        }), 201

    except (ValueError, PermissionError) as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


@bp.route('/projects/<project_id>/recurring', methods=['GET'])
def list_recurring(project_id):
    """List recurring transaction rules"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    try:
        from app.services.recurring_service import RecurringService

        recurring_rules = RecurringService.get_recurring_rules(
            project_id=project_id,
            user_id=user.id,
            active_only=active_only
        )

        return jsonify({
            'recurring_rules': [rule.to_dict() for rule in recurring_rules]
        })

    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/recurring/<recurring_id>', methods=['PUT'])
def update_recurring(project_id, recurring_id):
    """Update recurring transaction rule"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        from app.services.recurring_service import RecurringService

        recurring_rule = RecurringService.update_recurring_rule(
            recurring_id=recurring_id,
            user_id=user.id,
            updates=data
        )

        return jsonify({
            'recurring_rule': recurring_rule.to_dict()
        })

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/recurring/<recurring_id>', methods=['DELETE'])
def delete_recurring(project_id, recurring_id):
    """Delete (deactivate) recurring transaction rule"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.recurring_service import RecurringService

        RecurringService.delete_recurring_rule(
            recurring_id=recurring_id,
            user_id=user.id
        )

        return jsonify({
            'success': True,
            'message': 'ลบรายการประจำเรียบร้อยแล้ว'
        })

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/recurring/<recurring_id>/execute', methods=['POST'])
def execute_recurring(project_id, recurring_id):
    """Manually execute recurring transaction rule"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.recurring_service import RecurringService

        transaction = RecurringService.execute_recurring_rule(
            recurring_id=recurring_id,
            user_id=user.id
        )

        return jsonify({
            'transaction': transaction.to_dict(include_category=True),
            'message': 'บันทึกรายการสำเร็จ'
        }), 201

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


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


@bp.route('/projects/<project_id>/categories', methods=['POST'])
def create_category(project_id):
    """Create new category"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        from app.services.category_service import CategoryService

        category = CategoryService.create_category(
            project_id=project_id,
            user_id=user.id,
            name_th=data.get('name_th'),
            type=data.get('type'),
            icon=data.get('icon'),
            color=data.get('color')
        )

        return jsonify({
            'category': category.to_dict()
        }), 201

    except (ValueError, PermissionError) as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


@bp.route('/projects/<project_id>/categories/<category_id>', methods=['PUT'])
def update_category_route(project_id, category_id):
    """Update category"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        from app.services.category_service import CategoryService

        category = CategoryService.update_category(
            category_id=category_id,
            user_id=user.id,
            updates=data
        )

        return jsonify({
            'category': category.to_dict()
        })

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/categories/<category_id>', methods=['DELETE'])
def delete_category_route(project_id, category_id):
    """Soft delete category"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.category_service import CategoryService

        result = CategoryService.delete_category(
            category_id=category_id,
            user_id=user.id
        )

        return jsonify(result)

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


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


# Members & Invitations
@bp.route('/projects/<project_id>/members/invite', methods=['POST'])
def invite_member(project_id):
    """Send invitation to new member"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        from app.services.member_service import MemberService

        invite = MemberService.invite_member(
            project_id=project_id,
            inviter_user_id=user.id,
            invitee_email=data.get('email'),
            role=data.get('role', 'member')
        )

        return jsonify({
            'invite': {
                'id': invite.id,
                'email': invite.email,
                'role': invite.role,
                'token': invite.token,
                'invite_url': f'/invites/{invite.token}/accept'
            }
        }), 201

    except (ValueError, PermissionError) as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


@bp.route('/projects/<project_id>/members', methods=['GET'])
def list_members(project_id):
    """List project members"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.member_service import MemberService

        members = MemberService.get_project_members(
            project_id=project_id,
            user_id=user.id
        )

        return jsonify({
            'members': [{
                'id': m.id,
                'user_id': m.user_id,
                'role': m.role,
                'joined_at': m.joined_at.isoformat() if m.joined_at else None,
                'user': {
                    'display_name': m.user.display_name if m.user else None,
                    'email': m.user.email if m.user else None
                }
            } for m in members]
        })

    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/members/<member_id>', methods=['PUT'])
def update_member(project_id, member_id):
    """Update member role"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        from app.services.member_service import MemberService

        member = MemberService.update_member_role(
            member_id=member_id,
            user_id=user.id,
            new_role=data.get('role')
        )

        return jsonify({
            'member': {
                'id': member.id,
                'role': member.role
            }
        })

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/members/<member_id>', methods=['DELETE'])
def remove_member(project_id, member_id):
    """Remove member from project"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.member_service import MemberService

        MemberService.remove_member(
            member_id=member_id,
            user_id=user.id
        )

        return jsonify({
            'success': True,
            'message': 'ลบสมาชิกเรียบร้อยแล้ว'
        })

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/invites', methods=['GET'])
def list_invites(project_id):
    """List pending invitations"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.member_service import MemberService

        invites = MemberService.list_pending_invites(
            project_id=project_id,
            user_id=user.id
        )

        return jsonify({
            'invites': [{
                'id': inv.id,
                'email': inv.email,
                'role': inv.role,
                'created_at': inv.created_at.isoformat() if inv.created_at else None
            } for inv in invites]
        })

    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/projects/<project_id>/invites/<invite_id>', methods=['DELETE'])
def cancel_invite(project_id, invite_id):
    """Cancel pending invitation"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.member_service import MemberService

        MemberService.cancel_invite(
            invite_id=invite_id,
            user_id=user.id
        )

        return jsonify({
            'success': True,
            'message': 'ยกเลิกคำเชิญเรียบร้อยแล้ว'
        })

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except PermissionError as e:
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e)
            }
        }), 403


@bp.route('/invites/<token>/accept', methods=['POST'])
def accept_invite(token):
    """Accept invitation (public route)"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.member_service import MemberService

        member = MemberService.accept_invite(
            token=token,
            user_id=user.id
        )

        return jsonify({
            'member': {
                'id': member.id,
                'project_id': member.project_id,
                'role': member.role
            },
            'message': 'เข้าร่วมโปรเจกต์เรียบร้อยแล้ว'
        }), 201

    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@bp.route('/projects/<project_id>/analytics/summary', methods=['GET'])
def get_analytics_summary(project_id):
    """Get monthly summary (income, expense, balance)"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        # Get month parameter (default: current month)
        default_month = datetime.now().strftime('%Y-%m')
        month = request.args.get('month', default_month)

        # Validate month format
        if not re.match(r'^\d{4}-\d{2}$', month):
            return jsonify({
                "error": {"message": "Invalid month format. Use YYYY-MM"}
            }), 400

        # Get summary
        data = AnalyticsService.get_monthly_summary(project_id, month)

        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/by-category', methods=['GET'])
def get_analytics_by_category(project_id):
    """Get category breakdown with budget comparison"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        default_month = datetime.now().strftime('%Y-%m')
        month = request.args.get('month', default_month)
        type = request.args.get('type', 'expense')  # expense or income

        # Validate
        if type not in ['expense', 'income']:
            return jsonify({
                "error": {"message": "Type must be 'expense' or 'income'"}
            }), 400

        # Get breakdown
        data = AnalyticsService.get_category_breakdown(project_id, month, type)

        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/trends', methods=['GET'])
def get_analytics_trends(project_id):
    """Get income/expense trends for last N months"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        months = int(request.args.get('months', 6))

        # Validate
        if months < 1 or months > 12:
            return jsonify({
                "error": {"message": "Months must be between 1 and 12"}
            }), 400

        # Get trends
        data = AnalyticsService.get_trends(project_id, months)

        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500
