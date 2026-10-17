from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import service
from .db import Base, engine, get_db
from .schemas import AccountCreate, AccountOut, DepositIn, TransactionOut, TransferIn


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)  # в продакшене — Alembic-миграции
    yield


app = FastAPI(title="Wallet API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(service.NotFound)
def not_found(_: Request, exc: service.NotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(service.BadRequest)
def bad_request(_: Request, exc: service.BadRequest):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


IdemKey = Header(default=None, alias="Idempotency-Key", max_length=64)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "database unavailable")
    return {"status": "ok"}


@app.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(body: AccountCreate, db: Session = Depends(get_db)):
    return service.create_account(db, body.owner)


@app.get("/accounts/{account_id}", response_model=AccountOut)
def get_account(account_id: int, db: Session = Depends(get_db)):
    return service.get_account(db, account_id)


@app.post("/accounts/{account_id}/deposit", response_model=TransactionOut, status_code=201)
def deposit(account_id: int, body: DepositIn, key: Optional[str] = IdemKey, db: Session = Depends(get_db)):
    return service.deposit(db, account_id, body.amount, key)


@app.post("/transfers", response_model=TransactionOut, status_code=201)
def transfer(body: TransferIn, key: Optional[str] = IdemKey, db: Session = Depends(get_db)):
    return service.transfer(db, body.from_id, body.to_id, body.amount, key)


@app.get("/accounts/{account_id}/transactions", response_model=List[TransactionOut])
def transactions(
    account_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.history(db, account_id, limit, offset)
