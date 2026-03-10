# Налаштування автоматичної розсилки повідомлень в Windows

## Використання Task Scheduler

### Крок 1: Створення BAT-файлу

Створіть файл `run_notifications.bat` в папці `cinema_app`:

```batch
@echo off
cd /d "d:\Кузь\cinema_app"
"d:\Кузь\.venv\Scripts\python.exe" send_daily_notifications.py >> notifications.log 2>&1
```

### Крок 2: Налаштування Task Scheduler

1. **Запустіть Task Scheduler**:
   - Натисніть `Win + R`
   - Введіть `taskschd.msc`
   - Натисніть Enter

2. **Створіть нове завдання**:
   - В правій панелі натисніть "Create Basic Task..."
   - Або "Action" → "Create Basic Task..."

3. **Налаштуйте завдання**:

   **Крок 1: Name**
   - Name: `Cinema Notifications Daily`
   - Description: `Щоденна розсилка повідомлень про нові сеанси`

   **Крок 2: Trigger**
   - Виберіть: `Daily`
   - Start: `Виберіть будь-яку дату`
   - Start time: `21:00:00` (або інший зручний час)
   - Recur every: `1 days`

   **Крок 3: Action**
   - Виберіть: `Start a program`
   - Program/script: `d:\Кузь\cinema_app\run_notifications.bat`
   - (або повний шлях до bat-файлу)

   **Крок 4: Finish**
   - Поставте галочку: `Open the Properties dialog...`
   - Натисніть `Finish`

4. **Додаткові налаштування** (в Properties):

   **General tab:**
   - ✓ Run whether user is logged on or not
   - ✓ Run with highest privileges
   - Configure for: `Windows 10` (або ваша версія)

   **Conditions tab:**
   - ✓ Start the task only if the computer is on AC power (за бажанням)
   - ✓ Wake the computer to run this task (за бажанням)

   **Settings tab:**
   - ✓ Allow task to be run on demand
   - ✓ Run task as soon as possible after a scheduled start is missed
   - If the task fails, restart every: `1 hour`
   - Attempt to restart up to: `3 times`

5. **Збереження**:
   - Натисніть `OK`
   - Введіть пароль Windows (якщо потрібно)

### Крок 3: Тестування

1. В Task Scheduler знайдіть створене завдання
2. Правою кнопкою → `Run`
3. Перевірте файл `d:\Кузь\cinema_app\notifications.log`
4. Перевірте чи прийшли email

### Альтернатива: Використання PowerShell

Створіть файл `run_notifications.ps1`:

```powershell
Set-Location "d:\Кузь\cinema_app"
& "d:\Кузь\.venv\Scripts\python.exe" send_daily_notifications.py
```

В Task Scheduler:
- Program/script: `powershell.exe`
- Arguments: `-ExecutionPolicy Bypass -File "d:\Кузь\cinema_app\run_notifications.ps1"`

## Перевірка логів

Логи зберігаються в:
- `d:\Кузь\cinema_app\notifications.log` - якщо використовуєте bat-файл
- Task Scheduler History - подивитися результати виконання

## Усунення проблем

### Завдання не запускається автоматично
- Перевірте що комп'ютер увімкнений о 21:00
- Перевірте налаштування "Wake the computer to run this task"
- Подивіться History в Task Scheduler

### Помилки при виконанні
- Перевірте шлях до Python в bat/ps1 файлі
- Перевірте що віртуальне середовище активне
- Запустіть bat-файл вручну для діагностики

### Email не надсилаються
- Перевірте налаштування SMTP в `config.py`
- Подивіться логи в `notifications.log`
- Запустіть скрипт вручну: `python send_daily_notifications.py`

## Зміна часу розсилки

1. Відкрийте Task Scheduler
2. Знайдіть завдання `Cinema Notifications Daily`
3. Правою кнопкою → Properties
4. Triggers tab → Edit
5. Змініть час в "Start time"
6. OK → OK
