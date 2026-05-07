from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Film, Review
from forms import ReviewForm

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Р РµРґС–СЂРµРєС‚ РЅР° SPA"""
    return redirect('/app/')


@main_bp.route('/films')
def films():
    """Р РµРґС–СЂРµРєС‚ РЅР° SPA РІРµСЂСЃС–СЋ"""
    return redirect('/app/films')


@main_bp.route('/film/<int:film_id>')
def film_detail(film_id):
    """Р РµРґС–СЂРµРєС‚ РЅР° SPA РІРµСЂСЃС–СЋ"""
    return redirect(f'/app/film/{film_id}')


@main_bp.route('/film/<int:film_id>/review', methods=['POST'])
@login_required
def add_review(film_id):
    """Р”РѕРґР°РІР°РЅРЅСЏ РІС–РґРіСѓРєСѓ РЅР° С„С–Р»СЊРј"""
    film = Film.query.get_or_404(film_id)
    
    existing_review = Review.query.filter_by(film_id=film_id, user_id=current_user.id).first()
    if existing_review:
        flash('Р’Рё РІР¶Рµ Р·Р°Р»РёС€РёР»Рё РІС–РґРіСѓРє РЅР° С†РµР№ С„С–Р»СЊРј', 'warning')
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
        flash('Р”СЏРєСѓС”РјРѕ Р·Р° РІР°С€ РІС–РґРіСѓРє!', 'success')
    else:
        flash('РџРѕРјРёР»РєР° РїСЂРё РґРѕРґР°РІР°РЅРЅС– РІС–РґРіСѓРєСѓ', 'danger')
    
    return redirect(url_for('main.film_detail', film_id=film_id))


@main_bp.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    """Р’РёРґР°Р»РµРЅРЅСЏ РІС–РґРіСѓРєСѓ"""
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id and not current_user.is_admin:
        flash('Р’Рё РЅРµ РјРѕР¶РµС‚Рµ РІРёРґР°Р»РёС‚Рё С‡СѓР¶РёР№ РІС–РґРіСѓРє', 'danger')
        return redirect(url_for('main.film_detail', film_id=review.film_id))
    
    film_id = review.film_id
    db.session.delete(review)
    db.session.commit()
    flash('Р’С–РґРіСѓРє РІРёРґР°Р»РµРЅРѕ', 'success')
    
    return redirect(url_for('main.film_detail', film_id=film_id))
