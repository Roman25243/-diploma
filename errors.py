from flask import Blueprint, render_template
from extensions import db

errors_bp = Blueprint('errors', __name__)


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Обробка помилки 404 - Сторінку не знайдено"""
    return render_template('errors/404.html'), 404


@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Обробка помилки 500 - Внутрішня помилка сервера"""
    db.session.rollback()
    return render_template('errors/500.html'), 500


@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """Обробка помилки 403 - Доступ заборонено"""
    return render_template('errors/403.html'), 403


@errors_bp.app_errorhandler(405)
def method_not_allowed_error(error):
    """Обробка помилки 405 - Метод не дозволено"""
    return render_template('errors/405.html'), 405
