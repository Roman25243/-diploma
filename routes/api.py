"""
API endpoints для Vue.js frontend
REST API для поступового переходу на SPA архітектуру
"""
from flask import Blueprint, jsonify, request, url_for as flask_url_for, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime, timedelta
import os

from extensions import db
from models import Film, Session, Seat, Booking, User, Review, Favorite

api_bp = Blueprint('api', __name__, url_prefix='/api')


def film_to_dict(film):
    """Серіалізація фільму в словник"""
    return {
        'id': film.id,
        'title': film.title,
        'description': film.description,
        'image': flask_url_for('static', filename='uploads/' + film.image) if film.image else None,
        'trailer': film.trailer,
        'genre': film.genre,
        'director': film.director,
        'actors': film.actors,
        'duration': film.duration,
        'age_rating': film.age_rating,
        'release_year': film.release_year,
        'average_rating': film.average_rating(),
        'review_count': film.review_count(),
        'is_favorite': film.is_favorited_by(current_user) if current_user.is_authenticated else False
    }


# ============================================================================
# SEATS API
# ============================================================================

@api_bp.route('/sessions/<int:session_id>/seats', methods=['GET'])
@login_required
def get_seats(session_id):
    """Отримати всі місця для сеансу"""
    session = Session.query.get_or_404(session_id)

    if session.status == 'cancelled':
        return jsonify({'error': 'Сеанс скасовано'}), 400

    seats = Seat.query.filter_by(session_id=session_id)\
        .order_by(Seat.row, Seat.number).all()

    existing_bookings = Booking.query.join(Seat).filter(
        Seat.session_id == session_id,
        Booking.user_id == current_user.id
    ).count()

    return jsonify({
        'session': {
            'id': session.id,
            'film_title': session.film.title,
            'start_time': session.start_time,
            'price': float(session.price),
            'available_seats': session.available_seats_count()
        },
        'seats': [{
            'id': seat.id,
            'row': seat.row,
            'number': seat.number,
            'status': seat.status
        } for seat in seats],
        'user_bookings': {
            'count': existing_bookings,
            'remaining_slots': 5 - existing_bookings
        }
    })


@api_bp.route('/sessions/<int:session_id>/book', methods=['POST'])
@login_required
def book_seats(session_id):
    """Забронювати місця"""
    data = request.get_json()
    selected_seat_ids = data.get('seat_ids', [])

    if not selected_seat_ids:
        return jsonify({'error': 'Оберіть хоча б одне місце'}), 400

    session = Session.query.get_or_404(session_id)

    if session.status == 'cancelled':
        return jsonify({'error': 'Сеанс скасовано'}), 400

    existing_bookings = Booking.query.join(Seat).filter(
        Seat.session_id == session_id,
        Booking.user_id == current_user.id
    ).count()

    total_seats = existing_bookings + len(selected_seat_ids)
    if total_seats > 5:
        remaining = 5 - existing_bookings
        return jsonify({
            'error': f'Максимум 5 місць на сеанс. У вас вже {existing_bookings}, доступно ще {remaining}'
        }), 400

    booked_count = 0
    successfully_booked = []

    for seat_id in selected_seat_ids:
        seat = Seat.query.with_for_update().get(seat_id)
        if not seat or seat.session_id != session_id:
            continue

        if seat.status == 'booked':
            booked_count += 1
        else:
            seat.status = 'booked'
            booking = Booking(user_id=current_user.id, seat_id=seat.id)
            db.session.add(booking)
            successfully_booked.append({
                'row': seat.row,
                'number': seat.number
            })

    db.session.commit()

    if not successfully_booked:
        return jsonify({
            'success': False,
            'error': 'Усі обрані місця вже зайняті',
            'booked_seats': [],
            'total_booked': 0
        }), 409

    return jsonify({
        'success': True,
        'message': 'Місця успішно заброньовано!' if not booked_count else f'{booked_count} місць вже були заброньовані',
        'booked_seats': successfully_booked,
        'total_booked': len(successfully_booked)
    })


# ============================================================================
# FILMS API
# ============================================================================

@api_bp.route('/films/popular', methods=['GET'])
def get_popular_films():
    """Отримати популярні фільми (топ-4 за бронюваннями)"""
    popular_films = db.session.query(Film)\
        .outerjoin(Session).outerjoin(Seat).outerjoin(Booking)\
        .group_by(Film.id)\
        .order_by(func.count(Booking.id).desc())\
        .limit(4).all()
    
    if len(popular_films) < 4:
        popular_films = Film.query.order_by(Film.id.desc()).limit(4).all()
    
    return jsonify({
        'films': [{
            'id': f.id,
            'title': f.title,
            'description': f.description,
            'image': flask_url_for('static', filename='uploads/' + f.image) if f.image else None,
            'genre': f.genre,
            'duration': f.duration,
            'release_year': f.release_year,
            'average_rating': f.average_rating(),
            'review_count': f.review_count(),
            'is_favorited': f.is_favorited_by(current_user) if current_user.is_authenticated else False
        } for f in popular_films]
    })


@api_bp.route('/films', methods=['GET'])
def get_films():
    """Отримати список фільмів з пошуком"""
    query = request.args.get('q', '').strip()
    genre = request.args.get('genre', '').strip()

    films_query = Film.query

    if query:
        films_query = films_query.filter(
            Film.title.ilike(f'%{query}%') |
            Film.description.ilike(f'%{query}%')
        )

    if genre:
        films_query = films_query.filter(Film.genre == genre)

    films = films_query.all()

    all_genres = db.session.query(Film.genre).filter(Film.genre.isnot(None)).distinct().all()
    genres = sorted([g[0] for g in all_genres if g[0]])

    return jsonify({
        'films': [film_to_dict(f) for f in films],
        'genres': genres
    })


@api_bp.route('/films/<int:film_id>', methods=['GET'])
def get_film(film_id):
    """Отримати детальну інформацію про фільм"""
    film = Film.query.get_or_404(film_id)

    sessions = Session.query.filter_by(
        film_id=film_id,
        status='active'
    ).order_by(Session.start_time).all()

    reviews = Review.query.filter_by(film_id=film_id)\
        .order_by(Review.created_at.desc()).all()

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            film_id=film_id,
            user_id=current_user.id
        ).first()

    similar_films = film.get_similar_films(limit=4)

    return jsonify({
        'film': film_to_dict(film),
        'sessions': [{
            'id': s.id,
            'start_time': s.start_time,
            'price': float(s.price),
            'available_seats': s.available_seats_count(),
            'booked_seats': s.booked_seats_count()
        } for s in sessions],
        'reviews': [{
            'id': r.id,
            'user_name': r.user.name,
            'user_id': r.user_id,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat()
        } for r in reviews],
        'user_review': {
            'id': user_review.id,
            'rating': user_review.rating,
            'comment': user_review.comment
        } if user_review else None,
        'similar_films': [film_to_dict(f) for f in similar_films],
        'is_authenticated': current_user.is_authenticated,
        'current_user_id': current_user.id if current_user.is_authenticated else None,
        'is_admin': current_user.is_admin if current_user.is_authenticated else False
    })


# ============================================================================
# REVIEWS API
# ============================================================================

@api_bp.route('/films/<int:film_id>/reviews', methods=['POST'])
@login_required
def add_review(film_id):
    """Додати відгук"""
    Film.query.get_or_404(film_id)
    data = request.get_json()

    existing = Review.query.filter_by(
        film_id=film_id,
        user_id=current_user.id
    ).first()

    if existing:
        return jsonify({'error': 'Ви вже залишили відгук на цей фільм'}), 400

    rating = data.get('rating')
    comment = data.get('comment', '').strip()

    if not rating or not (1 <= int(rating) <= 5):
        return jsonify({'error': 'Оцінка має бути від 1 до 5'}), 400

    review = Review(
        film_id=film_id,
        user_id=current_user.id,
        rating=int(rating),
        comment=comment
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({
        'success': True,
        'review': {
            'id': review.id,
            'user_name': current_user.name,
            'user_id': current_user.id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat()
        },
        'new_average_rating': review.film.average_rating()
    })


@api_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    """Видалити відгук"""
    review = Review.query.get_or_404(review_id)

    if review.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Немає прав на видалення'}), 403

    film = review.film
    db.session.delete(review)
    db.session.commit()

    return jsonify({
        'success': True,
        'new_average_rating': film.average_rating()
    })


# ============================================================================
# FAVORITES API
# ============================================================================

@api_bp.route('/favorites', methods=['GET'])
@login_required
def get_favorites():
    """Отримати улюблені фільми"""
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()

    return jsonify({
        'favorites': [{
            **film_to_dict(fav.film),
            'added_at': fav.added_at.isoformat()
        } for fav in favorites]
    })


@api_bp.route('/favorites/<int:film_id>', methods=['POST', 'DELETE'])
@login_required
def toggle_favorite(film_id):
    """Додати/видалити з улюблених"""
    Film.query.get_or_404(film_id)

    existing = Favorite.query.filter_by(
        user_id=current_user.id,
        film_id=film_id
    ).first()

    if request.method == 'DELETE' or existing:
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'success': True, 'action': 'removed'})
        return jsonify({'error': 'Не знайдено в обраних'}), 404
    else:
        favorite = Favorite(user_id=current_user.id, film_id=film_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})


# ============================================================================
# USER API
# ============================================================================

@api_bp.route('/user/profile', methods=['GET'])
@login_required
def get_profile():
    """Отримати профіль з бронюваннями"""
    all_bookings = Booking.query.filter_by(user_id=current_user.id).all()

    total_spent = sum(
        b.seat.session.price for b in all_bookings
        if b.seat.session.status != 'cancelled'
    )

    return jsonify({
        'user': {
            'name': current_user.name,
            'email': current_user.email,
            'is_admin': current_user.is_admin
        },
        'total_spent': total_spent,
        'bookings': [{
            'id': b.id,
            'film_id': b.seat.session.film.id,
            'film_title': b.seat.session.film.title,
            'film_image': flask_url_for('static', filename='uploads/' + b.seat.session.film.image) if b.seat.session.film.image else None,
            'session_time': b.seat.session.start_time,
            'seat_row': b.seat.row,
            'seat_number': b.seat.number,
            'price': float(b.seat.session.price),
            'is_cancelled': b.seat.session.status == 'cancelled'
        } for b in all_bookings]
    })


@api_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Скасувати бронювання"""
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        return jsonify({'error': 'Немає прав'}), 403

    if booking.seat.session.status == 'cancelled':
        return jsonify({'error': 'Сеанс вже скасовано'}), 400

    seat = booking.seat
    seat.status = 'free'
    db.session.delete(booking)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Бронювання скасовано'})


# ============================================================================
# AUTH API
# ============================================================================

@api_bp.route('/auth/status', methods=['GET'])
def auth_status():
    """Отримати статус авторизації поточного користувача"""
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
    """Вхід користувача через API"""
    if current_user.is_authenticated:
        return jsonify({'success': True, 'message': 'Вже авторизовані'})

    data = request.get_json()
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
    """Реєстрація нового користувача через API"""
    if current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Ви вже авторизовані'}), 400

    data = request.get_json()
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
    """Вихід користувача через API"""
    logout_user()
    return jsonify({'success': True, 'message': 'Вихід виконано'})


# ============================================================================
# ADMIN API
# ============================================================================

def api_admin_required(f):
    """Декоратор для перевірки прав адміністратора в API"""
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Доступ заборонено'}), 403
        return f(*args, **kwargs)
    return decorated


@api_bp.route('/admin/stats', methods=['GET'])
@api_admin_required
def admin_stats():
    """Статистика для адмін-панелі"""
    total_users = User.query.count()
    total_bookings = Booking.query.count()
    total_films = Film.query.count()
    total_sessions = Session.query.count()
    total_revenue = db.session.query(func.sum(Session.price)).join(Seat).join(Booking).scalar() or 0

    popular_films = db.session.query(
        Film.title, func.count(Booking.id).label('count')
    ).join(Session).join(Seat).join(Booking)\
     .group_by(Film.id).order_by(func.count(Booking.id).desc()).limit(5).all()

    revenue_films = db.session.query(
        Film.title, func.sum(Session.price).label('revenue')
    ).join(Session).join(Seat).join(Booking)\
     .group_by(Film.id).order_by(func.sum(Session.price).desc()).limit(5).all()

    top_users = db.session.query(
        User, func.count(Booking.id).label('booking_count'),
        func.sum(Session.price).label('spent')
    ).outerjoin(Booking).outerjoin(Seat).outerjoin(Session)\
     .group_by(User.id).order_by(func.count(Booking.id).desc()).limit(10).all()

    return jsonify({
        'total_users': total_users,
        'total_bookings': total_bookings,
        'total_films': total_films,
        'total_sessions': total_sessions,
        'total_revenue': float(total_revenue),
        'popular_films': {
            'labels': [f[0] for f in popular_films],
            'data': [f[1] for f in popular_films]
        },
        'revenue_films': {
            'labels': [f[0] for f in revenue_films],
            'data': [float(f[1] or 0) for f in revenue_films]
        },
        'top_users': [
            {'name': u.name, 'email': u.email, 'booking_count': bc, 'spent': float(spent or 0)}
            for u, bc, spent in top_users
        ]
    })


@api_bp.route('/admin/films', methods=['GET'])
@api_admin_required
def admin_films_list():
    """Список фільмів для адміна"""
    films = Film.query.order_by(Film.id.desc()).all()
    return jsonify({'films': [{
        'id': f.id,
        'title': f.title,
        'description': f.description,
        'genre': f.genre,
        'director': f.director,
        'actors': f.actors,
        'duration': f.duration,
        'age_rating': f.age_rating,
        'release_year': f.release_year,
        'trailer': f.trailer,
        'image': f'/static/uploads/{f.image}' if f.image else None,
        'sessions_count': len(f.sessions),
        'review_count': f.review_count(),
        'average_rating': f.average_rating()
    } for f in films]})


@api_bp.route('/admin/films', methods=['POST'])
@api_admin_required
def admin_film_create():
    """Створення фільму"""
    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()

    if not title:
        return jsonify({'success': False, 'error': 'Назва обов\'язкова'}), 400
    if not description or len(description) < 10:
        return jsonify({'success': False, 'error': 'Опис мінімум 10 символів'}), 400

    filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            allowed = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if ext not in allowed:
                return jsonify({'success': False, 'error': 'Дозволені тільки зображення (jpg, png, gif, webp)'}), 400
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

    film = Film(
        title=title,
        description=description,
        genre=(request.form.get('genre') or '').strip() or None,
        director=(request.form.get('director') or '').strip() or None,
        actors=(request.form.get('actors') or '').strip() or None,
        duration=int(request.form.get('duration') or 0) or None,
        age_rating=(request.form.get('age_rating') or '').strip() or None,
        release_year=int(request.form.get('release_year') or 0) or None,
        trailer=(request.form.get('trailer') or '').strip() or None,
        image=filename
    )
    db.session.add(film)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Фільм додано', 'film_id': film.id}), 201


@api_bp.route('/admin/films/<int:film_id>', methods=['PUT'])
@api_admin_required
def admin_film_update(film_id):
    """Оновлення фільму"""
    film = Film.query.get_or_404(film_id)

    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()

    if not title:
        return jsonify({'success': False, 'error': 'Назва обов\'язкова'}), 400
    if not description or len(description) < 10:
        return jsonify({'success': False, 'error': 'Опис мінімум 10 символів'}), 400

    film.title = title
    film.description = description
    film.genre = (request.form.get('genre') or '').strip() or None
    film.director = (request.form.get('director') or '').strip() or None
    film.actors = (request.form.get('actors') or '').strip() or None
    film.duration = int(request.form.get('duration') or 0) or None
    film.age_rating = (request.form.get('age_rating') or '').strip() or None
    film.release_year = int(request.form.get('release_year') or 0) or None
    film.trailer = (request.form.get('trailer') or '').strip() or film.trailer

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            allowed = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if ext not in allowed:
                return jsonify({'success': False, 'error': 'Дозволені тільки зображення'}), 400
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            film.image = filename

    db.session.commit()
    return jsonify({'success': True, 'message': 'Фільм оновлено'})


@api_bp.route('/admin/films/<int:film_id>', methods=['DELETE'])
@api_admin_required
def admin_film_delete(film_id):
    """Видалення фільму"""
    film = Film.query.get_or_404(film_id)
    db.session.delete(film)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Фільм видалено'})


@api_bp.route('/admin/sessions', methods=['GET'])
@api_admin_required
def admin_sessions_list():
    """Список сеансів для адміна"""
    sessions = Session.query.order_by(Session.start_time.desc()).all()
    return jsonify({'sessions': [{
        'id': s.id,
        'film_id': s.film_id,
        'film_title': s.film.title,
        'start_time': s.start_time,
        'price': s.price,
        'status': s.status,
        'booked': s.booked_seats_count(),
        'available': s.available_seats_count(),
        'total_seats': len(s.seats)
    } for s in sessions]})


@api_bp.route('/admin/sessions', methods=['POST'])
@api_admin_required
def admin_session_create():
    """Створення сеансу"""
    data = request.get_json()
    film_id = data.get('film_id')
    start_time = (data.get('start_time') or '').strip()
    price = data.get('price')

    if not film_id or not start_time or price is None:
        return jsonify({'success': False, 'error': 'Заповніть всі поля'}), 400

    film = Film.query.get(film_id)
    if not film:
        return jsonify({'success': False, 'error': 'Фільм не знайдено'}), 404

    try:
        price = float(price)
        if price < 0 or price > 10000:
            return jsonify({'success': False, 'error': 'Ціна від 0 до 10000'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Невірна ціна'}), 400

    session = Session(film_id=film_id, start_time=start_time, price=price, status='active')
    db.session.add(session)
    db.session.commit()

    for row in range(1, 11):
        for num in range(1, 13):
            seat = Seat(session_id=session.id, row=row, number=num, status='free')
            db.session.add(seat)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Сеанс створено (120 місць)', 'session_id': session.id}), 201


@api_bp.route('/admin/sessions/<int:session_id>/cancel', methods=['POST'])
@api_admin_required
def admin_session_cancel(session_id):
    """Скасування сеансу"""
    session = Session.query.get_or_404(session_id)

    if session.status == 'cancelled':
        return jsonify({'success': False, 'error': 'Сеанс вже скасовано'}), 400

    session.status = 'cancelled'

    booked_seats = [seat for seat in session.seats if seat.status == 'booked']
    affected_users = []
    seen_ids = set()

    for seat in booked_seats:
        if seat.booking and seat.booking.user_id not in seen_ids:
            affected_users.append(seat.booking.user)
            seen_ids.add(seat.booking.user_id)
        if seat.booking:
            db.session.delete(seat.booking)
        seat.status = 'free'

    db.session.commit()

    try:
        from utils import send_session_cancellation_email
        for user in affected_users:
            send_session_cancellation_email(user, session)
    except Exception as e:
        current_app.logger.error(f'Помилка відправки email: {e}')

    return jsonify({
        'success': True,
        'message': f'Сеанс скасовано. Повідомлено {len(affected_users)} користувачів.'
    })


@api_bp.route('/admin/calendar', methods=['GET'])
@api_admin_required
def admin_calendar():
    """API для отримання календаря сеансів"""
    from datetime import datetime, timedelta
    
    # Отримуємо параметр week_offset (0 = поточний тиждень, 1 = наступний тиждень)
    week_offset = request.args.get('week', 0, type=int)
    
    # Визначаємо початок тижня (понеділок)
    today = datetime.now().date()
    days_since_monday = today.weekday()  # 0 = понеділок, 6 = неділя
    start_of_week = today - timedelta(days=days_since_monday) + timedelta(weeks=week_offset)
    
    # Генеруємо 7 днів тижня
    week_days = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        week_days.append({
            'date': day.isoformat(),
            'day_name': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'][day.weekday()],
            'full_date': day.strftime('%d.%m.%Y')
        })
    
    # Часові слоти (з 9:00 до 23:00 з кроком 3 години)
    time_slots = []
    for hour in range(9, 24, 3):
        time_slots.append(f"{hour:02d}:00")
    
    # Отримуємо всі сеанси на цей тиждень
    end_of_week = start_of_week + timedelta(days=7)
    all_sessions = Session.query.join(Film).filter(
        Session.start_time >= start_of_week.strftime('%Y-%m-%d'),
        Session.start_time < end_of_week.strftime('%Y-%m-%d')
    ).all()
    
    # Організовуємо сеанси по днях і часах
    sessions_grid = {}
    for session in all_sessions:
        try:
            # Парсимо час сеансу
            session_datetime = datetime.strptime(session.start_time, '%Y-%m-%d %H:%M')
            session_date = session_datetime.date()
            
            # Округлюємо до найближчого 3-годинного слоту (9, 12, 15, 18, 21)
            hour = session_datetime.hour
            if hour < 9:
                slot_hour = 9
            elif hour < 12:
                slot_hour = 9
            elif hour < 15:
                slot_hour = 12
            elif hour < 18:
                slot_hour = 15
            elif hour < 21:
                slot_hour = 18
            else:
                slot_hour = 21
            
            session_time = f"{slot_hour:02d}:00"
            
            # Ключ: (дата, час)
            key = f"{session_date.isoformat()}#{session_time}"
            
            if key not in sessions_grid:
                sessions_grid[key] = []
            
            sessions_grid[key].append({
                'id': session.id,
                'film_title': session.film.title,
                'exact_time': session_datetime.strftime('%H:%M'),
                'price': session.price,
                'status': session.status,
                'booked': session.booked_seats_count(),
                'available': session.available_seats_count()
            })
        except:
            continue
    
    # Отримуємо всі фільми для швидкого створення
    films = Film.query.all()
    films_list = [{'id': f.id, 'title': f.title} for f in films]
    
    return jsonify({
        'success': True,
        'week_days': week_days,
        'time_slots': time_slots,
        'sessions_grid': sessions_grid,
        'films': films_list,
        'week_offset': week_offset,
        'start_of_week': start_of_week.isoformat()
    })


@api_bp.route('/admin/calendar/create-session', methods=['POST'])
@api_admin_required
def admin_calendar_create_session():
    """Швидке створення сеансу з календаря"""
    data = request.get_json()
    
    film_id = data.get('film_id')
    date = data.get('date')
    time = data.get('time')
    price = data.get('price')
    
    if not all([film_id, date, time, price]):
        return jsonify({'success': False, 'error': 'Заповніть всі поля'}), 400
    
    try:
        # Формуємо datetime
        start_time = f"{date} {time}"
        
        # Створюємо сеанс
        session = Session(
            film_id=film_id,
            start_time=start_time,
            price=price,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        # Автоматичне створення місць: 10 рядів × 12 місць
        for row in range(1, 11):
            for num in range(1, 13):
                seat = Seat(session_id=session.id, row=row, number=num, status='free')
                db.session.add(seat)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Сеанс створено на {start_time}',
            'session_id': session.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
