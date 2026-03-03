from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models import Film, Session, Seat, Booking, Review
from forms import ReviewForm

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Головна сторінка з популярними фільмами"""
    # Спроба отримати популярні фільми за бронюваннями (з outerjoin для включення всіх фільмів)
    popular_films = db.session.query(Film)\
        .outerjoin(Session).outerjoin(Seat).outerjoin(Booking)\
        .group_by(Film.id)\
        .order_by(func.count(Booking.id).desc())\
        .limit(4).all()
    
    # Fallback: якщо немає фільмів або менше 4, показуємо найновіші
    if len(popular_films) < 4:
        # Отримуємо найновіші фільми (за ID, бо це порядок додавання)
        popular_films = Film.query.order_by(Film.id.desc()).limit(4).all()
    
    return render_template('landing.html', popular_films=popular_films)


@main_bp.route('/films')
def films():
    """Список всіх фільмів з пошуком"""
    query = request.args.get('q', '').strip()
    if query:
        films_query = Film.query.filter(
            Film.title.ilike(f'%{query}%') |
            Film.description.ilike(f'%{query}%')
        )
    else:
        films_query = Film.query
    
    films = films_query.all()
    return render_template('films.html', films=films, search_query=query)


@main_bp.route('/film/<int:film_id>')
def film_detail(film_id):
    """Детальна інформація про фільм"""
    film = Film.query.get_or_404(film_id)
    # Показуємо лише активні сеанси
    sessions = Session.query.filter_by(film_id=film_id, status='active').all()
    
    # Відгуки (сортування за датою, новіші першими)
    reviews = Review.query.filter_by(film_id=film_id).order_by(Review.created_at.desc()).all()
    
    # Форма відгуку
    form = ReviewForm()
    
    # Перевірка чи користувач вже залишив відгук
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(film_id=film_id, user_id=current_user.id).first()
    
    # Схожі фільми
    similar_films = film.get_similar_films(limit=4)
    
    return render_template('film_detail.html', 
                         film=film, 
                         sessions=sessions, 
                         reviews=reviews,
                         form=form,
                         user_review=user_review,
                         similar_films=similar_films)


@main_bp.route('/film/<int:film_id>/review', methods=['POST'])
@login_required
def add_review(film_id):
    """Додавання відгуку на фільм"""
    film = Film.query.get_or_404(film_id)
    
    # Перевірка чи користувач вже залишав відгук
    existing_review = Review.query.filter_by(film_id=film_id, user_id=current_user.id).first()
    if existing_review:
        flash('Ви вже залишили відгук на цей фільм', 'warning')
        return redirect(url_for('main.film_detail', film_id=film_id))
    
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            user_id=current_user.id,
            film_id=film_id,
            rating=form.rating.data,
            comment=form.comment.data
        )
        db.session.add(review)
        db.session.commit()
        flash('Дякуємо за ваш відгук!', 'success')
    else:
        flash('Помилка при додаванні відгуку', 'danger')
    
    return redirect(url_for('main.film_detail', film_id=film_id))


@main_bp.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    """Видалення відгуку"""
    review = Review.query.get_or_404(review_id)
    
    # Перевірка що це відгук поточного користувача або адмін
    if review.user_id != current_user.id and not current_user.is_admin:
        flash('Ви не можете видалити чужий відгук', 'danger')
        return redirect(url_for('main.film_detail', film_id=review.film_id))
    
    film_id = review.film_id
    db.session.delete(review)
    db.session.commit()
    flash('Відгук видалено', 'success')
    
    return redirect(url_for('main.film_detail', film_id=film_id))
