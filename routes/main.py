from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Film, Review
from forms import ReviewForm

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Редірект на SPA"""
    return redirect('/app/')


@main_bp.route('/films')
def films():
    """Редірект на SPA версію"""
    return redirect('/app/films')


@main_bp.route('/film/<int:film_id>')
def film_detail(film_id):
    """Редірект на SPA версію"""
    return redirect(f'/app/film/{film_id}')


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
