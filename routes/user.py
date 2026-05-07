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
    """Р РµРґС–СЂРµРєС‚ РЅР° SPA РІРµСЂСЃС–СЋ"""
    return redirect('/app/profile')


@user_bp.route('/seats/<int:session_id>')
@login_required
def seats(session_id):
    """Р РµРґС–СЂРµРєС‚ РЅР° SPA РІРµСЂСЃС–СЋ"""
    return redirect(f'/app/seats/{session_id}')


@user_bp.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """РЎРєР°СЃСѓРІР°РЅРЅСЏ Р±СЂРѕРЅСЋРІР°РЅРЅСЏ"""
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    seat = booking.seat
    session = seat.session
    user = booking.user if current_user.is_admin else current_user
    
    seat.status = 'free'
    db.session.delete(booking)
    db.session.commit()

    try:
        send_booking_cancellation_email(user, session, seat)
    except Exception as e:
        print(f"Email error: {e}")

    flash('Р‘СЂРѕРЅСЋРІР°РЅРЅСЏ СѓСЃРїС–С€РЅРѕ СЃРєР°СЃРѕРІР°РЅРѕ', 'success')
    return redirect(url_for('user.profile'))


@user_bp.route('/favorites')
@login_required
def favorites():
    """Р РµРґС–СЂРµРєС‚ РЅР° SPA РІРµСЂСЃС–СЋ"""
    return redirect('/app/favorites')


@user_bp.route('/favorite/toggle/<int:film_id>', methods=['POST'])
@login_required
def toggle_favorite(film_id):
    """РџРµСЂРµРјРєРЅСѓС‚Рё СЃС‚Р°РЅ (РґРѕРґР°С‚Рё/РІРёРґР°Р»РёС‚Рё)"""
    film = Film.query.get_or_404(film_id)
    
    favorite = Favorite.query.filter_by(
        user_id=current_user.id, 
        film_id=film_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash(f'"{film.title}" РІРёРґР°Р»РµРЅРѕ Р· РѕР±СЂР°РЅРёС…', 'success')
    else:
        favorite = Favorite(user_id=current_user.id, film_id=film_id)
        db.session.add(favorite)
        db.session.commit()
        flash(f'"{film.title}" РґРѕРґР°РЅРѕ РґРѕ РѕР±СЂР°РЅРёС…!', 'success')
    
    return redirect(request.referrer or url_for('main.films'))


@user_bp.route('/favorite/remove/<int:film_id>', methods=['POST'])
@login_required
def remove_from_favorites(film_id):
    """Р’РёРґР°Р»РёС‚Рё Р· РѕР±СЂР°РЅРёС…"""
    favorite = Favorite.query.filter_by(
        user_id=current_user.id, 
        film_id=film_id
    ).first_or_404()
    
    film_title = favorite.film.title
    db.session.delete(favorite)
    db.session.commit()
    flash(f'"{film_title}" РІРёРґР°Р»РµРЅРѕ Р· РѕР±СЂР°РЅРёС…', 'success')
    
    return redirect(request.referrer or url_for('user.favorites'))


@user_bp.route('/app/')
@user_bp.route('/app/<path:path>')
def spa(path=''):
    """Vue Router SPA вЂ” РІСЃС– РјР°СЂС€СЂСѓС‚Рё РѕР±СЂРѕР±Р»СЏСЋС‚СЊСЃСЏ РєР»С–С”РЅС‚РѕРј"""
    return render_template('spa.html')
