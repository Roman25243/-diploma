from flask import Flask
from werkzeug.security import generate_password_hash
import os
from sqlalchemy import inspect, text
from sqlalchemy.orm import selectinload

from config import Config
from extensions import db, login_manager, mail, csrf, cache, compress
from models import Hall, Session, User

from routes.main import main_bp
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.api import api_bp  # API РґР»СЏ Vue.js
from errors import errors_bp


def _ensure_payment_schema_updates(app):
    """Apply minimal non-destructive schema updates for payment rollout."""
    inspector = inspect(db.engine)

    booking_columns = {col['name'] for col in inspector.get_columns('booking')} if inspector.has_table('booking') else set()
    payment_columns = {
        col['name'] for col in inspector.get_columns('payment_transaction')
    } if inspector.has_table('payment_transaction') else set()

    statements = []

    if 'payment_id' not in booking_columns:
        statements.append("ALTER TABLE booking ADD COLUMN payment_id INTEGER")
    if 'payment_status' not in booking_columns:
        statements.append("ALTER TABLE booking ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid' NOT NULL")
    if 'provider_payment_id' not in payment_columns and inspector.has_table('payment_transaction'):
        statements.append("ALTER TABLE payment_transaction ADD COLUMN provider_payment_id VARCHAR(128)")

    if not statements:
        return

    for ddl in statements:
        try:
            db.session.execute(text(ddl))
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.warning('Schema patch skipped for DDL "%s": %s', ddl, exc)


def _session_hall_dimensions(session):
    """Determine hall dimensions from an existing session layout."""
    if not session.seats:
        return 10, 12

    max_row = max((seat.row or 0) for seat in session.seats) or 10
    max_number = max((seat.number or 0) for seat in session.seats) or 12
    return max_row, max_number


def _ensure_hall_schema_updates(app):
    """Apply hall-related schema updates and backfill existing sessions."""
    inspector = inspect(db.engine)

    session_columns = {col['name'] for col in inspector.get_columns('session')} if inspector.has_table('session') else set()
    statements = []

    if 'hall_id' not in session_columns:
        statements.append('ALTER TABLE session ADD COLUMN hall_id INTEGER')

    for ddl in statements:
        try:
            db.session.execute(text(ddl))
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.warning('Schema patch skipped for DDL "%s": %s', ddl, exc)

    halls = {(hall.rows, hall.seats_per_row): hall for hall in Hall.query.order_by(Hall.id.asc()).all()}
    if not halls:
        default_hall = Hall(name='РћСЃРЅРѕРІРЅРёР№ Р·Р°Р»', rows=10, seats_per_row=12)
        db.session.add(default_hall)
        db.session.commit()
        halls[(default_hall.rows, default_hall.seats_per_row)] = default_hall

    existing_names = {hall.name for hall in halls.values()}
    next_index = len(halls) + 1
    sessions = Session.query.options(selectinload(Session.seats)).order_by(Session.id.asc()).all()
    changed = False

    for session in sessions:
        dimensions = _session_hall_dimensions(session)
        hall = halls.get(dimensions)
        if hall is None:
            name = f'Р—Р°Р» {next_index}'
            while name in existing_names:
                next_index += 1
                name = f'Р—Р°Р» {next_index}'
            hall = Hall(name=name, rows=dimensions[0], seats_per_row=dimensions[1])
            db.session.add(hall)
            db.session.flush()
            halls[dimensions] = hall
            existing_names.add(name)
            next_index += 1

        if session.hall_id != hall.id:
            session.hall_id = hall.id
            changed = True

    if changed:
        db.session.commit()


def create_app():
    """Р¤Р°Р±СЂРёРєР° РґРѕРґР°С‚РєСѓ Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    if app.config.get('SECRET_KEY') == 'super_secret_key':
        app.logger.warning('Using default SECRET_KEY. Set SECRET_KEY in environment before production deploy.')
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)  # REST API РґР»СЏ Vue.js
    app.register_blueprint(errors_bp)
    
    if app.debug:
        from routes.test_errors import test_errors_bp
        app.register_blueprint(test_errors_bp)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        db.create_all()
        _ensure_payment_schema_updates(app)
        _ensure_hall_schema_updates(app)
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
    debug_mode = os.environ.get('DEBUG', 'false').lower() in ['true', 'on', '1']
    app.run(debug=debug_mode)

