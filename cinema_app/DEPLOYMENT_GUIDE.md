# 🚀 Гайд розгортання CinemaBook на Heroku

Цей гайд пояснює, як розгорнути додаток на Heroku з PostgreSQL базою даних.

---

## 📋 Передумови

1. **Heroku Account** - створіть акаунт на https://www.heroku.com/
2. **Heroku CLI** - встановіть з https://devcenter.heroku.com/articles/heroku-cli
3. **Git** - для контролю версій
4. **GitHub Account** - для сховища коду (опціонально, але рекомендується)

---

## 🔧 Крок 1: Підготовка локального середовища

### 1.1 Ініціалізація Git (якщо ще не зроблено)
```bash
cd cinema_app
git init
git add .
git commit -m "Initial commit - CinemaBook app"
```

### 1.2 Перевірка файлів для Heroku
Переконайтесь, що ці файли є в корені проекту:
- ✅ `Procfile` - команда запуску
- ✅ `runtime.txt` - версія Python
- ✅ `requirements.txt` - залежності (з gunicorn)
- ✅ `config.py` - конфігурація (оновлена для Heroku)

### 1.3 Тестування локально з production конфігом
```bash
# Встановіть gunicorn локально
pip install gunicorn

# Запустіть як Heroku це робить
gunicorn app:app --bind 0.0.0.0:5000
```

---

## 🌍 Крок 2: Створення Heroku додатку

### 2.1 Логін до Heroku
```bash
heroku login
```

### 2.2 Створення нового додатку
```bash
heroku create your-app-name
# або без імена (Heroku генерує автоматично)
heroku create
```

**Результат:** Ви отримаєте URL типу `https://your-app-name.herokuapp.com`

### 2.3 Перевірка додатку
```bash
heroku apps
heroku info
```

---

## 🗄️ Крок 3: PostgreSQL база даних

### 3.1 Додання PostgreSQL додатку
```bash
heroku addons:create heroku-postgresql:mini
```

**Варіанти плану:**
- `mini` - $5/місяць (до 10K рядків) - хороший для тесту
- `basic` - $9/місяць (до 10M рядків) - рекомендується
- `standard` - $50+/місяць - для production
- `free` - DEPRECATED (більше недоступна)

**Перевірка:**
```bash
heroku addons
```

Це автоматично встановить змінну середовища `DATABASE_URL`!

### 3.2 Інша опція: PostgreSQL провайдер Heroku Postgres
Якщо вам потрібна більша гнучкість, розглядайте:
- **ElephantSQL** (heroku-postgresql хороший стандартний вибір)
- **AWS RDS** (якщо переходите за межі Heroku)

---

## 🔐 Крок 4: Змінні середовища (Config Vars)

### 4.1 Встановлення необхідних змінних

```bash
# Обов'язково
heroku config:set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
heroku config:set DEBUG=False
heroku config:set FLASK_ENV=production

# Email (Gmail приклад)
heroku config:set MAIL_SERVER=smtp.gmail.com
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USE_TLS=True
heroku config:set MAIL_USERNAME=your-email@gmail.com
heroku config:set MAIL_PASSWORD=your-app-password
heroku config:set MAIL_DEFAULT_SENDER=your-email@gmail.com

# Платежі (якщо використовуєте Stripe)
heroku config:set STRIPE_SECRET_KEY=sk_live_your_secret_key
heroku config:set STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Payment URLs
heroku config:set PAYMENT_APP_BASE_URL=https://your-app-name.herokuapp.com
heroku config:set PAYMENT_SUCCESS_URL=https://your-app-name.herokuapp.com/app/profile?payment=success
heroku config:set PAYMENT_CANCEL_URL=https://your-app-name.herokuapp.com/app/profile?payment=cancel
```

### 4.2 Перевірка змінних
```bash
heroku config
```

### 4.3 Генерація надійного SECRET_KEY
Якщо потребуєте генерації SECRET_KEY на Windows:
```bash
# PowerShell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📤 Крок 5: Розгортання

### 5.1 Push на Heroku
```bash
# Якщо використовуєте heroku git remote
git push heroku main
# або
git push heroku master
```

**Або якщо використовуєте GitHub:**
```bash
# Пов'яжіть GitHub з Heroku Dashboard
# Settings → Deployment method → GitHub
# Оберіть репозиторій і гілку для auto-deploy
```

### 5.2 Запуск міграцій бази даних
Heroku автоматично запустить `flask db upgrade` через `release` команду в Procfile!

Якщо потрібне ручне запуск:
```bash
heroku run flask db upgrade
```

### 5.3 Створення admin користувача (опціонально)
```bash
heroku run python create_admin.py
```

### 5.4 Перегляд логів
```bash
# Реальні логи
heroku logs --tail

# Останні логи
heroku logs --num=50
```

---

## ✅ Крок 6: Перевірка розгортання

### 6.1 Відвідайте додаток
```bash
heroku open
```

### 6.2 Перевірте endpoints
```bash
# Основна сторінка
curl https://your-app-name.herokuapp.com/

# API статус
curl https://your-app-name.herokuapp.com/api/films

# Auth статус
curl https://your-app-name.herokuapp.com/api/auth/status
```

### 6.3 Перевірте БД
```bash
# Підключіться до PostgreSQL
heroku pg:psql

# Усередині psql
\dt  -- список таблиць
SELECT COUNT(*) FROM users;
```

---

## 🔄 Оновлення коду

### Якщо використовуєте Git на Heroku:
```bash
git add .
git commit -m "Your changes"
git push heroku main
```

### Якщо використовуєте GitHub Auto-Deploy:
Просто push на GitHub, Heroku автоматично розгортає!

### Перегляд статусу розгортання:
```bash
heroku releases
heroku releases:info v12  # Конкретна версія
heroku rollback v11       # Повернення до попередньої версії
```

---

## 🐛 Розв'язування проблем

### Проблема: "Application error"
```bash
heroku logs --tail
```
Перевірте логи для деталей помилки.

### Проблема: DATABASE_URL не встановлена
```bash
heroku addons:create heroku-postgresql:mini
heroku config:get DATABASE_URL
```

### Проблема: Email не надходить
- Перевірте MAIL_USERNAME і MAIL_PASSWORD
- Для Gmail використовуйте "App Password", не звичайний пароль
- Перевірте MAIL_DEFAULT_SENDER

### Проблема: Port зайнятий
Heroku автоматично встановлює PORT. Додаток це читає через `os.environ.get('PORT')`

### Проблема: Міграції не запустились
```bash
heroku run flask db stamp head  # Якщо це новий додаток
heroku run flask db upgrade
```

### Перезавантаження додатка
```bash
heroku restart
```

---

## 📊 Моніторинг

### Перегляд використання ресурсів
```bash
# Memoria/CPU
heroku ps

# Детальна інформація
heroku dyno:type
```

### Встановлення скейлінгу (додатково)
```bash
# Один web dyno (за замовчуванням)
heroku ps:scale web=1

# Якщо потрібно більше:
heroku ps:scale web=2
```

---

## 💰 Вартість

### Безплатна тарифа (2022+)
⚠️ **Heroku припинила безплатну тарифу з 28 листопада 2022**

### Мінімальна конфігурація (~$7-9/місяць):
- **Basic Dyno**: $5/місяц (web процес)
- **PostgreSQL mini**: $5/місяц
- **TOTAL**: ~$10/місяц

---

## 🎯 Рекомендації для Production

1. **Email**: Використовуйте SendGrid чи MailTrap замість Gmail
2. **Сеанси**: Розглядайте Redis для кешування (`redis-28`)
3. **Моніторинг**: Увімкніть Heroku Logging або Datadog
4. **CDN**: Додайте Cloudflare для фронтенду/статики
5. **SSL**: Heroku автоматично додає SSL сертифікат
6. **Backups**: Увімкніть PostgreSQL automatic backups

---

## 📚 Корисні посилання

- [Heroku Python Support](https://devcenter.heroku.com/articles/python-support)
- [Flask on Heroku](https://devcenter.heroku.com/articles/getting-started-with-python)
- [Heroku PostgreSQL](https://devcenter.heroku.com/articles/heroku-postgresql)
- [Config Vars](https://devcenter.heroku.com/articles/config-vars)
- [Procfile Format](https://devcenter.heroku.com/articles/procfile)

---

## 🎬 TL;DR - Швидкий старт (3 кроки)

```bash
# 1. Логін та створення
heroku login
heroku create my-cinema-app

# 2. PostgreSQL + config vars
heroku addons:create heroku-postgresql:mini
heroku config:set SECRET_KEY="your-secret-key"

# 3. Deploy!
git push heroku main
heroku open
```

---

**Питання?** Перевірте логи: `heroku logs --tail`
