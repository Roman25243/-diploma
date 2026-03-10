# Налаштування PostgreSQL для Cinema App

Цей посібник крок за кроком допоможе вам налаштувати PostgreSQL для вашого додатку.

---

## 📋 Крок 1: Встановлення PostgreSQL

### 1.1 Завантаження PostgreSQL

1. Відкрийте браузер і перейдіть на https://www.postgresql.org/download/windows/
2. Натисніть **Download the installer**
3. Виберіть версію **PostgreSQL 16.x** (або останню стабільну)
4. Завантажте інсталятор для Windows x86-64

### 1.2 Встановлення PostgreSQL

1. **Запустіть завантажений файл** (наприклад, `postgresql-16.2-1-windows-x64.exe`)
2. Натисніть **Next** на вітальному екрані
3. **Installation Directory**: залиште за замовчуванням (`C:\Program Files\PostgreSQL\16`)
4. **Select Components**: залиште всі галочки (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools)
5. **Data Directory**: залиште за замовчуванням
6. **Password**: 
   - Введіть пароль для користувача `postgres` (наприклад, `admin123`)
   - ⚠️ **ВАЖЛИВО: Запам'ятайте цей пароль!** Він буде потрібен далі
   - Підтвердіть пароль
7. **Port**: залиште `5432` (стандартний порт)
8. **Locale**: залиште за замовчуванням (або виберіть Ukrainian)
9. Натисніть **Next** → **Next** → **Finish**

### 1.3 Перевірка встановлення

Відкрийте PowerShell і виконайте:
```powershell
psql --version
```

Має з'явитися щось на кшталт:
```
psql (PostgreSQL) 16.2
```

---

## 🗄️ Крок 2: Створення бази даних

### Варіант А: Через pgAdmin (графічний інтерфейс, РЕКОМЕНДОВАНО)

1. **Запустіть pgAdmin 4** (знайдіть в меню Пуск)
2. **Перше відкриття**: pgAdmin попросить встановити master password - введіть будь-який пароль
3. В лівому меню розгорніть **Servers** → **PostgreSQL 16**
4. Введіть пароль `postgres`, який ви встановили при інсталяції
5. Правою кнопкою миші на **Databases** → **Create** → **Database...**
6. Введіть дані:
   - **Database**: `cinema_db`
   - **Owner**: `postgres`
   - Натисніть **Save**
7. ✅ База даних створена! Ви побачите `cinema_db` в списку баз даних

### Варіант Б: Через командний рядок

```powershell
# Підключіться до PostgreSQL
psql -U postgres

# Введіть пароль postgres коли попросить
# Потім виконайте команду:
CREATE DATABASE cinema_db;

# Перевірте створення:
\l

# Вийдіть:
\q
```

---

## ⚙️ Крок 3: Налаштування .env файлу

### 3.1 Створення .env файлу

1. Відкрийте папку `cinema_app`
2. Знайдіть файл `.env` (якщо його немає - створіть новий файл з назвою `.env`)

### 3.2 Додайте налаштування PostgreSQL

Відкрийте `.env` файл і додайте/змініть такі рядки:

```env
# ========================================
# БАЗА ДАНИХ POSTGRESQL
# ========================================
# Формат: postgresql://username:password@host:port/database_name
# ВАЖЛИВО: Якщо пароль містить спеціальні символи (#, &, @, тощо), їх потрібно URL-кодувати
# Приклад: пароль admin123 → DATABASE_URL=postgresql://postgres:admin123@localhost:5432/cinema_db
# Якщо пароль містить #: pass#123 →pass%23123
# Якщо пароль містить &: pass&word → pass%26word
DATABASE_URL=postgresql://postgres:admin123@localhost:5432/cinema_db

# ⚠️ Замініть 'admin123' на ваш реальний пароль postgres!

# ========================================
# ІНШІ НАЛАШТУВАННЯ
# ========================================
SECRET_KEY=my_super_secret_key_12345

# Email налаштування (якщо потрібні)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=cinema@example.com
```

**Пояснення DATABASE_URL:**
- `postgresql://` - тип бази даних
- `postgres` - ім'я користувача
- `admin123` - пароль (замініть на свій!)
- `localhost` - адреса сервера (локальний комп'ютер)
- `5432` - порт PostgreSQL
- `cinema_db` - назва бази даних

### ⚠️ ВАЖЛИВО: Спеціальні символи в паролі

Якщо ваш пароль містить спеціальні символи, їх потрібно **URL-кодувати**:

| Символ | URL-код | Приклад |
|--------|---------|---------|
| `#` | `%23` | `pass#123` → `pass%23123` |
| `&` | `%26` | `pass&word` → `pass%26word` |
| `@` | `%40` | `pass@123` → `pass%40123` |
| `/` | `%2F` | `pass/123` → `pass%2F123` |
| `:` | `%3A` | `pass:123` → `pass%3A123` |
| `?` | `%3F` | `pass?123` → `pass%3F123` |
| `%` | `%25` | `pass%123` → `pass%25123` |
| пробіл | `%20` | `pass 123` → `pass%20123` |

**Приклад:**  
Пароль: `MyP@ss#123`  
DATABASE_URL: `postgresql://postgres:MyP%40ss%23123@localhost:5432/cinema_db`

### 3.3 Перевірка .env файлу

Файл `.env` має бути в папці `cinema_app` поруч з файлом `app.py`:
```
cinema_app/
├── .env          ← тут
├── app.py
├── config.py
└── ...
```

---

## 🔧 Крок 4: Встановлення залежностей

Переконайтесь, що віртуальне середовище активоване:

```powershell
# Якщо не активоване, активуйте:
.venv\Scripts\Activate.ps1

# Встановіть/оновіть всі залежності:
pip install -r cinema_app/requirements.txt
```

Ви побачите встановлення `psycopg2-binary-2.9.11` - це драйвер PostgreSQL.

---

## 🏗️ Крок 5: Ініціалізація таблиць в PostgreSQL

```powershell
# Переконайтесь що ви в папці cinema_app
cd cinema_app

# Запустіть Python
python

# В Python консолі виконайте:
```

```python
from app import app, db

with app.app_context():
    db.create_all()
    print("✅ Таблиці успішно створені в PostgreSQL!")

exit()
```

---

## ✅ Крок 6: Перевірка роботи

### 6.1 Перевірка підключення

```powershell
# Запустіть скрипт перегляду бази даних
python view_database.py
```

Ви маєте побачити:
```
================================================================================
 БАЗА ДАНИХ: PostgreSQL
================================================================================
URI: postgresql://postgres:***@localhost:5432/cinema_db

================================================================================
 КОРИСТУВАЧІ
================================================================================
Всього користувачів: X
...
```

### 6.2 Запуск додатку

```powershell
# Запустіть веб-додаток
python app.py
```

Відкрийте браузер: http://localhost:5000

Якщо сторінка відкрилася без помилок - **PostgreSQL працює!** 🎉

---

## � Крок 7: Перегляд даних в PostgreSQL

### Варіант 1: Через view_database.py (найпростіший)

```powershell
python view_database.py
```

### Варіант 2: Через pgAdmin

1. Відкрийте **pgAdmin**
2. Розгорніть: **Servers** → **PostgreSQL 16** → **Databases** → **cinema_db** → **Schemas** → **public** → **Tables**
3. Правою кнопкою на таблиці (наприклад, `film`) → **View/Edit Data** → **All Rows**

### Варіант 3: Через командний рядок

```powershell
# Підключіться до бази даних
psql -U postgres -d cinema_db

# Переглядайте дані:
```

```sql
-- Список всіх таблиць
\dt

-- Переглянути фільми
SELECT id, title, genre FROM film;

-- Переглянути користувачів
SELECT id, username, email, is_admin FROM "user";

-- Переглянути сеанси
SELECT s.id, f.title, s.start_time, s.price, s.available_seats 
FROM session s 
JOIN film f ON s.film_id = f.id;

-- Статистика бронювань
SELECT COUNT(*), SUM(total_price) FROM booking WHERE status = 'confirmed';

-- Вийти
\q
```

### Варіант 4: Через Python інтерактивно

```powershell
python
```

```python
from app import app, db
from models import Film, User, Session, Booking

with app.app_context():
    # Всі фільми
    films = Film.query.all()
    for f in films:
        print(f"{f.id}: {f.title} - {f.genre}")
    
    # Адміністратори
    admins = User.query.filter_by(is_admin=True).all()
    for a in admins:
        print(f"Admin: {a.username}")
    
    # Найближчі сеанси
    from datetime import datetime
    upcoming = Session.query.filter(
        Session.start_time > datetime.now(),
        Session.status == 'scheduled'
    ).order_by(Session.start_time).limit(5).all()
    
    for s in upcoming:
        print(f"{s.film.title} - {s.start_time}")

exit()
```

---

## ⚠️ Поширені помилки та їх вирішення

### Помилка 1: `FATAL: password authentication failed for user "postgres"`

**Причина**: Невірний пароль в `.env`

**Рішення**:
1. Перевірте пароль в `.env` файлі
2. Спробуйте скинути пароль postgres:
```powershell
# В PowerShell від імені адміністратора:
psql -U postgres
# Введіть команду:
ALTER USER postgres WITH PASSWORD 'новий_пароль';
\q
```
3. Оновіть `DATABASE_URL` в `.env` з новим паролем

### Помилка 2: `could not connect to server: Connection refused`

**Причина**: PostgreSQL не запущений

**Рішення**:
1. Відкрийте **Служби Windows** (Services)
2. Знайдіть **postgresql-x64-16**
3. Правою кнопкою → **Запустити** (Start)

Або через командний рядок:
```powershell
# Перевірка статусу
Get-Service postgresql-x64-16

# Запуск служби
Start-Service postgresql-x64-16
```

### Помилка 3: `database "cinema_db" does not exist`

**Причина**: База даних не створена

**Рішення**:
```powershell
psql -U postgres
CREATE DATABASE cinema_db;
\q
```

### Помилка 4: `ModuleNotFoundError: No module named 'psycopg2'`

**Причина**: Драйвер PostgreSQL не встановлений

**Рішення**:
```powershell
pip install psycopg2-binary
```

### Помилка 5: `relation "user" does not exist`

**Причина**: Таблиці не створені

**Рішення**:
```python
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Помилка 6: `SSL connection required`

**Причина**: PostgreSQL вимагає SSL (зазвичай на Windows не виникає)

**Рішення**: Додайте до DATABASE_URL параметр `?sslmode=disable`:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/cinema_db?sslmode=disable
```

### Помилка 7: `port 5432 already in use`

**Причина**: Порт зайнятий іншою програмою

**Рішення**:
1. Знайдіть процес:
```powershell
netstat -ano | findstr :5432
```
2. Зупиніть процес або змініть порт PostgreSQL в настройках

---

##  Порівняння SQLite vs PostgreSQL

| Характеристика | SQLite | PostgreSQL |
|---------------|--------|------------|
| **Складність налаштування** | ✅ Дуже простий | ⚠️ Потрібне встановлення |
| **Продуктивність (мало даних)** | ✅ Висока | ✅ Висока |
| **Продуктивність (багато даних)** | ⚠️ Середня | ✅ Висока |
| **Concurrent доступ** | ❌ Обмежений | ✅ Відмінний |
| **Production-ready** | ⚠️ Для малих проектів | ✅ Так |
| **Backup/Recovery** | ⚠️ Ручний | ✅ Вбудований |
| **Розширені функції** | ❌ Обмежені | ✅ Багато |
| **Розмір файлу БД** | ✅ Один файл | ⚠️ Папка з файлами |

**Рекомендації**:
- **SQLite**: Розробка, тестування, невеликі проекти, портативність
- **PostgreSQL**: Production, багато користувачів, складні запити, масштабування

---

## 🎯 Корисні команди PostgreSQL

### Управління базами даних

```sql
-- Список баз даних
\l

-- Підключитися до бази
\c cinema_db

-- Створити базу
CREATE DATABASE cinema_db;

-- Видалити базу (ОБЕРЕЖНО!)
DROP DATABASE cinema_db;

-- Створити резервну копію
```
```powershell
pg_dump -U postgres cinema_db > backup.sql
```

```sql
-- Відновити з резервної копії
```
```powershell
psql -U postgres cinema_db < backup.sql
```

### Управління таблицями

```sql
-- Список таблиць
\dt

-- Структура таблиці
\d film

-- Видалити всі дані з таблиці (ОБЕРЕЖНО!)
TRUNCATE TABLE booking CASCADE;

-- Видалити таблицю
DROP TABLE IF EXISTS booking;
```

### Запити

```sql
-- Кількість записів
SELECT COUNT(*) FROM film;

-- Пошук
SELECT * FROM film WHERE title LIKE '%Матриця%';

-- З'єднання таблиць
SELECT u.username, COUNT(b.id) as bookings_count
FROM "user" u
LEFT JOIN booking b ON u.id = b.user_id
GROUP BY u.id, u.username;

-- Оновлення
UPDATE "user" SET is_admin = true WHERE username = 'admin';

-- Видалення
DELETE FROM booking WHERE status = 'cancelled';
```

### Моніторинг

```sql
-- Поточні підключення
SELECT * FROM pg_stat_activity WHERE datname = 'cinema_db';

-- Розмір бази даних
SELECT pg_size_pretty(pg_database_size('cinema_db'));

-- Розмір таблиць
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🛠️ Додаткові інструменти

### DBeaver (Universal Database Tool)

Потужний безкоштовний клієнт для роботи з базами даних:
- Завантажте: https://dbeaver.io/download/
- Підтримує PostgreSQL, SQLite, MySQL та багато інших
- Зручний інтерфейс, візуалізація схеми, експорт даних

### pgAdmin Web Interface

Доступ через браузер:
```powershell
# Запустіть pgAdmin
# Відкрийте в браузері: http://localhost:5433
```

---

## 📝 Checklist: Що зробити

- [ ] Встановити PostgreSQL
- [ ] Створити базу даних `cinema_db`
- [ ] Налаштувати `.env` файл з `DATABASE_URL`
- [ ] Встановити `pip install psycopg2-binary`
- [ ] Створити таблиці через `db.create_all()`
- [ ] Перевірити підключення через `view_database.py`
- [ ] Запустити додаток `python app.py`
- [ ] Перевірити роботу в браузері

---

## 🎓 Навчальні ресурси

- [Офіційна документація PostgreSQL](https://www.postgresql.org/docs/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [SQLAlchemy PostgreSQL Guide](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)

---

## ❓ Потрібна допомога?

Якщо виникли проблеми:

1. **Перевірте логи PostgreSQL**:
   - Windows: `C:\Program Files\PostgreSQL\16\data\log\`

2. **Перевірте підключення**:
   ```powershell
   psql -U postgres -d cinema_db
   ```

3. **Перевірте .env файл**:
   - Чи правильний пароль?
   - Чи немає зайвих пробілів?
   - Чи правильна назва бази даних?

4. **Перезапустіть PostgreSQL**:
   ```powershell
   Restart-Service postgresql-x64-16
   ```

---

**Успіхів з PostgreSQL! 🚀**
