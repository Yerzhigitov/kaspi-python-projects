"""Бизнес-логика переводов. Вся работа с деньгами идёт в одной транзакции БД."""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Account, Transaction


class NotFound(Exception):
    pass


class BadRequest(Exception):
    pass


def create_account(db: Session, owner: str) -> Account:
    acc = Account(owner=owner, balance=Decimal("0.00"))
    db.add(acc)
    db.commit()
    return acc


def get_account(db: Session, account_id: int) -> Account:
    acc = db.get(Account, account_id)
    if acc is None:
        raise NotFound(f"Счёт {account_id} не найден")
    return acc


def _find_by_key(db: Session, key: Optional[str]) -> Optional[Transaction]:
    if not key:
        return None
    return db.scalar(select(Transaction).where(Transaction.idempotency_key == key))


def _lock_accounts(db: Session, *ids: int) -> dict:
    # Блокируем строки всегда в порядке возрастания id: так два встречных
    # перевода A->B и B->A не уйдут в deadlock.
    rows = db.scalars(
        select(Account).where(Account.id.in_(ids)).order_by(Account.id).with_for_update()
    ).all()
    found = {a.id: a for a in rows}
    for i in ids:
        if i not in found:
            raise NotFound(f"Счёт {i} не найден")
    return found


def _commit_tx(db: Session, tx: Transaction) -> Transaction:
    db.add(tx)
    try:
        db.commit()
    except IntegrityError:
        # Параллельный запрос с тем же ключом успел первым — отдаём его результат.
        db.rollback()
        existing = _find_by_key(db, tx.idempotency_key)
        if existing is None:
            raise
        return existing
    return tx


def deposit(db: Session, account_id: int, amount: Decimal, key: Optional[str] = None) -> Transaction:
    existing = _find_by_key(db, key)
    if existing:
        return existing
    acc = _lock_accounts(db, account_id)[account_id]
    acc.balance += amount
    return _commit_tx(db, Transaction(from_id=None, to_id=account_id, amount=amount, idempotency_key=key))


def transfer(db: Session, from_id: int, to_id: int, amount: Decimal, key: Optional[str] = None) -> Transaction:
    if from_id == to_id:
        raise BadRequest("Нельзя перевести на тот же счёт")
    existing = _find_by_key(db, key)
    if existing:
        return existing
    accounts = _lock_accounts(db, from_id, to_id)
    src, dst = accounts[from_id], accounts[to_id]
    if src.balance < amount:
        db.rollback()
        raise BadRequest("Недостаточно средств")
    src.balance -= amount
    dst.balance += amount
    return _commit_tx(db, Transaction(from_id=from_id, to_id=to_id, amount=amount, idempotency_key=key))


def history(db: Session, account_id: int, limit: int, offset: int) -> List[Transaction]:
    get_account(db, account_id)
    return list(db.scalars(
        select(Transaction)
        .where(or_(Transaction.from_id == account_id, Transaction.to_id == account_id))
        .order_by(Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    ))
