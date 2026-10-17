"""Кошелёк с переводами: Decimal, идемпотентность, потокобезопасность, журнал операций."""
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional


class WalletError(Exception):
    pass


class InsufficientFunds(WalletError):
    pass


def money(value) -> Decimal:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise WalletError("Сумма должна быть положительной")
    return amount


@dataclass
class Transaction:
    id: str
    src: Optional[str]
    dst: str
    amount: Decimal
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Bank:
    def __init__(self) -> None:
        self._balances: Dict[str, Decimal] = {}
        self._ledger: List[Transaction] = []
        self._idempotency: Dict[str, Transaction] = {}
        self._lock = threading.Lock()

    def open_account(self) -> str:
        acc = uuid.uuid4().hex[:12]
        with self._lock:
            self._balances[acc] = Decimal("0.00")
        return acc

    def balance(self, acc: str) -> Decimal:
        with self._lock:
            return self._get(acc)

    def deposit(self, acc: str, amount, key: Optional[str] = None) -> Transaction:
        return self._apply(None, acc, money(amount), key)

    def transfer(self, src: str, dst: str, amount, key: Optional[str] = None) -> Transaction:
        if src == dst:
            raise WalletError("Нельзя перевести самому себе")
        return self._apply(src, dst, money(amount), key)

    def history(self, acc: str) -> List[Transaction]:
        with self._lock:
            return [t for t in self._ledger if acc in (t.src, t.dst)]

    def _get(self, acc: str) -> Decimal:
        if acc not in self._balances:
            raise WalletError(f"Счёт {acc} не найден")
        return self._balances[acc]

    def _apply(self, src, dst, amount, key) -> Transaction:
        with self._lock:
            if key and key in self._idempotency:
                return self._idempotency[key]  # повторный запрос — тот же результат
            self._get(dst)
            if src is not None:
                if self._get(src) < amount:
                    raise InsufficientFunds(f"Недостаточно средств на {src}")
                self._balances[src] -= amount
            self._balances[dst] += amount
            tx = Transaction(uuid.uuid4().hex, src, dst, amount)
            self._ledger.append(tx)
            if key:
                self._idempotency[key] = tx
            return tx
