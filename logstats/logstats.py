"""CLI-анализатор access-логов: RPS, доля ошибок, p50/p95/p99 latency, топ медленных эндпоинтов.

Формат строки: 2026-10-17T10:00:00 GET /api/pay 200 123ms
Запуск: python3 logstats.py access.log [--top 5]
"""
import argparse
import math
import re
import sys
from collections import Counter, defaultdict
from statistics import mean

LINE = re.compile(r"^(?P<ts>\S+) (?P<method>[A-Z]+) (?P<path>\S+) (?P<status>\d{3}) (?P<ms>\d+)ms$")


def percentile(sorted_vals, p):
    if not sorted_vals:
        return 0
    k = max(0, math.ceil(p / 100 * len(sorted_vals)) - 1)  # nearest-rank
    return sorted_vals[k]


def analyze(lines, top=5):
    latencies, by_path, statuses, bad = [], defaultdict(list), Counter(), 0
    for line in lines:
        m = LINE.match(line.strip())
        if not m:
            bad += 1
            continue
        ms = int(m["ms"])
        path = re.sub(r"/\d+", "/{id}", m["path"])  # нормализуем /users/42 -> /users/{id}
        latencies.append(ms)
        by_path[f'{m["method"]} {path}'].append(ms)
        statuses[m["status"][0] + "xx"] += 1
    latencies.sort()
    total = len(latencies)
    return {
        "total": total,
        "malformed": bad,
        "error_rate": round(statuses["5xx"] / total * 100, 2) if total else 0.0,
        "statuses": dict(statuses),
        "p50": percentile(latencies, 50),
        "p95": percentile(latencies, 95),
        "p99": percentile(latencies, 99),
        "slowest": sorted(((p, round(mean(v), 1), len(v)) for p, v in by_path.items()),
                          key=lambda x: -x[1])[:top],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("logfile")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    with open(args.logfile, encoding="utf-8") as f:
        r = analyze(f, args.top)
    print(f"Запросов: {r['total']} (битых строк: {r['malformed']})")
    print(f"Статусы: {r['statuses']}  |  5xx: {r['error_rate']}%")
    print(f"Latency p50={r['p50']}ms p95={r['p95']}ms p99={r['p99']}ms")
    print("Самые медленные эндпоинты:")
    for path, avg, n in r["slowest"]:
        print(f"  {path:<30} avg={avg}ms  n={n}")


if __name__ == "__main__":
    sys.exit(main())
