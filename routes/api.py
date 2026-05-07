"""API blueprint aggregator.

This module keeps a stable import path for `api_bp` while splitting handlers
into focused modules.
"""

from flask import Blueprint

from extensions import csrf

from routes.admin_api import register_admin_routes
from routes.auth_api import register_auth_routes
from routes.bookings_api import register_bookings_routes
from routes.films_api import register_films_routes
from routes.payments_api import register_payments_routes
from routes.tickets_api import register_tickets_routes

api_bp = Blueprint('api', __name__, url_prefix='/api')
csrf.exempt(api_bp)

register_auth_routes(api_bp)
register_films_routes(api_bp)
register_bookings_routes(api_bp)
register_payments_routes(api_bp)
register_tickets_routes(api_bp)
register_admin_routes(api_bp)
