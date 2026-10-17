import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def new_account(client, owner="Ali", deposit=None):
    acc = client.post("/accounts", json={"owner": owner}).json()
    if deposit:
        client.post(f"/accounts/{acc['id']}/deposit", json={"amount": deposit})
    return acc["id"]


def balance(client, acc_id):
    return client.get(f"/accounts/{acc_id}").json()["balance"]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_transfer_moves_money(client):
    a, b = new_account(client, deposit="100.00"), new_account(client, "Dana")
    r = client.post("/transfers", json={"from_id": a, "to_id": b, "amount": "30.50"})
    assert r.status_code == 201
    assert balance(client, a) == "69.50"
    assert balance(client, b) == "30.50"


def test_insufficient_funds(client):
    a, b = new_account(client, deposit="10"), new_account(client)
    r = client.post("/transfers", json={"from_id": a, "to_id": b, "amount": "11"})
    assert r.status_code == 422
    assert balance(client, a) == "10.00"


@pytest.mark.parametrize("amount", ["0", "-5", "1.001"])
def test_invalid_amount(client, amount):
    a, b = new_account(client, deposit="10"), new_account(client)
    assert client.post("/transfers", json={"from_id": a, "to_id": b, "amount": amount}).status_code == 422


def test_self_transfer_and_missing_account(client):
    a = new_account(client, deposit="10")
    assert client.post("/transfers", json={"from_id": a, "to_id": a, "amount": "1"}).status_code == 422
    assert client.post("/transfers", json={"from_id": a, "to_id": 999, "amount": "1"}).status_code == 404


def test_idempotency_key(client):
    a, b = new_account(client, deposit="100"), new_account(client)
    headers = {"Idempotency-Key": "order-42"}
    r1 = client.post("/transfers", json={"from_id": a, "to_id": b, "amount": "25"}, headers=headers)
    r2 = client.post("/transfers", json={"from_id": a, "to_id": b, "amount": "25"}, headers=headers)
    assert r1.json()["id"] == r2.json()["id"]
    assert balance(client, a) == "75.00"


def test_history_pagination(client):
    a, b = new_account(client, deposit="100"), new_account(client)
    for _ in range(3):
        client.post("/transfers", json={"from_id": a, "to_id": b, "amount": "1"})
    page = client.get(f"/accounts/{a}/transactions?limit=2").json()
    assert len(page) == 2
    assert len(client.get(f"/accounts/{a}/transactions?limit=10").json()) == 4
