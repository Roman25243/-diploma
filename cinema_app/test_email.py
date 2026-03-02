"""Тестовий скрипт для перевірки email"""
from app import create_app
from flask_mail import Message
from extensions import mail

app = create_app()

with app.app_context():
    print("🧪 Тестування відправки email...")
    print(f"📧 MAIL_SERVER: {app.config['MAIL_SERVER']}")
    print(f"📧 MAIL_PORT: {app.config['MAIL_PORT']}")
    print(f"📧 MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"📧 MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")
    print()
    
    try:
        msg = Message(
            subject="🎬 Тестовий лист з Cinema App",
            recipients=["test@example.com"],
            body="Це тестовий лист. Якщо ви бачите це в MailTrap - все працює!",
            html="<h1>🎉 Вітаємо!</h1><p>Це тестовий лист. Якщо ви бачите це в MailTrap - <strong>все працює!</strong></p>"
        )
        mail.send(msg)
        print("✅ Email успішно відправлено!")
        print("📬 Перевірте ваш MailTrap inbox: https://mailtrap.io/inboxes")
    except Exception as e:
        print(f"❌ Помилка: {e}")
        print("\n💡 Перевірте:")
        print("   1. Чи правильні дані в .env файлі")
        print("   2. Чи активоване віртуальне середовище")
        print("   3. Чи встановлено Flask-Mail")
