"""
Тестування оптимізацій бази даних
Перевіряє кількість SQL запитів для кожного endpoint
"""
import sys
from datetime import datetime
from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
from extensions import db

# Счетчик запитів
class QueryCounter:
    def __init__(self):
        self.queries = []
        self.count = 0
    
    def reset(self):
        self.queries = []
        self.count = 0
    
    def add_query(self, statement):
        self.queries.append({
            'sql': statement,
            'timestamp': datetime.now()
        })
        self.count += 1
    
    def print_report(self):
        print(f"\n{'='*80}")
        print(f"📊 SQL Query Report - Total: {self.count} queries")
        print(f"{'='*80}")
        
        select_count = 0
        for i, q in enumerate(self.queries, 1):
            if 'SELECT' in q['sql']:
                select_count += 1
                # Скоротити довгій запит для виводу
                sql = q['sql'].replace('\n', ' ')
                if len(sql) > 100:
                    sql = sql[:97] + '...'
                print(f"{i}. {sql}")
        
        print(f"\n📈 SELECT queries: {select_count}/{self.count}")
        print(f"{'='*80}\n")
        
        return select_count


def setup_query_logging(query_counter):
    """Налаштувати записування всіх SQL запитів"""
    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        query_counter.add_query(statement)


def test_film_list(app, client):
    """Тест: GET /api/films"""
    print("\n🧪 TEST 1: GET /api/films (список фільмів)")
    
    counter = QueryCounter()
    setup_query_logging(counter)
    
    response = client.get('/api/films')
    
    counter.print_report()
    
    # Перевірка: має бути максимум 3 запити (films, reviews, favorites, genres)
    if counter.count <= 4:
        print("✅ PASS: Кількість запитів оптимальна (≤4)")
    else:
        print(f"❌ FAIL: Занадто багато запитів ({counter.count}). Очікується ≤4")
    
    return counter.count <= 4


def test_film_detail(app, client):
    """Тест: GET /api/films/<id>"""
    print("\n🧪 TEST 2: GET /api/films/1 (деталі фільму)")
    
    counter = QueryCounter()
    setup_query_logging(counter)
    
    response = client.get('/api/films/1')
    
    counter.print_report()
    
    # Перевірка: має бути максимум 5 запитів (film, reviews, sessions, favorites, similar films)
    if counter.count <= 6:
        print("✅ PASS: Кількість запитів оптимальна (≤6)")
    else:
        print(f"❌ FAIL: Занадто багато запитів ({counter.count}). Очікується ≤6")
    
    return counter.count <= 6


def test_user_profile(app, client, user_id=1):
    """Тест: GET /api/user/profile"""
    print("\n🧪 TEST 3: GET /api/user/profile (профіль користувача)")
    
    counter = QueryCounter()
    setup_query_logging(counter)
    
    response = client.get('/api/user/profile')
    
    counter.print_report()
    
    # Перевірка: має бути максимум 2 запити (user bookings з eager loading)
    if counter.count <= 2:
        print("✅ PASS: Кількість запитів оптимальна (≤2)")
    else:
        print(f"❌ FAIL: Занадто багато запитів ({counter.count}). Очікується ≤2")
        print("   🔍 Причина: N+1 запити при завантаженні бронювань")
    
    return counter.count <= 2


def test_popular_films(app, client):
    """Тест: GET /api/films/popular"""
    print("\n🧪 TEST 4: GET /api/films/popular (популярні фільми)")
    
    counter = QueryCounter()
    setup_query_logging(counter)
    
    response = client.get('/api/films/popular')
    
    counter.print_report()
    
    # Перевірка: має бути максимум 3 запити
    if counter.count <= 3:
        print("✅ PASS: Кількість запитів оптимальна (≤3)")
    else:
        print(f"❌ FAIL: Занадто багато запитів ({counter.count}). Очікується ≤3")
    
    return counter.count <= 3


def test_favorites(app, client):
    """Тест: GET /api/favorites"""
    print("\n🧪 TEST 5: GET /api/favorites (улюблені фільми)")
    
    counter = QueryCounter()
    setup_query_logging(counter)
    
    response = client.get('/api/favorites')
    
    counter.print_report()
    
    # Перевірка: має бути максимум 2 запити
    if counter.count <= 2:
        print("✅ PASS: Кількість запитів оптимальна (≤2)")
    else:
        print(f"❌ FAIL: Занадто багато запитів ({counter.count}). Очікується ≤2")
    
    return counter.count <= 2


def test_admin_stats(app, client):
    """Тест: GET /api/admin/stats"""
    print("\n🧪 TEST 6: GET /api/admin/stats (статистика адміна)")
    
    counter = QueryCounter()
    setup_query_logging(counter)
    
    response = client.get('/api/admin/stats')
    
    counter.print_report()
    
    # Перевірка: має бути максимум 8 запитів (complex aggregation queries)
    if counter.count <= 8:
        print("✅ PASS: Кількість запитів оптимальна (≤8)")
    else:
        print(f"❌ FAIL: Занадто багато запитів ({counter.count}). Очікується ≤8")
    
    return counter.count <= 8


def run_all_tests(app, client):
    """Запустити всі тести оптимізації"""
    print("\n" + "="*80)
    print("🔍 DATABASE OPTIMIZATION TEST SUITE")
    print("="*80)
    
    results = {
        'GET /api/films': test_film_list(app, client),
        'GET /api/films/<id>': test_film_detail(app, client),
        'GET /api/user/profile': test_user_profile(app, client),
        'GET /api/films/popular': test_popular_films(app, client),
        'GET /api/favorites': test_favorites(app, client),
        'GET /api/admin/stats': test_admin_stats(app, client),
    }
    
    # Підсумок
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*80}")
    print(f"Overall: {passed}/{total} tests passed ({100*passed//total}%)")
    print("="*80)
    
    return passed == total


if __name__ == '__main__':
    # Для запуску: python test_db_optimization.py
    print("⚠️  Запустіть цей скрипт з контексту Flask додатку")
    print("Приналежне використання:")
    print("  from test_db_optimization import run_all_tests")
    print("  run_all_tests(app, client)")
