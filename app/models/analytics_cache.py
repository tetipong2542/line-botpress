"""
Analytics Cache Model
Stores cached analytics results to improve performance
"""
from datetime import datetime
from app import db
from app.utils.helpers import generate_id


class AnalyticsCache(db.Model):
    """Cached analytics results"""

    __tablename__ = 'analytics_cache'

    id = db.Column(db.String(36), primary_key=True, default=generate_id)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    cache_key = db.Column(db.String(255), nullable=False, index=True)
    cache_data = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    # Relationships
    project = db.relationship('Project', backref='analytics_caches')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'cache_key': self.cache_key,
            'cache_data': self.cache_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @staticmethod
    def get_cached(cache_key, project_id):
        """Get cached data if not expired"""
        from datetime import datetime

        cache = AnalyticsCache.query.filter_by(
            cache_key=cache_key,
            project_id=project_id
        ).first()

        if cache and cache.expires_at > datetime.utcnow():
            import json
            return json.loads(cache.cache_data)

        return None

    @staticmethod
    def set_cached(cache_key, project_id, data, ttl_minutes=60):
        """Set cached data with TTL"""
        from datetime import timedelta
        import json

        # Delete existing cache
        existing = AnalyticsCache.query.filter_by(
            cache_key=cache_key,
            project_id=project_id
        ).first()

        if existing:
            db.session.delete(existing)

        # Create new cache entry
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        cache = AnalyticsCache(
            project_id=project_id,
            cache_key=cache_key,
            cache_data=json.dumps(data),
            expires_at=expires_at
        )
        db.session.add(cache)
        db.session.commit()

        return cache

    @staticmethod
    def clear_expired():
        """Clear expired cache entries"""
        from datetime import datetime

        expired = AnalyticsCache.query.filter(
            AnalyticsCache.expires_at < datetime.utcnow()
        ).all()

        for cache in expired:
            db.session.delete(cache)

        db.session.commit()
        return len(expired)
