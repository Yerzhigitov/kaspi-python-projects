# tour-booking-api — бронирование туров на Django

REST API для сервиса путешествий: каталог туров с фильтрами, бронирование мест, оплата и отмена.
Стек: **Python, Django 4.2, Django REST Framework, PostgreSQL, Docker**.

## Запуск
```bash
docker compose up --build
```
- API: http://localhost:8000/api/tours/
- Админка: http://localhost:8000/admin/ (пользователь: `docker compose exec web python manage.py createsuperuser`)

Без Docker (SQLite):
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install Django==4.2.16 djangorestframework==3.15.2 django-filter==24.3
python manage.py migrate && python manage.py seed_tours && python manage.py runserver
```

## API
| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/auth/token/` | Получить токен (`username`, `password`) |
| `GET` | `/api/tours/?city=&min_price=&max_price=&date_from=&has_seats=true&ordering=price` | Каталог с фильтрами, сортировкой и пагинацией |
| `POST` | `/api/bookings/` | Забронировать: `{"tour_id": 1, "seats": 2}`, заголовок `Idempotency-Key` |
| `GET` | `/api/bookings/` | Мои брони |
| `POST` | `/api/bookings/{id}/pay/` | Оплатить |
| `POST` | `/api/bookings/{id}/cancel/` | Отменить и вернуть места |

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/token/ -d 'username=ali&password=pass12345' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
curl -X POST localhost:8000/api/bookings/ -H "Authorization: Token $TOKEN" \
     -H 'Idempotency-Key: order-1' -d 'tour_id=1&seats=2'
```

## Инженерные решения
- **Нет овербукинга.** Бронь выполняется в `transaction.atomic()` с `select_for_update()` по туру. Два запроса на последнее место выстраиваются в очередь, второй получает `409 Conflict`.
- **Идемпотентность.** Повтор запроса с тем же `Idempotency-Key` возвращает ту же бронь. Ключ уникален в паре с пользователем (`UniqueConstraint`), гонку двух одинаковых запросов ловит `IntegrityError`.
- **Статусы брони.** `pending → paid → cancelled`; переходы проверяются в сервисном слое, повторная оплата или отмена безопасны.
- **Инварианты в БД.** `CheckConstraint` не даёт свободным местам превысить общее число.
- **Без N+1.** Список броней загружается с `select_related("tour")`; тест проверяет, что запросов ровно 2.
- **Доступ.** Каталог открыт всем, брони видит и меняет только владелец (чужая бронь → 404).
- **Слои.** `views` (HTTP) → `services` (бизнес-логика и транзакции) → `models`. Логику можно вызывать из админки, Celery-задач или management-команд.

## Тесты
```bash
python manage.py test
```
9 тестов: фильтры, расчёт цены, овербукинг, тур в прошлом, авторизация, идемпотентность, оплата и отмена, изоляция пользователей, отсутствие N+1.

## Что дальше
Celery-задача для автоотмены неоплаченных броней через 15 минут, кэш каталога в Redis, Swagger через drf-spectacular, GitHub Actions.
