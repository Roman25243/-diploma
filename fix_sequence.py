"""
Скрипт для виправлення послідовності ID у таблицях PostgreSQL
"""
from app import app, db
from sqlalchemy import text

def fix_sequences():
    """Виправлення послідовностей для всіх таблиць"""
    with app.app_context():
        try:
            # Список таблиць з їх первинними ключами
            tables = [
                ('session', 'id'),
                ('film', 'id'),
                ('booking', 'id'),
                ('review', 'id'),
                ('seat', 'id'),
                ('"user"', 'id'),  # Екранування для зарезервованого слова
            ]
            
            for table_name, id_column in tables:
                # Отримуємо максимальний ID
                result = db.session.execute(
                    text(f"SELECT MAX({id_column}) FROM {table_name}")
                ).scalar()
                
                max_id = result if result else 0
                next_id = max_id + 1
                
                # Скидаємо послідовність (без лапок для назви послідовності)
                sequence_name = f"{table_name.strip('\"')}_{id_column}_seq"
                db.session.execute(
                    text(f"SELECT setval('{sequence_name}', {next_id}, false)")
                )
                
                print(f"✅ Таблиця {table_name}: послідовність встановлено на {next_id}")
            
            db.session.commit()
            print("\n🎉 Всі послідовності виправлено успішно!")
            
        except Exception as e:
            print(f"❌ Помилка: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_sequences()
