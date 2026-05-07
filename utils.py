"""Р”РѕРїРѕРјС–Р¶РЅС– С„СѓРЅРєС†С–С— РґР»СЏ РґРѕРґР°С‚РєСѓ"""
from io import BytesIO
import importlib

from flask import render_template, url_for
from flask_mail import Message
from extensions import mail
from threading import Thread


def send_async_email(app, msg):
    """РђСЃРёРЅС…СЂРѕРЅРЅР° РІС–РґРїСЂР°РІРєР° email"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as exc:
            app.logger.error('Email send failed: %s', exc)


def send_email(subject, sender, recipients, text_body, html_body, app, attachments=None):
    """
    Р’С–РґРїСЂР°РІРєР° email Р· РїС–РґС‚СЂРёРјРєРѕСЋ Р°СЃРёРЅС…СЂРѕРЅРЅРѕСЃС‚С–
    
    Args:
        subject: РўРµРјР° Р»РёСЃС‚Р°
        sender: Р’С–РґРїСЂР°РІРЅРёРє
        recipients: РЎРїРёСЃРѕРє РѕС‚СЂРёРјСѓРІР°С‡С–РІ
        text_body: РўРµРєСЃС‚РѕРІР° РІРµСЂСЃС–СЏ
        html_body: HTML РІРµСЂСЃС–СЏ
        app: Flask РґРѕРґР°С‚РѕРє
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
        subject=f'Р’Р°С€ QR-РєРІРёС‚РѕРє: {session.film.title}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body,
        app=app,
        attachments=qr_attachment,
    )


def send_booking_confirmation_email(user, session, seats):
    """
    Р’С–РґРїСЂР°РІРєР° email-РїС–РґС‚РІРµСЂРґР¶РµРЅРЅСЏ Р±СЂРѕРЅСЋРІР°РЅРЅСЏ
    
    Args:
        user: РћР±'С”РєС‚ РєРѕСЂРёСЃС‚СѓРІР°С‡Р°
        session: РћР±'С”РєС‚ СЃРµР°РЅСЃСѓ
        seats: РЎРїРёСЃРѕРє Р·Р°Р±СЂРѕРЅСЊРѕРІР°РЅРёС… РјС–СЃС†СЊ
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
        subject=f'РџС–РґС‚РІРµСЂРґР¶РµРЅРЅСЏ Р±СЂРѕРЅСЋРІР°РЅРЅСЏ: {session.film.title}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body,
        app=current_app._get_current_object()
    )


def send_booking_cancellation_email(user, session, seat):
    """
    Р’С–РґРїСЂР°РІРєР° email РїСЂРѕ СЃРєР°СЃСѓРІР°РЅРЅСЏ Р±СЂРѕРЅСЋРІР°РЅРЅСЏ
    
    Args:
        user: РћР±'С”РєС‚ РєРѕСЂРёСЃС‚СѓРІР°С‡Р°
        session: РћР±'С”РєС‚ СЃРµР°РЅСЃСѓ
        seat: РћР±'С”РєС‚ РјС–СЃС†СЏ
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
        subject=f'РЎРєР°СЃСѓРІР°РЅРЅСЏ Р±СЂРѕРЅСЋРІР°РЅРЅСЏ: {session.film.title}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body,
        app=current_app._get_current_object()
    )


def send_session_cancellation_email(user, session):
    """
    Р’С–РґРїСЂР°РІРєР° email РїСЂРѕ СЃРєР°СЃСѓРІР°РЅРЅСЏ СЃРµР°РЅСЃСѓ Р°РґРјС–РЅС–СЃС‚СЂР°С‚РѕСЂРѕРј
    
    Args:
        user: РћР±'С”РєС‚ РєРѕСЂРёСЃС‚СѓРІР°С‡Р°
        session: РћР±'С”РєС‚ СЃРµР°РЅСЃСѓ
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
        subject=f'РЎРєР°СЃСѓРІР°РЅРЅСЏ СЃРµР°РЅСЃСѓ: {session.film.title}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body,
        app=current_app._get_current_object()
    )


def notify_favorites_about_new_sessions(session):
    """
    Р’С–РґРїСЂР°РІРєР° РїРѕРІС–РґРѕРјР»РµРЅСЊ РєРѕСЂРёСЃС‚СѓРІР°С‡Р°Рј РїСЂРѕ РЅРѕРІС– СЃРµР°РЅСЃРё РѕР±СЂР°РЅРёС… С„С–Р»СЊРјС–РІ
    РќР°РґСЃРёР»Р°С”С‚СЊСЃСЏ Р»РёС€Рµ РѕРґРЅРµ РїРѕРІС–РґРѕРјР»РµРЅРЅСЏ РЅР° РґРµРЅСЊ РґР»СЏ РєРѕР¶РЅРѕРіРѕ С„С–Р»СЊРјСѓ
    
    Args:
        session: РћР±'С”РєС‚ РЅРѕРІРѕСЃС‚РІРѕСЂРµРЅРѕРіРѕ СЃРµР°РЅСЃСѓ
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
                subject=f'РќРѕРІС– СЃРµР°РЅСЃРё: {session.film.title}',
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
        
        current_app.logger.info(f'РќР°РґС–СЃР»Р°РЅРѕ {len(favorites)} РїРѕРІС–РґРѕРјР»РµРЅСЊ РїСЂРѕ РЅРѕРІС– СЃРµР°РЅСЃРё С„С–Р»СЊРјСѓ {session.film.title} РЅР° {session_date}')
        
    except Exception as e:
        current_app.logger.error(f'РџРѕРјРёР»РєР° РЅР°РґСЃРёР»Р°РЅРЅСЏ РїРѕРІС–РґРѕРјР»РµРЅСЊ РїСЂРѕ РЅРѕРІС– СЃРµР°РЅСЃРё: {str(e)}')
        db.session.rollback()
