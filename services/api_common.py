from datetime import datetime

from flask import jsonify, request, url_for as flask_url_for

from extensions import db
from models import Booking, Seat


def json_error(message, status=400):
    """Unified JSON error response."""
    return jsonify({'success': False, 'error': message}), status


def get_json_payload():
    """Safely parse JSON payload from request."""
    if not request.is_json:
        return None, json_error('Очікується JSON payload')

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, json_error('Невірний JSON формат')
    return data, None


def parse_int_field(raw_value, field_name, min_value=None, max_value=None):
    """Parse int field and validate optional range."""
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None, f'Поле {field_name} має бути цілим числом'

    if min_value is not None and value < min_value:
        return None, f'Поле {field_name} має бути не менше {min_value}'
    if max_value is not None and value > max_value:
        return None, f'Поле {field_name} має бути не більше {max_value}'
    return value, None


def parse_float_field(raw_value, field_name, min_value=None, max_value=None):
    """Parse float field and validate optional range."""
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None, f'Поле {field_name} має бути числом'

    if min_value is not None and value < min_value:
        return None, f'Поле {field_name} має бути не менше {min_value}'
    if max_value is not None and value > max_value:
        return None, f'Поле {field_name} має бути не більше {max_value}'
    return value, None


def parse_session_datetime(start_time_str):
    """Parse session datetime from supported formats."""
    if not start_time_str:
        return None

    normalized = start_time_str.replace('T', ' ').strip()
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def is_session_in_past(session):
    """Check whether session has already started."""
    session_dt = parse_session_datetime(session.start_time)
    if not session_dt:
        return False
    return session_dt < datetime.now()


def time_multiplier(session):
    """Calculate time-based dynamic pricing multiplier."""
    session_dt = parse_session_datetime(session.start_time)
    if not session_dt:
        return 1.0, 'standard'

    hour = session_dt.hour
    if 9 <= hour < 12:
        return 0.9, 'morning'
    if 12 <= hour < 17:
        return 1.0, 'daytime'
    if 17 <= hour < 22:
        return 1.25, 'prime_time'
    return 1.05, 'late'


def demand_multiplier(session):
    """Calculate demand-based dynamic pricing multiplier."""
    total_seats = len(session.seats)
    if total_seats == 0:
        return 1.0, 0.0

    booked_ratio = session.booked_seats_count() / total_seats
    if booked_ratio < 0.3:
        return 0.9, booked_ratio
    if booked_ratio < 0.6:
        return 1.0, booked_ratio
    if booked_ratio < 0.85:
        return 1.15, booked_ratio
    return 1.3, booked_ratio


def pricing_for_session(session, user=None, loyalty_data=None):
    """Calculate dynamic price: time x demand."""
    base_price = float(session.price or 0)

    t_mult, time_band = time_multiplier(session)
    d_mult, occupancy = demand_multiplier(session)

    dynamic_price = round(base_price * t_mult * d_mult, 2)

    return {
        'base_price': round(base_price, 2),
        'dynamic_price': dynamic_price,
        'time_multiplier': t_mult,
        'time_band': time_band,
        'demand_multiplier': d_mult,
        'occupancy_ratio': round(occupancy, 4)
    }


def film_to_dict(film, user=None):
    """Serialize film model to API dict."""
    is_auth = bool(user and user.is_authenticated)
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
        'is_favorite': film.is_favorited_by(user) if is_auth else False
    }


def create_seats_for_session(session_id, rows=10, seats_per_row=12, hall=None):
    """Create default hall seats for a new session."""
    if hall is not None:
        rows = hall.rows
        seats_per_row = hall.seats_per_row

    for row in range(1, rows + 1):
        for num in range(1, seats_per_row + 1):
            db.session.add(Seat(session_id=session_id, row=row, number=num, status='free'))
