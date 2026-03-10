"""Допоміжні функції для додатку"""
from flask import render_template, url_for
from flask_mail import Message
from extensions import mail
from threading import Thread


def send_async_email(app, msg):
    """Асинхронна відправка email"""
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body, app):
    """
    Відправка email з підтримкою асинхронності
    
    Args:
        subject: Тема листа
        sender: Відправник
        recipients: Список отримувачів
        text_body: Текстова версія
        html_body: HTML версія
        app: Flask додаток
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Асинхронна відправка, щоб не блокувати основний потік
    Thread(target=send_async_email, args=(app, msg)).start()


def send_booking_confirmation_email(user, session, seats):
    """
    Відправка email-підтвердження бронювання
    
    Args:
        user: Об'єкт користувача
        session: Об'єкт сеансу
        seats: Список заброньованих місць
    """
    from flask import current_app
    
    # Розрахунок загальної ціни
    total_price = session.price * len(seats)
    
    # Формування URL для профілю
    profile_url = url_for('user.profile', _external=True)
    
    # Рендеринг шаблонів
    html_body = render_template(
        'emails/booking_confirmation.html',
        user_name=user.name,
        film_title=session.film.title,
        session_time=session.start_time,
        seats=seats,
        total_price=total_price,
        profile_url=profile_url
    )
    
    text_body = render_template(
        'emails/booking_confirmation.txt',
        user_name=user.name,
        film_title=session.film.title,
        session_time=session.start_time,
        seats=seats,
        total_price=total_price,
        profile_url=profile_url
    )
    
    # Відправка email
    send_email(
        subject=f'Підтвердження бронювання: {session.film.title}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body,
        app=current_app._get_current_object()
    )


def send_booking_cancellation_email(user, session, seat):
    """
    Відправка email про скасування бронювання
    
    Args:
        user: Об'єкт користувача
        session: Об'єкт сеансу
        seat: Об'єкт місця
    """
    from flask import current_app
    
    # Формування URL для каталогу фільмів
    films_url = url_for('main.films', _external=True)
    
    # Рендеринг шаблонів
    html_body = render_template(
        'emails/booking_cancelled.html',
        user_name=user.name,
        film_title=session.film.title,
        session_time=session.start_time,
        seat_row=seat.row,
        seat_number=seat.number,
        films_url=films_url
    )
    
    text_body = render_template(
        'emails/booking_cancelled.txt',
        user_name=user.name,
        film_title=session.film.title,
        session_time=session.start_time,
        seat_row=seat.row,
        seat_number=seat.number,
        films_url=films_url
    )
    
    # Відправка email
    send_email(
        subject=f'Скасування бронювання: {session.film.title}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body,
        app=current_app._get_current_object()
    )


def send_session_cancellation_email(user, session):
    """
    Відправка email про скасування сеансу адміністратором
    
    Args:
        user: Об'єкт користувача
        session: Об'єкт сеансу
    """
    from flask import current_app
    
    # Формування URL для каталогу фільмів
    films_url = url_for('main.films', _external=True)
    
    # Рендеринг шаблонів
    html_body = render_template(
        'emails/session_cancelled.html',
        user_name=user.name,
        film_title=session.film.title,
        session_time=session.start_time,
        films_url=films_url
    )
    
    text_body = render_template(
        'emails/session_cancelled.txt',
        user_name=user.name,
        film_title=session.film.title,
        session_time=session.start_time,
        films_url=films_url
    )
    
    # Відправка email
    send_email(
        subject=f'Скасування сеансу: {session.film.title}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body,
        app=current_app._get_current_object()
    )


def notify_favorites_about_new_sessions(session):
    """
    Відправка повідомлень користувачам про нові сеанси обраних фільмів
    Надсилається лише одне повідомлення на день для кожного фільму
    
    Args:
        session: Об'єкт новоствореного сеансу
    """
    from flask import current_app
    from models import Favorite, User, SessionNotification
    from extensions import db
    from datetime import datetime
    
    try:
        # Витягуємо дату з start_time (формат "YYYY-MM-DD HH:MM")
        session_date = session.start_time.split(' ')[0]
        
        # Перевіряємо, чи вже надсилали повідомлення про цей фільм на цей день
        existing_notification = SessionNotification.query.filter_by(
            film_id=session.film_id,
            session_date=session_date
        ).first()
        
        if existing_notification:
            # Вже надсилали повідомлення для цього фільму на цей день
            return
        
        # Знаходимо всіх користувачів, у яких цей фільм в обраних
        favorites = Favorite.query.filter_by(film_id=session.film_id).all()
        
        if not favorites:
            # Немає користувачів з цим фільмом в обраних
            return
        
        # Отримуємо всі сеанси цього фільму на цей день
        all_sessions_today = [s for s in session.film.sessions 
                            if s.start_time.startswith(session_date) and s.status == 'active']
        
        # Формування URL для сторінки фільму
        from flask import url_for
        film_url = url_for('main.film_detail', film_id=session.film_id, _external=True)
        
        # Надсилаємо повідомлення кожному користувачу
        for favorite in favorites:
            user = favorite.user
            
            # Рендеринг шаблонів
            html_body = render_template(
                'emails/new_sessions_notification.html',
                user_name=user.name,
                film_title=session.film.title,
                session_date=session_date,
                sessions=all_sessions_today,
                film_url=film_url
            )
            
            text_body = render_template(
                'emails/new_sessions_notification.txt',
                user_name=user.name,
                film_title=session.film.title,
                session_date=session_date,
                sessions=all_sessions_today,
                film_url=film_url
            )
            
            # Відправка email
            send_email(
                subject=f'Нові сеанси: {session.film.title}',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email],
                text_body=text_body,
                html_body=html_body,
                app=current_app._get_current_object()
            )
        
        # Записуємо, що надіслали повідомлення для цього фільму на цей день
        notification_record = SessionNotification(
            film_id=session.film_id,
            session_date=session_date
        )
        db.session.add(notification_record)
        db.session.commit()
        
        current_app.logger.info(f'Надіслано {len(favorites)} повідомлень про нові сеанси фільму {session.film.title} на {session_date}')
        
    except Exception as e:
        current_app.logger.error(f'Помилка надсилання повідомлень про нові сеанси: {str(e)}')
        # Не падаємо, просто логуємо помилку
        db.session.rollback()
