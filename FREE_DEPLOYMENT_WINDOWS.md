# 🚀 Безплатний деплой CinemaBook для Windows

Якщо вам потрібен саме безплатний варіант, то **Heroku не підходить**, бо нові акаунти більше не мають безплатних dyno. Найпростіша безплатна зв'язка для вашого Flask-проєкту:

- **Render** для веб-додатку
- **Neon** для PostgreSQL

Ваш код уже майже готовий до цього, бо `config.py` читає `DATABASE_URL`, а `requirements.txt` уже містить `gunicorn`.

---

## Що буде безплатним

- **Render Free Web Service** - безплатний хостинг застосунку, але він може засинати після простою
- **Neon Free PostgreSQL** - безплатна база даних для старту

---

## 1. Підготуйте код

Переконайтеся, що у вас є:

- `Procfile` у корені проєкту
- `requirements.txt` з `gunicorn`
- `config.py`, який бере `DATABASE_URL` з середовища

Для цього проєкту це вже зроблено.

---

## 2. Створіть безплатну PostgreSQL у Neon

1. Зареєструйтесь на https://neon.tech/
2. Створіть новий проєкт
3. Скопіюйте connection string
4. Якщо рядок починається з `postgres://`, залиште як є або замініть на `postgresql://` для сумісності

Приклад:
```text
postgresql://user:password@ep-xxxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

---

## 3. Розгорніть веб-додаток на Render

1. Зареєструйтесь на https://render.com/
2. Підключіть GitHub repository з `cinema_app`
3. Створіть новий **Web Service**
4. Оберіть цей репозиторій
5. Вкажіть такі налаштування:

### Build Command
```powershell
pip install -r requirements.txt
```

### Start Command
```powershell
gunicorn app:app --bind 0.0.0.0:$PORT
```

Render сам дасть змінну `PORT`, тому саме такий запуск потрібен.

---

## 4. Встановіть змінні середовища на Render

У Render Dashboard додайте такі variables:

```text
SECRET_KEY=your-random-secret-key
DEBUG=False
DATABASE_URL=postgresql://...from_neon...
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
PAYMENT_ONLINE_ENABLED=True
PAYMENT_PROVIDER=stripe
PAYMENT_CURRENCY=UAH
PAYMENT_APP_BASE_URL=https://your-render-app.onrender.com
PAYMENT_SUCCESS_URL=https://your-render-app.onrender.com/app/profile?payment=success
PAYMENT_CANCEL_URL=https://your-render-app.onrender.com/app/profile?payment=cancel
```

### Згенерувати SECRET_KEY на Windows
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. Міграції бази даних

Після першого деплою виконайте міграції локально, підключившись до Neon через `DATABASE_URL`.

### Варіант через PowerShell
```powershell
$env:DATABASE_URL = "postgresql://...from_neon..."
$env:SECRET_KEY = "your-random-secret-key"
$env:DEBUG = "False"

flask db upgrade
```

Якщо `flask` не знайдено, активуйте віртуальне середовище проєкту перед командою.

---

## 6. Перевірка

Після деплою відкрийте Render URL і перевірте:

- головну сторінку
- `/api/films`
- логін/реєстрацію
- створення бронювання

Якщо щось не стартує, відкрийте логи Render і подивіться помилку під час запуску.

---

## 7. Що важливо знати про безплатний варіант

- Render free service може засинати після простою
- Перший запит після паузи може бути повільнішим
- PostgreSQL у Neon free tier має обмеження, але для тесту і малого проєкту цього зазвичай достатньо

---

## 8. Коротко: послідовність дій

```powershell
# 1. Створити Neon DB
# 2. Створити Render Web Service
# 3. Додати DATABASE_URL і SECRET_KEY
# 4. Build: pip install -r requirements.txt
# 5. Start: gunicorn app:app --bind 0.0.0.0:$PORT
# 6. Запустити flask db upgrade
```

---

## Якщо хочете лишитися саме на Heroku

Тоді безплатного варіанту вже не буде. Для Heroku доведеться або:

- платити за Heroku dyno + Heroku Postgres
- або використовувати іншу платформу

Для повністю безплатного шляху рекомендую саме **Render + Neon**.
