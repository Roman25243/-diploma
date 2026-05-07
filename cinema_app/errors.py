import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from flask import Blueprint, current_app, render_template, request
from flask_login import current_user
from extensions import db

errors_bp = Blueprint('errors', __name__)


def _build_error_payload(error, status_code):
    """Формує структуровані дані для логування HTTP помилок."""
    request_id = request.headers.get('X-Request-ID') or str(uuid4())
    user_id = current_user.id if getattr(current_user, 'is_authenticated', False) else None

    return {
        'event': 'http_error',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'request_id': request_id,
        'status_code': status_code,
        'method': request.method,
        'path': request.path,
        'endpoint': request.endpoint,
        'remote_addr': request.headers.get('X-Forwarded-For', request.remote_addr),
        'user_agent': request.user_agent.string,
        'user_id': user_id,
        'error_type': type(error).__name__,
        'error_message': str(error),
    }


def _log_http_error(error, status_code, level=logging.WARNING, exc_info=False):
    """Пише структурований JSON-лог для 4xx/5xx помилок."""
    payload = _build_error_payload(error, status_code)
    current_app.logger.log(level, json.dumps(payload, ensure_ascii=False), exc_info=exc_info)


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Обробка помилки 404 - Сторінку не знайдено"""
    _log_http_error(error, 404, level=logging.INFO)
    return render_template('errors/404.html'), 404


@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Обробка помилки 500 - Внутрішня помилка сервера"""
    _log_http_error(error, 500, level=logging.ERROR, exc_info=True)
    db.session.rollback()
    return render_template('errors/500.html'), 500


@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """Обробка помилки 403 - Доступ заборонено"""
    _log_http_error(error, 403, level=logging.WARNING)
    return render_template('errors/403.html'), 403


@errors_bp.app_errorhandler(405)
def method_not_allowed_error(error):
    """Обробка помилки 405 - Метод не дозволено"""
    _log_http_error(error, 405, level=logging.WARNING)
    return render_template('errors/405.html'), 405
