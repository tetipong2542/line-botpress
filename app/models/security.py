"""
Security models - Bot authentication and idempotency
"""
from datetime import datetime, timedelta
from app import db
from app.utils.helpers import generate_id


class BotNonce(db.Model):
    """Bot nonce model for replay attack prevention"""

    __tablename__ = 'bot_nonce'

    id = db.Column(db.String(50), primary_key=True)
    nonce = db.Column(db.String(100), unique=True, nullable=False, index=True)
    bot_id = db.Column(db.String(50), nullable=False)
    used_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, nonce, bot_id, ttl_seconds=300):
        self.id = generate_id('non')
        self.nonce = nonce
        self.bot_id = bot_id
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    def is_expired(self):
        """Check if nonce is expired"""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<BotNonce {self.nonce[:20]}...>'


class IdempotencyKey(db.Model):
    """Idempotency key model for preventing duplicate operations"""

    __tablename__ = 'idempotency_key'

    id = db.Column(db.String(50), primary_key=True)
    event_id = db.Column(db.String(200), unique=True, nullable=False, index=True)
    endpoint = db.Column(db.String(200), nullable=False)
    response_status = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, event_id, endpoint, ttl_hours=24):
        self.id = generate_id('idk')
        self.event_id = event_id
        self.endpoint = endpoint
        self.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

    def is_expired(self):
        """Check if key is expired"""
        return datetime.utcnow() > self.expires_at

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'endpoint': self.endpoint,
            'response_status': self.response_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<IdempotencyKey {self.event_id}>'
