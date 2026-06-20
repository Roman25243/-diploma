Cloudflare Pages — деплой фронтенду (CinemaBook)

Кроки для розгортання статичного SPA з монорепозиторію:

1) Підготовка (виконано в репозиторії)
- Папка `cinema_app/frontend_dist/` містить готові файли: `index.html`, `_routes.json`, `static/js/spa-app.min.js` та інші статичні ресурси.
- `index.html` вже містить рядок, який встановлює `window.__CINEMABOOK_API_BASE_URL__` на URL бекенду Heroku. За потреби змініть його на інший URL.

2) Створення проекту на Cloudflare Pages
- Увійдіть в Cloudflare Dashboard (https://dash.cloudflare.com/) → Pages → Create a project.
- Підключіть GitHub репозиторій (https://github.com/<your_user>/<repo>). Виберіть гілку `main` (або ту гілку, куди ви запушили `cinema_app/frontend_dist`).
- Build settings:
  - Framework: (none / static)
  - Build command: (залишити порожнім)
  - Build output directory: `cinema_app/frontend_dist`
- Deploy.

3) Редіректи / SPA fallback
- Cloudflare Pages підтримує файл `_routes.json` у вихідній директорії. Ми вже додали `cinema_app/frontend_dist/_routes.json` з правилом:
  - `/app(.*)` → `/index.html`
  - `/` → `/index.html`
- Якщо хочете кастомний шлях, можна додати правило в Pages UI: Rewrite `/app/*` → `/index.html`.

4) Налаштування API URL і змінних середовища
- В `index.html` ми вставили `window.__CINEMABOOK_API_BASE_URL__` зі значенням Heroku. Якщо бажаєте, можна встановити Pages environment variable `CINEMABOOK_API_BASE_URL` і замінити в `index.html` під час build (для статичного сайту зазвичай вбудовано прямо в `index.html`).

5) CORS та cookie (важливо)
- Після деплоя отримайте Pages URL, наприклад: `https://<project>.pages.dev`.
- Додайте цей URL у `CORS_ORIGINS` на Heroku (кома-розділений список). Наприклад:
  - `heroku config:set CORS_ORIGINS="https://<project>.pages.dev" --app cinema-book-backend`
- Переконайтесь, що на Heroku встановлено:
  - `SESSION_COOKIE_SAMESITE=None`
  - `SESSION_COOKIE_SECURE=True`
  (ми вже ставили ці змінні під час деплою бекенду).

6) Перевірка
- Відкрийте `https://<project>.pages.dev/app/` і перевірте, що SPA завантажується.
- У DevTools -> Network переконайтесь, що запити до `/api/...` відправляються на Heroku і що у запитах відправляються cookie (Request headers -> Cookie). Також переконайтесь, що `Access-Control-Allow-Origin` в відповіді містить ваш Pages домен.

7) Якщо щось не працює
- Надішліть мені Pages URL, і я:
  - додам його в `CORS_ORIGINS` на Heroku за вас; або
  - перевірю запити та дам точні підказки, які заголовки відповідають, та що треба змінити.

Чеклист для вас (що потрібно надати):
- URL проекту Pages (наприклад `https://<project>.pages.dev`) — щоб я зміг додати до `CORS_ORIGINS` і перевірити cookie.
- Підтвердження, чи хочете ви зберегти `window.__CINEMABOOK_API_BASE_URL__` в `index.html` або використовувати змінну середовища Pages.

Опціонально (я можу зробити):
- Автоматично додати Pages URL в Heroku `CORS_ORIGINS` (як тільки ви дасте мені URL).
- Налаштувати `index.html`, щоб підставляв `window.__CINEMABOOK_API_BASE_URL__` з `CINEMABOOK_API_BASE_URL` Pages (потрібна робота зі збіркою) — скажіть, якщо хочете це.

Безпечні рекомендації:
- Не додавайте `CORS_ORIGINS='*'` якщо ви використовуєте cookie-based auth.
- Для production використовуйте HTTPS (Pages вже HTTPS) і переконайтесь, що `SESSION_COOKIE_SECURE=True`.

---
Файли, які я додав/змінив:
- `cinema_app/frontend_dist/index.html`
- `cinema_app/frontend_dist/_routes.json`
- `cinema_app/frontend_dist/static/js/spa-app.min.js` (копія minified app)

Готовий продовжувати після того, як ви надасте Pages URL або скажете, щоб я сам встановив Pages URL в Heroku (як тільки ви надасте URL).