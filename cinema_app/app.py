from flask import Flask
from werkzeug.security import generate_password_hash
import os

from config import Config
from extensions import db, login_manager, mail
from models import User

# Імпорт blueprints
from routes.main import main_bp
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from errors import errors_bp


def create_app():
    """Фабрика додатку Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Створення папки для завантажень
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Ініціалізація розширень
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Реєстрація blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(errors_bp)
    
    # Тестові маршрути для помилок (тільки в debug режимі)
    if app.debug:
        from routes.test_errors import test_errors_bp
        app.register_blueprint(test_errors_bp)
    
    # User loader для Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Створення БД та першого адміна
    with app.app_context():
        db.create_all()
        if not User.query.first():
            admin = User(
                email='admin@example.com',
                password=generate_password_hash('admin'),
                name='Admin',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    
    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)

