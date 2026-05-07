from datetime import datetime
import secrets

from extensions import db
from models import Ticket


def _generate_ticket_token():
    return secrets.token_urlsafe(24)


def issue_ticket_for_booking(booking):
    """Issue ticket for a paid booking if it doesn't exist yet."""
    if booking.payment_status != 'paid':
        return None

    if booking.ticket:
        return booking.ticket

    ticket = Ticket(
        booking_id=booking.id,
        token=_generate_ticket_token(),
        status='active',
        issued_at=datetime.utcnow(),
        scan_count=0,
    )
    db.session.add(ticket)
    return ticket


def issue_tickets_for_payment(payment):
    """Issue tickets for all paid bookings in transaction."""
    issued = []
    for booking in payment.bookings:
        ticket = issue_ticket_for_booking(booking)
        if ticket:
            issued.append(ticket)
    return issued
