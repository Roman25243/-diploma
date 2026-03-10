@echo off
cd /d "d:\Кузь\cinema_app"
"d:\Кузь\.venv\Scripts\python.exe" send_daily_notifications.py >> notifications.log 2>&1
