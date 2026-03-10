"""
Скрипт для щоденної відправки повідомлень про нові сеанси обраних фільмів.

Запускати щодня увечері (наприклад о 21:00) через планувальник задач:
- Windows: Task Scheduler
- Linux/Mac: cron

Приклад для Task Scheduler:
python d:\Кузь\cinema_app\send_daily_notifications.py

Приклад для cron (щодня о 21:00):
0 21 * * * cd /path/to/cinema_app && python send_daily_notifications.py
"""

from app import app, db
from models import Session, Film, Favorite, User, SessionNotification
from utils import send_email
from flask import render_template, url_for
from datetime import datetime, timedelta
from collections import defaultdict


def send_daily_session_notifications():
    """
    Надсилає щоденні повідомлення про нові сеанси.
    
    Логіка:
    1. Знаходить всі сеанси створені сьогодні
    2. Групує їх по film_id
    3. Для кожного фільму перевіряє чи вже надсилали повідомлення сьогодні
    4. Надсилає одне повідомлення з усіма новими сеансами (на різні дні)
    5. Записує факт надсилання
    """
    with app.app_context():
        # Визначаємо сьогоднішню дату (початок дня)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_str = today_start.strftime('%Y-%m-%d')
        
        # Знаходимо всі сеанси створені сьогодні
        new_sessions = Session.query.filter(
            Session.created_at >= today_start,
            Session.created_at < today_end,
            Session.status == 'active'
        ).all()
        
        if not new_sessions:
            print(f"[{datetime.now()}] Нових сеансів сьогодні не створено")
            return
        
        print(f"[{datetime.now()}] Знайдено {len(new_sessions)} нових сеансів")
        
        # Групуємо сеанси по film_id
        sessions_by_film = defaultdict(list)
        for session in new_sessions:
            sessions_by_film[session.film_id].append(session)
        
        print(f"[{datetime.now()}] Згруповано для {len(sessions_by_film)} фільмів")
        
        # Обробляємо кожен фільм
        total_sent = 0
        for film_id, sessions in sessions_by_film.items():
            try:
                # Перевіряємо чи вже надсилали повідомлення для цього фільму сьогодні
                existing_notification = SessionNotification.query.filter_by(
                    film_id=film_id,
                    notification_date=today_str
                ).first()
                
                if existing_notification:
                    print(f"[{datetime.now()}] Пропускаємо: повідомлення для фільму {film_id} вже надсилалося сьогодні")
                    continue
                
                # Знаходимо фільм
                film = Film.query.get(film_id)
                if not film:
                    print(f"[{datetime.now()}] Помилка: фільм {film_id} не знайдено")
                    continue
                
                # Знаходимо користувачів з цим фільмом в обраних
                favorites = Favorite.query.filter_by(film_id=film_id).all()
                
                if not favorites:
                    print(f"[{datetime.now()}] Пропускаємо: фільм '{film.title}' немає в обраних у жодного користувача")
                    continue
                
                # Групуємо сеанси по датах
                sessions_by_date = defaultdict(list)
                for session in sessions:
                    session_date = session.start_time.split(' ')[0]
                    sessions_by_date[session_date].append(session)
                
                # Сортуємо дати
                sorted_dates = sorted(sessions_by_date.keys())
                
                # Надсилаємо повідомлення кожному користувачу
                for favorite in favorites:
                    user = favorite.user
                    
                    try:
                        # Формування URL для сторінки фільму
                        film_url = url_for('main.film_detail', film_id=film.id, _external=True)
                        
                        # Рендеринг шаблонів
                        html_body = render_template(
                            'emails/new_sessions_batch_notification.html',
                            user_name=user.name,
                            film_title=film.title,
                            sessions_by_date=sessions_by_date,
                            sorted_dates=sorted_dates,
                            film_url=film_url
                        )
                        
                        text_body = render_template(
                            'emails/new_sessions_batch_notification.txt',
                            user_name=user.name,
                            film_title=film.title,
                            sessions_by_date=sessions_by_date,
                            sorted_dates=sorted_dates,
                            film_url=film_url
                        )
                        
                        # Відправка email
                        send_email(
                            subject=f'Нові сеанси: {film.title}',
                            sender=app.config['MAIL_DEFAULT_SENDER'],
                            recipients=[user.email],
                            text_body=text_body,
                            html_body=html_body,
                            app=app
                        )
                        
                        total_sent += 1
                        
                    except Exception as e:
                        print(f"[{datetime.now()}] Помилка відправки email користувачу {user.email}: {str(e)}")
                
                # Записуємо що повідомлення надіслано сьогодні для цього фільму
                notification_record = SessionNotification(
                    film_id=film_id,
                    notification_date=today_str
                )
                db.session.add(notification_record)
                db.session.commit()
                
                dates_str = ', '.join(sorted_dates)
                print(f"[{datetime.now()}] ✓ Надіслано {len(favorites)} повідомлень про '{film.title}' (дати: {dates_str})")
                
            except Exception as e:
                print(f"[{datetime.now()}] Помилка обробки фільму {film_id}: {str(e)}")
                db.session.rollback()
                continue
        
        print(f"[{datetime.now()}] Завершено! Всього надіслано {total_sent} повідомлень")


if __name__ == '__main__':
    print("=" * 70)
    print(f"Запуск щоденної розсилки повідомлень про нові сеанси")
    print(f"Час запуску: {datetime.now()}")
    print("=" * 70)
    
    try:
        send_daily_session_notifications()
    except Exception as e:
        print(f"[{datetime.now()}] КРИТИЧНА ПОМИЛКА: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("=" * 70)
    print(f"Робота завершена: {datetime.now()}")
    print("=" * 70)
