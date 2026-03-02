# 📧 Налаштування Email-Сповіщень

Інструкція з налаштування email-повідомлень про бронювання квитків.

## 🚀 Швидкий старт

### 1️⃣ Встановіть змінні середовища

Створіть файл `.env` в корені проекту (скопіюйте `.env.example`):

```bash
cp .env.example .env
```

### 2️⃣ Налаштуйте SMTP

Оберіть один із варіантів:

---

## 📮 Варіанти SMTP-сервісів

### ✅ Gmail (Рекомендовано для продакшну)

1. **Увімкніть 2-факторну автентифікацію** в Google Account
2. **Створіть App Password**: 
   - Перейдіть: https://myaccount.google.com/apppasswords
   - Оберіть "Mail" → "Windows Computer"
   - Скопіюйте згенерований пароль (16 символів)
   
3. **Додайте в `.env`**:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App Password (без пробілів)
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

---

### 🧪 MailTrap (Для тестування)

Ідеально для розробки - всі листи йдуть в тестовий inbox.

1. Зареєструйтесь: https://mailtrap.io/
2. Створіть inbox
3. Скопіюйте SMTP credentials

```env
MAIL_SERVER=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USE_TLS=True
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
MAIL_DEFAULT_SENDER=cinema@example.com
```

---

### 📧 Outlook / Hotmail

```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-email@outlook.com
```

---

### 🚀 SendGrid (Для високого навантаження)

```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

---

## 🧪 Тестування

### Перевірка конфігурації:

```python
# В Python консолі
from flask import Flask
from flask_mail import Mail, Message
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)

with app.app_context():
    msg = Message(
        subject="Тест",
        recipients=["test@example.com"],
        body="Тестовий лист"
    )
    mail.send(msg)
    print("✅ Email відправлено!")
```

### Тест через додаток:

1. Запустіть сервер: `python app.py`
2. Зареєструйте користувача
3. Забронюйте квиток
4. Перевірте email (або MailTrap inbox)

---

## 📋 Що відправляється:

### При бронюванні:
- ✅ Підтвердження з деталями (фільм, час, місця, ціна)
- ✅ Красивий HTML-шаблон
- ✅ Посилання на профіль

### При скасуванні:
- ✅ Повідомлення про скасування
- ✅ Деталі скасованого бронювання

---

## ⚠️ Типові помилки

### "SMTPAuthenticationError: Username and Password not accepted"
- Перевірте правильність email/пароля
- Для Gmail: використовуйте **App Password**, не звичайний пароль
- Переконайтесь, що 2FA увімкнена (для Gmail)

### "Connection timeout"
- Перевірте MAIL_SERVER та MAIL_PORT
- Переконайтесь, що ваш firewall не блокує з'єднання
- Спробуйте MAIL_USE_TLS=False (не рекомендовано)

### Листи не приходять
- Перевірте папку SPAM
- Переконайтесь, що email в базі даних правильний
- Перевірте логи: `print(f"Sending to: {user.email}")`

### Листи відправляються повільно
- ✅ **Вже виправлено!** Використовується асинхронна відправка через Thread
- Користувач не чекає на відправку email

---

## 🔒 Безпека

⚠️ **НІКОЛИ не commit'те `.env` файл!**

Додайте в `.gitignore`:
```
.env
*.env
```

---

## 💡 Поради

1. **Для розробки**: Використовуйте MailTrap - безпечно і зручно
2. **Для продакшну**: Gmail (безкоштовно) або SendGrid (12k листів/місяць безкоштовно)
3. **Перевірте**: Що email-адреси користувачів валідні
4. **Моніторинг**: Логуйте помилки відправки для дебагу

---

## 📧 Email-шаблони

Розташовані в `templates/emails/`:
- `booking_confirmation.html` - HTML версія підтвердження
- `booking_confirmation.txt` - текстова версія
- `booking_cancelled.html` - HTML версія скасування
- `booking_cancelled.txt` - текстова версія

Можете їх кастомізувати під свій дизайн! 🎨

---

## 🆘 Потрібна допомога?

Якщо щось не працює:
1. Перевірте `.env` файл
2. Протестуйте з MailTrap
3. Перевірте логи сервера
4. Переконайтесь, що Flask-Mail встановлено: `pip install Flask-Mail`

---

**Готово! 🎉** Тепер ваші користувачі будуть отримувати професійні email-сповіщення.
