import os
from functools import wraps
from datetime import datetime

from flask import current_app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename

from extensions import db
from models import Booking, Film, Hall, Seat, Session, User
from services.api_common import (
    create_seats_for_session,
    get_json_payload,
    json_error,
    parse_float_field,
    parse_int_field,
    parse_session_datetime,
)

DEFAULT_HALL_ROWS = 10
DEFAULT_HALL_SEATS_PER_ROW = 12
SEAT_LAYOUT_STATUSES = {'free', 'blocked'}


def _hall_dimensions(session):
    if not session.seats:
        return DEFAULT_HALL_ROWS, DEFAULT_HALL_SEATS_PER_ROW

    max_row = max((seat.row or 0) for seat in session.seats) or DEFAULT_HALL_ROWS
    max_number = max((seat.number or 0) for seat in session.seats) or DEFAULT_HALL_SEATS_PER_ROW
    return max_row, max_number


def _serialize_hall_seat(seat):
    return {
        'id': seat.id,
        'row': seat.row,
        'number': seat.number,
        'status': seat.status,
        'is_booked': seat.status == 'booked'
    }


def _serialize_hall(hall):
    return {
        'id': hall.id,
        'name': hall.name,
        'rows': hall.rows,
        'seats_per_row': hall.seats_per_row,
        'capacity': hall.capacity(),
        'sessions_count': len(hall.sessions),
    }


def _resolve_hall(hall_id_raw=None):
    if hall_id_raw not in (None, ''):
        hall_id, hall_error = parse_int_field(hall_id_raw, 'hall_id', 1)
        if hall_error:
            return None, json_error(hall_error)
        hall = Hall.query.get(hall_id)
        if not hall:
            return None, (jsonify({'success': False, 'error': 'Р—Р°Р» РЅРµ Р·РЅР°Р№РґРµРЅРѕ'}), 404)
        return hall, None

    hall = Hall.query.order_by(Hall.id.asc()).first()
    if not hall:
        return None, (jsonify({'success': False, 'error': 'РЎРїРѕС‡Р°С‚РєСѓ СЃС‚РІРѕСЂС–С‚СЊ Р·Р°Р»'}), 400)
    return hall, None


def register_admin_routes(api_bp):
    def api_admin_required(f):
        """Require authenticated admin for API endpoint."""
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if not current_user.is_admin:
                return jsonify({'error': 'Р”РѕСЃС‚СѓРї Р·Р°Р±РѕСЂРѕРЅРµРЅРѕ'}), 403
            return f(*args, **kwargs)

        return decorated

    @api_bp.route('/admin/stats', methods=['GET'])
    @api_admin_required
    def admin_stats():
        """Admin dashboard statistics with multi-hall support."""
        total_users = User.query.count()
        total_bookings = Booking.query.count()
        total_films = Film.query.count()
        total_sessions = Session.query.count()
        total_halls = Hall.query.count()
        
        total_revenue = db.session.query(func.sum(Session.price)).join(Seat).join(Booking).scalar() or 0
        
        popular_films = db.session.query(
            Film.title, func.count(Booking.id).label('count')
        ).join(Session).join(Seat).join(Booking).group_by(Film.id).order_by(func.count(Booking.id).desc()).limit(5).all()

        revenue_films = db.session.query(
            Film.title, func.sum(Session.price).label('revenue')
        ).join(Session).join(Seat).join(Booking).group_by(Film.id).order_by(func.sum(Session.price).desc()).limit(5).all()

        top_users = db.session.query(
            User, func.count(Booking.id).label('booking_count'), func.sum(Session.price).label('spent')
        ).outerjoin(Booking).outerjoin(Seat).outerjoin(Session).group_by(User.id).order_by(func.count(Booking.id).desc()).limit(10).all()
        
        halls_stats = []
        for hall in Hall.query.all():
            hall_sessions = Session.query.filter(Session.hall_id == hall.id).all()
            total_seats = sum(len(s.seats) for s in hall_sessions)
            booked_seats = sum(sum(1 for seat in s.seats if seat.status == 'booked') for s in hall_sessions)
            hall_revenue = db.session.query(func.sum(Session.price)).filter(
                Session.hall_id == hall.id
            ).join(Seat).join(Booking).scalar() or 0
            
            occupancy_pct = round((booked_seats / total_seats * 100) if total_seats > 0 else 0, 1)
            
            halls_stats.append({
                'hall_id': hall.id,
                'hall_name': hall.name,
                'total_seats': total_seats,
                'booked_seats': booked_seats,
                'occupancy_pct': occupancy_pct,
                'revenue': float(hall_revenue),
                'sessions_count': len(hall_sessions)
            })

        return jsonify({
            'total_users': total_users,
            'total_bookings': total_bookings,
            'total_films': total_films,
            'total_sessions': total_sessions,
            'total_halls': total_halls,
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
            ],
            'halls_stats': halls_stats
        })

    @api_bp.route('/admin/stats/occupancy', methods=['GET'])
    @api_admin_required
    def admin_stats_occupancy():
        """Occupancy statistics by hall for chart."""
        halls_occupancy = []
        
        for hall in Hall.query.all():
            hall_sessions = Session.query.filter(Session.hall_id == hall.id).all()
            total_seats = sum(len(s.seats) for s in hall_sessions)
            booked_seats = sum(sum(1 for seat in s.seats if seat.status == 'booked') for s in hall_sessions)
            
            occupancy_pct = round((booked_seats / total_seats * 100) if total_seats > 0 else 0, 1)
            
            halls_occupancy.append({
                'name': hall.name,
                'occupancy': occupancy_pct,
                'booked': booked_seats,
                'total': total_seats
            })
        
        halls_occupancy.sort(key=lambda x: x['name'])
        
        return jsonify({
            'labels': [h['name'] for h in halls_occupancy],
            'occupancy': [h['occupancy'] for h in halls_occupancy],
            'booked': [h['booked'] for h in halls_occupancy],
            'total': [h['total'] for h in halls_occupancy],
            'data': halls_occupancy
        })

    @api_bp.route('/admin/stats/revenue', methods=['GET'])
    @api_admin_required
    def admin_stats_revenue():
        """Revenue statistics by hall for chart."""
        halls_revenue = []
        
        for hall in Hall.query.all():
            hall_revenue = db.session.query(func.sum(Session.price)).filter(
                Session.hall_id == hall.id
            ).join(Seat).join(Booking).scalar() or 0
            
            hall_bookings = db.session.query(func.count(Booking.id)).join(Seat).join(Session).filter(
                Session.hall_id == hall.id
            ).scalar() or 0
            
            halls_revenue.append({
                'name': hall.name,
                'revenue': float(hall_revenue),
                'bookings': hall_bookings
            })
        
        halls_revenue.sort(key=lambda x: x['revenue'], reverse=True)
        
        return jsonify({
            'labels': [h['name'] for h in halls_revenue],
            'revenue': [h['revenue'] for h in halls_revenue],
            'bookings': [h['bookings'] for h in halls_revenue],
            'data': halls_revenue
        })

    @api_bp.route('/admin/halls', methods=['GET'])
    @api_admin_required
    def admin_halls_list():
        """Get hall list for admin."""
        halls = Hall.query.options(selectinload(Hall.sessions)).order_by(Hall.id.asc()).all()
        return jsonify({'halls': [_serialize_hall(hall) for hall in halls]})

    @api_bp.route('/admin/halls', methods=['POST'])
    @api_admin_required
    def admin_hall_create():
        """Create a new hall."""
        data, error_response = get_json_payload()
        if error_response:
            return error_response

        name = (data.get('name') or '').strip()
        rows, rows_error = parse_int_field(data.get('rows'), 'rows', 1, 30)
        if rows_error:
            return json_error(rows_error)

        seats_per_row, seats_error = parse_int_field(data.get('seats_per_row'), 'seats_per_row', 1, 30)
        if seats_error:
            return json_error(seats_error)

        if not name:
            name = f'Р—Р°Р» {rows}x{seats_per_row}'

        base_name = name
        suffix = 2
        while Hall.query.filter_by(name=name).first():
            name = f'{base_name} {suffix}'
            suffix += 1

        hall = Hall(name=name, rows=rows, seats_per_row=seats_per_row)
        db.session.add(hall)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Р—Р°Р» СЃС‚РІРѕСЂРµРЅРѕ', 'hall': _serialize_hall(hall)}), 201

    @api_bp.route('/admin/halls/<int:hall_id>', methods=['PUT'])
    @api_admin_required
    def admin_hall_update(hall_id):
        """Update hall name or dimensions when it has no sessions."""
        hall = Hall.query.get_or_404(hall_id)
        if len(hall.sessions) > 0:
            return jsonify({'success': False, 'error': 'РќРµРјРѕР¶Р»РёРІРѕ Р·РјС–РЅРёС‚Рё Р·Р°Р», РїРѕРєРё РІ РЅСЊРѕРјСѓ С” СЃРµР°РЅСЃРё'}), 400

        data, error_response = get_json_payload()
        if error_response:
            return error_response

        name = (data.get('name') or '').strip()
        rows, rows_error = parse_int_field(data.get('rows'), 'rows', 1, 30)
        if rows_error:
            return json_error(rows_error)

        seats_per_row, seats_error = parse_int_field(data.get('seats_per_row'), 'seats_per_row', 1, 30)
        if seats_error:
            return json_error(seats_error)

        if not name:
            name = f'Р—Р°Р» {rows}x{seats_per_row}'

        base_name = name
        suffix = 2
        while Hall.query.filter(Hall.name == name, Hall.id != hall.id).first():
            name = f'{base_name} {suffix}'
            suffix += 1

        hall.name = name
        hall.rows = rows
        hall.seats_per_row = seats_per_row
        db.session.commit()

        return jsonify({'success': True, 'message': 'Р—Р°Р» РѕРЅРѕРІР»РµРЅРѕ', 'hall': _serialize_hall(hall)})

    @api_bp.route('/admin/halls/<int:hall_id>', methods=['DELETE'])
    @api_admin_required
    def admin_hall_delete(hall_id):
        """Delete a hall if it has no sessions."""
        hall = Hall.query.get_or_404(hall_id)
        sessions_count = len(hall.sessions) if hall.sessions is not None else 0
        if sessions_count:
            return jsonify({'success': False, 'error': f'РќРµРјРѕР¶Р»РёРІРѕ РІРёРґР°Р»РёС‚Рё Р·Р°Р» вЂ” С–СЃРЅСѓС” {sessions_count} СЃРµР°РЅСЃС–РІ'}), 400

        db.session.delete(hall)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Р—Р°Р» РІРёРґР°Р»РµРЅРѕ'})

    @api_bp.route('/admin/films', methods=['GET'])
    @api_admin_required
    def admin_films_list():
        """Get films list for admin."""
        films = Film.query.options(
            selectinload(Film.sessions),
            selectinload(Film.reviews),
            selectinload(Film.favorited_by)
        ).order_by(Film.id.desc()).all()

        return jsonify({'films': [{
            'id': film.id,
            'title': film.title,
            'description': film.description,
            'genre': film.genre,
            'director': film.director,
            'actors': film.actors,
            'duration': film.duration,
            'age_rating': film.age_rating,
            'release_year': film.release_year,
            'trailer': film.trailer,
            'image': f'/static/uploads/{film.image}' if film.image else None,
            'sessions_count': len(film.sessions),
            'review_count': film.review_count(),
            'average_rating': film.average_rating()
        } for film in films]})

    @api_bp.route('/admin/films', methods=['POST'])
    @api_admin_required
    def admin_film_create():
        """Create film."""
        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()

        if not title:
            return jsonify({'success': False, 'error': 'РќР°Р·РІР° РѕР±РѕРІ\'СЏР·РєРѕРІР°'}), 400
        if not description or len(description) < 10:
            return jsonify({'success': False, 'error': 'РћРїРёСЃ РјС–РЅС–РјСѓРј 10 СЃРёРјРІРѕР»С–РІ'}), 400

        duration_raw = (request.form.get('duration') or '').strip()
        release_year_raw = (request.form.get('release_year') or '').strip()

        duration = None
        if duration_raw:
            duration, duration_error = parse_int_field(duration_raw, 'duration', 1, 600)
            if duration_error:
                return json_error(duration_error)

        release_year = None
        if release_year_raw:
            current_year = datetime.now().year + 2
            release_year, year_error = parse_int_field(release_year_raw, 'release_year', 1888, current_year)
            if year_error:
                return json_error(year_error)

        filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                allowed = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                if ext not in allowed:
                    return jsonify({'success': False, 'error': 'Р”РѕР·РІРѕР»РµРЅС– С‚С–Р»СЊРєРё Р·РѕР±СЂР°Р¶РµРЅРЅСЏ (jpg, png, gif, webp)'}), 400
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

        film = Film(
            title=title,
            description=description,
            genre=(request.form.get('genre') or '').strip() or None,
            director=(request.form.get('director') or '').strip() or None,
            actors=(request.form.get('actors') or '').strip() or None,
            duration=duration,
            age_rating=(request.form.get('age_rating') or '').strip() or None,
            release_year=release_year,
            trailer=(request.form.get('trailer') or '').strip() or None,
            image=filename
        )
        db.session.add(film)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Р¤С–Р»СЊРј РґРѕРґР°РЅРѕ', 'film_id': film.id}), 201

    @api_bp.route('/admin/films/<int:film_id>', methods=['PUT'])
    @api_admin_required
    def admin_film_update(film_id):
        """Update film."""
        film = Film.query.get_or_404(film_id)

        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()

        if not title:
            return jsonify({'success': False, 'error': 'РќР°Р·РІР° РѕР±РѕРІ\'СЏР·РєРѕРІР°'}), 400
        if not description or len(description) < 10:
            return jsonify({'success': False, 'error': 'РћРїРёСЃ РјС–РЅС–РјСѓРј 10 СЃРёРјРІРѕР»С–РІ'}), 400

        duration_raw = (request.form.get('duration') or '').strip()
        release_year_raw = (request.form.get('release_year') or '').strip()

        duration = None
        if duration_raw:
            duration, duration_error = parse_int_field(duration_raw, 'duration', 1, 600)
            if duration_error:
                return json_error(duration_error)

        release_year = None
        if release_year_raw:
            current_year = datetime.now().year + 2
            release_year, year_error = parse_int_field(release_year_raw, 'release_year', 1888, current_year)
            if year_error:
                return json_error(year_error)

        film.title = title
        film.description = description
        film.genre = (request.form.get('genre') or '').strip() or None
        film.director = (request.form.get('director') or '').strip() or None
        film.actors = (request.form.get('actors') or '').strip() or None
        film.duration = duration
        film.age_rating = (request.form.get('age_rating') or '').strip() or None
        film.release_year = release_year
        film.trailer = (request.form.get('trailer') or '').strip() or film.trailer

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                allowed = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                if ext not in allowed:
                    return jsonify({'success': False, 'error': 'Р”РѕР·РІРѕР»РµРЅС– С‚С–Р»СЊРєРё Р·РѕР±СЂР°Р¶РµРЅРЅСЏ'}), 400
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                film.image = filename

        db.session.commit()
        return jsonify({'success': True, 'message': 'Р¤С–Р»СЊРј РѕРЅРѕРІР»РµРЅРѕ'})

    @api_bp.route('/admin/films/<int:film_id>', methods=['DELETE'])
    @api_admin_required
    def admin_film_delete(film_id):
        """Delete film."""
        film = Film.query.get_or_404(film_id)
        db.session.delete(film)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Р¤С–Р»СЊРј РІРёРґР°Р»РµРЅРѕ'})

    @api_bp.route('/admin/sessions', methods=['GET'])
    @api_admin_required
    def admin_sessions_list():
        """Get sessions list for admin."""
        sessions = Session.query.options(
            selectinload(Session.film),
            selectinload(Session.hall),
            selectinload(Session.seats)
        ).order_by(Session.start_time.desc()).all()
        return jsonify({'sessions': [{
            'id': s.id,
            'film_id': s.film_id,
            'film_title': s.film.title if s.film else 'Р¤С–Р»СЊРј РІРёРґР°Р»РµРЅРѕ',
            'hall_id': s.hall_id,
            'hall_name': s.hall.name if s.hall else 'РќРµРІС–РґРѕРјРёР№ Р·Р°Р»',
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
        """Create session and default seats."""
        data, error_response = get_json_payload()
        if error_response:
            return error_response

        film_id = data.get('film_id')
        hall_id = data.get('hall_id')
        start_time = (data.get('start_time') or '').strip()
        price = data.get('price')

        if not film_id or not start_time or price is None:
            return jsonify({'success': False, 'error': 'Р—Р°РїРѕРІРЅС–С‚СЊ РІСЃС– РїРѕР»СЏ'}), 400

        film_id_value, film_id_error = parse_int_field(film_id, 'film_id', 1)
        if film_id_error:
            return json_error(film_id_error)

        if parse_session_datetime(start_time) is None:
            return json_error('РџРѕР»Рµ start_time РјР°С” Р±СѓС‚Рё Сѓ С„РѕСЂРјР°С‚С– YYYY-MM-DD HH:MM')

        film = Film.query.get(film_id_value)
        if not film:
            return jsonify({'success': False, 'error': 'Р¤С–Р»СЊРј РЅРµ Р·РЅР°Р№РґРµРЅРѕ'}), 404

        hall, hall_error = _resolve_hall(hall_id)
        if hall_error:
            return hall_error

        price_value, price_error = parse_float_field(price, 'price', 0, 10000)
        if price_error:
            return json_error(price_error)

        session = Session(film_id=film_id_value, hall_id=hall.id, start_time=start_time, price=price_value, status='active')
        db.session.add(session)
        db.session.commit()

        create_seats_for_session(session.id, hall=hall)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'РЎРµР°РЅСЃ СЃС‚РІРѕСЂРµРЅРѕ ({hall.capacity()} РјС–СЃС†СЊ)',
            'session_id': session.id,
            'session': {
                'id': session.id,
                'film_id': session.film_id,
                'film_title': film.title,
                'hall_id': hall.id,
                'hall_name': hall.name,
                'start_time': session.start_time,
                'price': session.price,
                'status': session.status,
                'booked': 0,
                'available': len(session.seats),
                'total_seats': len(session.seats)
            }
        }), 201

    @api_bp.route('/admin/sessions/<int:session_id>/hall', methods=['GET'])
    @api_admin_required
    def admin_session_hall(session_id):
        """Get editable hall layout for a session."""
        session = Session.query.options(
            selectinload(Session.film),
            selectinload(Session.seats)
        ).get_or_404(session_id)

        rows, seats_per_row = _hall_dimensions(session)
        booked_count = sum(1 for seat in session.seats if seat.status == 'booked')
        blocked_count = sum(1 for seat in session.seats if seat.status == 'blocked')

        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'film_title': session.film.title,
                'hall_id': session.hall_id,
                'hall_name': session.hall.name if session.hall else 'РќРµРІС–РґРѕРјРёР№ Р·Р°Р»',
                'start_time': session.start_time,
                'price': session.price,
                'status': session.status,
                'booked_count': booked_count,
                'blocked_count': blocked_count,
                'total_seats': len(session.seats),
                'can_resize': booked_count == 0,
            },
            'layout': {
                'rows': rows,
                'seats_per_row': seats_per_row,
            },
            'seats': [
                _serialize_hall_seat(seat)
                for seat in sorted(session.seats, key=lambda s: (s.row, s.number))
            ]
        })

    @api_bp.route('/admin/sessions/<int:session_id>/hall', methods=['POST'])
    @api_admin_required
    def admin_session_hall_update(session_id):
        """Update hall layout and seat states for a session."""
        data, error_response = get_json_payload()
        if error_response:
            return error_response

        session = Session.query.options(selectinload(Session.seats)).get_or_404(session_id)
        seats_payload = data.get('seats', [])

        if not isinstance(seats_payload, list):
            return jsonify({'success': False, 'error': 'РџРѕР»Рµ seats РјР°С” Р±СѓС‚Рё СЃРїРёСЃРєРѕРј'}), 400

        current_rows, current_seats_per_row = _hall_dimensions(session)
        rows_raw = data.get('rows', current_rows)
        seats_per_row_raw = data.get('seats_per_row', current_seats_per_row)

        rows, rows_error = parse_int_field(rows_raw, 'rows', 1, 30)
        if rows_error:
            return json_error(rows_error)

        seats_per_row, seats_error = parse_int_field(seats_per_row_raw, 'seats_per_row', 1, 30)
        if seats_error:
            return json_error(seats_error)

        requested_layout_changed = rows != current_rows or seats_per_row != current_seats_per_row
        booked_count = sum(1 for seat in session.seats if seat.status == 'booked')

        if requested_layout_changed and booked_count > 0:
            return jsonify({
                'success': False,
                'error': 'РќРµРјРѕР¶Р»РёРІРѕ Р·РјС–РЅРёС‚Рё СЂРѕР·РјС–СЂ Р·Р°Р»Сѓ, РїРѕРєРё С” Р·Р°Р±СЂРѕРЅСЊРѕРІР°РЅС– РјС–СЃС†СЏ. РЎРїРµСЂС€Сѓ СЃРєР°СЃСѓР№С‚Рµ Р±СЂРѕРЅСЋРІР°РЅРЅСЏ Р°Р±Рѕ СЃС‚РІРѕСЂС–С‚СЊ РЅРѕРІРёР№ СЃРµР°РЅСЃ.'
            }), 400

        seat_map = {}
        for item in seats_payload:
            if not isinstance(item, dict):
                return jsonify({'success': False, 'error': 'РљРѕР¶РЅРµ РјС–СЃС†Рµ РјР°С” Р±СѓС‚Рё РѕР±вЂ™С”РєС‚РѕРј'}), 400

            row_value, row_error = parse_int_field(item.get('row'), 'row', 1, 30)
            if row_error:
                return json_error(row_error)

            number_value, number_error = parse_int_field(item.get('number'), 'number', 1, 30)
            if number_error:
                return json_error(number_error)

            status = (item.get('status') or 'free').strip().lower()
            if status not in SEAT_LAYOUT_STATUSES and status != 'booked':
                return jsonify({'success': False, 'error': 'РќРµРІС–СЂРЅРёР№ СЃС‚Р°С‚СѓСЃ РјС–СЃС†СЏ'}), 400

            seat_map[(row_value, number_value)] = status

        if requested_layout_changed:
            db.session.query(Seat).filter(Seat.session_id == session.id).delete(synchronize_session=False)
            db.session.flush()
            create_seats_for_session(session.id, rows=rows, seats_per_row=seats_per_row)
            db.session.flush()
            session = Session.query.options(selectinload(Session.seats)).get(session_id)

        existing_coords = {(seat.row, seat.number): seat for seat in session.seats}
        for coords, status in seat_map.items():
            seat = existing_coords.get(coords)
            if not seat:
                if requested_layout_changed:
                    continue
                return jsonify({'success': False, 'error': f'РњС–СЃС†Рµ СЂСЏРґ {coords[0]}, РЅРѕРјРµСЂ {coords[1]} РЅРµ С–СЃРЅСѓС” РІ С†С–Р№ СЃС…РµРјС–'}), 400
            if seat.status == 'booked' and status != 'booked':
                return jsonify({'success': False, 'error': f'РќРµРјРѕР¶Р»РёРІРѕ Р·РјС–РЅРёС‚Рё Р·Р°Р±СЂРѕРЅСЊРѕРІР°РЅРµ РјС–СЃС†Рµ СЂСЏРґ {seat.row}, РЅРѕРјРµСЂ {seat.number}'}), 400
            if seat.status != 'booked':
                seat.status = 'blocked' if status == 'blocked' else 'free'

        if requested_layout_changed:
            for seat in session.seats:
                coords = (seat.row, seat.number)
                status = seat_map.get(coords)
                if status == 'blocked':
                    seat.status = 'blocked'

        db.session.commit()

        updated_rows, updated_seats_per_row = _hall_dimensions(session)
        booked_count = sum(1 for seat in session.seats if seat.status == 'booked')
        blocked_count = sum(1 for seat in session.seats if seat.status == 'blocked')

        return jsonify({
            'success': True,
            'message': 'РЎС…РµРјСѓ Р·Р°Р»Сѓ РѕРЅРѕРІР»РµРЅРѕ',
            'session_id': session.id,
            'layout': {
                'rows': updated_rows,
                'seats_per_row': updated_seats_per_row,
                'total_seats': len(session.seats),
                'booked_count': booked_count,
                'blocked_count': blocked_count,
            }
        })

    @api_bp.route('/admin/sessions/<int:session_id>/cancel', methods=['POST'])
    @api_admin_required
    def admin_session_cancel(session_id):
        """Cancel session and rollback user bookings."""
        session = Session.query.get_or_404(session_id)

        if session.status == 'cancelled':
            return jsonify({'success': False, 'error': 'РЎРµР°РЅСЃ РІР¶Рµ СЃРєР°СЃРѕРІР°РЅРѕ'}), 400

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
        except Exception as exc:
            current_app.logger.error(f'РџРѕРјРёР»РєР° РІС–РґРїСЂР°РІРєРё email: {exc}')

        return jsonify({
            'success': True,
            'message': f'РЎРµР°РЅСЃ СЃРєР°СЃРѕРІР°РЅРѕ. РџРѕРІС–РґРѕРјР»РµРЅРѕ {len(affected_users)} РєРѕСЂРёСЃС‚СѓРІР°С‡С–РІ.'
        })

    @api_bp.route('/admin/calendar', methods=['GET'])
    @api_admin_required
    def admin_calendar():
        """Get sessions calendar view."""
        from datetime import datetime, timedelta

        week_offset = request.args.get('week', 0, type=int)
        if week_offset < -52 or week_offset > 52:
            return json_error('РџР°СЂР°РјРµС‚СЂ week РјР°С” Р±СѓС‚Рё РІ РјРµР¶Р°С… РІС–Рґ -52 РґРѕ 52')

        hall_id = request.args.get('hall_id', type=int)
        halls_query = Hall.query.order_by(Hall.id.asc())
        halls = halls_query.all()
        if not halls:
            return jsonify({
                'success': True,
                'week_days': [],
                'time_slots': [],
                'sessions_grid': {},
                'films': [],
                'halls': [],
                'selected_hall_id': None,
                'selected_hall': None,
                'week_offset': week_offset,
                'start_of_week': None,
            })

        selected_hall = None
        if hall_id is not None:
            selected_hall = Hall.query.get(hall_id)
            if not selected_hall:
                return jsonify({'success': False, 'error': 'Р—Р°Р» РЅРµ Р·РЅР°Р№РґРµРЅРѕ'}), 404
        else:
            selected_hall = halls[0]

        today = datetime.now().date()
        days_since_monday = today.weekday()
        start_of_week = today - timedelta(days=days_since_monday) + timedelta(weeks=week_offset)

        week_days = []
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            week_days.append({
                'date': day.isoformat(),
                'day_name': ['РџРЅ', 'Р’С‚', 'РЎСЂ', 'Р§С‚', 'РџС‚', 'РЎР±', 'РќРґ'][day.weekday()],
                'full_date': day.strftime('%d.%m.%Y')
            })

        time_slots = [f'{hour:02d}:00' for hour in range(9, 24, 3)]

        end_of_week = start_of_week + timedelta(days=7)
        all_sessions = Session.query.join(Film).filter(
            Session.hall_id == selected_hall.id,
            Session.start_time >= start_of_week.strftime('%Y-%m-%d'),
            Session.start_time < end_of_week.strftime('%Y-%m-%d')
        ).all()

        sessions_grid = {}
        for session in all_sessions:
            try:
                session_datetime = datetime.strptime(session.start_time, '%Y-%m-%d %H:%M')
                session_date = session_datetime.date()

                hour = session_datetime.hour
                if hour < 12:
                    slot_hour = 9
                elif hour < 15:
                    slot_hour = 12
                elif hour < 18:
                    slot_hour = 15
                elif hour < 21:
                    slot_hour = 18
                else:
                    slot_hour = 21

                session_time = f'{slot_hour:02d}:00'
                key = f'{session_date.isoformat()}#{session_time}'
                sessions_grid.setdefault(key, []).append({
                    'id': session.id,
                    'film_title': session.film.title,
                    'exact_time': session_datetime.strftime('%H:%M'),
                    'price': session.price,
                    'status': session.status,
                    'booked': session.booked_seats_count(),
                    'available': session.available_seats_count()
                })
            except Exception:
                continue

        films = Film.query.all()

        return jsonify({
            'success': True,
            'week_days': week_days,
            'time_slots': time_slots,
            'sessions_grid': sessions_grid,
            'films': [{'id': f.id, 'title': f.title} for f in films],
            'halls': [_serialize_hall(hall) for hall in halls],
            'selected_hall_id': selected_hall.id,
            'selected_hall': _serialize_hall(selected_hall),
            'week_offset': week_offset,
            'start_of_week': start_of_week.isoformat()
        })

    @api_bp.route('/admin/calendar/create-session', methods=['POST'])
    @api_admin_required
    def admin_calendar_create_session():
        """Quick create session from calendar view."""
        data, error_response = get_json_payload()
        if error_response:
            return error_response

        film_id = data.get('film_id')
        hall_id = data.get('hall_id')
        date = (data.get('date') or '').strip()
        time = (data.get('time') or '').strip()
        price = data.get('price')

        if not all([film_id, date, time, price]):
            return jsonify({'success': False, 'error': 'Р—Р°РїРѕРІРЅС–С‚СЊ РІСЃС– РїРѕР»СЏ'}), 400

        film_id_value, film_id_error = parse_int_field(film_id, 'film_id', 1)
        if film_id_error:
            return json_error(film_id_error)

        price_value, price_error = parse_float_field(price, 'price', 0, 10000)
        if price_error:
            return json_error(price_error)

        start_time = f'{date} {time}'
        if parse_session_datetime(start_time) is None:
            return json_error('РќРµРІС–СЂРЅРёР№ С„РѕСЂРјР°С‚ РґР°С‚Рё/С‡Р°СЃСѓ. РћС‡С–РєСѓС”С‚СЊСЃСЏ YYYY-MM-DD С‚Р° HH:MM')

        film = Film.query.get(film_id_value)
        if not film:
            return jsonify({'success': False, 'error': 'Р¤С–Р»СЊРј РЅРµ Р·РЅР°Р№РґРµРЅРѕ'}), 404

        hall, hall_error = _resolve_hall(hall_id)
        if hall_error:
            return hall_error

        try:
            session = Session(film_id=film_id_value, hall_id=hall.id, start_time=start_time, price=price_value, status='active')
            db.session.add(session)
            db.session.commit()

            create_seats_for_session(session.id, hall=hall)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'РЎРµР°РЅСЃ СЃС‚РІРѕСЂРµРЅРѕ РЅР° {start_time}',
                'session_id': session.id,
                'hall_id': hall.id,
                'hall_name': hall.name
            })
        except Exception as exc:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(exc)}), 500
