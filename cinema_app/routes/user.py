from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from extensions import db
from models import Booking, Seat, Session, Film, Favorite
from utils import send_booking_confirmation_email, send_booking_cancellation_email

user_bp = Blueprint('user', __name__)


@user_bp.route('/profile')
@login_required
def profile():
    """Редірект на SPA версію"""
    return redirect('/app/profile')


@user_bp.route('/seats/<int:session_id>')
@login_required
def seats(session_id):
    """Редірект на SPA версію"""
    return redirect(f'/app/seats/{session_id}')


@user_bp.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Скасування бронювання"""
    booking = Booking.query.get_or_404(booking_id)

    # Перевірка що це бронювання поточного користувача
    if booking.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    # Зберігаємо дані для email до видалення
    seat = booking.seat
    session = seat.session
    user = booking.user if current_user.is_admin else current_user
    
    # Звільняємо місце
    seat.status = 'free'
    db.session.delete(booking)
    db.session.commit()

    # Відправка email про скасування
    try:
        send_booking_cancellation_email(user, session, seat)
    except Exception as e:
        # Логуємо помилку, але не показуємо користувачу
        print(f"Email error: {e}")

    flash('Бронювання успішно скасовано', 'success')
    return redirect(url_for('user.profile'))


@user_bp.route('/favorites')
@login_required
def favorites():
    """Редірект на SPA версію"""
    return redirect('/app/favorites')


@user_bp.route('/favorite/toggle/<int:film_id>', methods=['POST'])
@login_required
def toggle_favorite(film_id):
    """Перемкнути стан (додати/видалити)"""
    film = Film.query.get_or_404(film_id)
    
    favorite = Favorite.query.filter_by(
        user_id=current_user.id, 
        film_id=film_id
    ).first()
    
    if favorite:
        # Видалити з обраних
        db.session.delete(favorite)
        db.session.commit()
        flash(f'"{film.title}" видалено з обраних', 'success')
    else:
        # Додати до обраних
        favorite = Favorite(user_id=current_user.id, film_id=film_id)
        db.session.add(favorite)
        db.session.commit()
        flash(f'"{film.title}" додано до обраних!', 'success')
    
    return redirect(request.referrer or url_for('main.films'))


@user_bp.route('/favorite/remove/<int:film_id>', methods=['POST'])
@login_required
def remove_from_favorites(film_id):
    """Видалити з обраних"""
    favorite = Favorite.query.filter_by(
        user_id=current_user.id, 
        film_id=film_id
    ).first_or_404()
    
    film_title = favorite.film.title
    db.session.delete(favorite)
    db.session.commit()
    flash(f'"{film_title}" видалено з обраних', 'success')
    
    return redirect(request.referrer or url_for('user.favorites'))


@user_bp.route('/app/')
@user_bp.route('/app/<path:path>')
def spa(path=''):
    """Vue Router SPA — всі маршрути обробляються клієнтом"""
    return render_template('spa.html')
