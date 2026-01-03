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
    """Get user's default project (first project they own)"""
    project = Project.query.filter_by(owner_user_id=user_id).first()
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
