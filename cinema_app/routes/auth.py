from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User
from forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вхід користувача"""
    if request.method == 'GET':
        return redirect('/app/login')
    
    # POST - обробка старої форми (legacy)
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Успішний вхід!', 'success')
            return redirect(url_for('main.index'))
        flash('Невірний email або пароль', 'danger')
    
    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Реєстрація нового користувача"""
    if request.method == 'GET':
        return redirect('/app/register')
    
    # POST - обробка старої форми (legacy)
    form = RegistrationForm()
    
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        user = User(
            email=form.email.data,
            password=hashed,
            name=form.name.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Вихід користувача"""
    logout_user()
    return redirect(url_for('main.index'))
