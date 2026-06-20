# 🚀 Швидкий старт Heroku розгортання для Windows

Цей гайд - для користувачів Windows які хочуть швидко задеплоїти CinemaBook на Heroku.

Важливо: **Heroku зараз не має повністю безплатного варіанту** для нового деплою. Якщо вам потрібен саме free deployment, відкрийте [FREE_DEPLOYMENT_WINDOWS.md](FREE_DEPLOYMENT_WINDOWS.md) і використовуйте Render + Neon.

---

## 1️⃣ Встановлення Heroku CLI

### Варіант А: Через Chocolatey (рекомендується)
```powershell
# Якщо у вас Chocolatey встановлена:
choco install heroku-cli
```

### Варіант Б: Пряме завантаження
1. Завантажте з https://devcenter.heroku.com/articles/heroku-cli
2. Встановіть `.exe` файл
3. Перезавантажте PowerShell

### Перевірка
```powershell
heroku --version
# Вихід: heroku/8.X.X
```

---

## 2️⃣ Інініціалізація Git (якщо ще не зроблено)

```powershell
cd d:\Кузь\cinema_app

# Ініціалізація Git (якщо ще немає .git папки)
git init

# Встановіть git configuration
git config user.email "your-email@example.com"
git config user.name "Your Name"

# Додайте всі файли
git add .

# Перший commit
git commit -m "Initial commit - CinemaBook app ready for Heroku"
```

**Перевірка:**
```powershell
git status
# Вихід: On branch main, nothing to commit
```

---

## 3️⃣ Логін до Heroku

```powershell
heroku login
```

**Це откроє браузер для автентифікації. Виконайте логін там.**

### Перевірка
```powershell
heroku auth:whoami
# Вихід: your-email@example.com
```

---

## 4️⃣ Створення Heroku додатку

```powershell
# Створити додаток з унікальним іменем
heroku create cinema-app-ua-2026

# Або дозвольте Heroku генерувати ім'я
heroku create
```

**Запам'ятайте назву! Вона буде у форматі:** `https://cinema-app-ua-2026.herokuapp.com`

### Перевірка
```powershell
heroku apps
# Вихід: === Your apps cinema-app-ua-2026
```

---

## 5️⃣ Додання PostgreSQL

Heroku PostgreSQL - це платний addon. Для безплатного варіанту використовуйте Neon і дивіться [FREE_DEPLOYMENT_WINDOWS.md](FREE_DEPLOYMENT_WINDOWS.md).

```powershell
# Додайте мінімальний план PostgreSQL ($5/місяц)
heroku addons:create heroku-postgresql:mini --app cinema-app-ua-2026
```

**Це автоматично встановить `DATABASE_URL`**

### Перевірка
```powershell
heroku config:get DATABASE_URL --app cinema-app-ua-2026
# Вихід: postgres://user:pass@host:port/dbname
```

---

## 6️⃣ Встановлення конфіг змінних

### Генеруємо SECRET_KEY
```powershell
# Генеруємо випадкову строку
python -c "import secrets; print(secrets.token_hex(32))"
# Копіюємо результат
```

### Встановлюємо змінні
```powershell
$app_name = "cinema-app-ua-2026"

# Безпека (замініть YOUR_SECRET на результат вище)
heroku config:set SECRET_KEY="YOUR_SECRET_KEY_HERE" --app $app_name
heroku config:set DEBUG=False --app $app_name

# Email (вибрати ОДИН варіант)

# --- Варіант 1: Gmail ---
heroku config:set MAIL_SERVER=smtp.gmail.com --app $app_name
heroku config:set MAIL_PORT=587 --app $app_name
heroku config:set MAIL_USE_TLS=True --app $app_name
heroku config:set MAIL_USERNAME=your-email@gmail.com --app $app_name
heroku config:set MAIL_PASSWORD=your-app-password --app $app_name
heroku config:set MAIL_DEFAULT_SENDER=your-email@gmail.com --app $app_name

# --- Варіант 2: SendGrid (краще для production) ---
# heroku config:set MAIL_SERVER=smtp.sendgrid.net --app $app_name
# heroku config:set MAIL_PORT=587 --app $app_name
# heroku config:set MAIL_USERNAME=apikey --app $app_name
# heroku config:set MAIL_PASSWORD=SG.your_api_key --app $app_name
# heroku config:set MAIL_DEFAULT_SENDER=noreply@cinemabook.com --app $app_name

# Payment URLs (якщо використовуєте Stripe)
heroku config:set PAYMENT_APP_BASE_URL=https://cinema-app-ua-2026.herokuapp.com --app $app_name
```

### Перевірка
```powershell
heroku config --app cinema-app-ua-2026
# Вихід: === cinema-app-ua-2026 Config Vars DATABASE_URL: postgres://...
```

---

## 7️⃣ Розгортання (Deploy)

```powershell
$app_name = "cinema-app-ua-2026"

# Додаємо remote для Heroku (якщо ще не додано)
# Це має бути автоматично, але якщо потрібне:
# heroku git:remote --app $app_name

# Push коду на Heroku
git push heroku main

# Якщо у вас гілка 'master' замість 'main':
# git push heroku master
```

**Це запустить розгортання. Чекайте 2-3 хвилин...**

### Перегляд логів під час deploy
```powershell
heroku logs --tail --app cinema-app-ua-2026
```

---

## 8️⃣ Першого запуск БД

```powershell
$app_name = "cinema-app-ua-2026"

# Запустіть міграції (автоматично через Procfile)
# Але якщо потрібне ручне:
heroku run flask db upgrade --app $app_name

# Перевірте БД
heroku run flask shell --app $app_name
# Потім у shell:
# from models import User
# User.query.count()
# exit()
```

### Opціонально: Створіть admin користувача
```powershell
heroku run python create_admin.py --app cinema-app-ua-2026
```

---

## 9️⃣ Перевірка

```powershell
# Відкрийте додаток у браузері
heroku open --app cinema-app-ua-2026
```

### Тестові посилання:
- **Головна:** https://cinema-app-ua-2026.herokuapp.com/
- **API Фільми:** https://cinema-app-ua-2026.herokuapp.com/api/films
- **Реєстрація:** https://cinema-app-ua-2026.herokuapp.com/register
- **Адмін:** https://cinema-app-ua-2026.herokuapp.com/admin

---

## 🔄 Оновлення коду після розгортання

Після змін у коді:

```powershell
$app_name = "cinema-app-ua-2026"

# Комітимо зміни
git add .
git commit -m "Description of changes"

# Push на Heroku
git push heroku main

# Перегляд статусу
heroku logs --tail --app $app_name
```

---

## 📊 Корисні команди

```powershell
$app_name = "cinema-app-ua-2026"

# Інформація про додаток
heroku info --app $app_name

# Статус процесів
heroku ps --app $app_name

# Перегляд конфіг
heroku config --app $app_name

# Редагування конфіг
heroku config:set KEY=value --app $app_name
heroku config:unset KEY --app $app_name

# Логи в реальному часі
heroku logs --tail --app $app_name

# Останні 50 рядків логів
heroku logs --num=50 --app $app_name

# Підключення до PostgreSQL
heroku pg:psql --app $app_name

# Список додатків
heroku apps

# Видалення додатку (обережно!)
heroku apps:destroy --app $app_name --confirm $app_name
```

---

## 🐛 Вирішення проблем

### Проблема: "Application error"
```powershell
# Перегляд логів
heroku logs --tail --app cinema-app-ua-2026
```

### Проблема: Build Failed
- Перевірте `requirements.txt` синтаксис
- Переконайтесь, що Procfile коректний
- Перегляд логів для деталей

### Проблема: DATABASE_URL не встановлена
```powershell
# Перевіримо
heroku config:get DATABASE_URL --app cinema-app-ua-2026

# Якщо порожня - додайте PostgreSQL:
heroku addons:create heroku-postgresql:mini --app cinema-app-ua-2026
```

### Проблема: Email не надходить
- Перевірте MAIL_USERNAME та MAIL_PASSWORD
- Для Gmail - використовуйте App Password (не звичайний пароль)
- Перегляд логів для деталей SMTP

### Проблема: Port Error
- Heroku автоматично встановлює PORT
- app.py уже налаштована для цього

---

## 💾 Backup бази даних

```powershell
$app_name = "cinema-app-ua-2026"

# Створити backup
heroku pg:backups:capture --app $app_name

# Завантажити backup
heroku pg:backups:download --app $app_name
# Файл буде завантажений в поточну директорію

# Список backups
heroku pg:backups --app $app_name
```

---

## 🎉 Готово!

Якщо все пройшло успішно, ваш додаток доступний на:
**https://cinema-app-ua-2026.herokuapp.com**

---

## 📚 Наступні кроки

1. **Налаштуйте домен** (опціонально)
   ```powershell
   heroku domains:add www.your-domain.com --app $app_name
   ```

2. **Додайте Redis для кешування**
   ```powershell
   heroku addons:create heroku-redis:premium-0 --app $app_name
   ```

3. **Встановіть Papertrail для логування**
   ```powershell
   heroku addons:create papertrail --app $app_name
   ```

4. **Auto-deploy з GitHub** (безпечніше)
   - Heroku Dashboard → Deploy → Connect to GitHub
   - Оберіть репозиторій та гілку

---

**Успіхів! 🎬**
