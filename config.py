import os

# Flask configuration
SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key")
DEBUG = True

# Database configuration - Using SQLite as per requirements
SQLALCHEMY_DATABASE_URI = "sqlite:///quiz_master.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Redis configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Celery configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Email configuration
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() in ["true", "1", "t", "y", "yes"]
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "your-email@gmail.com")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "your-password")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "quiz-master@example.com")

# Admin credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin@quizmaster.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Cache configuration
CACHE_TYPE = "RedisCache"
CACHE_REDIS_URL = REDIS_URL
CACHE_DEFAULT_TIMEOUT = 300
