"""
Security utilities for HMAC verification and authentication
"""
import hmac
import hashlib
import base64
from datetime import datetime
from flask import current_app, request, g
from functools import wraps
from app import db
from app.models.security import BotNonce, IdempotencyKey


def verify_line_signature(body, signature):
    """
    Verify LINE webhook signature

    Args:
        body: Request body (bytes)
        signature: X-Line-Signature header value

    Returns:
        bool: True if signature is valid
    """
    secret = current_app.config['LINE_MESSAGING_CHANNEL_SECRET']
    hash_obj = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    )
    expected_signature = base64.b64encode(hash_obj.digest()).decode('utf-8')
    return hmac.compare_digest(signature, expected_signature)


def verify_bot_hmac(bot_id, timestamp, signature, body=''):
    """
    Verify Botpress bot HMAC signature

    Args:
        bot_id: Bot ID from X-BOT-ID header
        timestamp: Timestamp from X-BOT-TS header
        signature: HMAC signature from X-BOT-HMAC header
        body: Request body string

    Returns:
        bool: True if signature is valid
    """
    # Check timestamp (prevent replay attacks beyond 5 minutes)
    try:
        ts = int(timestamp)
        now = int(datetime.utcnow().timestamp())
        if abs(now - ts) > 300:  # 5 minutes
            return False
    except (ValueError, TypeError):
        return False

    # Verify HMAC
    secret = current_app.config['BOT_HMAC_SECRET']
    message = f"{bot_id}:{timestamp}:{body}"

    hash_obj = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    expected_signature = hash_obj.hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def check_bot_nonce(nonce, bot_id):
    """
    Check if bot nonce has been used (prevent replay attacks)

    Args:
        nonce: Nonce value
        bot_id: Bot ID

    Returns:
        bool: True if nonce is valid (not used before)
    """
    existing = BotNonce.query.filter_by(nonce=nonce).first()

    if existing:
        return False

    # Store nonce
    bot_nonce = BotNonce(nonce=nonce, bot_id=bot_id)
    db.session.add(bot_nonce)
    db.session.commit()

    return True


def check_idempotency(event_id, endpoint):
    """
    Check if request with event_id has been processed before

    Args:
        event_id: Unique event ID
        endpoint: API endpoint path

    Returns:
        tuple: (is_duplicate, existing_response)
    """
    existing = IdempotencyKey.query.filter_by(event_id=event_id).first()

    if existing and not existing.is_expired():
        # Return cached response
        return True, {
            'status': existing.response_status,
            'body': existing.response_body
        }

    # Not a duplicate or expired
    return False, None


def store_idempotency_response(event_id, endpoint, status_code, response_body):
    """
    Store response for idempotency check

    Args:
        event_id: Unique event ID
        endpoint: API endpoint path
        status_code: HTTP status code
        response_body: Response body (as string)
    """
    key = IdempotencyKey.query.filter_by(event_id=event_id).first()

    if not key:
        key = IdempotencyKey(event_id=event_id, endpoint=endpoint)
        db.session.add(key)

    key.response_status = status_code
    key.response_body = response_body
    db.session.commit()


def require_bot_auth(require_idempotency=False):
    """
    Decorator to require bot authentication with HMAC

    Args:
        require_idempotency: Whether to check for idempotency key

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get headers
            bot_id = request.headers.get('X-BOT-ID')
            timestamp = request.headers.get('X-BOT-TS')
            signature = request.headers.get('X-BOT-HMAC')
            nonce = request.headers.get('X-BOT-NONCE')

            if not all([bot_id, timestamp, signature]):
                return {
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Missing bot authentication headers'
                    }
                }, 401

            # Verify HMAC
            body = request.get_data(as_text=True)
            if not verify_bot_hmac(bot_id, timestamp, signature, body):
                return {
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Invalid bot signature'
                    }
                }, 401

            # Check nonce if provided
            if nonce and not check_bot_nonce(nonce, bot_id):
                return {
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Nonce already used'
                    }
                }, 401

            # Check idempotency if required
            if require_idempotency:
                event_id = request.json.get('event_id') if request.json else None
                if not event_id:
                    return {
                        'error': {
                            'code': 'BAD_REQUEST',
                            'message': 'Missing event_id for idempotency check'
                        }
                    }, 400

                is_duplicate, cached_response = check_idempotency(event_id, request.path)
                if is_duplicate:
                    return cached_response['body'], cached_response['status']

                # Store event_id in g for later use
                g.event_id = event_id

            # Store bot_id in g
            g.bot_id = bot_id

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_line_signature():
    """
    Decorator to verify LINE webhook signature

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            signature = request.headers.get('X-Line-Signature')

            if not signature:
                return {
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Missing LINE signature'
                    }
                }, 401

            body = request.get_data()
            if not verify_line_signature(body, signature):
                return {
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Invalid LINE signature'
                    }
                }, 401

            return f(*args, **kwargs)

        return decorated_function
    return decorator
