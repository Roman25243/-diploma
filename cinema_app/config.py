import os
import re
from dotenv import load_dotenv

# Завантаження змінних з .env файлу
load_dotenv()

class Config:
    """Конфігурація додатку"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key'
    
    # База даних - PostgreSQL або SQLite
    # Для PostgreSQL встановіть DATABASE_URL у .env файлі:
    # DATABASE_URL=postgresql://username:password@localhost:5432/cinema_db
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    # Для Heroku: замінюємо postgres:// на postgresql://
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    
    # Flask-WTF конфігурація
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Токен не має терміну дії
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Максимум 16MB для завантаження файлів
    
    # Flask-Mail конфігурація
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'cinema@example.com'
    
    # Flask-Caching конфігурація
    CACHE_TYPE = 'simple'  # Кешування в пам'яті (для development)
    # Для production використовуйте Redis:
    # CACHE_TYPE = 'redis'
    # CACHE_REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 хвилин за замовчуванням
    
    # Таймаути для конкретних операцій
    CACHE_POPULAR_FILMS_TIMEOUT = 3600      # 1 година для популярних фільмів
    CACHE_GENRES_TIMEOUT = 3600              # 1 година для жанрів
    CACHE_ADMIN_STATS_TIMEOUT = 1800         # 30 хвилин для статистики адміна
    
    # Flask-Compress конфігурація (GZIP)
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'text/plain',
        'application/javascript', 'application/xml+rss', 'application/json',
        'application/xml'
    ]
    COMPRESS_LEVEL = 6  # Рівень стиснення 1-9 (6 - оптимальний баланс)
    COMPRESS_MIN_SIZE = 500  # Мінімум 500 байт для стиснення

    # Online payments (phase 1)
    PAYMENT_ONLINE_ENABLED = os.environ.get('PAYMENT_ONLINE_ENABLED', 'true').lower() in ['true', 'on', '1']
    PAYMENT_PROVIDER = os.environ.get('PAYMENT_PROVIDER') or ''
    PAYMENT_CURRENCY = os.environ.get('PAYMENT_CURRENCY') or 'UAH'
    PAYMENT_WEBHOOK_SECRET = os.environ.get('PAYMENT_WEBHOOK_SECRET') or ''
    PAYMENT_APP_BASE_URL = os.environ.get('PAYMENT_APP_BASE_URL') or 'http://127.0.0.1:5000'
    PAYMENT_SUCCESS_URL = os.environ.get('PAYMENT_SUCCESS_URL') or f"{PAYMENT_APP_BASE_URL}/app/profile?payment=success"
    PAYMENT_CANCEL_URL = os.environ.get('PAYMENT_CANCEL_URL') or f"{PAYMENT_APP_BASE_URL}/app/profile?payment=cancel"
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or ''
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY') or ''
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET') or ''

    # Cross-origin frontend support (Cloudflare Pages -> Heroku API)
    cors_origins = os.environ.get('CORS_ORIGINS', '')
    CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    CORS_ORIGINS.extend([
        'http://localhost:3000',
        'http://localhost:4173',
        'http://127.0.0.1:5500',
        'https://acd8cd15.diploma-1qj.pages.dev',
        'https://4ff47227.diploma-1qj.pages.dev',
        re.compile(r'^https://.*\.pages\.dev$'),
    ])

    deduped_origins: list[object] = []
    seen_literals: set[str] = set()
    for origin in CORS_ORIGINS:
        if isinstance(origin, str):
            if origin in seen_literals:
                continue
            seen_literals.add(origin)
        deduped_origins.append(origin)
    CORS_ORIGINS = deduped_origins

    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE') or 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() in ['true', 'on', '1']
