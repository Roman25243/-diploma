from datetime import datetime
import importlib
import secrets
from urllib.parse import urljoin

from flask import current_app, jsonify, redirect, request
from flask_login import current_user, login_required

from extensions import csrf, db
from models import Booking, PaymentTransaction
from services.api_common import get_json_payload
from services.ticket_service import issue_tickets_for_payment
from utils import send_ticket_email


def _normalize_base_url(value):
    base_url = (value or '').strip()
    return base_url.rstrip('/')


def _build_absolute_url(base_url, path):
    if not path:
        return _normalize_base_url(base_url)
    if path.startswith(('http://', 'https://')):
        return path

    normalized_base = _normalize_base_url(base_url)
    normalized_path = path if path.startswith('/') else f'/{path}'
    if not normalized_base:
        return normalized_path
    return urljoin(f'{normalized_base}/', normalized_path.lstrip('/'))


def _resolve_payment_provider():
    configured_provider = (current_app.config.get('PAYMENT_PROVIDER') or '').strip().lower()
    if configured_provider:
        return configured_provider
    if current_app.config.get('STRIPE_SECRET_KEY'):
        return 'stripe'
    return 'mock'


def _mark_payment_paid(payment):
    """Mark payment as paid idempotently and sync related bookings."""
    if payment.status == 'paid':
        return []

    payment.status = 'paid'
    payment.paid_at = datetime.utcnow()

    for booking in payment.bookings:
        booking.payment_status = 'paid'

    return issue_tickets_for_payment(payment)


def _mark_payment_failed(payment):
    """Mark payment as failed and sync related bookings."""
    if payment.status == 'paid':
        return

    payment.status = 'failed'
    for booking in list(payment.bookings):
        if booking.payment_status != 'paid':
            booking.payment_status = 'failed'
            booking.seat.status = 'free'
            db.session.delete(booking)


def _create_stripe_checkout_session(payment, seats_count):
    """Create Stripe Checkout session and return hosted checkout URL."""
    try:
        stripe = importlib.import_module('stripe')
    except ImportError:
        return None, 'Stripe SDK не встановлено. Додайте пакет stripe у requirements та перевстановіть залежності.'

    stripe_secret_key = current_app.config.get('STRIPE_SECRET_KEY') or ''
    if not stripe_secret_key:
        return None, 'Не налаштовано STRIPE_SECRET_KEY'

    stripe.api_key = stripe_secret_key

    public_app_base = current_app.config.get('PAYMENT_APP_BASE_URL') or request.host_url
    success_url = _build_absolute_url(public_app_base, current_app.config.get('PAYMENT_SUCCESS_URL') or '/app/profile?payment=success')
    cancel_url = _build_absolute_url(public_app_base, current_app.config.get('PAYMENT_CANCEL_URL') or '/app/profile?payment=cancel')

    try:
        checkout_session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': (payment.currency or 'UAH').lower(),
                    'product_data': {
                        'name': f'Cinema tickets ({seats_count} seats)'
                    },
                    'unit_amount': int(round(float(payment.amount) * 100)),
                },
                'quantity': 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'provider_order_id': payment.provider_order_id,
                'payment_id': str(payment.id),
                'user_id': str(payment.user_id),
            },
            client_reference_id=str(payment.user_id),
        )
    except Exception as exc:
        return None, f'Не вдалося створити Stripe Checkout: {exc}'

    payment.provider_payment_id = checkout_session.id
    return checkout_session.url, None


def _handle_stripe_webhook():
    """Validate and process Stripe webhook event."""
    try:
        stripe = importlib.import_module('stripe')
    except ImportError:
        return jsonify({'success': False, 'error': 'Stripe SDK не встановлено'}), 500

    stripe_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET') or ''
    if not stripe_secret:
        return jsonify({'success': False, 'error': 'Не налаштовано STRIPE_WEBHOOK_SECRET'}), 500

    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature', '')

    try:
        event = stripe.Webhook.construct_event(payload, signature, stripe_secret)
    except Exception:
        return jsonify({'success': False, 'error': 'Невірний підпис webhook'}), 400

    event_type = event.get('type')
    data_obj = event.get('data', {}).get('object', {})
    metadata = data_obj.get('metadata') or {}
    order_id = metadata.get('provider_order_id')

    if not order_id:
        return jsonify({'success': False, 'error': 'В webhook відсутній provider_order_id'}), 400

    payment = PaymentTransaction.query.filter_by(provider_order_id=order_id).first()
    if not payment:
        return jsonify({'success': False, 'error': 'Транзакцію не знайдено'}), 404

    stripe_session_id = data_obj.get('id')
    if stripe_session_id:
        payment.provider_payment_id = stripe_session_id

    issued_tickets = []

    if event_type == 'checkout.session.completed':
        issued_tickets = _mark_payment_paid(payment)
    elif event_type in {'checkout.session.async_payment_failed', 'checkout.session.expired'}:
        _mark_payment_failed(payment)

    db.session.commit()

    if issued_tickets:
        for ticket in issued_tickets:
            send_ticket_email(ticket.booking.user, ticket, current_app._get_current_object())

    return jsonify({'success': True})


def register_payments_routes(api_bp):
    @api_bp.route('/payments/create-checkout', methods=['POST'])
    @login_required
    def create_checkout():
        """Create payment transaction and return checkout URL."""
        if not current_app.config.get('PAYMENT_ONLINE_ENABLED', False):
            return jsonify({'success': False, 'error': 'Онлайн-оплату тимчасово вимкнено'}), 503

        data, error_response = get_json_payload()
        if error_response:
            return error_response

        booking_ids = data.get('booking_ids', [])
        if not isinstance(booking_ids, list) or not booking_ids:
            return jsonify({'success': False, 'error': 'Передайте непорожній список booking_ids'}), 400

        clean_ids = list(dict.fromkeys(booking_ids))
        if not all(isinstance(i, int) and i > 0 for i in clean_ids):
            return jsonify({'success': False, 'error': 'booking_ids має містити лише додатні числові ID'}), 400

        bookings = Booking.query.filter(
            Booking.id.in_(clean_ids),
            Booking.user_id == current_user.id
        ).all()

        if len(bookings) != len(clean_ids):
            return jsonify({'success': False, 'error': 'Деякі бронювання не знайдено або недоступні'}), 404

        unpaid_bookings = [b for b in bookings if b.payment_status != 'paid']
        if not unpaid_bookings:
            return jsonify({'success': False, 'error': 'Усі вибрані бронювання вже оплачені'}), 400

        total_amount = round(sum(float(b.seat.session.price or 0) for b in unpaid_bookings), 2)
        if total_amount <= 0:
            return jsonify({'success': False, 'error': 'Некоректна сума до оплати'}), 400

        provider_order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
        checkout_token = secrets.token_urlsafe(24)

        payment = PaymentTransaction(
            user_id=current_user.id,
            amount=total_amount,
            currency=current_app.config.get('PAYMENT_CURRENCY', 'UAH'),
            status='pending',
            provider=_resolve_payment_provider(),
            provider_order_id=provider_order_id,
            checkout_token=checkout_token
        )
        db.session.add(payment)
        db.session.flush()

        for booking in unpaid_bookings:
            booking.payment_id = payment.id
            booking.payment_status = 'pending'

        checkout_url = None

        if payment.provider == 'stripe':
            checkout_url, stripe_error = _create_stripe_checkout_session(payment, len(unpaid_bookings))
            if stripe_error:
                db.session.rollback()
                return jsonify({'success': False, 'error': stripe_error}), 500
        else:
            checkout_url = _build_absolute_url(request.host_url, f'/api/payments/mock/checkout/{checkout_token}')

        db.session.commit()

        return jsonify({
            'success': True,
            'payment': {
                'id': payment.id,
                'status': payment.status,
                'amount': payment.amount,
                'currency': payment.currency,
                'provider_order_id': payment.provider_order_id,
                'checkout_url': checkout_url
            }
        })

    @api_bp.route('/payments/mock/checkout/<string:token>', methods=['GET'])
    @login_required
    def mock_checkout(token):
        """MVP checkout for local/dev: confirms payment immediately."""
        payment = PaymentTransaction.query.filter_by(checkout_token=token, user_id=current_user.id).first_or_404()

        issued_tickets = _mark_payment_paid(payment)
        db.session.commit()

        for ticket in issued_tickets:
            send_ticket_email(ticket.booking.user, ticket, current_app._get_current_object())

        success_url = current_app.config.get('PAYMENT_SUCCESS_URL') or _build_absolute_url(
            current_app.config.get('PAYMENT_APP_BASE_URL') or request.host_url,
            '/app/profile?payment=success'
        )
        return redirect(success_url)

    @api_bp.route('/payments/webhook', methods=['POST'])
    @csrf.exempt
    def payment_webhook():
        """Webhook endpoint for payment providers."""
        provider = _resolve_payment_provider()
        if provider == 'stripe':
            return _handle_stripe_webhook()

        expected_secret = current_app.config.get('PAYMENT_WEBHOOK_SECRET') or ''
        request_secret = request.headers.get('X-Webhook-Secret', '')

        if expected_secret and request_secret != expected_secret:
            return jsonify({'success': False, 'error': 'Невірний webhook secret'}), 403

        payload = request.get_json(silent=True) or {}
        order_id = payload.get('order_id')
        status = payload.get('status')

        if not order_id or status not in {'paid', 'failed'}:
            return jsonify({'success': False, 'error': 'Некоректний payload webhook'}), 400

        payment = PaymentTransaction.query.filter_by(provider_order_id=order_id).first()
        if not payment:
            return jsonify({'success': False, 'error': 'Транзакцію не знайдено'}), 404

        if status == 'paid':
            _mark_payment_paid(payment)
        else:
            _mark_payment_failed(payment)

        db.session.commit()
        return jsonify({'success': True})
