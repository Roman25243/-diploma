"""Допоміжні функції для додатку"""
from io import BytesIO
import importlib

from flask import render_template, url_for
from flask_mail import Message
from extensions import mail
from threading import Thread


def send_async_email(app, msg):
    """Асинхронна відправка email"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as exc:
            app.logger.error('Email send failed: %s', exc)


def send_email(subject, sender, recipients, text_body, html_body, app, attachments=None):
    """
    Відправка email з підтримкою асинхронності
    
    Args:
        subject: Тема листа
        sender: Відправник
        recipients: Список отримувачів
        text_body: Текстова версія
        html_body: HTML-версія
        app: Flask-додаток
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body

    for attachment in attachments or []:
        filename, mimetype, data = attachment
        msg.attach(filename, mimetype, data)
    
    thread = Thread(target=send_async_email, args=(app, msg))
    thread.daemon = True
    thread.start()


def send_ticket_email(user, ticket, app):
    """Send issued ticket with QR code attachment."""
    from flask import current_app

    ticket = ticket.booking.ticket if getattr(ticket, 'booking', None) and ticket.booking.ticket else ticket
    booking = ticket.booking
    session = booking.seat.session
    qr_url = url_for('api.public_ticket_view', token=ticket.token, _external=True)
    profile_url = url_for('user.profile', _external=True)

    html_body = render_template(
        'emails/ticket_issued.html',
        user_name=user.name,
        film_title=session.film.title,
        session_time=session.start_time,
        seat_row=booking.seat.row,
        seat_number=booking.seat.number,
        qr_url=qr_url,
        profile_url=profile_url,
        ticket_token=ticket.token,
    )

    text_body = render_template(
        'emails/ticket_issued.txt',
        user_name=user.name,
        film_title=session.film.title,
        session_time=session.start_time,
        seat_row=booking.seat.row,
        seat_number=booking.seat.number,
        qr_url=qr_url,
        profile_url=profile_url,
        ticket_token=ticket.token,
    )

    try:
        qrcode = importlib.import_module('qrcode')
        payload = qr_url
        image = qrcode.make(payload)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        qr_attachment = [('ticket-qr.png', 'image/png', buffer.getvalue())]
    except Exception:
        qr_attachment = []

    send_email(
        subject=f'Ваш QR-квиток: {session.film.title}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body,
        app=app,
        attachments=qr_attachment,
    )


def send_booking_confirmation_email(user, session, seats):
    """
    Відправка email-підтвердження бронювання
    
    Args:
        user: Об'єкт користувача
        session: Об'єкт сеансу
        seats: Список заброньованих місць
    """
    from flask import current_app
    
    total_price = session.price * len(seats)
    
    profile_url = url_for('user.profile', _external=True)
    
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
    
    films_url = url_for('main.films', _external=True)
    
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
    
    films_url = url_for('main.films', _external=True)
    
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
        session_date = session.start_time.split(' ')[0]
        
        existing_notification = SessionNotification.query.filter_by(
            film_id=session.film_id,
            session_date=session_date
        ).first()
        
        if existing_notification:
            return
        
        favorites = Favorite.query.filter_by(film_id=session.film_id).all()
        
        if not favorites:
            return
        
        all_sessions_today = [s for s in session.film.sessions 
                            if s.start_time.startswith(session_date) and s.status == 'active']
        
        from flask import url_for
        film_url = url_for('main.film_detail', film_id=session.film_id, _external=True)
        
        for favorite in favorites:
            user = favorite.user
            
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
            
            send_email(
                subject=f'Нові сеанси: {session.film.title}',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email],
                text_body=text_body,
                html_body=html_body,
                app=current_app._get_current_object()
            )
        
        notification_record = SessionNotification(
            film_id=session.film_id,
            session_date=session_date
        )
        db.session.add(notification_record)
        db.session.commit()
        
        current_app.logger.info(
            f'Надіслано {len(favorites)} повідомлень про нові сеанси фільму '
            f'{session.film.title} на {session_date}'
        )
        
    except Exception as e:
        current_app.logger.error(
            f'Помилка надсилання повідомлень про нові сеанси: {str(e)}'
        )
        db.session.rollback()
