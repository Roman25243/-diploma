from flask import Blueprint, abort

test_errors_bp = Blueprint('test_errors', __name__, url_prefix='/test')


@test_errors_bp.route('/404')
def test_404():
    """Тестування сторінки 404"""
    abort(404)


@test_errors_bp.route('/500')
def test_500():
    """Тестування сторінки 500"""
    # Викликаємо помилку ділення на нуль
    result = 1 / 0
    return str(result)


@test_errors_bp.route('/403')
def test_403():
    """Тестування сторінки 403"""
    abort(403)


@test_errors_bp.route('/405', methods=['GET'])
def test_405():
    """Тестування сторінки 405"""
    abort(405)
