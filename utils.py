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
