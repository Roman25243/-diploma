from flask_login import UserMixin
from extensions import db
from datetime import datetime
from sqlalchemy import func


class User(UserMixin, db.Model):
    """Модель користувача"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)


class Film(db.Model):
    """Модель фільму"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    image = db.Column(db.String(100))
    trailer = db.Column(db.String(200))
    
    # Розширена інформація
    genre = db.Column(db.String(100))  # Жанр
    director = db.Column(db.String(100))  # Режисер
    actors = db.Column(db.Text)  # Актори (через кому)
    duration = db.Column(db.Integer)  # Тривалість у хвилинах
    age_rating = db.Column(db.String(10))  # Віковий рейтинг (PG, PG-13, R тощо)
    release_year = db.Column(db.Integer)  # Рік випуску
    
    sessions = db.relationship('Session', backref='film', lazy=True)
    reviews = db.relationship('Review', backref='film', lazy=True)
    
    def average_rating(self):
        """Підрахунок середнього рейтингу фільму"""
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)
    
    def review_count(self):
        """Кількість відгуків"""
        return len(self.reviews)
    
    def get_similar_films(self, limit=4):
        """Знайти схожі фільми на основі жанру та режисера"""
        if not self.genre and not self.director:
            # Якщо немає даних, повертаємо популярні фільми
            return Film.query.filter(Film.id != self.id)\
                .order_by(Film.id.desc()).limit(limit).all()
        
        similar = []
        
        # Пріоритет 1: Той самий жанр + той самий режисер
        if self.genre and self.director:
            same_genre_director = Film.query.filter(
                Film.id != self.id,
                Film.genre == self.genre,
                Film.director == self.director
            ).limit(limit).all()
            similar.extend(same_genre_director)
        
        # Пріоритет 2: Той самий режисер
        if len(similar) < limit and self.director:
            same_director = Film.query.filter(
                Film.id != self.id,
                Film.director == self.director,
                Film.id.notin_([f.id for f in similar])
            ).limit(limit - len(similar)).all()
            similar.extend(same_director)
        
        # Пріоритет 3: Той самий жанр
        if len(similar) < limit and self.genre:
            same_genre = Film.query.filter(
                Film.id != self.id,
                Film.genre == self.genre,
                Film.id.notin_([f.id for f in similar])
            ).order_by(func.random()).limit(limit - len(similar)).all()
            similar.extend(same_genre)
        
        # Якщо все ще не вистачає, додаємо популярні
        if len(similar) < limit:
            popular = Film.query.filter(
                Film.id != self.id,
                Film.id.notin_([f.id for f in similar])
            ).order_by(Film.id.desc()).limit(limit - len(similar)).all()
            similar.extend(popular)
        
        return similar[:limit]


class Session(db.Model):
    """Модель сеансу"""
    id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'))
    start_time = db.Column(db.String(50))
    price = db.Column(db.Float)
    seats = db.relationship('Seat', backref='session', lazy=True)


class Seat(db.Model):
    """Модель місця в кінозалі"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    row = db.Column(db.Integer)
    number = db.Column(db.Integer)
    status = db.Column(db.String(20), default='free')
    booking = db.relationship('Booking', backref='seat', uselist=False, lazy=True)


class Booking(db.Model):
    """Модель бронювання"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'))


class Review(db.Model):
    """Модель відгуку на фільм"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 зірок
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Review {self.user.name} - {self.film.title}: {self.rating}/5>'
