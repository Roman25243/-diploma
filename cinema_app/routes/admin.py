from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func
import os
from datetime import datetime, timedelta
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


@admin_bp.route('/calendar')
@admin_required
def calendar():
    """Календарний вигляд сеансів на тиждень"""
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
            'date': day,
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
            key = (session_date.isoformat(), session_time)
            
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
    
    return render_template('admin/calendar.html', 
                         week_days=week_days,
                         time_slots=time_slots,
                         sessions_grid=sessions_grid,
                         films=films,
                         week_offset=week_offset,
                         start_of_week=start_of_week,
                         timedelta=timedelta)


@admin_bp.route('/calendar/create-session', methods=['POST'])
@admin_required
def create_session_from_calendar():
    """Швидке створення сеансу з календаря"""
    try:
        film_id = request.form.get('film_id', type=int)
        date = request.form.get('date')
        time = request.form.get('time')
        price = request.form.get('price', type=float)
        
        if not all([film_id, date, time, price]):
            flash('Заповніть всі поля', 'danger')
            return redirect(url_for('admin.calendar'))
        
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
        
        flash(f'Сеанс створено на {start_time}', 'success')
    except Exception as e:
        flash(f'Помилка: {str(e)}', 'danger')
    
    return redirect(url_for('admin.calendar') + f'?week={request.form.get("week_offset", 0)}')


@admin_bp.route('/sessions/<int:session_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_session_api(session_id):
    """API для скасування сеансу з календаря"""
    from utils import send_session_cancellation_email
    
    session = Session.query.get_or_404(session_id)
    
    if session.status == 'cancelled':
        return jsonify({'error': 'Сеанс вже скасовано'}), 400
    
    try:
        # Отримуємо дані перед зміною статусу
        film_title = session.film.title
        session_time = session.start_time
        
        # Отримуємо всі місця для цього сеансу
        seats = Seat.query.filter_by(session_id=session.id).all()
        
        # Збираємо унікальних користувачів, які мають бронювання
        users_to_notify = []
        seen_user_ids = set()
        
        for seat in seats:
            # Для кожного місця перевіряємо бронювання
            bookings = Booking.query.filter_by(seat_id=seat.id).all()
            for booking in bookings:
                if booking.user_id not in seen_user_ids:
                    user = User.query.get(booking.user_id)
                    if user and user.email:
                        users_to_notify.append(user)
                        seen_user_ids.add(booking.user_id)
        
        # Скасовуємо сеанс
        session.status = 'cancelled'
        db.session.commit()
        
        # Відправка email користувачам після успішного збереження
        for user in users_to_notify:
            try:
                send_session_cancellation_email(user, session)
            except Exception as e:
                print(f"Помилка відправки email до {user.email}: {e}")
        
        return jsonify({'success': True, 'message': 'Сеанс скасовано'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Помилка скасування сеансу: {e}")
        return jsonify({'error': str(e)}), 500
