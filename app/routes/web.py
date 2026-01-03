"""
Web routes - HTML pages
"""
from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint('web', __name__)


@bp.route('/')
def index():
    """Home page"""
    if session.get('user_id'):
        return redirect('/app')
    return render_template('login.html')


@bp.route('/app')
def app():
    """App page (requires login)"""
    if not session.get('user_id'):
        return redirect('/')
    return render_template('app.html')
