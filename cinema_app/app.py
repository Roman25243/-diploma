from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from sqlalchemy.orm import joinedload  # Додайте цей імпорт на початку файлу


app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Моделі
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)

class Film(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    image = db.Column(db.String(100))
    trailer = db.Column(db.String(200))
    sessions = db.relationship('Session', backref='film', lazy=True)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'))
    start_time = db.Column(db.String(50))
    price = db.Column(db.Float)
    seats = db.relationship('Seat', backref='session', lazy=True)

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    row = db.Column(db.Integer)
    number = db.Column(db.Integer)
    status = db.Column(db.String(20), default='free')
    booking = db.relationship('Booking', backref='seat', uselist=False, lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Створення БД та першого адміна
with app.app_context():
    db.create_all()
    if not User.query.first():
        admin = User(email='admin@example.com', password=generate_password_hash('admin'), name='Admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    # Отримуємо 4 популярні фільми для слайдера
    popular_films = db.session.query(Film)\
        .join(Session).join(Seat).join(Booking)\
        .group_by(Film.id)\
        .order_by(func.count(Booking.id).desc())\
        .limit(4).all()
    return render_template('landing.html', popular_films=popular_films)

@app.route('/films')
def films():
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Невірний email або пароль')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form['password'])
        user = User(email=request.form['email'], password=hashed, name=request.form['name'])
        db.session.add(user)
        db.session.commit()
        flash('Реєстрація успішна')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    bookings = Booking.query.options(
        joinedload(Booking.seat).joinedload(Seat.session).joinedload(Session.film)
    ).filter_by(user_id=current_user.id).all()
    return render_template('profile.html', bookings=bookings)


@app.route('/film/<int:film_id>')
def film_detail(film_id):
    film = Film.query.get_or_404(film_id)
    sessions = Session.query.filter_by(film_id=film_id).all()
    return render_template('film_detail.html', film=film, sessions=sessions)

@app.route('/seats/<int:session_id>', methods=['GET', 'POST'])
@login_required
def seats(session_id):
    session = Session.query.get_or_404(session_id)
    seats = Seat.query.filter_by(session_id=session_id).order_by(Seat.row, Seat.number).all()

    if request.method == 'POST':
        selected_seats = request.form.getlist('seat')
        if not selected_seats:
            flash('Оберіть хоча б одне місце', 'warning')
            return redirect(url_for('seats', session_id=session_id))

        booked_count = 0
        for seat_id in selected_seats:
            seat = Seat.query.get(seat_id)
            if seat.status == 'booked':
                booked_count += 1
            else:
                seat.status = 'booked'
                booking = Booking(user_id=current_user.id, seat_id=seat.id)
                db.session.add(booking)
        db.session.commit()

        if booked_count > 0:
            flash(f'{booked_count} з вибраних місць вже були заброньовані іншими. Решта заброньовано успішно!', 'info')
        else:
            flash('Місця успішно заброньовано!', 'success')
        return redirect(url_for('profile'))

    return render_template('seats.html', session=session, seats=seats)
# Адмін-панель
from sqlalchemy import func

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    # Основна статистика
    total_users = User.query.count()
    total_bookings = Booking.query.count()
    total_films = Film.query.count()
    total_revenue = db.session.query(func.sum(Session.price)).join(Seat).join(Booking).scalar() or 0

    # Топ популярних фільмів
    popular_films = db.session.query(
        Film.title, func.count(Booking.id).label('count')
    ).join(Session).join(Seat).join(Booking)\
     .group_by(Film.id).order_by(func.count(Booking.id).desc()).limit(5).all()

    popular_labels = [f[0] for f in popular_films]
    popular_data = [f[1] for f in popular_films]

    # Прибуток по фільмах
    revenue_films = db.session.query(
        Film.title, func.sum(Session.price).label('revenue')
    ).join(Session).join(Seat).join(Booking)\
     .group_by(Film.id).order_by(func.sum(Session.price).desc()).limit(5).all()

    revenue_labels = [f[0] for f in revenue_films]
    revenue_data = [float(f[1] or 0) for f in revenue_films]

    # Топ користувачів
    top_users = db.session.query(
        User, func.count(Booking.id).label('booking_count'),
        func.sum(Session.price).label('spent')
    ).outerjoin(Booking).outerjoin(Seat).outerjoin(Session)\
     .group_by(User.id).order_by(func.count(Booking.id).desc()).limit(10).all()

    stats = {
        'total_users': total_users,
        'total_bookings': total_bookings,
        'total_films': total_films,
        'total_revenue': total_revenue,
        'popular_films': {'labels': popular_labels, 'data': popular_data},
        'revenue_films': {'labels': revenue_labels, 'data': revenue_data},
        'top_users': [{'name': u.name, 'email': u.email, 'booking_count': bc, 'spent': float(spent or 0)} 
                      for u, bc, spent in top_users]
    }

    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/films', methods=['GET', 'POST'])
@login_required
def admin_films():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'delete_film' in request.form:
            film_id = request.form['delete_film']
            film = Film.query.get_or_404(film_id)
            db.session.delete(film)
            db.session.commit()
            flash('Фільм видалено')
        else:
            file = request.files.get('image')
            filename = None
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            film_id = request.form.get('film_id')
            if film_id:  # Редагування
                film = Film.query.get_or_404(film_id)
                film.title = request.form['title']
                film.description = request.form['description']
                film.trailer = request.form['trailer'] or film.trailer
                if filename:
                    film.image = filename
            else:  # Додавання
                film = Film(title=request.form['title'], description=request.form['description'],
                            image=filename, trailer=request.form['trailer'])
                db.session.add(film)
            db.session.commit()
            flash('Фільм збережено')
    
    films = Film.query.all()
    return render_template('admin/films.html', films=films)

@app.route('/admin/sessions', methods=['GET', 'POST'])
@login_required
def admin_sessions():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    films = Film.query.all()
    if request.method == 'POST':
        session = Session(film_id=request.form['film_id'],
                          start_time=request.form['start_time'],
                          price=request.form['price'])
        db.session.add(session)
        db.session.commit()

        # Автоматичне створення місць: 10 рядів × 12 місць
        for row in range(1, 11):
            for num in range(1, 13):
                seat = Seat(session_id=session.id, row=row, number=num, status='free')
                db.session.add(seat)
        db.session.commit()
        flash('Сеанс додано з 120 місцями')
    sessions = Session.query.all()
    return render_template('admin/sessions.html', films=films, sessions=sessions)

if __name__ == '__main__':
    app.run(debug=True)