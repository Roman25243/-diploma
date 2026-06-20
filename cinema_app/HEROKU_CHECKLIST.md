# 📋 Heroku Deployment Checklist для CinemaBook

Використовуйте цей чеклист перед розгортанням на Heroku.

---

## ✅ Локальна підготовка

- [ ] Всі файли закомічені в Git
- [ ] Немає error messages при `pip install -r requirements.txt`
- [ ] Додаток запускається локально: `gunicorn app:app --bind 0.0.0.0:5000`
- [ ] Базові тести пройдені (якщо є)
- [ ] .env файл містить SECRET_KEY (не порожня)

### Файли для перевірки:
- [ ] ✅ `Procfile` існує
- [ ] ✅ `runtime.txt` існує з `python-3.12.3`
- [ ] ✅ `requirements.txt` включає `gunicorn`
- [ ] ✅ `config.py` оновлена для DATABASE_URL

---

## 🔐 Heroku Конфігурація

### Встановлення Heroku CLI
```bash
# Windows (Chocolatey)
choco install heroku-cli

# Windows (або завантажте з https://devcenter.heroku.com/)
```

- [ ] Heroku CLI встановлена: `heroku --version`
- [ ] Ви залоговані: `heroku login`

### Створення додатку
```bash
heroku create your-unique-app-name
```

- [ ] Додаток створений: `heroku apps`
- [ ] App URL: `https://your-unique-app-name.herokuapp.com`

---

## 🗄️ База даних

### Додання PostgreSQL

```bash
heroku addons:create heroku-postgresql:mini
```

- [ ] PostgreSQL додана: `heroku addons`
- [ ] DATABASE_URL присутня: `heroku config:get DATABASE_URL`

---

## 🔑 Config Variables

Встановіть ці змінні середовища:

```bash
# Безпека
heroku config:set SECRET_KEY="your-random-secret-key"
heroku config:set DEBUG=False

# Email (вибрати ОДИН сервіс)
# Опція 1: Gmail
heroku config:set MAIL_SERVER=smtp.gmail.com
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USE_TLS=True
heroku config:set MAIL_USERNAME=your-email@gmail.com
heroku config:set MAIL_PASSWORD=your-app-password-not-regular-password
heroku config:set MAIL_DEFAULT_SENDER=your-email@gmail.com

# Опція 2: SendGrid (рекомендується для production)
# heroku config:set MAIL_SERVER=smtp.sendgrid.net
# heroku config:set MAIL_PORT=587
# heroku config:set MAIL_USERNAME=apikey
# heroku config:set MAIL_PASSWORD=SG.your-sendgrid-api-key

# Платежі (якщо використовуєте)
# heroku config:set STRIPE_SECRET_KEY=sk_live_...
# heroku config:set STRIPE_PUBLISHABLE_KEY=pk_live_...
# heroku config:set PAYMENT_ONLINE_ENABLED=True
```

- [ ] SECRET_KEY встановлена: `heroku config:get SECRET_KEY`
- [ ] MAIL_SERVER встановлена: `heroku config:get MAIL_SERVER`
- [ ] MAIL_USERNAME встановлена: `heroku config:get MAIL_USERNAME`
- [ ] MAIL_PASSWORD встановлена: `heroku config:get MAIL_PASSWORD`
- [ ] Усі змінні встановлені: `heroku config`

---

## 📤 Розгортання

### Via Heroku Git (простіше для першого разу)

```bash
cd cinema_app
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

- [ ] Deploy успішний (не має ошибок в консолі)
- [ ] Логи показують успіх: `heroku logs --tail`

### Via GitHub (рекомендується)

1. Push код на GitHub
2. У Heroku Dashboard → App Settings → Deployment Method → GitHub
3. Connect GitHub → Select Repository → Select Branch
4. Enable "Automatic Deploys"

- [ ] GitHub connected
- [ ] Branch selected
- [ ] Auto-deploy enabled

---

## 🗄️ Міграції БД

Після першого deploy:

```bash
# Автоматично запускається через Procfile
# Але якщо потрібне ручне:
heroku run flask db upgrade
```

- [ ] Міграції пройшли: `heroku logs --tail | grep "Upgrading"`
- [ ] БД має таблиці: `heroku pg:psql` → `\dt`

### Opціонально: Створення Admin

```bash
heroku run python create_admin.py
```

- [ ] Admin створений

---

## ✨ Перевірка

Відвідайте додаток:

```bash
heroku open
```

### Тестові endpoints:

```bash
# Основна сторінка
https://your-app-name.herokuapp.com/

# Фільми (JSON API)
https://your-app-name.herokuapp.com/api/films

# Статус автентифікації
https://your-app-name.herokuapp.com/api/auth/status

# Адмін-панель
https://your-app-name.herokuapp.com/admin
```

- [ ] Додаток завантажується без помилок
- [ ] Фронтенд (Vue 3) відображається коректно
- [ ] API endpoints відповідають (200 OK)
- [ ] Email сповіщення надходять (тестуйте реєстрацію)

---

## 🔄 Оновлення коду

Після змін у коді:

```bash
# Якщо використовуєте Heroku Git
git add .
git commit -m "Your changes description"
git push heroku main

# Якщо використовуєте GitHub Auto-Deploy
git add .
git commit -m "Your changes description"
git push origin main
# (Heroku автоматично розгортає)

# Перегляд статусу
heroku releases
heroku logs --tail
```

---

## 🐛 Розв'язування проблем

| Проблема | Рішення |
|----------|---------|
| "Application error" | `heroku logs --tail` для деталей |
| Database connection failed | `heroku config:get DATABASE_URL` |
| Email не надходить | Перевірте MAIL_USERNAME/PASSWORD та SMTP сервер |
| PORT error | Heroku автоматично встановлює PORT (не потрібно встановлювати) |
| Міграції не запустились | `heroku run flask db upgrade` |
| Restart потрібен | `heroku restart` |
| Перевірити БД | `heroku pg:psql` → `SELECT * FROM users;` |

---

## 📊 Моніторинг

```bash
# Перегляд процесів
heroku ps

# Логи
heroku logs --tail

# Конфігурація
heroku config

# Інформація про додаток
heroku info
```

---

## 💡 Поради

1. **Завжди робіть backup БД перед великими змінами**
   ```bash
   heroku pg:backups:capture
   heroku pg:backups:download
   ```

2. **Встановіть Papertrail для розширеного логування**
   ```bash
   heroku addons:create papertrail:choklad
   ```

3. **Проводьте тестування локально перед push**
   ```bash
   # Симулюйте production
   FLASK_ENV=production gunicorn app:app
   ```

4. **Використовуйте GitHub для auto-deploy** (безпечніше ніж Heroku Git)

---

## 🎉 Готово!

Якщо все пройшло успішно:
- ✅ Додаток доступний на `https://your-app-name.herokuapp.com`
- ✅ Користувачі можуть реєструватись і бронювати квитки
- ✅ Email сповіщення надходять
- ✅ База даних синхронізована з Heroku PostgreSQL

---

## 📞 Якщо щось не працює

1. Перевірте логи: `heroku logs --tail`
2. Перевірте конфіг: `heroku config`
3. Перевірте БД: `heroku pg:psql`
4. Перезавантажте: `heroku restart`
5. Прочитайте DEPLOYMENT_GUIDE.md для деталей

**Успіхів з деплоєм! 🚀**
