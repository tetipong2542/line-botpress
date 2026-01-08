"""
Core API routes - CRUD operations for web and bot
"""
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app.services.transaction_service import TransactionService
from app.services.analytics_service import AnalyticsService
from app.services.budget_service import BudgetService
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
    
    user = User.query.get(user_id)
    if not user:
        # User doesn't exist (e.g., database was reset), clear session
        session.clear()
        return None
    
    return user


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


@bp.route('/projects/<project_id>/recurring/<recurring_id>', methods=['GET'])
def get_recurring(project_id, recurring_id):
    """Get a single recurring transaction rule"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()

    try:
        from app.services.recurring_service import RecurringService

        recurring_rule = RecurringService.get_recurring_rule(
            recurring_id=recurring_id,
            user_id=user.id
        )

        return jsonify({
            'recurring_rule': recurring_rule.to_dict()
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
                    'email': m.user.email if m.user else None,
                    'picture_url': m.user.picture_url if m.user else None
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
    except Exception as e:
        import traceback
        print(f"ERROR in list_members: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'เกิดข้อผิดพลาด: {str(e)}'
            }
        }), 500


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
                'token': inv.token,
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
    except Exception as e:
        import traceback
        print(f"ERROR in list_invites: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'เกิดข้อผิดพลาด: {str(e)}'
            }
        }), 500


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


# ============================================================
# BUDGETS
# ============================================================

@bp.route('/projects/<project_id>/budgets', methods=['POST'])
def create_budget(project_id):
    """Create a budget for a category"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        data = request.get_json()

        # Required fields
        category_id = data.get('category_id')
        month_yyyymm = data.get('month')
        limit_amount = data.get('limit_amount')

        if not all([category_id, month_yyyymm, limit_amount]):
            return jsonify({
                "error": {"message": "category_id, month, and limit_amount are required"}
            }), 400

        # Optional
        rollover_policy = data.get('rollover_policy', 'none')

        # Create budget
        budget = BudgetService.create_budget(
            project_id=project_id,
            category_id=category_id,
            month_yyyymm=month_yyyymm,
            limit_amount=int(limit_amount),
            rollover_policy=rollover_policy
        )

        # Get enriched data
        budget_dict = BudgetService.get_budget(budget.id, project_id)

        return jsonify({"budget": budget_dict}), 201

    except ValueError as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 400
    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/budgets', methods=['GET'])
def get_budgets_list(project_id):
    """Get all budgets for a project, optionally filtered by month"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        month = request.args.get('month')  # Optional: "YYYY-MM"

        budgets = BudgetService.get_budgets(project_id, month)

        return jsonify({"budgets": budgets}), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/budgets/<budget_id>', methods=['GET'])
def get_single_budget(project_id, budget_id):
    """Get a single budget"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        budget = BudgetService.get_budget(budget_id, project_id)

        return jsonify({"budget": budget}), 200

    except ValueError as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 404
    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/budgets/<budget_id>', methods=['PUT'])
def update_single_budget(project_id, budget_id):
    """Update a budget"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        data = request.get_json()

        # Optional fields
        limit_amount = data.get('limit_amount')
        rollover_policy = data.get('rollover_policy')

        # Convert limit_amount to int if provided
        if limit_amount is not None:
            limit_amount = int(limit_amount)

        budget = BudgetService.update_budget(
            budget_id=budget_id,
            project_id=project_id,
            limit_amount=limit_amount,
            rollover_policy=rollover_policy
        )

        return jsonify({"budget": budget}), 200

    except ValueError as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 400
    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/budgets/<budget_id>', methods=['DELETE'])
def delete_single_budget(project_id, budget_id):
    """Delete a budget"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        BudgetService.delete_budget(budget_id, project_id)

        return jsonify({"message": "Budget deleted successfully"}), 200

    except ValueError as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 404
    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/budgets/summary', methods=['GET'])
def get_budget_summary_data(project_id):
    """Get budget summary for a month"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        # Get month from query params (default to current month)
        month = request.args.get('month')
        if not month:
            from datetime import datetime
            now = datetime.now()
            month = f"{now.year}-{str(now.month).zfill(2)}"

        summary = BudgetService.get_budget_summary(project_id, month)

        return jsonify({"summary": summary}), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================
# EXPORT
# ============================================================

@bp.route('/projects/<project_id>/export/transactions', methods=['GET'])
def export_transactions_csv(project_id):
    """Export transactions to CSV"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        import csv
        import io
        from flask import make_response

        # Get filters from query params
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category_id = request.args.get('category_id')
        tx_type = request.args.get('type')

        # Query transactions
        query = Transaction.query.filter_by(
            project_id=project_id,
            deleted_at=None
        )

        if start_date:
            query = query.filter(Transaction.occurred_at >= start_date)
        if end_date:
            query = query.filter(Transaction.occurred_at <= end_date)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if tx_type:
            query = query.filter_by(type=tx_type)

        transactions = query.order_by(Transaction.occurred_at.desc()).all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'วันที่',
            'เวลา',
            'ประเภท',
            'หมวดหมู่',
            'จำนวนเงิน (บาท)',
            'หมายเหตุ',
            'สร้างเมื่อ'
        ])

        # Write data
        for tx in transactions:
            writer.writerow([
                tx.occurred_at.strftime('%Y-%m-%d') if tx.occurred_at else '',
                tx.occurred_at.strftime('%H:%M:%S') if tx.occurred_at else '',
                'รายรับ' if tx.type == 'income' else 'รายจ่าย',
                tx.category.name_th if tx.category else '',
                f"{tx.amount / 100:.2f}",
                tx.note or '',
                tx.created_at.strftime('%Y-%m-%d %H:%M:%S') if tx.created_at else ''
            ])

        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'  # UTF-8 with BOM for Excel
        response.headers['Content-Disposition'] = f'attachment; filename=transactions_{project_id}.csv'

        return response

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================
# DASHBOARD WIDGETS
# ============================================================

@bp.route('/projects/<project_id>/dashboard/widgets', methods=['GET'])
def get_dashboard_widgets(project_id):
    """Get all dashboard widgets data in one call"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from datetime import datetime
        now = datetime.now()
        current_month = f"{now.year}-{str(now.month).zfill(2)}"
        
        # Calculate previous month
        prev_month_num = now.month - 1 if now.month > 1 else 12
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_month = f"{prev_year}-{str(prev_month_num).zfill(2)}"
        
        # Get data in parallel
        current_summary = AnalyticsService.get_monthly_summary(project_id, current_month)
        prev_summary = AnalyticsService.get_monthly_summary(project_id, prev_month)
        top_budgets = BudgetService.get_dashboard_budgets(project_id, current_month, limit=3)
        
        # Calculate comparison
        comparison = calculate_month_comparison(
            current_summary['summary'],
            prev_summary['summary']
        )
        
        # Get budget alerts
        alerts = generate_budget_alerts(top_budgets)
        
        return jsonify({
            'current_month': current_month,
            'previous_month': prev_month,
            'summary': current_summary['summary'],
            'comparison': comparison,
            'top_budgets': top_budgets,
            'alerts': alerts
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


def calculate_month_comparison(current, previous):
    """Calculate comparison between current and previous month"""
    
    def calc_change(current_val, prev_val):
        if prev_val == 0:
            if current_val == 0:
                return {'amount': 0, 'percentage': 0, 'direction': 'same'}
            else:
                return {'amount': current_val, 'percentage': 100, 'direction': 'up'}
        
        diff = current_val - prev_val
        pct = (diff / prev_val) * 100
        direction = 'up' if diff > 0 else ('down' if diff < 0 else 'same')
        
        return {
            'amount': diff,
            'percentage': abs(round(pct, 1)),
            'direction': direction
        }
    
    return {
        'income': calc_change(
            current['income']['total'],
            previous['income']['total']
        ),
        'expense': calc_change(
            current['expense']['total'],
            previous['expense']['total']
        ),
        'balance': calc_change(
            current['balance']['total'],
            previous['balance']['total']
        )
    }


def generate_budget_alerts(budgets):
    """Generate alert messages from budget data"""
    alerts = []
    
    for budget in budgets:
        usage = budget['usage_percentage']
        cat_name = budget.get('category', {}).get('name_th', 'หมวดหมู่')
        cat_icon = budget.get('category', {}).get('icon', '📁')
        
        if usage > 100:
            # Over budget
            over_amount = budget['spent'] - budget['limit_amount']
            alerts.append({
                'type': 'error',
                'icon': '🚨',
                'category': f"{cat_icon} {cat_name}",
                'message': f"เกินงบแล้ว {usage}% (เกิน ฿{abs(over_amount/100):.2f})",
                'budget_id': budget['id']
            })
        elif usage > 80:
            # Near limit
            remaining = budget['remaining']
            alerts.append({
                'type': 'warning',
                'icon': '⚠️',
                'category': f"{cat_icon} {cat_name}",
                'message': f"ใช้ไป {usage}% แล้ว (เหลือ ฿{remaining/100:.2f})",
                'budget_id': budget['id']
            })
        elif usage > 0:
            # Good progress
            alerts.append({
                'type': 'info',
                'icon': '✅',
                'category': f"{cat_icon} {cat_name}",
                'message': f"ใช้ไป {usage}% (ควบคุมได้ดี)",
                'budget_id': budget['id']
            })
    
    return alerts
