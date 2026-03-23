from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Декоратор для перевірки прав адміністратора"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """Редірект на SPA версію"""
    return redirect('/app/admin')


@admin_bp.route('/films')
@admin_required
def films():
    """Редірект на SPA версію"""
    return redirect('/app/admin/films')


@admin_bp.route('/sessions')
@admin_required
def sessions():
    """Редірект на SPA версію"""
    return redirect('/app/admin/sessions')


@admin_bp.route('/calendar')
@admin_required
def calendar():
    """Редірект на SPA версію"""
    return redirect('/app/admin/calendar')
