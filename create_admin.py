"""
Скрипт для створення адміністратора
Використання: python create_admin.py
"""

from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash


def create_admin():
    """Створення адмін-акаунту"""
    with app.app_context():
        print("=== Створення адміністратора ===\n")
        
        # Перевірка чи вже існує адмін
        existing_admin = User.query.filter_by(is_admin=True).first()
        if existing_admin:
            print(f"⚠️  Адміністратор вже існує: {existing_admin.email}")
            print(f"📧 Email: {existing_admin.email}")
            print(f"👤 Ім'я: {existing_admin.name}")
            print("\nЯкщо ви забули пароль, видаліть користувача в базі даних та створіть нового.")
            return
        
        # Введення даних
        email = input("📧 Email адміна (наприклад, admin@cinema.com): ").strip()
        if not email:
            print("❌ Email не може бути порожнім!")
            return
            
        # Перевірка чи email вже використовується
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ Користувач з email {email} вже існує!")
            
            # Пропонуємо зробити його адміном
            make_admin = input("Зробити цього користувача адміністратором? (y/n): ").strip().lower()
            if make_admin == 'y':
                existing_user.is_admin = True
                db.session.commit()
                print(f"✅ Користувач {email} тепер адміністратор!")
                print(f"👤 Ім'я: {existing_user.name}")
                return
            else:
                print("❌ Операція скасована")
                return
        
        name = input("👤 Ім'я адміна (наприклад, Admin): ").strip()
        if not name:
            name = "Admin"
            
        password = input("🔐 Пароль (мінімум 6 символів): ").strip()
        if len(password) < 6:
            print("❌ Пароль занадто короткий! Мінімум 6 символів.")
            return
        
        # Створення адміна
        hashed_password = generate_password_hash(password)
        admin = User(
            email=email,
            password=hashed_password,
            name=name,
            is_admin=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n✅ Адміністратор успішно створений!")
        print(f"📧 Email: {email}")
        print(f"👤 Ім'я: {name}")
        print(f"🔐 Пароль: {'*' * len(password)}")
        print("\n🚀 Тепер ви можете увійти на http://localhost:5000/app/login")
        print("🔧 Адмін-панель доступна на http://localhost:5000/app/admin")


if __name__ == '__main__':
    create_admin()
