from flask_login import UserMixin
from extensions import db
from datetime import datetime
from sqlalchemy import func, Index


class User(UserMixin, db.Model):
    """Модель користувача"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, index=True)
    password = db.Column(db.String(255))  # Збільшено для хешованих паролів
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy='select')
    scanned_tickets = db.relationship('Ticket', backref='scanned_by', lazy='select', foreign_keys='Ticket.scanned_by_id')
    reviews = db.relationship('Review', backref='user', lazy='select')
    favorites = db.relationship('Favorite', backref='user', lazy='select', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_is_admin', 'is_admin'),
    )


class Film(db.Model):
    """Модель фільму"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    image = db.Column(db.String(100))
    trailer = db.Column(db.String(200))
    
    # Розширена інформація
    genre = db.Column(db.String(100), index=True)  # Жанр
    director = db.Column(db.String(100), index=True)  # Режисер
    actors = db.Column(db.Text)  # Актори (через кому)
    duration = db.Column(db.Integer)  # Тривалість у хвилинах
    age_rating = db.Column(db.String(10))  # Віковий рейтинг (PG, PG-13, R тощо)
    release_year = db.Column(db.Integer)  # Рік випуску
    
    sessions = db.relationship('Session', backref='film', lazy='select')
    reviews = db.relationship('Review', backref='film', lazy='select')
    favorited_by = db.relationship('Favorite', backref='film', lazy='select', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_film_genre', 'genre'),
        Index('idx_film_director', 'director'),
        Index('idx_film_genre_director', 'genre', 'director'),
    )
    
    def average_rating(self):
        """Підрахунок середнього рейтингу фільму (оптимізовано)"""
        if not self.reviews:
            return 0
        total = sum(r.rating for r in self.reviews)
        return round(total / len(self.reviews), 1) if self.reviews else 0
    
    def review_count(self):
        """Кількість відгуків"""
        return len(self.reviews)
    
    @classmethod
    def with_rating_stats(cls):
        """Отримати фільми з приєднаними даними про рейтинги (оптимізовано)"""
        from sqlalchemy import func, outerjoin
        return db.session.query(
            cls,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('review_count')
        ).outerjoin(Review).group_by(cls.id)
    
    def is_favorited_by(self, user):
        """Перевірка чи фільм в обраних у користувача"""
        if not user or not user.is_authenticated:
            return False
        return any(f.user_id == user.id for f in self.favorited_by)
    
    def favorites_count(self):
        """Скільки користувачів додали фільм в обрані"""
        return len(self.favorited_by)
    
    def get_similar_films(self, limit=4):
        """Знайти схожі фільми на основі жанру та режисера (оптимізовано)"""
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
            existing_ids = {f.id for f in similar}
            same_director = Film.query.filter(
                Film.id != self.id,
                Film.director == self.director,
                ~Film.id.in_(existing_ids)
            ).limit(limit - len(similar)).all()
            similar.extend(same_director)
        
        # Пріоритет 3: Той самий жанр
        if len(similar) < limit and self.genre:
            existing_ids = {f.id for f in similar}
            same_genre = Film.query.filter(
                Film.id != self.id,
                Film.genre == self.genre,
                ~Film.id.in_(existing_ids)
            ).order_by(func.random()).limit(limit - len(similar)).all()
            similar.extend(same_genre)
        
        # Якщо все ще не вистачає, додаємо популярні
        if len(similar) < limit:
            existing_ids = {f.id for f in similar}
            popular = Film.query.filter(
                Film.id != self.id,
                ~Film.id.in_(existing_ids)
            ).order_by(Film.id.desc()).limit(limit - len(similar)).all()
            similar.extend(popular)
        
        return similar[:limit]


class Hall(db.Model):
    """Модель кінозалу."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    rows = db.Column(db.Integer, nullable=False)
    seats_per_row = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sessions = db.relationship('Session', backref='hall', lazy='select')

    __table_args__ = (
        Index('idx_hall_name', 'name'),
    )

    def capacity(self):
        """Загальна місткість залу."""
        return int(self.rows or 0) * int(self.seats_per_row or 0)


class Session(db.Model):
    """Модель сеансу"""
    id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), index=True)
    hall_id = db.Column(db.Integer, db.ForeignKey('hall.id'), index=True, nullable=False)
    start_time = db.Column(db.String(50))
    price = db.Column(db.Float)
    status = db.Column(db.String(20), default='active', index=True)  # active, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Коли сеанс було створено
    seats = db.relationship('Seat', backref='session', lazy='select')
    
    __table_args__ = (
        Index('idx_session_film_status', 'film_id', 'status'),
        Index('idx_session_hall_start_time', 'hall_id', 'start_time'),
        Index('idx_session_start_time', 'start_time'),
        Index('idx_session_hall_status', 'hall_id', 'status'),  # Для календаря по залу
        Index('idx_session_hall_status_start', 'hall_id', 'status', 'start_time'),  # Оптимізована версія
    )
    
    def is_cancelled(self):
        """Перевірка чи сеанс скасовано"""
        return self.status == 'cancelled'
    
    def booked_seats_count(self):
        """Кількість заброньованих місць"""
        return sum(1 for seat in self.seats if seat.status == 'booked')
    
    def available_seats_count(self):
        """Кількість доступних місць"""
        return sum(1 for seat in self.seats if seat.status == 'free')


class Seat(db.Model):
    """Модель місця в кінозалі"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), index=True)
    row = db.Column(db.Integer)
    number = db.Column(db.Integer)
    status = db.Column(db.String(20), default='free', index=True)
    booking = db.relationship('Booking', backref='seat', uselist=False, lazy='select')
    
    __table_args__ = (
        Index('idx_seat_session_status', 'session_id', 'status'),
        Index('idx_seat_row_number', 'row', 'number'),
        Index('idx_seat_session_id', 'session_id'),  # Для пошуку всіх місць сеансу
    )


class Booking(db.Model):
    """Модель бронювання"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), index=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment_transaction.id'), index=True, nullable=True)
    payment_status = db.Column(db.String(20), default='unpaid', index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ticket = db.relationship('Ticket', backref='booking', uselist=False, lazy='select', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('seat_id', name='unique_booking_seat'),
        Index('idx_booking_user_id', 'user_id'),
        Index('idx_booking_seat_id', 'seat_id'),
        Index('idx_booking_user_payment', 'user_id', 'payment_status'),  # Для пошуку платіжних бронювань
    )


class Ticket(db.Model):
    """Електронний квиток для проходу в зал."""
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False, unique=True, index=True)
    token = db.Column(db.String(64), nullable=False, unique=True, index=True)
    status = db.Column(db.String(20), nullable=False, default='active', index=True)  # active, used, revoked
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    scanned_at = db.Column(db.DateTime, nullable=True)
    scanned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    scan_count = db.Column(db.Integer, default=0, nullable=False)

    __table_args__ = (
        Index('idx_ticket_status_issued', 'status', 'issued_at'),
        Index('idx_ticket_booking_status', 'booking_id', 'status'),  # Для пошуку квитків за статусом
    )


class PaymentTransaction(db.Model):
    """Платіжна транзакція (MVP для онлайн-оплати)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='UAH', nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    provider = db.Column(db.String(30), default='mock', nullable=False)
    provider_order_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    provider_payment_id = db.Column(db.String(128), nullable=True, index=True)
    checkout_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    paid_at = db.Column(db.DateTime, nullable=True)

    bookings = db.relationship('Booking', backref='payment', lazy='select')

    __table_args__ = (
        Index('idx_payment_user_status', 'user_id', 'status'),
    )


class Review(db.Model):
    """Модель відгуку на фільм"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 зірок
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_review_film_id', 'film_id'),
        Index('idx_review_user_film', 'user_id', 'film_id'),
    )
    
    def __repr__(self):
        return f'<Review {self.user.name} - {self.film.title}: {self.rating}/5>'


class Favorite(db.Model):
    """Обрані фільми користувача"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False, index=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Унікальність: один користувач не може додати той самий фільм двічі
    __table_args__ = (
        db.UniqueConstraint('user_id', 'film_id', name='unique_user_film'),
        Index('idx_favorite_user_id', 'user_id'),
        Index('idx_favorite_film_id', 'film_id'),
    )
    
    def __repr__(self):
        return f'<Favorite User:{self.user_id} Film:{self.film_id}>'


class SessionNotification(db.Model):
    """Запис про надіслані повідомлення про нові сеанси"""
    id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
    notification_date = db.Column(db.String(20), nullable=False)  # Дата коли надіслали повідомлення (YYYY-MM-DD)
    notified_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Унікальність: одне повідомлення на фільм на день (розсилки)
    __table_args__ = (
        db.UniqueConstraint('film_id', 'notification_date', name='unique_film_notification_date'),
    )
    
    def __repr__(self):
        return f'<SessionNotification Film:{self.film_id} NotificationDate:{self.notification_date}>'
