"""
Application configuration
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Railway volume mount support (/data)
    # Strategy: Try /data first (Railway persistent storage), then instance dir, then /tmp
    
    # 1. Determine candidate paths in priority order
    candidates = []
    
    # Priority 1: /data (Railway persistent volume)
    if os.path.exists('/data'):
        candidates.append(('/data', 'Railway persistent storage'))
    
    # Priority 2: Custom DATA_DIR from environment
    if os.getenv('DATA_DIR'):
        candidates.append((os.getenv('DATA_DIR'), 'Custom DATA_DIR'))
    
    # Priority 3: Local instance directory (for development)
    instance_dir = os.path.join(BASE_DIR, 'instance')
    candidates.append((instance_dir, 'Local instance directory'))
    
    # Priority 4: /tmp (guaranteed writable fallback)
    candidates.append(('/tmp', 'Temporary directory'))
    
    DATA_DIR = None
    
    # Try each candidate in order
    for candidate_dir, description in candidates:
        try:
            # Try to create/use the candidate directory
            os.makedirs(candidate_dir, exist_ok=True)
            
            # Test write permissions
            test_file = os.path.join(candidate_dir, 'perm_test.tmp')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
            
            # If we got here, it's writable
            DATA_DIR = candidate_dir
            print(f"✅ Using {description}: {DATA_DIR}")
            break
        except Exception as e:
            print(f"⚠️ Cannot use {description} ({candidate_dir}): {e}")
            continue
    
    if not DATA_DIR:
        raise RuntimeError("❌ No writable directory found for database!")

    # Construct DB URI - only use DATABASE_URL if explicitly set and is an absolute path
    env_db_url = os.getenv('DATABASE_URL')
    if env_db_url and (env_db_url.startswith('sqlite:////') or env_db_url.startswith('postgresql://') or env_db_url.startswith('mysql://')):
        # Use explicit DATABASE_URL if it's an absolute path or external DB
        SQLALCHEMY_DATABASE_URI = env_db_url
        print(f"🔌 Using explicit DATABASE_URL: {SQLALCHEMY_DATABASE_URI}")
    else:
        # Use auto-configured path
        db_path = os.path.join(DATA_DIR, "finance.db")
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        print(f"🔌 Database path: {db_path}")
        print(f"🔌 Database URI: {SQLALCHEMY_DATABASE_URI}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = FLASK_ENV == 'development'

    # Session
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # LINE Login (OAuth2)
    LINE_CHANNEL_ID = os.getenv('LINE_CHANNEL_ID', '')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
    LINE_REDIRECT_URI = os.getenv('LINE_REDIRECT_URI', 'http://localhost:5000/auth/line/callback')

    # LINE Messaging API
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
    LINE_MESSAGING_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

    # Botpress Integration
    BOTPRESS_WEBHOOK_URL = os.getenv(
        'BOTPRESS_WEBHOOK_URL',
        'https://webhook.botpress.cloud/68043144-896b-4278-b4d3-66693df66942'
    )
    BOTPRESS_BOT_ID = os.getenv('BOTPRESS_BOT_ID', 'botpress-prod')
    BOTPRESS_BOT_SECRET = os.getenv('BOTPRESS_BOT_SECRET', '')

    # Security
    BOT_HMAC_SECRET = os.getenv('BOT_HMAC_SECRET', 'change-this-secret-minimum-32-characters')

    # App Settings
    APP_NAME = os.getenv('APP_NAME', 'จดรายรับรายจ่าย')
    APP_TIMEZONE = os.getenv('APP_TIMEZONE', 'Asia/Bangkok')
    DEFAULT_CURRENCY = os.getenv('DEFAULT_CURRENCY', 'THB')

    # Insight Policy (Botpress Mode B)
    INSIGHT_MAX_RECORDS = int(os.getenv('INSIGHT_MAX_RECORDS', '100'))
    INSIGHT_MAX_DAYS = int(os.getenv('INSIGHT_MAX_DAYS', '30'))
    INSIGHT_FIELDS_LEVEL = os.getenv('INSIGHT_FIELDS_LEVEL', 'minimal')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
