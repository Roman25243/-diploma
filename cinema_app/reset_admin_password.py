"""
Скрипт для зміни паролю адміністратора
Використання: python reset_admin_password.py
"""

from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


def reset_admin_password():
    """Зміна паролю адміна"""
    with app.app_context():
        print("=== Зміна паролю адміністратора ===\n")
        
        # Знаходимо адміна
        admin = User.query.filter_by(is_admin=True).first()
        
        if not admin:
            print("❌ Адміністратор не знайдений!")
            print("Спочатку створіть адміна за допомогою: python create_admin.py")
            return
        
        print(f"👤 Знайдено адміна:")
        print(f"📧 Email: {admin.email}")
        print(f"👤 Ім'я: {admin.name}\n")
        
        # Введення нового паролю
        new_password = input("🔐 Введіть новий пароль (мінімум 6 символів): ").strip()
        
        if len(new_password) < 6:
            print("❌ Пароль занадто короткий! Мінімум 6 символів.")
            return
        
        # Підтвердження
        confirm = input(f"Підтвердити зміну паролю для {admin.email}? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Операція скасована")
            return
        
        # Зміна паролю
        admin.password = generate_password_hash(new_password)
        db.session.commit()
        
        print("\n✅ Пароль успішно змінено!")
        print(f"📧 Email: {admin.email}")
        print(f"🔐 Новий пароль: {'*' * len(new_password)}")
        print("\n🚀 Тепер ви можете увійти на http://localhost:5000/app/login")


if __name__ == '__main__':
    reset_admin_password()
