"""
Authentication routes - LINE Login OAuth2
"""
import secrets
import requests
from flask import Blueprint, redirect, request, session, current_app, jsonify, url_for
from app import db
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/line/login')
def line_login():
    """
    Initiate LINE Login OAuth2 flow

    Query params:
        redirect: URL to redirect after successful login (default: /app)
    """
    # Generate and store state for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # Store redirect URL
    redirect_after = request.args.get('redirect', '/app')
    session['redirect_after_login'] = redirect_after

    # LINE OAuth2 authorize URL
    authorize_url = 'https://access.line.me/oauth2/v2.1/authorize'

    params = {
        'response_type': 'code',
        'client_id': current_app.config['LINE_CHANNEL_ID'],
        'redirect_uri': current_app.config['LINE_REDIRECT_URI'],
        'state': state,
        'scope': 'profile openid email'
    }

    # Build authorization URL
    auth_url = f"{authorize_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    return redirect(auth_url)


@bp.route('/line/callback')
def line_callback():
    """
    LINE Login OAuth2 callback

    Query params:
        code: Authorization code from LINE
        state: CSRF state token
    """
    # Verify state (CSRF protection)
    state = request.args.get('state')
    if not state or state != session.get('oauth_state'):
        return jsonify({
            'error': {
                'code': 'INVALID_STATE',
                'message': 'Invalid OAuth state'
            }
        }), 400

    # Get authorization code
    code = request.args.get('code')
    if not code:
        return jsonify({
            'error': {
                'code': 'MISSING_CODE',
                'message': 'Missing authorization code'
            }
        }), 400

    # Exchange code for access token
    token_url = 'https://api.line.me/oauth2/v2.1/token'

    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': current_app.config['LINE_REDIRECT_URI'],
        'client_id': current_app.config['LINE_CHANNEL_ID'],
        'client_secret': current_app.config['LINE_CHANNEL_SECRET']
    }

    token_response = requests.post(token_url, data=token_data)

    if token_response.status_code != 200:
        return jsonify({
            'error': {
                'code': 'TOKEN_EXCHANGE_FAILED',
                'message': 'Failed to exchange code for token'
            }
        }), 400

    token_json = token_response.json()
    access_token = token_json.get('access_token')

    # Get user profile
    profile_url = 'https://api.line.me/v2/profile'
    headers = {'Authorization': f'Bearer {access_token}'}

    profile_response = requests.get(profile_url, headers=headers)

    if profile_response.status_code != 200:
        return jsonify({
            'error': {
                'code': 'PROFILE_FETCH_FAILED',
                'message': 'Failed to fetch user profile'
            }
        }), 400

    profile_json = profile_response.json()

    # Get or create user
    line_user_id = profile_json.get('userId')
    user = User.query.filter_by(line_user_id=line_user_id).first()

    if not user:
        # Create new user
        user = User(
            line_user_id=line_user_id,
            display_name=profile_json.get('displayName', 'Unknown'),
            picture_url=profile_json.get('pictureUrl'),
            email=token_json.get('email')
        )
        db.session.add(user)
        db.session.commit()

        # Create default project for new user
        from app.models.project import Project
        from app.utils.helpers import generate_id

        default_project = Project(
            name=f"บัญชี {user.display_name}",
            owner_user_id=user.id
        )
        default_project.id = generate_id('prj')
        db.session.add(default_project)
        db.session.commit()

        # Create default categories for the project
        from app.models.category import Category

        default_categories = [
            # Expense categories
            {'type': 'expense', 'name_th': 'อาหารและเครื่องดื่ม', 'icon': 'utensils', 'color': '#EF4444'},
            {'type': 'expense', 'name_th': 'ค่าเดินทาง', 'icon': 'car', 'color': '#F59E0B'},
            {'type': 'expense', 'name_th': 'ช้อปปิ้ง', 'icon': 'shopping-bag', 'color': '#EC4899'},
            {'type': 'expense', 'name_th': 'ความบันเทิง', 'icon': 'tv', 'color': '#8B5CF6'},
            {'type': 'expense', 'name_th': 'ค่าสาธารณูปโภค', 'icon': 'lightbulb', 'color': '#10B981'},
            {'type': 'expense', 'name_th': 'สุขภาพ', 'icon': 'heart-pulse', 'color': '#06B6D4'},
            # Income categories
            {'type': 'income', 'name_th': 'เงินเดือน', 'icon': 'dollar-sign', 'color': '#10B981'},
            {'type': 'income', 'name_th': 'รายได้เสริม', 'icon': 'trending-up', 'color': '#3B82F6'},
            {'type': 'income', 'name_th': 'ของขวัญ', 'icon': 'gift', 'color': '#EC4899'},
        ]

        for idx, cat_data in enumerate(default_categories):
            category = Category(
                project_id=default_project.id,
                type=cat_data['type'],
                name_th=cat_data['name_th'],
                icon=cat_data['icon'],
                color=cat_data['color'],
                sort_order=idx + 1
            )
            db.session.add(category)

        db.session.commit()
    else:
        # Update existing user
        user.display_name = profile_json.get('displayName', user.display_name)
        user.picture_url = profile_json.get('pictureUrl', user.picture_url)
        if token_json.get('email'):
            user.email = token_json.get('email')
        db.session.commit()

        # Check if user has at least one project, if not create default
        from app.models.project import Project
        from app.utils.helpers import generate_id

        existing_project = Project.query.filter_by(owner_user_id=user.id).first()
        if not existing_project:
            default_project = Project(
                name=f"บัญชี {user.display_name}",
                owner_user_id=user.id
            )
            default_project.id = generate_id('prj')
            db.session.add(default_project)
            db.session.commit()

            # Create default categories
            from app.models.category import Category

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
                    project_id=default_project.id,
                    type=cat_data['type'],
                    name_th=cat_data['name_th'],
                    icon=cat_data['icon'],
                    color=cat_data['color'],
                    sort_order=idx + 1
                )
                db.session.add(category)

            db.session.commit()

    # Create session
    session['user_id'] = user.id
    session['line_user_id'] = user.line_user_id
    session.permanent = True

    # Clear OAuth state
    session.pop('oauth_state', None)

    # Redirect to app or specified URL
    redirect_url = session.pop('redirect_after_login', '/app')

    return redirect(redirect_url)


@bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })


@bp.route('/me')
def me():
    """Get current user information"""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Not logged in'
            }
        }), 401

    user = User.query.get(user_id)

    if not user:
        # User doesn't exist (e.g., database was reset), clear session
        session.clear()
        return jsonify({
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found'
            }
        }), 404

    return jsonify({
        'user': user.to_dict()
    })
