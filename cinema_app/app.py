from flask import Flask
from werkzeug.security import generate_password_hash
import os

from config import Config
from extensions import db, login_manager, mail, csrf, cache, compress, migrate, cors
from models import User

from routes.main import main_bp
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.api import api_bp  # API  Vue.js
from errors import errors_bp


def create_app():
    """Р¤Р°Р±СЂРёРєР° РґРѕРґР°С‚РєСѓ Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    if app.config.get('SECRET_KEY') == 'super_secret_key':
        app.logger.warning('Using default SECRET_KEY. Set SECRET_KEY in environment before production deploy.')
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', [])}},
        supports_credentials=True,
    )
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)  # REST API  Vue.js
    app.register_blueprint(errors_bp)

    @app.after_request
    def enforce_utf8_charset(response):
        content_type = response.headers.get('Content-Type', '')
        content_type_lower = content_type.lower()
        if content_type_lower.startswith('text/') and 'charset=' not in content_type_lower:
            response.headers['Content-Type'] = f"{content_type}; charset=utf-8"
        elif content_type_lower.startswith('application/javascript') and 'charset=' not in content_type_lower:
            response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        return response
    
    if app.debug:
        from routes.test_errors import test_errors_bp
        app.register_blueprint(test_errors_bp)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
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
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'false').lower() in ['true', 'on', '1']
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

