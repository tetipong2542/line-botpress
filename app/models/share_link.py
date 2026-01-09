"""
Share Link Model
Stores shareable report links with optional password protection
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id
import hashlib
import secrets


class ShareLink(db.Model):
    """Shareable report links"""

    __tablename__ = 'share_links'

    id = db.Column(db.String(36), primary_key=True, default=generate_id)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    report_id = db.Column(db.String(36))
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_by = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, index=True)
    password_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = db.relationship('Project', backref='share_links')
    creator = db.relationship('User', backref='share_links')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'report_id': self.report_id,
            'token': self.token,
            'created_by': self.created_by,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def generate_token():
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    def set_password(self, password):
        """Set password hash"""
        if password:
            self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        else:
            self.password_hash = None

    def check_password(self, password):
        """Check password"""
        if not self.password_hash:
            return True  # No password set
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def is_valid(self):
        """Check if link is still valid"""
        from datetime import datetime
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    @staticmethod
    def get_by_token(token):
        """Get share link by token"""
        return ShareLink.query.filter_by(token=token).first()

    @staticmethod
    def clear_expired():
        """Clear expired share links"""
        from datetime import datetime

        expired = ShareLink.query.filter(
            ShareLink.expires_at < datetime.utcnow()
        ).all()

        for link in expired:
            db.session.delete(link)

        db.session.commit()
        return len(expired)
