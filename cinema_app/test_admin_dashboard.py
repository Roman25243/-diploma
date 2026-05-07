#!/usr/bin/env python3
"""
Тестування нових admin stats endpoints з підтримкою залів
"""
from app import app, db
from models import User, Hall, Session, Seat, Booking, Film
import json

def test_admin_stats():
    """Тестування /api/admin/stats endpoint"""
    print("\n" + "="*80)
    print("📊 ТЕСТУВАННЯ ADMIN STATS ENDPOINTS")
    print("="*80 + "\n")
    
    with app.app_context():
        with app.test_client() as client:
            # 1. Перевіримо що эндпоинт є і повертає дані
            print("1️⃣ Тестування /api/admin/stats")
            print("-" * 80)
            
            # Спочатку нам потрібен admin користувач
            admin_user = User.query.filter_by(is_admin=True).first()
            
            if not admin_user:
                print("❌ Немає admin користувача. Створюємо...")
                admin_user = User(
                    email='admin_test@test.com',
                    name='Test Admin',
                    is_admin=True
                )
                admin_user.set_password('test123')
                db.session.add(admin_user)
                db.session.commit()
            
            # Логінуємось
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
            
            # Тестуємо основну статистику
            res = client.get('/api/admin/stats')
            print(f"Status: {res.status_code}")
            
            if res.status_code == 200:
                data = res.get_json()
                print(f"✅ Основна статистика завантажена:")
                print(f"   - Користувачів: {data.get('total_users')}")
                print(f"   - Бронювань: {data.get('total_bookings')}")
                print(f"   - Фільмів: {data.get('total_films')}")
                print(f"   - Сеансів: {data.get('total_sessions')}")
                print(f"   - Залів: {data.get('total_halls')}")
                print(f"   - Виручка: {data.get('total_revenue')} грн")
                
                # Перевіримо що є інформація по залам
                if 'halls_stats' in data:
                    print(f"\n✅ Статистика по залам:")
                    for hall in data['halls_stats']:
                        print(f"   - {hall['hall_name']}: {hall['occupancy_pct']}% окупованість, {hall['revenue']} грн виручки")
                else:
                    print("⚠️ Немає інформації по залам")
            else:
                print(f"❌ Error: {res.data}")
            
            # 2. Тестування /api/admin/stats/occupancy
            print("\n\n2️⃣ Тестування /api/admin/stats/occupancy")
            print("-" * 80)
            
            res = client.get('/api/admin/stats/occupancy')
            print(f"Status: {res.status_code}")
            
            if res.status_code == 200:
                data = res.get_json()
                print(f"✅ Дані окупованості завантажені:")
                print(f"   - Залів: {len(data.get('labels', []))}")
                for i, label in enumerate(data.get('labels', [])):
                    occupancy = data.get('occupancy', [])[i] if i < len(data.get('occupancy', [])) else 0
                    print(f"      {label}: {occupancy}%")
                
                # Перевіримо структуру для графіка
                required_fields = ['labels', 'occupancy', 'booked', 'total']
                missing = [f for f in required_fields if f not in data]
                if missing:
                    print(f"⚠️ Відсутні поля: {missing}")
                else:
                    print("✅ Всі необхідні поля присутні для графіка")
            else:
                print(f"❌ Error: {res.data}")
            
            # 3. Тестування /api/admin/stats/revenue
            print("\n\n3️⃣ Тестування /api/admin/stats/revenue")
            print("-" * 80)
            
            res = client.get('/api/admin/stats/revenue')
            print(f"Status: {res.status_code}")
            
            if res.status_code == 200:
                data = res.get_json()
                print(f"✅ Дані виручки завантажені:")
                print(f"   - Залів: {len(data.get('labels', []))}")
                for i, label in enumerate(data.get('labels', [])):
                    revenue = data.get('revenue', [])[i] if i < len(data.get('revenue', [])) else 0
                    bookings = data.get('bookings', [])[i] if i < len(data.get('bookings', [])) else 0
                    print(f"      {label}: {revenue} грн ({bookings} бронювань)")
                
                # Перевіримо структуру для графіка
                required_fields = ['labels', 'revenue', 'bookings']
                missing = [f for f in required_fields if f not in data]
                if missing:
                    print(f"⚠️ Відсутні поля: {missing}")
                else:
                    print("✅ Всі необхідні поля присутні для графіка")
            else:
                print(f"❌ Error: {res.data}")
    
    print("\n" + "="*80)
    print("✅ ТЕСТУВАННЯ ЗАВЕРШЕНО")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_admin_stats()
