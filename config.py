import os
from dotenv import load_dotenv

# Завантаження змінних з .env файлу
load_dotenv()

class Config:
    """Конфігурація додатку"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
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
