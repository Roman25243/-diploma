from flask import Flask
import importlib
from sqlalchemy import func
from extensions import db
from models import User, Film, Session, Seat, Booking, Review, Favorite, SessionNotification, Ticket


def init_migration(app):
    try:
        migrate_module = importlib.import_module('flask_migrate')
        Migrate = getattr(migrate_module, 'Migrate')
    except ImportError as exc:
        raise RuntimeError(
            "flask_migrate не встановлено. Додайте Flask-Migrate до requirements для використання init_migration()."
        ) from exc

    return Migrate(app, db)


def create_indexes(app):
    with app.app_context():
        print("🔨 Створення індексів для оптимізації БД...")
        
        try:
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_user_is_admin ON "user"(is_admin)'))
            print("✅ User indexes created")
        except Exception as e:
            print(f"⚠️  User indexes: {e}")
        
        try:
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_film_genre ON film(genre)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_film_director ON film(director)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_film_genre_director ON film(genre, director)'))
            print("✅ Film indexes created")
        except Exception as e:
            print(f"⚠️  Film indexes: {e}")
        
        try:
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_session_film_status ON session(film_id, status)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_session_start_time ON session(start_time)'))
            print("✅ Session indexes created")
        except Exception as e:
            print(f"⚠️  Session indexes: {e}")
        
        try:
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_seat_session_status ON seat(session_id, status)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_seat_row_number ON seat(row, number)'))
            print("✅ Seat indexes created")
        except Exception as e:
            print(f"⚠️  Seat indexes: {e}")
        
        try:
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_booking_user_id ON booking(user_id)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_booking_seat_id ON booking(seat_id)'))

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
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_review_film_id ON review(film_id)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_review_user_film ON review(user_id, film_id)'))
            print("✅ Review indexes created")
        except Exception as e:
            print(f"⚠️  Review indexes: {e}")
        
        try:
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_favorite_user_id ON favorite(user_id)'))
            db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_favorite_film_id ON favorite(film_id)'))
            print("✅ Favorite indexes created")
        except Exception as e:
            print(f"⚠️  Favorite indexes: {e}")

        try:
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
    with app.app_context():
        print("🔍 Перевірка існуючих індексів:\n")
        result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"))
        
        indexes = result.fetchall()
        if indexes:
            for idx in indexes:
                print(f"  ✅ {idx[0]}")
        else:
            print("  ⚠️  Індексів не найдено")


def analyze_table_stats(app, table_name='film'):
    with app.app_context():
        print(f"\n📊 Статистика таблиці '{table_name}':")
        
        try:
            result = db.session.execute(db.text(f"PRAGMA table_info({table_name})"))
            columns = result.fetchall()
            
            print(f"\nКолонки ({len(columns)}):")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            count_result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table_name}"))
            count = count_result.scalar()
            print(f"\nВсього записів: {count}")
            
        except Exception as e:
            print(f"Помилка: {e}")


def migration_instructions():
     return None


if __name__ == '__main__':
    pass
