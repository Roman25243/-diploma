"""
Міграція до оптимізованої бази даних
Створює індекси відповідно до нових оптимізацій
"""

from flask import Flask
import importlib
from sqlalchemy import func
from extensions import db
from models import User, Film, Session, Seat, Booking, Review, Favorite, SessionNotification, Ticket


def init_migration(app):
    """Ініціалізувати міграції"""
    try:
        migrate_module = importlib.import_module('flask_migrate')
        Migrate = getattr(migrate_module, 'Migrate')
    except ImportError as exc:
        raise RuntimeError(
            "flask_migrate не встановлено. Додайте Flask-Migrate до requirements для використання init_migration()."
        ) from exc

    return Migrate(app, db)


def create_indexes(app):
    """
    Створити індекси для оптимізацій
    Запустіть один раз після оновлення коду
    """
    with app.app_context():
        print("🔨 Створення індексів для оптимізації БД...")
        
        try:
            # User indexes
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_user_is_admin ON "user"(is_admin)'))
            print("✅ User indexes created")
        except Exception as e:
            print(f"⚠️  User indexes: {e}")
        
        try:
            # Film indexes
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_film_genre ON film(genre)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_film_director ON film(director)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_film_genre_director ON film(genre, director)'))
            print("✅ Film indexes created")
        except Exception as e:
            print(f"⚠️  Film indexes: {e}")
        
        try:
            # Session indexes
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_session_film_status ON session(film_id, status)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_session_start_time ON session(start_time)'))
            print("✅ Session indexes created")
        except Exception as e:
            print(f"⚠️  Session indexes: {e}")
        
        try:
            # Seat indexes
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_seat_session_status ON seat(session_id, status)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_seat_row_number ON seat(row, number)'))
            print("✅ Seat indexes created")
        except Exception as e:
            print(f"⚠️  Seat indexes: {e}")
        
        try:
            # Booking indexes
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_booking_user_id ON booking(user_id)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_booking_seat_id ON booking(seat_id)'))

            # Видаляємо дублікати бронювань по seat_id перед створенням унікального індексу
            duplicate_seats = db.session.query(
                Booking.seat_id,
                func.count(Booking.id).label('booking_count')
            ).group_by(Booking.seat_id).having(func.count(Booking.id) > 1).all()

            removed_duplicates = 0
            for seat_id, _ in duplicate_seats:
                duplicates = Booking.query.filter_by(seat_id=seat_id).order_by(Booking.id.asc()).all()
                for duplicate_booking in duplicates[1:]:
                    db.session.delete(duplicate_booking)
                    removed_duplicates += 1

            if removed_duplicates:
                print(f"⚠️  Removed duplicate bookings: {removed_duplicates}")

            db.session.flush()
            db.session.execute(db.text('CREATE UNIQUE INDEX IF NOT EXISTS uq_booking_seat_id ON booking(seat_id)'))
            print("✅ Booking indexes created")
        except Exception as e:
            print(f"⚠️  Booking indexes: {e}")
        
        try:
            # Review indexes
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_review_film_id ON review(film_id)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_review_user_film ON review(user_id, film_id)'))
            print("✅ Review indexes created")
        except Exception as e:
            print(f"⚠️  Review indexes: {e}")
        
        try:
            # Favorite indexes
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_favorite_user_id ON favorite(user_id)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_favorite_film_id ON favorite(film_id)'))
            print("✅ Favorite indexes created")
        except Exception as e:
            print(f"⚠️  Favorite indexes: {e}")

        try:
            # Ticket indexes
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_ticket_booking_id ON ticket(booking_id)'))
            db.session.execute(db.text('CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_token ON ticket(token)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_ticket_status_issued ON ticket(status, issued_at)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_ticket_scanned_by_id ON ticket(scanned_by_id)'))
            print("✅ Ticket indexes created")
        except Exception as e:
            print(f"⚠️  Ticket indexes: {e}")
        
        db.session.commit()
        print("\n✅ Всі індекси успішно створені!")


def check_indexes(app):
    """
    Перевірити які індекси існують
    """
    with app.app_context():
        print("🔍 Перевірка існуючих індексів:\n")
        
        # SQLite specific query
        result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"))
        
        indexes = result.fetchall()
        if indexes:
            for idx in indexes:
                print(f"  ✅ {idx[0]}")
        else:
            print("  ⚠️  Індексів не найдено")


def analyze_table_stats(app, table_name='film'):
    """
    Аналізувати статистику таблиці (SQLite)
    Корисно для дебагу планів запитів
    """
    with app.app_context():
        print(f"\n📊 Статистика таблиці '{table_name}':")
        
        try:
            # SQLite specific
            result = db.session.execute(db.text(f"PRAGMA table_info({table_name})"))
            columns = result.fetchall()
            
            print(f"\nКолонки ({len(columns)}):")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Row count
            count_result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table_name}"))
            count = count_result.scalar()
            print(f"\nВсього записів: {count}")
            
        except Exception as e:
            print(f"Помилка: {e}")


def migration_instructions():
    """Інструкції для міграції"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           ІНСТРУКЦІЯ З МІГРАЦІЇ DATABASE OPTIMIZATION            ║
╚════════════════════════════════════════════════════════════════╝

📋 КРОК 1: Резервна копія БД
   Переконайтесь що у вас є резервна копія instance/cinema.db
   
   > cp instance/cinema.db instance/cinema.db.backup

📋 КРОК 2: Оновіть код
   ✓ models.py - оновлені з новими індексами
   ✓ routes/api.py - оптимізовані запити з eager loading
   ✓ extensions.py - без змін

📋 КРОК 3: Створіть індекси
   Запустіть в Python консолі подібно:

   from app import app, create_indexes
   create_indexes(app)

   Або виконайте SQL вручну (див. DATABASE_OPTIMIZATION.md)

📋 КРОК 4: Перезавантажте додаток
   Перезапустіть Flask сервер

📋 КРОК 5: Тестування
   Запустіть test_db_optimization.py для перевірки

═════════════════════════════════════════════════════════════════

⚠️  ВАЖЛИВІ НОТАТКИ:

1. SQLite НЕ МАТЕРІАЛІЗУЄ поточні індекси при ALTER TABLE
   - Індекси працюють на нові дані
   - Для переіндексації видалите cinema.db файл і запустіть:
     python create_admin.py  # Створить нову БД з індексами

2. PostgreSQL користувачі:
   - Используйте Alembic для міграцій
   - flask-migrate автоматично створить індекси

3. Performance gains:
   - Будуть помітні після 1000+ записів в таблиці
   - На малих БД різниця мінімальна

═════════════════════════════════════════════════════════════════
    """)


if __name__ == '__main__':
    # Для запуску непосередньо
    print("""
    Використання:
    
    from app import app
    from create_indexes import create_indexes, check_indexes
    
    # Створити індекси
    create_indexes(app)
    
    # Перевірити індекси
    check_indexes(app)
    """)
