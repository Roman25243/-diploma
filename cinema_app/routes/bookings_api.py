from flask import jsonify, url_for as flask_url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from extensions import db
from models import Booking, Seat, Session
from services.api_common import (
    get_json_payload,
    is_session_in_past,
    pricing_for_session,
)


def register_bookings_routes(api_bp):
    @api_bp.route('/sessions/<int:session_id>/seats', methods=['GET'])
    @login_required
    def get_seats(session_id):
        """Get all seats for session."""
        session = Session.query.options(
            joinedload(Session.film),
            selectinload(Session.seats)
        ).get_or_404(session_id)

        if session.status == 'cancelled':
            return jsonify({'error': 'Сеанс скасовано'}), 400
        if is_session_in_past(session):
            return jsonify({'error': 'Сеанс вже завершився'}), 400

        seats = sorted(session.seats, key=lambda s: (s.row, s.number))
        booked_seat_ids = {
            seat_id for (seat_id,) in db.session.query(Booking.seat_id)
            .join(Seat)
            .filter(Seat.session_id == session_id)
            .all()
        }
        existing_bookings = Booking.query.join(Seat).filter(
            Seat.session_id == session_id,
            Booking.user_id == current_user.id
        ).count()

        pricing = pricing_for_session(session, current_user)

        return jsonify({
            'session': {
                'id': session.id,
                'film_title': session.film.title,
                'start_time': session.start_time,
                'price': pricing['dynamic_price'],
                'base_price': pricing['base_price'],
                'pricing': pricing,
                'available_seats': sum(1 for seat in seats if seat.status == 'free')
            },
            'seats': [{
                'id': seat.id,
                'row': seat.row,
                'number': seat.number,
                'status': 'booked' if (seat.status == 'booked' or seat.id in booked_seat_ids) else ('blocked' if seat.status == 'blocked' else 'free')
            } for seat in seats],
            'user_bookings': {
                'count': existing_bookings,
                'remaining_slots': 5 - existing_bookings
            }
        })

    @api_bp.route('/sessions/<int:session_id>/book', methods=['POST'])
    @login_required
    def book_seats(session_id):
        """Book selected seats for current user."""
        data, error_response = get_json_payload()
        if error_response:
            return error_response

        selected_seat_ids = data.get('seat_ids', [])
        if not isinstance(selected_seat_ids, list):
            return jsonify({'success': False, 'error': 'Поле seat_ids має бути списком ID місць'}), 400

        if not all(isinstance(seat_id, int) and seat_id > 0 for seat_id in selected_seat_ids):
            return jsonify({'success': False, 'error': 'У seat_ids дозволені лише додатні числові ID місць'}), 400

        selected_seat_ids = list(dict.fromkeys(selected_seat_ids))
        if not selected_seat_ids:
            return jsonify({'error': 'Оберіть хоча б одне місце'}), 400

        session = Session.query.get_or_404(session_id)
        if session.status == 'cancelled':
            return jsonify({'error': 'Сеанс скасовано'}), 400
        if is_session_in_past(session):
            return jsonify({'error': 'Неможливо бронювати місця на минулий сеанс'}), 400

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

        pricing = pricing_for_session(session, current_user)
        booked_count = 0
        successfully_booked = []
        created_booking_ids = []

        for seat_id in selected_seat_ids:
            seat = Seat.query.with_for_update().get(seat_id)
            if not seat or seat.session_id != session_id:
                continue

            if seat.status != 'free':
                booked_count += 1
            else:
                savepoint = db.session.begin_nested()
                try:
                    seat.status = 'booked'
                    booking = Booking(user_id=current_user.id, seat_id=seat.id, payment_status='unpaid')
                    db.session.add(booking)
                    db.session.flush()
                    created_booking_ids.append(booking.id)
                    savepoint.commit()
                    successfully_booked.append({'row': seat.row, 'number': seat.number})
                except IntegrityError:
                    savepoint.rollback()
                    booked_count += 1
                    db.session.expire(seat)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Частина місць вже зайнята. Спробуйте обрати інші місця.',
                'booked_seats': successfully_booked,
                'total_booked': len(successfully_booked)
            }), 409

        total_amount = round(pricing['dynamic_price'] * len(successfully_booked), 2)

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
            'booking_ids': created_booking_ids,
            'total_booked': len(successfully_booked),
            'pricing': {
                **pricing,
                'seats_count': len(successfully_booked),
                'total_amount': total_amount
            }
        })

    @api_bp.route('/user/profile', methods=['GET'])
    @login_required
    def get_profile():
        """Get user profile and bookings."""
        all_bookings = Booking.query.filter_by(user_id=current_user.id).options(
            joinedload(Booking.seat).joinedload(Seat.session).joinedload(Session.film)
        ).all()

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
                'is_cancelled': b.seat.session.status == 'cancelled',
                'payment_status': b.payment_status,
                'ticket': {
                    'id': b.ticket.id,
                    'status': b.ticket.status,
                    'token': b.ticket.token,
                    'qr_url': f'/api/tickets/{b.ticket.token}/qr'
                } if b.ticket else None
            } for b in all_bookings]
        })

    @api_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
    @login_required
    def cancel_booking(booking_id):
        """Cancel booking by id."""
        booking = Booking.query.get_or_404(booking_id)

        if booking.user_id != current_user.id:
            return jsonify({'error': 'Немає прав'}), 403

        if booking.seat.session.status == 'cancelled':
            return jsonify({'error': 'Сеанс вже скасовано'}), 400

        booking.seat.status = 'free'
        db.session.delete(booking)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Бронювання скасовано'})
