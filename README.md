# 🎬 CinemaBook - Система бронювання квитків у кінотеатр

**Сучасний Vue 3 SPA додаток для керування кінотеатром**

![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?logo=flask)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952b3?logo=bootstrap)

---

## 📋 Зміст

- [Огляд](#-огляд)
- [Функціонал](#-функціонал)
- [Технології](#-технології)
- [Швидкий старт](#-швидкий-старт)
- [Структура проекту](#-структура-проекту)
- [API Endpoints](#-api-endpoints)
- [Адміністрування](#-адміністрування)
- [Документація](#-документація)

---

## 🎯 Огляд

**CinemaBook** - це повнофункціональна система бронювання квитків у кінотеатр з:
- ✨ Сучасним Vue 3 SPA інтерфейсом
- 🔥 REST API бекендом на Flask
- 👨‍💼 Адмін-панеллю з календарем
- 📧 Email сповіщеннями
- ⭐ Системою улюблених та відгуків
- 🎨 Красивим градієнтним дизайном

**Повністю мігровано на SPA** - весь код застарілих шаблонів видалено!

---

## ✨ Функціонал

### Для користувачів
- 🎥 **Каталог фільмів** - пошук, фільтри, детальна інформація
- 🪑 **Бронювання місць** - інтерактивний вибір місць
- ⭐ **Улюблені** - збережіть фільми що подобаються
- ⭐ **Відгуки** - оцінюйте та коментуйте фільми
- 👤 **Профіль** - керування бронюваннями
- 📧 **Email сповіщення** - підтвердження та нагадування

### Для адміністраторів
- 📊 **Dashboard** - статистика та аналітика
- 🎬 **Керування фільмами** - CRUD операції
- 📅 **Календар сеансів** - візуальне планування
- 🎫 **Керування сеансами** - створення, редагування, скасування
- 📧 **Email розсилки** - сповіщення про нові сеанси

### UX Features
- 🎨 **Transition анімації** - плавні переходи між сторінками
- 🍞 **Breadcrumbs** - навігаційні "хлібні крихти"
- ⬆️ **Back to Top** - кнопка швидкого повернення
- 📱 **Responsive** - адаптивний дизайн для всіх пристроїв
- 🔍 **404 сторінка** - красива сторінка помилки

---

## 🛠️ Технології

### Frontend
- **Vue 3** - Progressive JavaScript Framework
- **Vue Router 4** - Client-side routing
- **Bootstrap 5** - CSS Framework
- **Font Awesome 6** - Icons
- **Vanilla CSS** - Custom animations

### Backend
- **Python 3.11+** - Мова програмування
- **Flask 3.0+** - Web framework
- **SQLAlchemy** - ORM для роботи з БД
- **Flask-Login** - User session management
- **Flask-Mail** - Email розсилки
- **WTForms** - Forms validation

### База даних
- **SQLite** - Легка реляційна БД
- **7 таблиць** - User, Film, Session, Seat, Booking, Review, Favorite

---

## 🚀 Швидкий старт

### Передумови
- Python 3.11 або вище
- Віртуальне середовище Python
- Git (опціонально)

### Встановлення

1. **Клонуйте репозиторій** (або завантажте ZIP)
```bash
git clone <repository-url>
cd cinema_app
```

2. **Створіть віртуальне середовище**
```bash
python -m venv venv
```

3. **Активуйте віртуальне середовище**

Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

Windows (CMD):
```cmd
venv\Scripts\activate.bat
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Встановіть залежності**
```bash
pip install -r requirements.txt
```

5. **Ініціалізуйте базу даних**
```bash
cd cinema_app
python app.py
```

При першому запуску автоматично створяться:
- База даних `instance/cinema.db`
- Демо-дані (фільми, сеанси)

6. **Створіть адміністратора**
```bash
python create_admin.py
```

Слідуйте інструкціям на екрані.

7. **Запустіть додаток**
```bash
python app.py
```

8. **Відкрийте у браузері**
```
http://localhost:5000
```

---

## 📁 Структура проекту

```
cinema_app/
│
├── 📄 app.py                       # Точка входу Flask
├── 📄 config.py                    # Конфігурація
├── 📄 models.py                    # SQLAlchemy моделі
├── 📄 forms.py                     # WTForms
├── 📄 utils.py                     # Допоміжні функції
├── 📄 extensions.py                # Flask розширення
├── 📄 requirements.txt             # Python залежності
│
├── 📁 routes/                      # Flask маршрути
│   ├── __init__.py
│   ├── main.py                     # Головні маршрути
│   ├── auth.py                     # Авторизація
│   ├── user.py                     # Користувацькі маршрути
│   ├── admin.py                    # Адмін маршрути
│   └── api.py                      # REST API (900+ LOC)
│
├── 📁 templates/                   # Jinja2 шаблони
│   ├── base.html                   # Базовий layout
│   ├── spa.html                    # Vue 3 SPA (2100+ LOC)
│   ├── emails/                     # Email шаблони
│   │   ├── booking_confirmation.html
│   │   ├── booking_cancelled.html
│   │   ├── session_cancelled.html
│   │   └── new_sessions_*.html
│   └── errors/                     # Сторінки помилок
│       └── 403.html, 404.html, 500.html
│
├── 📁 static/                      # Статичні файли
│   ├── js/
│   │   └── spa-app.js              # Vue додaток (1400+ LOC)
│   └── uploads/                    # Зображення фільмів
│
├── 📁 instance/                    # База даних
│   └── cinema.db                   # SQLite БД
│
├── 📁 scripts/                     # Допоміжні скрипти
│   ├── create_admin.py             # Створення адміна
│   └── reset_admin_password.py     # Зміна паролю
│
└── 📁 docs/                        # Документація
    ├── PROJECT_STATUS.md           # Статус проекту
    ├── MIGRATION_CLEANUP_PLAN.md   # План міграції
    ├── ADMIN_GUIDE.md              # Інструкція для адміна
    └── README_*.md                 # Детальні інструкції
```

---

## 🔌 API Endpoints

### Авторизація
- `GET /api/auth/status` - Статус авторизації
- `POST /api/auth/login` - Вхід
- `POST /api/auth/register` - Реєстрація
- `POST /api/auth/logout` - Вихід

### Фільми
- `GET /api/films` - Список фільмів
- `GET /api/films/popular` - Популярні фільми
- `GET /api/films/<id>` - Деталі фільму
- `POST /api/films/<id>/favorite` - Додати в обрані

### Сеанси
- `GET /api/sessions/<id>` - Деталі сеансу
- `GET /api/sessions/<id>/seats` - Місця сеансу
- `POST /api/sessions/<id>/book` - Бронювання

### Користувач
- `GET /api/user/profile` - Профіль
- `GET /api/user/bookings` - Бронювання
- `GET /api/user/favorites` - Обрані фільми
- `POST /api/user/cancel-booking/<id>` - Скасування

### Відгуки
- `POST /api/films/<id>/reviews` - Додати відгук
- `DELETE /api/reviews/<id>` - Видалити відгук

### Адмін (потребує is_admin=True)
- `GET /api/admin/stats` - Статистика
- `GET/POST /api/admin/films` - CRUD фільмів
- `PUT/DELETE /api/admin/films/<id>` - Редагування/Видалення
- `GET/POST /api/admin/sessions` - CRUD сеансів
- `POST /api/admin/sessions/<id>/cancel` - Скасування сеансу
- `GET /api/admin/calendar` - Календарні дані
- `POST /api/admin/calendar/create-session` - Швидке створення

---

## 🔐 Адміністрування

### Створення адміністратора

**Спосіб 1: Інтерактивний скрипт**
```bash
python create_admin.py
```

**Спосіб 2: Зміна паролю існуючого**
```bash
python reset_admin_password.py
```

### Доступ до адмін-панелі

1. Увійдіть з адмін-акаунтом
2. Натисніть кнопку "Адмін" (⚙️) у навігації
3. Або перейдіть на `/app/admin`

### Можливості адміна

**Dashboard:**
- Загальна кількість фільмів, сеансів, користувачів
- Статистика бронювань
- Топ-5 популярних фільмів

**Керування фільмами:**
- Додавання нових фільмів
- Редагування деталей
- Завантаження зображень
- Видалення фільмів

**Керування сеансами:**
- Створення сеансів
- Календарний вигляд
- Швидке створення через календар
- Скасування сеансів з розсилкою email

**Email сповіщення:**
- Автоматичні підтвердження бронювань
- Сповіщення про скасування
- Розсилка про нові сеанси

---

## 📚 Документація

### Основні документи

- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Детальний статус проекту
- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - Повна інструкція для адміна
- **[MIGRATION_CLEANUP_PLAN.md](MIGRATION_CLEANUP_PLAN.md)** - Історія міграції

### Специфічні інструкції

- **README_EMAIL.md** - Налаштування email
- **README_POSTGRESQL.md** - Міграція на PostgreSQL
- **README_CALENDAR.md** - Календарний функціонал
- **README_REVIEWS.md** - Система відгуків
- **README_FAVORITES_NOTIFICATIONS.md** - Обрані та сповіщення
- **README_SESSION_CANCELLATION.md** - Скасування сеансів
- **README_VUE_MIGRATION.md** - Історія міграції на Vue

### Архітектура

**Frontend:**
- [templates/spa.html](templates/spa.html) - Всі Vue компоненти
- [static/js/spa-app.js](static/js/spa-app.js) - Vue додаток

**Backend:**
- [routes/api.py](routes/api.py) - REST API
- [models.py](models.py) - Моделі бази даних

---

## 🎨 Особливості дизайну

### Градієнтна схема
```css
Purple → Pink → Orange
linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #ffa726 100%)
```

### Анімації
- **Slide-fade** - переходи між сторінками
- **Backdrop blur** - розмиття фону модальних вікон
- **Hover effects** - інтерактивні картки
- **Smooth scroll** - плавна прокрутка

### Responsive breakpoints
- **Mobile:** < 768px
- **Tablet:** 768px - 992px
- **Desktop:** > 992px

---

## 🧪 Тестування

### Перевірка функціонала

**Публічні сторінки:**
- [ ] Головна сторінка завантажується
- [ ] Каталог фільмів відображається
- [ ] Пошук працює
- [ ] Детальна сторінка фільму показує інформацію

**Авторизація:**
- [ ] Реєстрація нового користувача
- [ ] Вхід з правильними даними
- [ ] Захист від неавторизованого доступу

**Бронювання:**
- [ ] Вибір місць працює
- [ ] Бронювання створюється
- [ ] Email приходить
- [ ] Скасування працює

**Адмін-панель:**
- [ ] Доступ тільки для адміна
- [ ] Створення фільму працює
- [ ] Створення сеансу працює
- [ ] Календар відображається
- [ ] Статистика правильна

---

## 📧 Email налаштування

### Gmail SMTP

Відредагуйте `config.py`:

```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'  # Не звичайний пароль!
MAIL_DEFAULT_SENDER = 'your-email@gmail.com'
```

**Отримання App Password:**
1. Увійдіть в Google Account
2. Security → 2-Step Verification
3. App Passwords → Generate

Детальніше: [README_EMAIL.md](README_EMAIL.md)

---

## 🔒 Безпека

### Реалізовано
- ✅ Хешування паролів (Werkzeug)
- ✅ CSRF захист (WTForms)
- ✅ Авторизаційні guard'и
- ✅ Admin-only endpoints
- ✅ Перевірка власності ресурсів

### Рекомендації для production
- [ ] Використовуйте HTTPS
- [ ] Змініть SECRET_KEY
- [ ] Налаштуйте rate limiting
- [ ] Додайте CORS політику
- [ ] Використовуйте PostgreSQL
- [ ] Налаштуйте logging

---

## 🚀 Deployment

### Підготовка до production

1. **Змініть SECRET_KEY**
```python
# config.py
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secure-random-key'
```

2. **Налаштуйте PostgreSQL** (замість SQLite)

Див. [README_POSTGRESQL.md](README_POSTGRESQL.md)

3. **Налаштуйте environment variables**
```bash
export FLASK_ENV=production
export DATABASE_URL=postgresql://...
export MAIL_USERNAME=...
export MAIL_PASSWORD=...
```

4. **Використовуйте production server**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Рекомендовані платформи
- **Heroku** - Простий deployment
- **PythonAnywhere** - Безкоштовний tier
- **Railway** - Сучасний підхід
- **DigitalOcean** - VPS з повним контролем

---

## 🤝 Внесок у проект

**Проект відкритий для покращень!**

### Список ідей
- [ ] Toast notifications замість alert()
- [ ] Skeleton loaders при завантаженні
- [ ] Search debounce оптимізація
- [ ] Infinite scroll або pagination
- [ ] Dark/Light theme toggle
- [ ] PWA features
- [ ] Image optimization
- [ ] Caching стратегія

### Як додати функцію

1. Fork проекту
2. Створіть feature branch
3. Зробіть зміни
4. Створіть Pull Request

---

## 📝 Ліцензія

MIT License - вільне використання для будь-яких цілей.

---

## 👨‍💻 Автор

Створено як навчальний проект для демонстрації:
- Міграції з традиційного MVC на SPA
- Separation of Concerns (Frontend ↔ Backend)
- REST API best practices
- Modern Vue 3 development
- Flask backend architecture

---

## 📞 Підтримка

**Проблеми або питання?**

1. Перевірте [PROJECT_STATUS.md](PROJECT_STATUS.md)
2. Прочитайте [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
3. Перегляньте документацію у `/docs`

---

## 🎉 Подяки

**Технології:**
- Vue.js Team
- Flask Community
- Bootstrap Team
- Font Awesome

**Інструменти:**
- VS Code
- Python
- SQLite

---

**Приємного використання CinemaBook! 🍿🎬**

