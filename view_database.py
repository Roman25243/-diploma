"""
Скрипт для перегляду бази даних Cinema App
Підтримує як SQLite, так і PostgreSQL
"""

from app import app, db
from models import User, Film, Session, Booking, Review, Favorite
from datetime import datetime

def print_separator(title=""):
    """Друкує роздільник"""
    if title:
        print(f"\n{'=' * 80}")
        print(f" {title}")
        print('=' * 80)
    else:
        print('-' * 80)

def view_database():
    """Показує всі дані з бази даних"""
    with app.app_context():
        # Отримуємо інформацію про базу даних
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_type = 'PostgreSQL' if db_uri.startswith('postgresql') else 'SQLite'
        
        print_separator(f"БАЗА ДАНИХ: {db_type}")
        print(f"URI: {db_uri}")
        
        # Користувачі
        print_separator("КОРИСТУВАЧІ")
        users = User.query.all()
        print(f"Всього користувачів: {len(users)}\n")
        for user in users:
            admin_badge = "👑 АДМІН" if user.is_admin else "👤 Користувач"
            print(f"ID: {user.id}")
            print(f"  Ім'я: {user.name}")
            print(f"  Email: {user.email}")
            print(f"  Тип: {admin_badge}")
            print()
        
        # Фільми
        print_separator("ФІЛЬМИ")
        films = Film.query.all()
        print(f"Всього фільмів: {len(films)}\n")
        for film in films:
            print(f"ID: {film.id}")
            print(f"  Назва: {film.title}")
            print(f"  Режисер: {film.director}")
            print(f"  Жанр: {film.genre}")
            print(f"  Тривалість: {film.duration} хв")
            print(f"  Опис: {film.description[:100]}..." if len(film.description) > 100 else f"  Опис: {film.description}")
            print(f"  Постер: {film.image if film.image else 'Не завантажено'}")
            print()
        
        # Сеанси
        print_separator("КІНОСЕАНСИ")
        sessions = Session.query.order_by(Session.start_time).all()
        print(f"Всього сеансів: {len(sessions)}\n")
        for session in sessions:
            status_icon = {
                'active': '✅ Активний',
                'cancelled': '❌ Скасовано',
                'completed': '📋 Завершено'
            }.get(session.status, session.status)
            
            # Підрахунок місць
            total_seats = len(session.seats) if session.seats else 0
            booked_seats = sum(1 for seat in session.seats if seat.status == 'booked') if session.seats else 0
            available_seats = total_seats - booked_seats
            
            print(f"ID: {session.id}")
            print(f"  Фільм: {session.film.title}")
            print(f"  Час: {session.start_time}")
            print(f"  Ціна: {session.price} грн")
            print(f"  Загальна кількість місць: {total_seats}")
            print(f"  Доступно місць: {available_seats}")
            print(f"  Заброньовано: {booked_seats}")
            print(f"  Статус: {status_icon}")
            print()
        
        # Бронювання
        print_separator("БРОНЮВАННЯ")
        bookings = Booking.query.all()
        print(f"Всього бронювань: {len(bookings)}\n")
        for booking in bookings:
            print(f"ID: {booking.id}")
            print(f"  Користувач: {booking.user.name}")
            print(f"  Місце: Ряд {booking.seat.row}, Місце {booking.seat.number}")
            print(f"  Сеанс: {booking.seat.session.film.title}")
            print(f"  Час: {booking.seat.session.start_time}")
            print(f"  Ціна: {booking.seat.session.price} грн")
            print()
        
        # Відгуки
        print_separator("ВІДГУКИ")
        reviews = Review.query.all()
        print(f"Всього відгуків: {len(reviews)}\n")
        for review in reviews:
            stars = '⭐' * review.rating
            print(f"ID: {review.id}")
            print(f"  Користувач: {review.user.name}")
            print(f"  Фільм: {review.film.title}")
            print(f"  Рейтинг: {stars} ({review.rating}/5)")
            print(f"  Коментар: {review.comment}")
            print(f"  Дата: {review.created_at.strftime('%d.%m.%Y %H:%M')}")
            print()
        
        # Обране
        print_separator("ОБРАНЕ")
        favorites = Favorite.query.all()
        print(f"Всього в обраному: {len(favorites)}\n")
        for favorite in favorites:
            print(f"ID: {favorite.id}")
            print(f"  Користувач: {favorite.user.name}")
            print(f"  Фільм: {favorite.film.title}")
            print(f"  Додано: {favorite.added_at.strftime('%d.%m.%Y %H:%M')}")
            print()
        
        # Статистика
        print_separator("СТАТИСТИКА")
        total_tickets = len(bookings)
        total_revenue = sum(b.seat.session.price for b in bookings)
        active_sessions = len([s for s in sessions if s.status == 'active'])
        cancelled_sessions = len([s for s in sessions if s.status == 'cancelled'])
        
        print(f"📊 Загальна виручка: {total_revenue} грн")
        print(f"🎫 Продано квитків: {total_tickets}")
        print(f"👥 Користувачів: {len(users)}")
        print(f"🎬 Фільмів: {len(films)}")
        print(f"📅 Сеансів: {len(sessions)} (активних: {active_sessions}, скасованих: {cancelled_sessions})")
        print(f"⭐ Відгуків: {len(reviews)}")
        print_separator()

if __name__ == '__main__':
    view_database()
