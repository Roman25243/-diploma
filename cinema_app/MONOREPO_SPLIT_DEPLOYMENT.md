# 🚀 Monorepo Split Deploy: Cloudflare Pages + Heroku

Цей гайд для схеми, де:

- **frontend** розміщується на **Cloudflare Pages**
- **backend API** розміщується на **Heroku**

У вашому проєкті SPA вже використовує базу маршруту `/app`, тому ця схема підходить без перепроєктування роутів.

---

## Що важливо знати

- Фронт і бек працюють з різних доменів, тому потрібні **CORS** та **cookies with credentials**.
- Бекенд повинен приймати cookie-сесію через `SESSION_COOKIE_SAMESITE=None` і `SESSION_COOKIE_SECURE=True`.
- Frontend має знати URL бекенду через `window.__CINEMABOOK_API_BASE_URL__`.

---

## 1. Backend on Heroku

### Heroku config vars

Встановіть такі змінні:

```powershell
heroku config:set DATABASE_URL="postgresql://..."
heroku config:set SECRET_KEY="your-random-secret-key"
heroku config:set DEBUG=False
heroku config:set SESSION_COOKIE_SAMESITE=None
heroku config:set SESSION_COOKIE_SECURE=True
heroku config:set CORS_ORIGINS=https://your-project.pages.dev
heroku config:set PAYMENT_APP_BASE_URL=https://your-project.pages.dev
heroku config:set PAYMENT_SUCCESS_URL=https://your-project.pages.dev/app/profile?payment=success
heroku config:set PAYMENT_CANCEL_URL=https://your-project.pages.dev/app/profile?payment=cancel
```

Якщо у вас custom domain на Cloudflare Pages, додайте і його теж у `CORS_ORIGINS` через кому.

### Запуск

```powershell
git push heroku main
heroku run flask db upgrade
```

---

## 2. Frontend on Cloudflare Pages

### Рекомендована структура в монорепі

```text
cinema_app/
  frontend/
  backend/
```

У вашому поточному коді вже є frontend-slice у:

- [static/js/spa-app.js](static/js/spa-app.js)
- [templates/spa.html](templates/spa.html)

### Що потрібно для Cloudflare Pages

Cloudflare Pages має віддати статичний `index.html`, який містить:

- шаблони Vue
- підключення Vue/Vue Router через CDN
- підключення [static/js/spa-app.js](static/js/spa-app.js)
- `window.__CINEMABOOK_API_BASE_URL__ = 'https://your-heroku-app.herokuapp.com'`

### Роутинг

Ваш SPA вже працює під `/app`:

- `/app/` - головна
- `/app/films`
- `/app/film/:id`
- `/app/profile`
- `/app/favorites`
- `/app/seats/:sessionId`

На Cloudflare Pages це означає, що треба налаштувати SPA fallback на `index.html` для всіх шляхів під `/app/*`.

### Pages variables

Якщо збираєте frontend через build step, передайте:

```text
CINEMABOOK_API_BASE_URL=https://your-heroku-app.herokuapp.com
```

Якщо без build step, просто додайте цей рядок у статичний config script на сторінці.

---

## 3. Що уже зроблено в коді

- API-виклики у SPA переведені на `apiFetch(...)`
- `apiFetch(...)` додає `credentials: 'include'`
- backend підтримує CORS на `/api/*`
- backend читає `CORS_ORIGINS` та cookie settings з env

---

## 4. Практичний workflow

1. Розгорніть бекенд на Heroku.
2. Перевірте, що `CORS_ORIGINS` містить домен Cloudflare Pages.
3. Розгорніть frontend на Cloudflare Pages.
4. Вкажіть API base URL бекенду в frontend config.
5. Перевірте логін, профіль, бронювання і оплату.

---

## 5. Перевірка

### Backend

```powershell
curl https://your-heroku-app.herokuapp.com/api/auth/status
```

### Frontend

Відкрийте:

```text
https://your-project.pages.dev/app/
```

І перевірте:

- авторизацію
- список фільмів
- профіль
- бронювання місць

---

## 6. Якщо хочете, я можу наступним повідомленням зробити ще один крок

Я можу підготувати окремий `frontend/` export для Cloudflare Pages, щоб у вас був реально готовий static site для монорепо, а не тільки інструкція.