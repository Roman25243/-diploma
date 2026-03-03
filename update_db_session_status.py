"""
Скрипт для оновлення бази даних - додавання поля status до таблиці Session
"""
from app import app, db
from models import Session

def update_database():
    """Додає поле status до існуючих сеансів"""
    with app.app_context():
        try:
            # Додаємо колонку status якщо її немає
            with db.engine.connect() as conn:
                # Перевіряємо чи колонка вже існує
                result = conn.execute(db.text(
                    "PRAGMA table_info(session)"
                ))
                columns = [row[1] for row in result]
                
                if 'status' not in columns:
                    print("Додаємо колонку 'status' до таблиці Session...")
                    conn.execute(db.text(
                        "ALTER TABLE session ADD COLUMN status VARCHAR(20) DEFAULT 'active'"
                    ))
                    conn.commit()
                    print("✓ Колонку 'status' успішно додано!")
                    
                    # Оновлюємо всі існуючі сеанси
                    conn.execute(db.text(
                        "UPDATE session SET status = 'active' WHERE status IS NULL"
                    ))
                    conn.commit()
                    print("✓ Всі існуючі сеанси позначені як 'active'")
                else:
                    print("✓ Колонка 'status' вже існує")
                    
        except Exception as e:
            print(f"✗ Помилка: {str(e)}")
            raise

if __name__ == '__main__':
    print("Початок оновлення бази даних...")
    update_database()
    print("Оновлення завершено!")
