"""
Core API routes - CRUD operations for web and bot
"""
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app.services.transaction_service import TransactionService
from app.services.analytics_service import AnalyticsService
from app.services.budget_service import BudgetService
from app.services.insights_service import InsightsService
from app.services.prediction_service import PredictionService
from app.services.aggregation_service import AggregationService
from app.models.user import User
from app.models.project import Project, ProjectMember, ProjectInvite, ProjectSettings
from app.models.category import Category
from app.models.budget import Budget
from app.models.savings_goal import SavingsGoal
from app.models.analytics_cache import AnalyticsCache
from app.models.report_template import ReportTemplate
from app.models.scheduled_report import ScheduledReport
from app.models.share_link import ShareLink
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


@bp.route('/projects/<project_id>/categories/<category_id>/usage', methods=['GET'])
def get_category_usage(project_id, category_id):
    """Get usage statistics for a category"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.models.transaction import Transaction
        from app.models.recurring import RecurringRule
        from app.models.budget import Budget
        from app.models.savings_goal import SavingsGoal

        # Verify category exists and belongs to project
        category = Category.query.filter_by(
            id=category_id,
            project_id=project_id
        ).first()

        if not category:
            return jsonify({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Category not found'
                }
            }), 404

        # Count transactions
        transactions_count = Transaction.query.filter_by(
            project_id=project_id,
            category_id=category_id
        ).filter(Transaction.deleted_at.is_(None)).count()

        # Count recurring transactions
        recurring_count = RecurringRule.query.filter_by(
            project_id=project_id,
            category_id=category_id,
            is_active=True
        ).count()

        # Count budgets
        budgets_count = Budget.query.filter_by(
            project_id=project_id,
            category_id=category_id
        ).count()

        # Count goals (savings goals)
        goals_count = 0
        try:
            goals_count = SavingsGoal.query.filter_by(
                project_id=project_id,
                category_id=category_id,
                is_active=True
            ).count()
        except:
            pass  # SavingsGoal table might not have category_id

        return jsonify({
            'category': category.to_dict(),
            'usage': {
                'transactions': transactions_count,
                'recurring_transactions': recurring_count,
                'budgets': budgets_count,
                'goals': goals_count,
                'total': transactions_count + recurring_count + budgets_count + goals_count
            }
        })

    except Exception as e:
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


# Budgets - GET endpoint moved to BudgetService section below for enriched data


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


# User Link Code for Chatbot
@bp.route('/user/link-code', methods=['POST'])
def generate_link_code():
    """Generate link code for connecting Chatbot with LINE account"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    
    # Check if user already has botpress_user_id linked
    if user.botpress_user_id:
        return jsonify({
            'success': True,
            'already_linked': True,
            'message': 'บัญชีเชื่อมต่อกับ Chatbot แล้ว!'
        })
    
    import random
    import string
    import time
    from flask import current_app
    
    # Generate 6-character alphanumeric code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Store code in app-level cache (simple in-memory storage)
    if not hasattr(current_app, '_link_codes'):
        current_app._link_codes = {}
    
    # Clean up expired codes (older than 5 minutes)
    current_time = time.time()
    expired_codes = [c for c, data in current_app._link_codes.items() 
                     if current_time - data['created_at'] > 300]
    for c in expired_codes:
        del current_app._link_codes[c]
    
    # Store new code
    current_app._link_codes[code] = {
        'user_id': user.id,
        'created_at': current_time
    }
    
    return jsonify({
        'success': True,
        'code': code,
        'expires_in': 300,  # 5 minutes
        'message': f'รหัสเชื่อมต่อ: {code}\nพิมพ์ "เชื่อมต่อ {code}" ในแชท LINE'
    })


@bp.route('/user/link-status', methods=['GET'])
def get_link_status():
    """Check if user's account is linked with Chatbot"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    
    return jsonify({
        'is_linked': bool(user.botpress_user_id),
        'botpress_user_id': user.botpress_user_id
    })


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


@bp.route('/projects/<project_id>/analytics/amount-suggestions', methods=['GET'])
def get_amount_suggestions(project_id):
    """Get smart amount suggestions based on spending history"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        category_id = request.args.get('category_id')
        type = request.args.get('type', 'expense')
        
        # Validate type
        if type not in ['expense', 'income']:
            return jsonify({
                "error": {"message": "Type must be 'expense' or 'income'"}
            }), 400

        # Get suggestions
        data = AnalyticsService.get_amount_suggestions(project_id, category_id, type)

        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/notes/suggestions', methods=['GET'])
def get_notes_suggestions(project_id):
    """Get auto-complete suggestions for transaction notes"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        query = request.args.get('q', '').strip()
        category_id = request.args.get('category_id')
        limit = min(int(request.args.get('limit', 10)), 20)
        
        from sqlalchemy import func, distinct
        from app.models.transaction import Transaction
        
        # Base query for notes
        base_query = db.session.query(
            Transaction.note,
            func.count(Transaction.id).label('usage_count')
        ).filter(
            Transaction.project_id == project_id,
            Transaction.note.isnot(None),
            Transaction.note != '',
            Transaction.deleted_at.is_(None)
        )
        
        # Filter by category if provided
        if category_id:
            base_query = base_query.filter(Transaction.category_id == category_id)
        
        # Filter by search query
        if query:
            base_query = base_query.filter(Transaction.note.ilike(f'%{query}%'))
        
        # Group and order by usage
        suggestions = base_query.group_by(Transaction.note).order_by(
            func.count(Transaction.id).desc()
        ).limit(limit).all()
        
        return jsonify({
            "suggestions": [
                {
                    "note": s.note,
                    "usage_count": s.usage_count
                }
                for s in suggestions if s.note
            ]
        }), 200

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
        
        # Debug logging
        print(f"[CREATE_BUDGET] Received data: {data}")

        # Required fields
        category_id = data.get('category_id')
        month_yyyymm = data.get('month')
        limit_amount = data.get('limit_amount')

        if not all([category_id, month_yyyymm, limit_amount]):
            return jsonify({
                "error": {"message": "category_id, month, and limit_amount are required"}
            }), 400

        # CRITICAL: Validate category_id starts with correct prefix
        if not category_id.startswith('cat_'):
            print(f"[CREATE_BUDGET] ERROR: Invalid category_id format: {category_id}")
            return jsonify({
                "error": {"message": f"Invalid category_id format. Expected 'cat_...' but got '{category_id}'"}
            }), 400

        # Optional
        rollover_policy = data.get('rollover_policy', 'none')

        print(f"[CREATE_BUDGET] Creating budget: project={project_id}, category={category_id}, month={month_yyyymm}")

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
        
        print(f"[CREATE_BUDGET] Successfully created budget: {budget.id}")

        return jsonify({"budget": budget_dict}), 201

    except ValueError as e:
        print(f"[CREATE_BUDGET] ValueError: {str(e)}")
        return jsonify({
            "error": {"message": str(e)}
        }), 400
    except Exception as e:
        print(f"[CREATE_BUDGET] Exception: {str(e)}")
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
                'icon': cat_icon,  # ใช้ icon ของหมวดหมู่แทน emoji
                'category': cat_name,  # ชื่อหมวดหมู่อย่างเดียว
                'message': f"เกินงบแล้ว {usage}% (เกิน ฿{abs(over_amount/100):.2f})",
                'budget_id': budget['id']
            })
        elif usage > 80:
            # Near limit
            remaining = budget['remaining']
            alerts.append({
                'type': 'warning',
                'icon': cat_icon,
                'category': cat_name,
                'message': f"ใช้ไป {usage}% แล้ว (เหลือ ฿{remaining/100:.2f})",
                'budget_id': budget['id']
            })
        elif usage > 0:
            # Good progress
            alerts.append({
                'type': 'info',
                'icon': cat_icon,
                'category': cat_name,
                'message': f"ใช้ไป {usage}% (ควบคุมได้ดี)",
                'budget_id': budget['id']
            })
    
    return alerts


# ============================================================
# SMART INSIGHTS & ALERTS
# ============================================================

@bp.route('/projects/<project_id>/insights/alerts', methods=['GET'])
def get_insights_alerts(project_id):
    """Get budget alerts and warnings"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        month = request.args.get('month', None)
        alerts = InsightsService.get_budget_alerts(project_id, month)
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts)
        }), 200
    except Exception as e:
        return jsonify({
            'error': {'message': str(e)}
        }), 500


@bp.route('/projects/<project_id>/insights/trends', methods=['GET'])
def get_insights_trends(project_id):
    """Get spending trends and patterns"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        trends = InsightsService.get_spending_trends(project_id)
        
        return jsonify({
            'trends': trends
        }), 200
    except Exception as e:
        return jsonify({
            'error': {'message': str(e)}
        }), 500


@bp.route('/projects/<project_id>/insights/reminders', methods=['GET'])
def get_insights_reminders(project_id):
    """Get recurring transaction reminders"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        days_ahead = int(request.args.get('days_ahead', 7))
        reminders = InsightsService.get_recurring_reminders(project_id, days_ahead)
        
        return jsonify({
            'reminders': reminders,
            'count': len(reminders)
        }), 200
    except Exception as e:
        return jsonify({
            'error': {'message': str(e)}
        }), 500


@bp.route('/projects/<project_id>/insights/recommendations', methods=['GET'])
def get_insights_recommendations(project_id):
    """Get smart financial recommendations"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        month = request.args.get('month', None)
        recommendations = InsightsService.get_smart_recommendations(project_id, month)
        
        return jsonify({
            'recommendations': recommendations,
            'count': len(recommendations)
        }), 200
    except Exception as e:
        return jsonify({
            'error': {'message': str(e)}
        }), 500


@bp.route('/projects/<project_id>/insights/all', methods=['GET'])
def get_all_insights(project_id):
    """Get all insights in one call (for performance)"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    try:
        month = request.args.get('month', None)
        days_ahead = int(request.args.get('days_ahead', 7))
        
        alerts = InsightsService.get_budget_alerts(project_id, month)
        trends = InsightsService.get_spending_trends(project_id)
        reminders = InsightsService.get_recurring_reminders(project_id, days_ahead)
        recommendations = InsightsService.get_smart_recommendations(project_id, month)
        
        return jsonify({
            'alerts': alerts,
            'trends': trends,
            'reminders': reminders,
            'recommendations': recommendations
        }), 200
    except Exception as e:
        return jsonify({
            'error': {'message': str(e)}
        }), 500


# ===== NOTIFICATION ROUTES =====

@bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for current user"""
    from app.services.notification_service import NotificationService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 50))

    notifications = NotificationService.get_user_notifications(user.id, unread_only, limit)

    return jsonify({
        'notifications': notifications,
        'count': len(notifications)
    })


@bp.route('/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """Get count of unread notifications"""
    from app.services.notification_service import NotificationService
    from app.models.notification import Notification
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    count = Notification.query.filter_by(user_id=user.id, is_read=False).count()

    return jsonify({
        'unread_count': count
    })


@bp.route('/notifications/<notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    from app.services.notification_service import NotificationService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    success = NotificationService.mark_as_read(notification_id, user.id)

    if not success:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Notification not found'
            }
        }), 404

    return jsonify({
        'success': True,
        'message': 'Notification marked as read'
    })


@bp.route('/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    """Mark all notifications as read"""
    from app.services.notification_service import NotificationService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    count = NotificationService.mark_all_as_read(user.id)

    return jsonify({
        'success': True,
        'message': f'Marked {count} notifications as read',
        'count': count
    })


@bp.route('/notifications/preferences', methods=['GET'])
def get_notification_preferences():
    """Get user notification preferences"""
    from app.services.notification_service import NotificationService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    preference = NotificationService.get_or_create_preference(user.id)

    return jsonify({
        'preferences': preference.to_dict()
    })


@bp.route('/notifications/preferences', methods=['PUT'])
def update_notification_preferences():
    """Update user notification preferences"""
    from app.services.notification_service import NotificationService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    updated_preference = NotificationService.update_preference(user.id, data)

    return jsonify({
        'preferences': updated_preference,
        'message': 'Preferences updated successfully'
    })


@bp.route('/notifications/check-alerts', methods=['POST'])
def check_budget_alerts():
    """Check budget alerts manually (for testing)"""
    from app.services.notification_service import NotificationService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    project_id = request.json.get('project_id')
    month_yyyymm = request.json.get('month_yyyymm')

    if not project_id:
        # Get user's default project
        project = Project.query.filter_by(owner_user_id=user.id).first()
        if not project:
            return jsonify({
                'error': {
                    'code': 'NO_PROJECT',
                    'message': 'No project found'
                }
            }), 404
        project_id = project.id

    alerts = NotificationService.check_budget_alerts(project_id, month_yyyymm)

    return jsonify({
        'alerts_created': alerts,
        'count': len(alerts),
        'message': f'Created {len(alerts)} budget alerts'
    })


# ===== EXPORT ROUTES =====

@bp.route('/export/summary', methods=['GET'])
def get_export_summary():
    """Get summary of data available for export"""
    from app.services.export_service import ExportService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    
    # Get user's default project
    project = Project.query.filter_by(owner_user_id=user.id).first()
    if not project:
        return jsonify({
            'error': {
                'code': 'NO_PROJECT',
                'message': 'No project found'
            }
        }), 404

    summary = ExportService.get_export_summary(project.id)

    return jsonify({
        'project': {
            'id': project.id,
            'name': project.name
        },
        'summary': summary
    })


@bp.route('/export/csv', methods=['GET'])
def export_csv():
    """Export transactions to CSV"""
    from app.services.export_service import ExportService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    
    # Get user's default project
    project = Project.query.filter_by(owner_user_id=user.id).first()
    if not project:
        return jsonify({
            'error': {
                'code': 'NO_PROJECT',
                'message': 'No project found'
            }
        }), 404

    # Get month filter
    month_yyyymm = request.args.get('month')
    
    # Export to CSV
    csv_data = ExportService.export_to_csv(project.id, month_yyyymm)
    filename = ExportService.generate_filename(project.name, 'csv', month_yyyymm)

    return ExportService.create_csv_response(csv_data, filename)


@bp.route('/export/json', methods=['GET'])
def export_json():
    """Export all project data to JSON"""
    from app.services.export_service import ExportService
    
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    
    # Get user's default project
    project = Project.query.filter_by(owner_user_id=user.id).first()
    if not project:
        return jsonify({
            'error': {
                'code': 'NO_PROJECT',
                'message': 'No project found'
            }
        }), 404

    # Get month filter
    month_yyyymm = request.args.get('month')
    
    # Export to JSON
    json_data = ExportService.export_to_json(project.id, month_yyyymm)
    if not json_data:
        return jsonify({
            'error': {
                'code': 'EXPORT_FAILED',
                'message': 'Failed to export data'
            }
        }), 500
    
    filename = ExportService.generate_filename(project.name, 'json', month_yyyymm)

    return ExportService.create_json_response(json_data, filename)


# ============================================================================
# ADVANCED ANALYTICS ENDPOINTS
# ============================================================================

@bp.route('/projects/<project_id>/analytics/daily-averages', methods=['GET'])
def get_daily_averages(project_id):
    """Get daily average spending/income"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            from datetime import timedelta
            end_date = datetime.now()
            start_date = (end_date - timedelta(days=30)).strftime('%Y-%m-%d')

        data = AnalyticsService.get_daily_averages(project_id, start_date, end_date)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/spending-velocity', methods=['GET'])
def get_spending_velocity(project_id):
    """Get spending velocity"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        days = int(request.args.get('days', 30))
        data = AnalyticsService.get_spending_velocity(project_id, days)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/savings-rate', methods=['GET'])
def get_savings_rate(project_id):
    """Get savings rate"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        months = int(request.args.get('months', 6))
        data = AnalyticsService.get_savings_rate(project_id, months)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/financial-health', methods=['GET'])
def get_financial_health(project_id):
    """Get financial health score"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        months = int(request.args.get('months', 3))
        data = AnalyticsService.get_financial_health_score(project_id, months)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/category-growth', methods=['GET'])
def get_category_growth(project_id):
    """Get category growth rates"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        months = int(request.args.get('months', 6))
        data = AnalyticsService.get_category_growth_rates(project_id, months)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/seasonal-patterns', methods=['GET'])
def get_seasonal_patterns(project_id):
    """Get seasonal spending patterns"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        years = int(request.args.get('years', 2))
        data = AnalyticsService.get_seasonal_patterns(project_id, years)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/heatmap', methods=['GET'])
def get_heatmap_data(project_id):
    """Get spending heatmap data"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        days = int(request.args.get('days', 30))
        data = AnalyticsService.get_heatmap_data(project_id, days)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/scatter', methods=['GET'])
def get_scatter_data(project_id):
    """Get scatter plot data"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        days = int(request.args.get('days', 30))
        data = AnalyticsService.get_scatter_data(project_id, days)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/analytics/compare', methods=['GET'])
def compare_periods(project_id):
    """Compare two date ranges"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        period1_start = request.args.get('period1_start')
        period1_end = request.args.get('period1_end')
        period2_start = request.args.get('period2_start')
        period2_end = request.args.get('period2_end')

        if not all([period1_start, period1_end, period2_start, period2_end]):
            return jsonify({
                "error": {"message": "All period parameters are required"}
            }), 400

        data = AnalyticsService.compare_periods(
            project_id, period1_start, period1_end,
            period2_start, period2_end
        )
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@bp.route('/projects/<project_id>/predictions/forecast', methods=['GET'])
def get_spending_forecast(project_id):
    """Get spending forecast"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        days = int(request.args.get('days', 30))
        data = PredictionService.get_spending_forecast(project_id, days)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/predictions/budget-projection', methods=['GET'])
def get_budget_projection(project_id):
    """Get budget projection"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        month = request.args.get('month')
        if not month:
            month = datetime.now().strftime('%Y-%m')

        data = PredictionService.get_budget_projection(project_id, month)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/predictions/savings-goal', methods=['GET'])
def get_savings_goal_tracking(project_id):
    """Get savings goal tracking"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        data = PredictionService.get_savings_goal_tracking(project_id)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/predictions/recurring', methods=['GET'])
def get_recurring_predictions(project_id):
    """Get recurring expense predictions"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        data = PredictionService.get_recurring_predictions(project_id)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/predictions/income-trend', methods=['GET'])
def get_income_trend(project_id):
    """Get income trend projection"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        months = int(request.args.get('months', 6))
        data = PredictionService.get_income_trend_projection(project_id, months)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================================
# SAVINGS GOALS ENDPOINTS
# ============================================================================

@bp.route('/projects/<project_id>/savings-goals', methods=['GET'])
def get_savings_goals(project_id):
    """Get all savings goals"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        goals = SavingsGoal.get_active_goals(project_id)
        return jsonify({
            'savings_goals': [g.to_dict() for g in goals]
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/savings-goals', methods=['POST'])
def create_savings_goal(project_id):
    """Create new savings goal"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        from datetime import datetime, timedelta

        # คำนวณ target_date จาก months หรือใช้ค่าที่ส่งมา
        target_date = None
        if data.get('target_date'):
            target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        elif data.get('months'):
            target_date = (datetime.utcnow() + timedelta(days=int(data['months']) * 30)).date()

        goal = SavingsGoal(
            project_id=project_id,
            name=data.get('name'),
            target_amount=int(data.get('target_amount')),  # frontend ส่ง satang มาแล้ว
            target_date=target_date,
            category_id=data.get('category_id'),
            is_active=True
        )
        db.session.add(goal)
        db.session.commit()

        return jsonify({
            'goal': goal.to_dict()
        }), 201

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 400


@bp.route('/projects/<project_id>/savings-goals/<goal_id>', methods=['PUT'])
def update_savings_goal(project_id, goal_id):
    """Update savings goal"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    user = get_current_user()
    data = request.json

    try:
        from datetime import datetime, timedelta
        
        goal = SavingsGoal.get_goal(goal_id, project_id)
        if not goal:
            return jsonify({
                "error": {"message": "Goal not found"}
            }), 404

        if 'name' in data:
            goal.name = data['name']
        if 'target_amount' in data:
            goal.target_amount = int(data['target_amount'])  # frontend ส่ง satang มาแล้ว
        if 'target_date' in data and data['target_date']:
            goal.target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        elif 'months' in data:
            # คำนวณ target_date จากวันนี้บวก months
            goal.target_date = (datetime.utcnow() + timedelta(days=int(data['months']) * 30)).date()
        if 'category_id' in data:
            goal.category_id = data['category_id']
        if 'is_active' in data:
            goal.is_active = data['is_active']

        goal.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'goal': goal.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 400


@bp.route('/projects/<project_id>/savings-goals/<goal_id>', methods=['DELETE'])
def delete_savings_goal(project_id, goal_id):
    """Delete savings goal"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        goal = SavingsGoal.get_goal(goal_id, project_id)
        if not goal:
            return jsonify({
                "error": {"message": "Goal not found"}
            }), 404

        goal.is_active = False
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'ลบเป้าหมายการออมเงินเรียบร้อยแล้ว'
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/savings-goals/<goal_id>/contribute', methods=['POST'])
def contribute_to_goal(project_id, goal_id):
    """Contribute money to savings goal"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data = request.json
    amount = data.get('amount', 0)

    try:
        goal = SavingsGoal.get_goal(goal_id, project_id)
        if not goal:
            return jsonify({
                "error": {"message": "Goal not found"}
            }), 404

        goal.current_amount = (goal.current_amount or 0) + amount
        db.session.commit()

        return jsonify({
            'success': True,
            'goal': goal.to_dict(),
            'message': f'เพิ่มเงินออม ฿{amount/100:,.0f} สำเร็จ'
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/savings-goals/<goal_id>/withdraw', methods=['POST'])
def withdraw_from_goal(project_id, goal_id):
    """Withdraw money from savings goal"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    data = request.json
    amount = data.get('amount', 0)

    try:
        goal = SavingsGoal.get_goal(goal_id, project_id)
        if not goal:
            return jsonify({
                "error": {"message": "Goal not found"}
            }), 404

        if amount > goal.current_amount:
            return jsonify({
                "error": {"message": f"ยอดเงินไม่พอ มี ฿{goal.current_amount/100:,.0f}"}
            }), 400

        goal.current_amount = goal.current_amount - amount
        db.session.commit()

        return jsonify({
            'success': True,
            'goal': goal.to_dict(),
            'message': f'ถอนเงิน ฿{amount/100:,.0f} สำเร็จ'
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================================
# AGGREGATION ENDPOINTS
# ============================================================================

@bp.route('/projects/<project_id>/aggregations/weekly', methods=['GET'])
def get_weekly_aggregations(project_id):
    """Get weekly summaries"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        weeks = int(request.args.get('weeks', 12))
        data = AggregationService.get_weekly_summaries(project_id, weeks)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/aggregations/quarterly', methods=['GET'])
def get_quarterly_aggregations(project_id):
    """Get quarterly summaries"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        quarters = int(request.args.get('quarters', 4))
        data = AggregationService.get_quarterly_summaries(project_id, quarters)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/aggregations/yearly', methods=['GET'])
def get_yearly_aggregations(project_id):
    """Get yearly summaries"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        years = int(request.args.get('years', 3))
        data = AggregationService.get_yearly_summaries(project_id, years)
        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/aggregations/custom', methods=['POST'])
def get_custom_aggregation(project_id):
    """Get custom period aggregation"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        data = request.json
        period_name = data.get('period_name', 'Custom Period')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not start_date or not end_date:
            return jsonify({
                "error": {"message": "start_date and end_date are required"}
            }), 400

        result = AggregationService.get_custom_period_aggregation(
            project_id, period_name, start_date, end_date
        )
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================
# QUICK TEMPLATES
# ============================================================

@bp.route('/projects/<project_id>/quick-templates', methods=['GET'])
def get_quick_templates(project_id):
    """Get quick templates for a project"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.models.quick_template import QuickTemplate
        
        include_suggestions = request.args.get('include_suggestions', 'false').lower() == 'true'
        
        # Get active templates
        templates = QuickTemplate.get_active_templates(project_id, limit=10)
        
        result = {
            "templates": [t.to_dict() for t in templates]
        }
        
        # Include AI-generated suggestions if requested
        if include_suggestions:
            result["suggestions"] = QuickTemplate.generate_from_frequent_transactions(project_id, limit=5)
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/quick-templates', methods=['POST'])
def create_quick_template(project_id):
    """Create a quick template"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.models.quick_template import QuickTemplate
        from app.utils.helpers import baht_to_satang
        
        user = get_current_user()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({
                "error": {"message": "Template name is required"}
            }), 400
        
        if not data.get('amount'):
            return jsonify({
                "error": {"message": "Amount is required"}
            }), 400
        
        # Convert amount to satang
        amount = baht_to_satang(float(data['amount']))
        
        template = QuickTemplate(
            project_id=project_id,
            user_id=user.id,
            name=data.get('name'),
            icon=data.get('icon', '📝'),
            category_id=data.get('category_id'),
            amount=amount,
            note=data.get('note'),
            type=data.get('type', 'expense'),
            is_auto_generated=data.get('is_auto_generated', False)
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            "template": template.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/quick-templates/<template_id>', methods=['PUT'])
def update_quick_template(project_id, template_id):
    """Update a quick template"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.models.quick_template import QuickTemplate
        from app.utils.helpers import baht_to_satang
        
        template = QuickTemplate.query.filter_by(
            id=template_id,
            project_id=project_id
        ).first()
        
        if not template:
            return jsonify({
                "error": {"message": "Template not found"}
            }), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            template.name = data['name']
        if 'icon' in data:
            template.icon = data['icon']
        if 'category_id' in data:
            template.category_id = data['category_id']
        if 'amount' in data:
            template.amount = baht_to_satang(float(data['amount']))
        if 'note' in data:
            template.note = data['note']
        if 'type' in data:
            template.type = data['type']
        if 'sort_order' in data:
            template.sort_order = data['sort_order']
        if 'is_active' in data:
            template.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            "template": template.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/quick-templates/<template_id>', methods=['DELETE'])
def delete_quick_template(project_id, template_id):
    """Delete (deactivate) a quick template"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.models.quick_template import QuickTemplate
        
        template = QuickTemplate.query.filter_by(
            id=template_id,
            project_id=project_id
        ).first()
        
        if not template:
            return jsonify({
                "error": {"message": "Template not found"}
            }), 404
        
        # Soft delete by marking inactive
        template.is_active = False
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "ลบ template เรียบร้อยแล้ว"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/quick-templates/<template_id>/use', methods=['POST'])
def use_quick_template(project_id, template_id):
    """Use a quick template to create a transaction"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.models.quick_template import QuickTemplate
        from datetime import datetime
        
        user = get_current_user()
        
        template = QuickTemplate.query.filter_by(
            id=template_id,
            project_id=project_id,
            is_active=True
        ).first()
        
        if not template:
            return jsonify({
                "error": {"message": "Template not found"}
            }), 404
        
        # Get optional overrides from request
        data = request.get_json() or {}
        
        # Create transaction using template values (with optional overrides)
        transaction = TransactionService.create_transaction(
            project_id=project_id,
            user_id=user.id,
            type=data.get('type', template.type),
            category_id=data.get('category_id', template.category_id),
            amount=data.get('amount', template.amount / 100),  # Convert satang to baht for service
            occurred_at=data.get('occurred_at', datetime.now().isoformat()),
            note=data.get('note', template.note)
        )
        
        # Increment template usage
        template.increment_usage()
        db.session.commit()
        
        return jsonify({
            "transaction": transaction.to_dict(include_category=True),
            "message": f"บันทึกจาก {template.name} สำเร็จ"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================
# AI-POWERED FEATURES (Bundle B)
# ============================================================

@bp.route('/projects/<project_id>/ai/suggest-category', methods=['POST'])
def ai_suggest_category(project_id):
    """Smart Auto-Categorization - Suggest category for transaction"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.services.gemini_nlp_service import gemini_nlp
        from app.models.category import Category
        from app.models.transaction import Transaction
        
        data = request.get_json()
        note = data.get('note', '')
        type = data.get('type', 'expense')
        
        if not note:
            return jsonify({
                "error": {"message": "Note is required"}
            }), 400
        
        # Get categories for this project
        categories = Category.query.filter_by(
            project_id=project_id,
            type=type,
            is_active=True
        ).all()
        
        cat_list = [c.to_dict() for c in categories]
        
        # Get history for learning (last 50 similar transactions)
        history = []
        similar_transactions = Transaction.query.filter(
            Transaction.project_id == project_id,
            Transaction.type == type,
            Transaction.note.isnot(None),
            Transaction.deleted_at.is_(None)
        ).order_by(Transaction.created_at.desc()).limit(50).all()
        
        for t in similar_transactions:
            if t.category:
                history.append({
                    'note': t.note,
                    'category_name': t.category.name_th,
                    'category_id': t.category_id
                })
        
        # Get AI suggestion
        suggestion = gemini_nlp.suggest_category(note, cat_list, history)
        
        return jsonify({
            "suggestion": suggestion
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/ai/financial-coach', methods=['GET'])
def ai_financial_coach(project_id):
    """AI Financial Coach - Get personalized insights and recommendations"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.services.gemini_nlp_service import gemini_nlp
        from app.services.analytics_service import AnalyticsService
        from app.models.savings_goal import SavingsGoal
        from datetime import datetime
        
        month = request.args.get('month', datetime.now().strftime('%Y-%m'))
        
        # Get monthly summary
        summary = AnalyticsService.get_monthly_summary(project_id, month)
        
        # Get category breakdown
        category_data = AnalyticsService.get_category_breakdown(project_id, month, 'expense')
        spending_data = category_data.get('categories', [])
        
        # Get goals progress
        goals = SavingsGoal.query.filter_by(
            project_id=project_id,
            is_active=True
        ).all()
        
        goals_data = []
        for g in goals:
            progress_pct = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
            goals_data.append({
                'name': g.name,
                'current': g.current_amount / 100,  # satang to baht
                'target': g.target_amount / 100,
                'progress': progress_pct
            })
        
        # Get AI insights
        insights = gemini_nlp.generate_financial_insights(
            summary.get('summary', {}),
            spending_data,
            goals_data
        )
        
        return jsonify({
            "coach": insights,
            "summary": summary.get('summary', {}),
            "month": month
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/projects/<project_id>/ai/weekly-summary', methods=['GET'])
def ai_weekly_summary(project_id):
    """AI Weekly Summary - Get weekly financial summary with insights"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        from app.services.gemini_nlp_service import gemini_nlp
        from app.models.transaction import Transaction
        from datetime import datetime, timedelta
        from sqlalchemy import func
        from app.utils.helpers import satang_to_baht
        
        # Get date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get transactions for the week
        transactions = Transaction.query.filter(
            Transaction.project_id == project_id,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
            Transaction.deleted_at.is_(None)
        ).all()
        
        # Calculate totals
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expense = sum(t.amount for t in transactions if t.type == 'expense')
        
        # Get daily breakdown
        daily_data = {}
        for t in transactions:
            day_key = t.occurred_at.strftime('%Y-%m-%d')
            if day_key not in daily_data:
                daily_data[day_key] = {'income': 0, 'expense': 0}
            if t.type == 'income':
                daily_data[day_key]['income'] += t.amount
            else:
                daily_data[day_key]['expense'] += t.amount
        
        # Get top spending categories
        category_totals = {}
        for t in transactions:
            if t.type == 'expense' and t.category:
                cat_name = t.category.name_th
                category_totals[cat_name] = category_totals.get(cat_name, 0) + t.amount
        
        top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Format data
        summary_data = {
            'income': {'formatted': satang_to_baht(total_income)},
            'expense': {'formatted': satang_to_baht(total_expense)},
            'balance': {'formatted': satang_to_baht(total_income - total_expense)}
        }
        
        spending_data = [
            {
                'category_name': cat,
                'formatted': satang_to_baht(amount),
                'percentage': (amount / total_expense * 100) if total_expense > 0 else 0
            }
            for cat, amount in top_categories
        ]
        
        # Get AI insights
        insights = gemini_nlp.generate_financial_insights(summary_data, spending_data)
        
        # Add weekly specific data
        insights['period'] = {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'days': 7
        }
        insights['totals'] = {
            'income': satang_to_baht(total_income),
            'expense': satang_to_baht(total_expense),
            'balance': satang_to_baht(total_income - total_expense),
            'transaction_count': len(transactions)
        }
        insights['daily_breakdown'] = [
            {
                'date': day,
                'income': satang_to_baht(data['income']),
                'expense': satang_to_baht(data['expense'])
            }
            for day, data in sorted(daily_data.items())
        ]
        
        return jsonify({
            "weekly_summary": insights
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================
# GEMINI API KEY MANAGEMENT
# ============================================================

@bp.route('/user/gemini-key', methods=['GET'])
def get_gemini_key_status():
    """Check if user has a custom Gemini API key"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        user = get_current_user()
        
        # Check if user has a custom key stored
        # We store encrypted key in user settings or a separate table
        has_key = bool(user.gemini_api_key if hasattr(user, 'gemini_api_key') else None)
        key_suffix = ''
        
        if has_key and user.gemini_api_key:
            # Show last 4 characters
            key_suffix = '...' + user.gemini_api_key[-4:]
        
        return jsonify({
            "has_key": has_key,
            "key_suffix": key_suffix
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/user/gemini-key', methods=['POST'])
def save_gemini_key():
    """Save user's custom Gemini API key"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        user = get_current_user()
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                "error": {"message": "API Key is required"}
            }), 400
        
        # Validate key format (starts with AIza)
        if not api_key.startswith('AIza'):
            return jsonify({
                "error": {"message": "Invalid API Key format. Gemini keys start with 'AIza'"}
            }), 400
        
        # Save to user
        user.gemini_api_key = api_key
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "API Key saved successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/user/gemini-key', methods=['DELETE'])
def delete_gemini_key():
    """Remove user's custom Gemini API key"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        user = get_current_user()
        user.gemini_api_key = None
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "API Key removed"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/user/gemini-key/test', methods=['POST'])
def test_gemini_key():
    """Test if a Gemini API key is valid"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API Key is required"
            }), 400
        
        # Test the key by making a simple API call
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Simple test prompt (English to avoid encoding issues)
            response = model.generate_content(
                "Reply with only the word 'hello'",
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 10,
                }
            )
            
            if response and response.text:
                return jsonify({
                    "success": True,
                    "message": "API Key is valid"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "No response from API"
                }), 200
                
        except Exception as api_error:
            error_msg = str(api_error)
            if 'API_KEY_INVALID' in error_msg or 'invalid' in error_msg.lower():
                return jsonify({
                    "success": False,
                    "error": "API Key invalid"
                }), 200
            elif 'quota' in error_msg.lower():
                return jsonify({
                    "success": False,
                    "error": "API Key quota exceeded"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": f"Error: {error_msg[:100]}"
                }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/user/ai-status', methods=['GET'])
def get_ai_status():
    """Get AI availability status"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        import os
        user = get_current_user()
        
        # Check user's custom keys (OpenRouter first as premium, then Gemini)
        openrouter_key = getattr(user, 'openrouter_api_key', None)
        gemini_key = getattr(user, 'gemini_api_key', None)
        system_key = os.environ.get('GEMINI_API_KEY')
        
        if openrouter_key:
            return jsonify({
                "is_available": True,
                "source": "openrouter",
                "message": "ใช้ OpenRouter API Key ของคุณ"
            }), 200
        elif gemini_key:
            return jsonify({
                "is_available": True,
                "source": "gemini",
                "message": "ใช้ Gemini API Key ของคุณ"
            }), 200
        elif system_key:
            return jsonify({
                "is_available": True,
                "source": "system",
                "message": "ใช้ค่าเริ่มต้นของระบบ"
            }), 200
        else:
            return jsonify({
                "is_available": False,
                "source": None,
                "message": "ยังไม่มี API Key"
            }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================
# UNIFIED AI KEYS ENDPOINT
# ============================================================

@bp.route('/user/ai-keys', methods=['GET'])
def get_all_ai_keys():
    """Get all AI keys status with masked values"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        user = get_current_user()
        
        def mask_key(key):
            if not key:
                return None
            # Show first 4 and last 4 characters
            if len(key) > 12:
                return key[:4] + '••••••••••' + key[-4:]
            return '••••••••••'
        
        result = {
            "gemini": {
                "has_key": bool(getattr(user, 'gemini_api_key', None)),
                "masked_key": mask_key(getattr(user, 'gemini_api_key', None))
            },
            "openrouter": {
                "has_key": bool(getattr(user, 'openrouter_api_key', None)),
                "masked_key": mask_key(getattr(user, 'openrouter_api_key', None))
            }
        }
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


# ============================================================
# OPENROUTER API KEY MANAGEMENT
# ============================================================

@bp.route('/user/openrouter-key', methods=['GET'])
def get_openrouter_key_status():
    """Check if user has a custom OpenRouter API key"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        user = get_current_user()
        
        has_key = bool(getattr(user, 'openrouter_api_key', None))
        key_suffix = ''
        
        if has_key and user.openrouter_api_key:
            key_suffix = '...' + user.openrouter_api_key[-4:]
        
        return jsonify({
            "has_key": has_key,
            "key_suffix": key_suffix
        }), 200

    except Exception as e:
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/user/openrouter-key', methods=['POST'])
def save_openrouter_key():
    """Save user's custom OpenRouter API key"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        user = get_current_user()
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                "error": {"message": "API Key is required"}
            }), 400
        
        # Validate key format (starts with sk-or-)
        if not api_key.startswith('sk-or-'):
            return jsonify({
                "error": {"message": "Invalid API Key format. OpenRouter keys start with 'sk-or-'"}
            }), 400
        
        # Save to user
        user.openrouter_api_key = api_key
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "API Key saved successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/user/openrouter-key', methods=['DELETE'])
def delete_openrouter_key():
    """Remove user's custom OpenRouter API key"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        user = get_current_user()
        user.openrouter_api_key = None
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "API Key removed"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": str(e)}
        }), 500


@bp.route('/user/openrouter-key/test', methods=['POST'])
def test_openrouter_key():
    """Test if an OpenRouter API key is valid"""
    auth_error = require_auth()
    if auth_error:
        return auth_error

    try:
        import requests
        
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API Key is required"
            }), 400
        
        # Test the key by making a simple API call
        try:
            import urllib.request
            import urllib.error
            import json as json_lib
            
            # Use urllib to avoid encoding issues with requests library
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            payload = json_lib.dumps({
                "model": "google/gemini-flash-1.5",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=payload, method='POST')
            req.add_header('Authorization', f'Bearer {api_key}')
            req.add_header('Content-Type', 'application/json')
            req.add_header('HTTP-Referer', 'https://promptjod.app')
            
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        return jsonify({
                            "success": True,
                            "message": "API Key is valid"
                        }), 200
                    else:
                        return jsonify({
                            "success": False,
                            "error": f"HTTP Error: {resp.status}"
                        }), 200
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    return jsonify({
                        "success": False,
                        "error": "API Key invalid"
                    }), 200
                elif e.code == 402:
                    return jsonify({
                        "success": False,
                        "error": "No credits"
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": f"HTTP {e.code}"
                    }), 200
            except urllib.error.URLError as e:
                return jsonify({
                    "success": False,
                    "error": f"Connection error: {str(e.reason)[:50]}"
                }), 200
                
        except Exception as api_error:
            return jsonify({
                "success": False,
                "error": f"Error: {str(api_error)[:100]}"
            }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
