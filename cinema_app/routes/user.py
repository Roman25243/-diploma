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
    """Профіль користувача з історією бронювань"""
    filter_type = request.args.get('filter', 'active')

    bookings_query = Booking.query.options(
        joinedload(Booking.seat)
        .joinedload(Seat.session)
        .joinedload(Session.film)
    ).filter_by(user_id=current_user.id)

    bookings = bookings_query.all()
    total_spent = sum(b.seat.session.price for b in bookings)

    return render_template(
        'profile.html',
        bookings=bookings,
        total_spent=total_spent,
        filter_type=filter_type
    )


@user_bp.route('/seats/<int:session_id>', methods=['GET', 'POST'])
@login_required
def seats(session_id):
    """Вибір та бронювання місць на сеанс"""
    session = Session.query.get_or_404(session_id)
    
    # Перевірка чи сеанс не скасовано
    if session.status == 'cancelled':
        flash('Цей сеанс скасовано. Будь ласка, оберіть інший.', 'danger')
        return redirect(url_for('main.film_detail', film_id=session.film_id))
    
    seats = Seat.query.filter_by(session_id=session_id).order_by(Seat.row, Seat.number).all()

    if request.method == 'POST':
        selected_seats = request.form.getlist('seat')
        if not selected_seats:
            flash('Оберіть хоча б одне місце', 'warning')
            return redirect(url_for('user.seats', session_id=session_id))

        booked_count = 0
        successfully_booked_seats = []
        
        for seat_id in selected_seats:
            seat = Seat.query.get(seat_id)
            if seat.status == 'booked':
                booked_count += 1
            else:
                seat.status = 'booked'
                booking = Booking(user_id=current_user.id, seat_id=seat.id)
                db.session.add(booking)
                successfully_booked_seats.append(seat)
        
        db.session.commit()

        # Відправка email-підтвердження (тільки якщо є успішно заброньовані місця)
        if successfully_booked_seats:
            try:
                send_booking_confirmation_email(current_user, session, successfully_booked_seats)
            except Exception as e:
                # Логуємо помилку, але не показуємо користувачу (бронювання вже зроблено)
                print(f"Email error: {e}")

        if booked_count > 0:
            flash(f'{booked_count} з вибраних місць вже були заброньовані іншими. Решта заброньовано успішно!', 'info')
        else:
            flash('Місця успішно заброньовано! Перевірте свою електронну пошту.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('seats.html', session=session, seats=seats)


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
    """Список обраних фільмів"""
    favorites = Favorite.query.filter_by(user_id=current_user.id)\
        .order_by(Favorite.added_at.desc()).all()
    
    films = [fav.film for fav in favorites]
    
    return render_template('favorites.html', films=films, favorites=favorites)


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
