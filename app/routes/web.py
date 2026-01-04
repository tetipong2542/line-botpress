"""
Web routes - HTML pages
"""
from flask import Blueprint, render_template, session, redirect, url_for
from app.models.user import User
from app.models.project import Project

bp = Blueprint('web', __name__)


def require_login(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/')
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


def get_user_project(user_id):
    """Get user's default project (first project they own)

    Auto-creates project if user doesn't have one
    """
    from app import db
    from app.models.category import Category
    from app.utils.helpers import generate_id

    project = Project.query.filter_by(owner_user_id=user_id).first()

    # Auto-create project if user doesn't have one
    if not project:
        user = User.query.get(user_id)

        # Create default project
        project = Project(
            name=f"บัญชี {user.display_name}",
            owner_user_id=user_id
        )
        project.id = generate_id('prj')
        db.session.add(project)
        db.session.commit()

        # Create default categories
        default_categories = [
            {'type': 'expense', 'name_th': 'อาหารและเครื่องดื่ม', 'icon': 'utensils', 'color': '#EF4444'},
            {'type': 'expense', 'name_th': 'ค่าเดินทาง', 'icon': 'car', 'color': '#F59E0B'},
            {'type': 'expense', 'name_th': 'ช้อปปิ้ง', 'icon': 'shopping-bag', 'color': '#EC4899'},
            {'type': 'expense', 'name_th': 'ความบันเทิง', 'icon': 'tv', 'color': '#8B5CF6'},
            {'type': 'expense', 'name_th': 'ค่าสาธารณูปโภค', 'icon': 'lightbulb', 'color': '#10B981'},
            {'type': 'expense', 'name_th': 'สุขภาพ', 'icon': 'heart-pulse', 'color': '#06B6D4'},
            {'type': 'income', 'name_th': 'เงินเดือน', 'icon': 'dollar-sign', 'color': '#10B981'},
            {'type': 'income', 'name_th': 'รายได้เสริม', 'icon': 'trending-up', 'color': '#3B82F6'},
            {'type': 'income', 'name_th': 'ของขวัญ', 'icon': 'gift', 'color': '#EC4899'},
        ]

        for idx, cat_data in enumerate(default_categories):
            category = Category(
                project_id=project.id,
                type=cat_data['type'],
                name_th=cat_data['name_th'],
                icon=cat_data['icon'],
                color=cat_data['color'],
                sort_order=idx + 1
            )
            db.session.add(category)

        db.session.commit()

    return project


@bp.route('/')
def index():
    """Home page"""
    if session.get('user_id'):
        return redirect('/app')
    return render_template('login.html')


@bp.route('/app')
@require_login
def app():
    """Dashboard page"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    project = get_user_project(user_id)
    return render_template('dashboard.html', user=user, project=project)


@bp.route('/transactions/new')
@require_login
def new_transaction():
    """New transaction form"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return render_template('transaction_form.html', user=user)


@bp.route('/categories')
@require_login
def categories():
    """Categories management page"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    project = get_user_project(user_id)
    return render_template('categories.html', user=user, project=project)


@bp.route('/recurring')
@require_login
def recurring():
    """Recurring transactions page"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    project = get_user_project(user_id)
    return render_template('recurring.html', user=user, project=project)


@bp.route('/analytics')
@require_login
def analytics():
    """Analytics and reports page"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    project = get_user_project(user_id)
    return render_template('analytics.html', user=user, project=project)


@bp.route('/members')
@require_login
def members():
    """Members management page"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    project = get_user_project(user_id)
    return render_template('members.html', user=user, project=project)


@bp.route('/profile')
@require_login
def profile():
    """User profile page"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return render_template('profile.html', user=user)


@bp.route('/invites/<token>/accept')
@require_login
def invite_accept_page(token):
    """Page to accept invitation"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return render_template('invite_accept.html', token=token, user=user)
