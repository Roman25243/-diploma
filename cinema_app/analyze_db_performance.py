#!/usr/bin/env python3
"""
Аналіз швидкодії БД: EXPLAIN QUERY PLAN для ключових запитів
"""
import sys
from sqlalchemy import text
from app import app, db

def analyze_query(description, query_str):
    """Виконати EXPLAIN для запиту"""
    print(f"\n{'='*80}")
    print(f"📊 {description}")
    print(f"{'='*80}")
    print(f"SQL:\n{query_str}\n")
    
    try:
        # Для PostgreSQL - просто EXPLAIN
        explain_query = f"EXPLAIN (FORMAT TEXT, ANALYZE false) {query_str}"
        result = db.session.execute(text(explain_query))
        rows = result.fetchall()
        
        if rows:
            print("Query Plan:")
            for row in rows:
                print(f"  {row[0]}")
        else:
            print("No plan available")
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}")
        db.session.rollback()  # Очистити транзакцію після помилки


def main():
    """Запустити аналіз"""
    with app.app_context():
        print("\n🔍 Аналіз швидкодії БД для cinema_app\n")
        print("Целі оптимізації:")
        print("  1. Календар по залу - фільтр сеансів за hall_id + start_time")
        print("  2. Місця сеансу - пошук місць за session_id + status")
        print("  3. Бронювання користувача - пошук за user_id + payment_status")
        print("  4. Активні сеанси - фільтр за status='active'")
        
        # Запит 1: Календар - всі сеанси для залу з датою
        analyze_query(
            "КАЛЕНДАР: Сеанси конкретного залу (для календаря)",
            """
            SELECT s.id, s.start_time, s.price, f.title, COUNT(st.id) as booked_count
            FROM session s
            LEFT JOIN film f ON s.film_id = f.id
            LEFT JOIN seat st ON st.session_id = s.id AND st.status = 'booked'
            WHERE s.hall_id = 1 AND s.status = 'active'
            GROUP BY s.id, s.start_time, s.price, f.title
            ORDER BY s.start_time
            """
        )
        
        # Запит 2: Місця сеансу - фільтр за статусом
        analyze_query(
            "МІСЦЯ: Доступні місця в сеансі",
            """
            SELECT id, row, number, status
            FROM seat
            WHERE session_id = 1 AND status = 'free'
            ORDER BY row, number
            """
        )
        
        # Запит 3: Бронювання користувача
        analyze_query(
            "БРОНЮВАННЯ: Активні бронювання користувача",
            """
            SELECT b.id, s.id, f.title, s.start_time, se.row, se.number
            FROM booking b
            JOIN seat se ON b.seat_id = se.id
            JOIN session s ON se.session_id = s.id
            LEFT JOIN film f ON s.film_id = f.id
            WHERE b.user_id = 1 AND b.payment_status = 'paid'
            ORDER BY s.start_time
            """
        )
        
        # Запит 4: Активні сеанси по залу + фільм
        analyze_query(
            "АКТИВНІ СЕАНСИ: По залу з деталями фільму",
            """
            SELECT s.id, s.hall_id, s.start_time, f.title, f.genre,
                   COUNT(CASE WHEN st.status = 'booked' THEN 1 END) as booked,
                   COUNT(CASE WHEN st.status = 'free' THEN 1 END) as free
            FROM session s
            LEFT JOIN film f ON s.film_id = f.id
            LEFT JOIN seat st ON st.session_id = s.id
            WHERE s.status = 'active' AND s.hall_id = 1
            GROUP BY s.id, s.hall_id, s.start_time, f.title, f.genre
            """
        )
        
        # Запит 5: Поточні індекси
        print(f"\n{'='*80}")
        print("📇 Поточні індекси в БД (PostgreSQL)")
        print(f"{'='*80}\n")
        
        try:
            result = db.session.execute(text("""
                SELECT schemaname, tablename, indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public' AND tablename IN ('session', 'seat', 'booking', 'hall')
                ORDER BY tablename, indexname
            """))
            
            indices = result.fetchall()
            if not indices:
                print("  Індексів не знайдено")
            else:
                current_table = None
                for idx in indices:
                    schema, table, name, definition = idx
                    
                    if table != current_table:
                        if current_table is not None:
                            print()
                        print(f"Таблиця '{table}':")
                        current_table = table
                    
                    print(f"  - {name}")
                    print(f"      {definition}")
                
        except Exception as e:
            print(f"  ❌ Error reading indexes: {str(e)[:200]}\n")
        
        print("\n✅ Аналіз завершено!")


if __name__ == '__main__':
    main()
