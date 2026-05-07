from flask import jsonify
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import User
from services.api_common import get_json_payload


def register_auth_routes(api_bp):
    @api_bp.route('/auth/status', methods=['GET'])
    def auth_status():
        """Get current user authentication status."""
        if current_user.is_authenticated:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': current_user.id,
                    'name': current_user.name,
                    'email': current_user.email,
                    'is_admin': current_user.is_admin
                }
            })
        return jsonify({'authenticated': False, 'user': None})

    @api_bp.route('/auth/login', methods=['POST'])
    def api_login():
        """Login user via API."""
        if current_user.is_authenticated:
            return jsonify({'success': True, 'message': 'Вже авторизовані'})

        data, error_response = get_json_payload()
        if error_response:
            return error_response

        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        if not email or not password:
            return jsonify({'success': False, 'error': 'Заповніть всі поля'}), 400

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return jsonify({
                'success': True,
                'message': 'Успішний вхід!',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'is_admin': user.is_admin
                }
            })

        return jsonify({'success': False, 'error': 'Невірний email або пароль'}), 401

    @api_bp.route('/auth/register', methods=['POST'])
    def api_register():
        """Register user via API."""
        if current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Ви вже авторизовані'}), 400

        data, error_response = get_json_payload()
        if error_response:
            return error_response

        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        errors = {}
        if not name or len(name) < 2:
            errors['name'] = "Ім'я має бути мінімум 2 символи"
        if len(name) > 100:
            errors['name'] = "Ім'я занадто довге (максимум 100 символів)"
        if not email:
            errors['email'] = 'Email обов\'язковий'
        if not password or len(password) < 6:
            errors['password'] = 'Пароль має бути мінімум 6 символів'

        if errors:
            return jsonify({'success': False, 'errors': errors}), 400

        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({'success': False, 'errors': {'email': 'Цей email вже зареєстрований'}}), 409

        user = User(
            email=email,
            password=generate_password_hash(password),
            name=name
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)

        return jsonify({
            'success': True,
            'message': 'Реєстрація успішна!',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 201

    @api_bp.route('/auth/logout', methods=['POST'])
    @login_required
    def api_logout():
        """Logout user via API."""
        logout_user()
        return jsonify({'success': True, 'message': 'Вихід виконано'})
