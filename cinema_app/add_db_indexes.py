#!/usr/bin/env python3
"""
Додавання оптимальних індексів до БД
"""
from sqlalchemy import text
from app import app, db

def add_index(name, table, columns_str, description):
    """Додати індекс з перевіркою чи він уже існує"""
    print(f"\n📍 {description}")
    print(f"   Індекс: {name} на {columns_str}")
    
    try:
        # Перевіримо чи індекс уже існує
        result = db.session.execute(text(f"""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = '{table}' AND indexname = '{name}'
        """))
        
        if result.fetchone():
            print(f"   ✅ Індекс вже існує")
            return True
        
        # Додамо індекс
        create_index_sql = f"CREATE INDEX {name} ON {table} ({columns_str})"
        db.session.execute(text(create_index_sql))
        db.session.commit()
        print(f"   ✅ Індекс створено успішно")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"   ❌ Error: {str(e)[:150]}")
        return False


def main():
    """Додати всі необхідні індекси"""
    with app.app_context():
        print("\n" + "="*80)
        print("🔧 Додавання оптимальних індексів для cinema_app")
        print("="*80)
        
        success_count = 0
        total_count = 0
        
        # ===== SESSION таблиця =====
        print("\n\n📋 ТАБЛИЦЯ: session")
        print("-" * 80)
        
        # Індекс 1: hall_id + status (для календаря і активних сеансів)
        total_count += 1
        if add_index(
            'idx_session_hall_status',
            'session',
            'hall_id, status',
            '1. Календар по залу + фільтр активних сеансів'
        ):
            success_count += 1
        
        # Індекс 2: hall_id + status + start_time (більш специфічний)
        total_count += 1
        if add_index(
            'idx_session_hall_status_start',
            'session',
            'hall_id, status, start_time',
            '2. Оптимізована версія для календаря'
        ):
            success_count += 1
        
        # ===== BOOKING таблиця =====
        print("\n\n📋 ТАБЛИЦЯ: booking")
        print("-" * 80)
        
        # Індекс 3: user_id + payment_status (для пошуку бронювань користувача)
        total_count += 1
        if add_index(
            'idx_booking_user_payment',
            'booking',
            'user_id, payment_status',
            '3. Пошук бронювань користувача за статусом платежу'
        ):
            success_count += 1
        
        # ===== FILM таблиця =====
        print("\n\n📋 ТАБЛИЦЯ: film")
        print("-" * 80)
        
        # Індекс 4: genre + director (для подібних фільмів)
        total_count += 1
        if add_index(
            'idx_film_genre_director',
            'film',
            'genre, director',
            '4. Пошук подібних фільмів за жанром і режисером'
        ):
            success_count += 1
        
        # ===== SEAT таблиця =====
        print("\n\n📋 ТАБЛИЦЯ: seat")
        print("-" * 80)
        
        # Перевіримо чи вже є idx_seat_session_status
        total_count += 1
        if add_index(
            'idx_seat_session_id',
            'seat',
            'session_id',
            '5. Пошук всіх місць для сеансу (додатковий індекс)'
        ):
            success_count += 1
        
        # ===== TICKET таблиця =====
        print("\n\n📋 ТАБЛИЦЯ: ticket")
        print("-" * 80)
        
        # Індекс 6: booking_id + status (для квитків)
        total_count += 1
        if add_index(
            'idx_ticket_booking_status',
            'ticket',
            'booking_id, status',
            '6. Пошук квитків за статусом'
        ):
            success_count += 1
        
        # Результат
        print("\n\n" + "="*80)
        print(f"📈 Результат: {success_count}/{total_count} індексів успішно створено/перевірено")
        print("="*80)
        
        if success_count == total_count:
            print("\n✅ Все готово! БД оптимізована.")
        else:
            print(f"\n⚠️  Деякі індекси не були додані. Перевірте помилки вище.")


if __name__ == '__main__':
    main()
