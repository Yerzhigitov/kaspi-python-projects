# Python Backend Portfolio

Витрина проектов: у каждого свой репозиторий, здесь копии для удобного просмотра. Набор проектов на Python, посвящённых задачам финтех-бэкенда: деньги, нагрузка, наблюдаемость, кэширование.

| Проект | О чём | Ключевые темы |
|---|---|---|
| [tour-booking-api](https://github.com/Yerzhigitov/tour-booking-api) | Бронирование туров | Django, DRF, PostgreSQL, `select_for_update`, идемпотентность, Docker |
| [wallet-api](https://github.com/Yerzhigitov/wallet-api) | REST-сервис кошельков и переводов | FastAPI, PostgreSQL, `SELECT ... FOR UPDATE`, идемпотентность, Docker |
| [wallet-core](https://github.com/Yerzhigitov/wallet-core) | In-memory ядро кошелька | `Decimal`, блокировки, идемпотентные операции, журнал транзакций |
| [rate-limiter](https://github.com/Yerzhigitov/rate-limiter) | Rate limiter'ы | Token Bucket, Sliding Window, декораторы |
| [log-analyzer](https://github.com/Yerzhigitov/log-analyzer) | CLI-анализатор access-логов | p50/p95/p99, error rate, нормализация путей, `argparse` |
| [ttl-cache](https://github.com/Yerzhigitov/ttl-cache) | LRU-кэш с TTL | O(1) операции, `asyncio`, защита от cache stampede |

Проекты `wallet`, `ratelimit`, `logstats`, `ttlcache` написаны только на стандартной библиотеке (Python 3.9+).

```bash
for d in wallet ratelimit logstats ttlcache; do (cd $d && python3 -m unittest -v); done
```
