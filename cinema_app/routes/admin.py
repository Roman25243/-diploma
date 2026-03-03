from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func
import os
from extensions import db
from models import User, Film, Session, Seat, Booking
from forms import FilmForm, SessionForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Декоратор для перевірки прав адміністратора"""
    from functools import wraps
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
    """Головна сторінка адміністратора з статистикою"""
    # Основна статистика
    total_users = User.query.count()
    total_bookings = Booking.query.count()
    total_films = Film.query.count()
    total_revenue = db.session.query(func.sum(Session.price)).join(Seat).join(Booking).scalar() or 0

    # Топ популярних фільмів
    popular_films = db.session.query(
        Film.title, func.count(Booking.id).label('count')
    ).join(Session).join(Seat).join(Booking)\
     .group_by(Film.id).order_by(func.count(Booking.id).desc()).limit(5).all()

    popular_labels = [f[0] for f in popular_films]
    popular_data = [f[1] for f in popular_films]

    # Прибуток по фільмах
    revenue_films = db.session.query(
        Film.title, func.sum(Session.price).label('revenue')
    ).join(Session).join(Seat).join(Booking)\
     .group_by(Film.id).order_by(func.sum(Session.price).desc()).limit(5).all()

    revenue_labels = [f[0] for f in revenue_films]
    revenue_data = [float(f[1] or 0) for f in revenue_films]

    # Топ користувачів
    top_users = db.session.query(
        User, func.count(Booking.id).label('booking_count'),
        func.sum(Session.price).label('spent')
    ).outerjoin(Booking).outerjoin(Seat).outerjoin(Session)\
     .group_by(User.id).order_by(func.count(Booking.id).desc()).limit(10).all()

    stats = {
        'total_users': total_users,
        'total_bookings': total_bookings,
        'total_films': total_films,
        'total_revenue': total_revenue,
        'popular_films': {'labels': popular_labels, 'data': popular_data},
        'revenue_films': {'labels': revenue_labels, 'data': revenue_data},
        'top_users': [{'name': u.name, 'email': u.email, 'booking_count': bc, 'spent': float(spent or 0)} 
                      for u, bc, spent in top_users]
    }

    return render_template('admin/dashboard.html', stats=stats)


@admin_bp.route('/films', methods=['GET', 'POST'])
@admin_required
def films():
    """Управління фільмами"""
    form = FilmForm()
    
    # Видалення фільму
    if request.method == 'POST' and 'delete_film' in request.form:
        film_id = request.form['delete_film']
        film = Film.query.get_or_404(film_id)
        db.session.delete(film)
        db.session.commit()
        flash('Фільм видалено', 'success')
        return redirect(url_for('admin.films'))
    
    # Додавання або редагування фільму
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
        film_id = request.form.get('film_id')
        if film_id:  # Редагування
            film = Film.query.get_or_404(film_id)
            film.title = form.title.data
            film.description = form.description.data
            film.genre = form.genre.data
            film.director = form.director.data
            film.actors = form.actors.data
            film.duration = form.duration.data
            film.age_rating = form.age_rating.data
            film.release_year = form.release_year.data
            film.trailer = form.trailer.data or film.trailer
            if filename:
                film.image = filename
            flash('Фільм оновлено', 'success')
        else:  # Додавання
            film = Film(
                title=form.title.data,
                description=form.description.data,
                genre=form.genre.data,
                director=form.director.data,
                actors=form.actors.data,
                duration=form.duration.data,
                age_rating=form.age_rating.data,
                release_year=form.release_year.data,
                image=filename,
                trailer=form.trailer.data
            )
            db.session.add(film)
            flash('Фільм додано', 'success')
        
        db.session.commit()
        return redirect(url_for('admin.films'))
    
    films = Film.query.all()
    return render_template('admin/films.html', films=films, form=form)


@admin_bp.route('/sessions', methods=['GET', 'POST'])
@admin_required
def sessions():
    """Управління сеансами"""
    form = SessionForm()
    films = Film.query.all()
    
    # Відміна сеансу
    if request.method == 'POST' and 'cancel_session' in request.form:
        session_id = request.form['cancel_session']
        session = Session.query.get_or_404(session_id)
        
        if session.status == 'cancelled':
            flash('Сеанс вже скасовано', 'warning')
        else:
            # Відміна сеансу
            session.status = 'cancelled'
            
            # Звільняємо всі заброньовані місця
            booked_seats = [seat for seat in session.seats if seat.status == 'booked']
            affected_users = []
            
            for seat in booked_seats:
                if seat.booking:
                    user = seat.booking.user
                    if user not in affected_users:
                        affected_users.append(user)
                    # Видаляємо бронювання
                    db.session.delete(seat.booking)
                # Звільняємо місце
                seat.status = 'free'
            
            db.session.commit()
            
            # Відправляємо email користувачам про відміну
            try:
                from utils import send_session_cancellation_email
                for user in affected_users:
                    send_session_cancellation_email(user, session)
            except Exception as e:
                current_app.logger.error(f'Помилка відправки email: {str(e)}')
            
            flash(f'Сеанс скасовано. Повідомлено {len(affected_users)} користувачів.', 'success')
        
        return redirect(url_for('admin.sessions'))
    
    if form.validate_on_submit():
        session = Session(
            film_id=request.form['film_id'],
            start_time=form.start_time.data,
            price=form.price.data,
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
        flash('Сеанс додано з 120 місцями', 'success')
        return redirect(url_for('admin.sessions'))
    
    sessions = Session.query.order_by(Session.start_time.desc()).all()
    return render_template('admin/sessions.html', films=films, sessions=sessions, form=form)
