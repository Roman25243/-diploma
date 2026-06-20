from flask import jsonify, request, url_for as flask_url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from extensions import cache, db
from models import Booking, Favorite, Film, Review, Seat, Session
from services.api_common import (
    film_to_dict,
    get_json_payload,
    is_session_in_past,
    parse_int_field,
    pricing_for_session,
)


def register_films_routes(api_bp):
    @api_bp.route('/films/popular', methods=['GET'])
    @cache.cached(timeout=3600)
    def get_popular_films():
        """Get top-4 popular films by bookings count."""
        popular_films = db.session.query(Film)\
            .outerjoin(Session).outerjoin(Seat).outerjoin(Booking)\
            .options(
                selectinload(Film.reviews),
                selectinload(Film.favorited_by)
            )\
            .group_by(Film.id)\
            .order_by(func.count(Booking.id).desc())\
            .limit(4).all()

        if len(popular_films) < 4:
            popular_films = Film.query.options(
                selectinload(Film.reviews),
                selectinload(Film.favorited_by)
            ).order_by(Film.id.desc()).limit(4).all()

        return jsonify({
            'films': [{
                'id': f.id,
                'title': f.title,
                'description': f.description,
                'image': flask_url_for('static', filename='uploads/' + f.image) if f.image else None,
                'genre': f.genre,
                'duration': f.duration,
                'release_year': f.release_year,
                'average_rating': f.average_rating(),
                'review_count': f.review_count(),
                'is_favorite': f.is_favorited_by(current_user) if current_user.is_authenticated else False
            } for f in popular_films]
        })

    @cache.cached(timeout=3600)
    def get_genres_cached():
        all_genres = db.session.query(Film.genre).filter(Film.genre.isnot(None)).distinct().all()
        return sorted([g[0] for g in all_genres if g[0]])

    @api_bp.route('/genres', methods=['GET'])
    @cache.cached(timeout=3600)
    def get_genres():
        """Get all genres list."""
        return jsonify({'genres': get_genres_cached()})

    @api_bp.route('/films', methods=['GET'])
    def get_films():
        """Get films list with search and genre filters."""
        query = request.args.get('q', '').strip()
        genre = request.args.get('genre', '').strip()

        films_query = Film.query.options(
            selectinload(Film.reviews),
            selectinload(Film.favorited_by)
        )

        if query:
            films_query = films_query.filter(
                Film.title.ilike(f'%{query}%') |
                Film.description.ilike(f'%{query}%')
            )

        if genre:
            films_query = films_query.filter(Film.genre == genre)

        films = films_query.all()
        return jsonify({
            'films': [film_to_dict(film, current_user) for film in films],
            'genres': get_genres_cached()
        })

    @api_bp.route('/films/<int:film_id>', methods=['GET'])
    def get_film(film_id):
        """Get film details with sessions, reviews and similar films."""
        film = Film.query.options(
            selectinload(Film.reviews),
            selectinload(Film.favorited_by),
            selectinload(Film.sessions)
        ).get_or_404(film_id)

        all_active_sessions = Session.query.filter_by(
            film_id=film_id,
            status='active'
        ).options(selectinload(Session.seats)).order_by(Session.start_time).all()
        sessions = [s for s in all_active_sessions if not is_session_in_past(s)]

        reviews = sorted(film.reviews, key=lambda r: r.created_at, reverse=True)
        user_review = None
        if current_user.is_authenticated:
            user_review = next((r for r in film.reviews if r.user_id == current_user.id), None)

        similar_films = film.get_similar_films(limit=4)

        serialized_sessions = []
        for session in sessions:
            pricing = pricing_for_session(session, current_user)
            serialized_sessions.append({
                'id': session.id,
                'start_time': session.start_time,
                'price': pricing['dynamic_price'],
                'base_price': pricing['base_price'],
                'pricing': pricing,
                'available_seats': session.available_seats_count(),
                'booked_seats': session.booked_seats_count()
            })

        return jsonify({
            'film': film_to_dict(film, current_user),
            'sessions': serialized_sessions,
            'reviews': [{
                'id': r.id,
                'user_name': r.user.name,
                'user_id': r.user_id,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at.isoformat()
            } for r in reviews],
            'user_review': {
                'id': user_review.id,
                'rating': user_review.rating,
                'comment': user_review.comment
            } if user_review else None,
            'similar_films': [film_to_dict(f, current_user) for f in similar_films],
            'is_authenticated': current_user.is_authenticated,
            'current_user_id': current_user.id if current_user.is_authenticated else None,
            'is_admin': current_user.is_admin if current_user.is_authenticated else False
        })

    @api_bp.route('/films/<int:film_id>/reviews', methods=['POST'])
    @login_required
    def add_review(film_id):
        """Create review for film."""
        Film.query.get_or_404(film_id)
        data, error_response = get_json_payload()
        if error_response:
            return error_response

        existing = Review.query.filter_by(film_id=film_id, user_id=current_user.id).first()
        if existing:
            return jsonify({'error': 'Ви вже залишили відгук на цей фільм'}), 400

        rating = data.get('rating')
        comment = (data.get('comment') or '').strip()

        rating_value, rating_error = parse_int_field(rating, 'rating', 1, 5)
        if rating_error:
            return jsonify({'error': 'Оцінка має бути від 1 до 5'}), 400

        if len(comment) > 2000:
            return jsonify({'error': 'Коментар занадто довгий (максимум 2000 символів)'}), 400

        review = Review(
            film_id=film_id,
            user_id=current_user.id,
            rating=rating_value,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()

        return jsonify({
            'success': True,
            'review': {
                'id': review.id,
                'user_name': current_user.name,
                'user_id': current_user.id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat()
            },
            'new_average_rating': review.film.average_rating()
        })

    @api_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
    @login_required
    def delete_review(review_id):
        """Delete review by owner or admin."""
        review = Review.query.get_or_404(review_id)

        if review.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'error': 'Немає прав на видалення'}), 403

        film = review.film
        db.session.delete(review)
        db.session.commit()

        return jsonify({
            'success': True,
            'new_average_rating': film.average_rating()
        })

    @api_bp.route('/favorites', methods=['GET'])
    @login_required
    def get_favorites():
        """Get user favorite films."""
        favorites = Favorite.query.filter_by(user_id=current_user.id).options(
            joinedload(Favorite.film).selectinload(Film.reviews),
            joinedload(Favorite.film).selectinload(Film.favorited_by)
        ).all()

        return jsonify({
            'favorites': [{
                **film_to_dict(fav.film, current_user),
                'added_at': fav.added_at.isoformat()
            } for fav in favorites]
        })

    @api_bp.route('/favorites/<int:film_id>', methods=['POST', 'DELETE'])
    @login_required
    def toggle_favorite(film_id):
        """Toggle favorite for current user."""
        Film.query.get_or_404(film_id)

        existing = Favorite.query.filter_by(user_id=current_user.id, film_id=film_id).first()

        if request.method == 'DELETE' or existing:
            if existing:
                db.session.delete(existing)
                db.session.commit()
                return jsonify({'success': True, 'action': 'removed'})
            return jsonify({'error': 'Не знайдено в обраних'}), 404

        favorite = Favorite(user_id=current_user.id, film_id=film_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})
