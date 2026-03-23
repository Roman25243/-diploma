# 🚀 Швидкий старт з Vue версією

## Як протестувати зараз

### 1️⃣ Запустіть додаток

```powershell
cd d:\Кузь\cinema_app
python app.py
```

### 2️⃣ Порівняйте старе і нове

**Стара версія (Flask):**
```
http://localhost:5000/seats/1
```
- Форма з кнопкою Submit  
- Перезавантаження сторінки після бронювання
- Традиційний підхід

**Нова версія (Vue):**
```
http://localhost:5000/seats-vue/1
```
- Інтерактивний вибір
- Без перезавантаження
- Плавні анімації
- API запити

### 3️⃣ Відкрийте Developer Tools (F12)

**Console вкладка:**
```javascript
// Побачите:
Vue app mounted!
Session ID: 1
```

**Network вкладка:**
```
GET /api/sessions/1/seats  →  200 OK
{
  "session": {...},
  "seats": [...],
  "user_bookings": {...}
}

POST /api/sessions/1/book  →  200 OK
{
  "success": true,
  "message": "Місця успішно заброньовано!",
  ...
}
```

### 4️⃣ Експериментуйте

**Змініть колір вибраних місць:**

Відкрийте `static/js/seats-app.js` і додайте в methods:

```javascript
getSeatClass(seat) {
    if (seat.status === 'booked') return 'booked';
    if (this.isSeatSelected(seat)) return 'selected';
    return 'free';
},

// 👇 Додайте новий метод
getSeatStyle(seat) {
    if (this.isSeatSelected(seat)) {
        return {
            background: 'linear-gradient(135deg, #ff6b6b, #ff8e53)',
            transform: 'scale(1.2)'
        };
    }
    return {};
}
```

Потім у `templates/seats_vue.html` додайте `:style`:

```html
<button
    :class="['seat', getSeatClass(seat)]"
    :style="getSeatStyle(seat)"
    @click="toggleSeat(seat)"
>
```

---

## 🎯 Що далі?

### Варіант 1: Продовжити з Vue (рекомендую)

**Наступний компонент - Пошук фільмів:**

```
Створи Vue компонент для пошуку фільмів з реактивним фільтруванням
```

**Що це дасть:**
- Навчитеся `watch` та `computed`
- Попрацюєте з API запитами
- Зробите корисну фічу

### Варіант 2: Переробити щось інше

Команди для AI:
```
1) Створи Vue компонент для відгуків
2) Зроби toggle кнопку для улюблених на Vue
3) Додай Vue компонент календаря для адміна
```

### Варіант 3: Почати повний SPA

Якщо вже впевнені й хочете все переписати:

```powershell
# Встановити Node.js (якщо немає)
winget install OpenJS.NodeJS

# Створити Vue проект
cd d:\Кузь
npm create vue@latest cinema-app-frontend

# Вибрати опції:
✅ Vue Router
✅ Pinia
✅ ESLint
```

Тоді команда: "Створи повну структуру Vue SPA проекту"

---

## 🐛 Якщо щось не працює

### Помилка: "Vue is not defined"

**Причина:** CDN не завантажився

**Рішення:**
```html
<!-- У templates/seats_vue.html замініть CDN на локальний файл -->
<script src="https://cdn.jsdelivr.net/npm/vue@3"></script>
```

або завантажте Vue локально:

```powershell
# Створити папку для vendor файлів
mkdir static/vendor

# Завантажити Vue (або скопіювати з CDN вручну)
# Покласти у static/vendor/vue.global.js
```

### Помилка: API повертає 401 Unauthorized

**Причина:** Не авторизовані

**Рішення:**
1. Спочатку залогіньтесь через `/login`
2. Потім йдіть на `/seats-vue/1`

### DevTools не показує Vue компонент

**Встановіть розширення:**
- Chrome: [Vue.js devtools](https://chrome.google.com/webstore/detail/vuejs-devtools)
- Firefox: [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)

---

## 💡 Корисні зміни для експериментів

### 1. Додати звук при виборі місця

```javascript
// В seats-app.js, метод toggleSeat
toggleSeat(seat) {
    if (seat.status === 'booked') return;
    
    // 👇 Додати звук
    const audio = new Audio('https://www.soundjay.com/button/sounds/button-09.mp3');
    audio.volume = 0.3;
    audio.play();
    
    // ... решта коду
}
```

### 2. Анімація при завантаженні

Замініть у `seats_vue.html`:

```html
<div v-if="loading" class="loading-spinner">
    <div class="spinner-border text-primary">
        <span class="visually-hidden">Завантаження...</span>
    </div>
    <p class="mt-3">Завантажуємо місця...</p>
</div>
```

### 3. Показати скільки людей вибрало це місце (fake analytics)

```javascript
// seats-app.js
data() {
    return {
        // ...
        seatPopularity: {} // Місце ID → кількість переглядів
    }
},

mounted() {
    // Генеруємо випадкові дані
    this.seats.forEach(seat => {
        this.seatPopularity[seat.id] = Math.floor(Math.random() * 10);
    });
}
```

```html
<!-- seats_vue.html, в tooltip -->
<button 
    :title="`Місце ${seat.number} • ${seatPopularity[seat.id]} переглядів`"
    ...
>
```

---

## 📊 Метрики успіху

Після тестування порівняйте:

| Метрика | Flask версія | Vue версія |
|---------|--------------|------------|
| Клік → Результат | ~500ms (reload) | ~100ms (API) |
| UX | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Інтерактивність | Низька | Висока |
| Складність коду | 🟢 Простий | 🟡 Середній |

---

**Готові почати? Запустіть додаток і відкрийте `/seats-vue/1`** 🚀
