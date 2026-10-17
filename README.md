# Python Backend Portfolio

Набор проектов на Python, посвящённых задачам финтех-бэкенда: деньги, нагрузка, наблюдаемость, кэширование.

| Проект | О чём | Ключевые темы |
|---|---|---|
| [wallet-api](wallet-api/) | REST-сервис кошельков и переводов | FastAPI, PostgreSQL, `SELECT ... FOR UPDATE`, идемпотентность, Docker |
| [wallet](wallet/) | In-memory ядро кошелька | `Decimal`, блокировки, идемпотентные операции, журнал транзакций |
| [ratelimit](ratelimit/) | Rate limiter'ы | Token Bucket, Sliding Window, декораторы |
| [logstats](logstats/) | CLI-анализатор access-логов | p50/p95/p99, error rate, нормализация путей, `argparse` |
| [ttlcache](ttlcache/) | LRU-кэш с TTL | O(1) операции, `asyncio`, защита от cache stampede |

Проекты `wallet`, `ratelimit`, `logstats`, `ttlcache` написаны только на стандартной библиотеке (Python 3.9+).

```bash
for d in wallet ratelimit logstats ttlcache; do (cd $d && python3 -m unittest -v); done
```
