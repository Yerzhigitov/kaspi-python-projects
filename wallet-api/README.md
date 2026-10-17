# wallet-api — сервис кошельков и переводов

REST API на **FastAPI + PostgreSQL**: счета, пополнения, переводы между счетами, история операций.
Основной упор — корректность денежных операций при конкурентных запросах.

## Запуск
```bash
docker compose up --build
```
Swagger UI: http://localhost:8000/docs

```bash
curl -X POST localhost:8000/accounts -H 'Content-Type: application/json' -d '{"owner":"Ali"}'
curl -X POST localhost:8000/accounts/1/deposit -H 'Content-Type: application/json' -d '{"amount":"1000"}'
curl -X POST localhost:8000/accounts -H 'Content-Type: application/json' -d '{"owner":"Dana"}'
curl -X POST localhost:8000/transfers -H 'Idempotency-Key: order-42' \
     -H 'Content-Type: application/json' -d '{"from_id":1,"to_id":2,"amount":"250.50"}'
```

## API
| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/accounts` | Открыть счёт |
| `GET` | `/accounts/{id}` | Баланс |
| `POST` | `/accounts/{id}/deposit` | Пополнение |
| `POST` | `/transfers` | Перевод (заголовок `Idempotency-Key`) |
| `GET` | `/accounts/{id}/transactions?limit=&offset=` | История с пагинацией |
| `GET` | `/health` | Проверка доступности БД |

## Инженерные решения
- **Пессимистичные блокировки.** `SELECT ... FOR UPDATE` блокирует оба счёта до конца транзакции: два параллельных списания не уведут баланс в минус.
- **Защита от deadlock.** Счета блокируются всегда в порядке возрастания `id`, поэтому встречные переводы A→B и B→A не блокируют друг друга навечно.
- **Идемпотентность.** Повтор запроса с тем же `Idempotency-Key` (например, клиент не дождался ответа) возвращает уже созданную транзакцию. Гонка двух одинаковых запросов решается уникальным индексом в БД.
- **Деньги — `NUMERIC(18,2)` и `Decimal`.** Никаких `float`. Pydantic отклоняет суммы ≤ 0 и с тремя знаками после запятой.
- **Инвариант в БД.** `CHECK (balance >= 0)` — последняя линия защиты, даже если в коде появится баг.
- **Слои.** `main.py` (HTTP) → `service.py` (бизнес-логика) → `models.py` (ORM). Сервис не знает про HTTP и тестируется отдельно.

## Тесты
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
```

## Что можно добавить
Alembic-миграции, мультивалютность с курсами, outbox-паттерн и Kafka для событий о переводах, rate limiting через Redis, метрики Prometheus.
