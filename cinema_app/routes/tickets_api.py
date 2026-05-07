from datetime import datetime
from io import BytesIO
import importlib
import re
from urllib.parse import urlparse

from flask import jsonify, render_template, send_file, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Ticket


def _normalize_ticket_token(value):
    raw_value = (value or '').strip()
    if raw_value.startswith('cinemabook:ticket:'):
        return raw_value.split('cinemabook:ticket:', 1)[1].strip()

    parsed = urlparse(raw_value)
    path_value = parsed.path if parsed.scheme else raw_value
    match = re.search(r'/api/tickets/([^/?#]+)', path_value)
    if match:
        return match.group(1).strip()

    return raw_value


def register_tickets_routes(api_bp):
    @api_bp.route('/tickets/<string:token>', methods=['GET'])
    def public_ticket_view(token):
        """Public ticket landing page that phone scanners can open in a browser."""
        ticket = Ticket.query.filter_by(token=_normalize_ticket_token(token)).first_or_404()
        booking = ticket.booking
        session = booking.seat.session

        return render_template(
            'tickets/ticket_public.html',
            ticket=ticket,
            booking=booking,
            session=session,
            ticket_url=url_for('api.public_ticket_view', token=ticket.token, _external=True),
        )

    @api_bp.route('/user/tickets', methods=['GET'])
    @login_required
    def get_user_tickets():
        """List all tickets for current user."""
        tickets = Ticket.query.join(Ticket.booking).filter(
            Ticket.booking.has(user_id=current_user.id)
        ).order_by(Ticket.issued_at.desc()).all()

        return jsonify({
            'tickets': [{
                'id': t.id,
                'token': t.token,
                'status': t.status,
                'issued_at': t.issued_at.isoformat() if t.issued_at else None,
                'scanned_at': t.scanned_at.isoformat() if t.scanned_at else None,
                'scan_count': t.scan_count,
                'booking_id': t.booking_id,
                'session_time': t.booking.seat.session.start_time,
                'film_title': t.booking.seat.session.film.title,
                'seat_row': t.booking.seat.row,
                'seat_number': t.booking.seat.number,
                'qr_url': f'/api/tickets/{t.token}/qr'
            } for t in tickets]
        })

    @api_bp.route('/tickets/<string:token>/qr', methods=['GET'])
    @login_required
    def get_ticket_qr(token):
        """Render ticket QR as PNG for owner or admin."""
        ticket = Ticket.query.filter_by(token=token).first_or_404()

        if ticket.booking.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Немає доступу до квитка'}), 403

        try:
            qrcode = importlib.import_module('qrcode')
        except ImportError:
            return jsonify({'success': False, 'error': 'Пакет qrcode не встановлено'}), 500

        payload = url_for('api.public_ticket_view', token=ticket.token, _external=True)
        img = qrcode.make(payload)

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return send_file(buffer, mimetype='image/png', download_name=f'ticket-{ticket.id}.png')

    @api_bp.route('/admin/tickets/scan', methods=['POST'])
    @login_required
    def scan_ticket():
        """Validate and mark ticket as used (admin only)."""
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Доступ заборонено'}), 403

        from services.api_common import get_json_payload

        data, error_response = get_json_payload()
        if error_response:
            return error_response

        token = _normalize_ticket_token(data.get('token'))

        if not token:
            return jsonify({'success': False, 'error': 'Передайте token'}), 400

        ticket = Ticket.query.filter_by(token=token).first()
        if not ticket:
            return jsonify({'success': False, 'error': 'Квиток не знайдено'}), 404

        booking = ticket.booking
        session = booking.seat.session

        if booking.payment_status != 'paid':
            return jsonify({'success': False, 'error': 'Квиток не оплачений'}), 400

        if session.status == 'cancelled':
            return jsonify({'success': False, 'error': 'Сеанс скасовано'}), 400

        if ticket.status == 'used':
            return jsonify({
                'success': False,
                'error': 'Квиток вже використано',
                'ticket': {
                    'id': ticket.id,
                    'token': ticket.token,
                    'status': ticket.status,
                    'scanned_at': ticket.scanned_at.isoformat() if ticket.scanned_at else None,
                    'film_title': session.film.title,
                    'session_time': session.start_time,
                    'seat_row': booking.seat.row,
                    'seat_number': booking.seat.number,
                }
            }), 409

        ticket.status = 'used'
        ticket.scanned_at = datetime.utcnow()
        ticket.scanned_by_id = current_user.id
        ticket.scan_count = (ticket.scan_count or 0) + 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Квиток валідний. Вхід дозволено.',
            'ticket': {
                'id': ticket.id,
                'token': ticket.token,
                'status': ticket.status,
                'scanned_at': ticket.scanned_at.isoformat() if ticket.scanned_at else None,
                'film_title': session.film.title,
                'session_time': session.start_time,
                'seat_row': booking.seat.row,
                'seat_number': booking.seat.number,
                'user_name': booking.user.name,
            }
        })
