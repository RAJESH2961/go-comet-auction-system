import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "postgresql+psycopg://balaji@localhost:5432/rfq_auction_test"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.auction_config import TriggerType  # noqa: E402
from app.models.supplier import Supplier  # noqa: E402

engine = create_engine(os.environ["DATABASE_URL"])
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def clean_tables():
    for table in reversed(Base.metadata.sorted_tables):
        engine.execute(table.delete()) if hasattr(engine, "execute") else None
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


@pytest.fixture
def db():
    s = TestingSession()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(db):
    def override():
        yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _register(client, email, role, name="User"):
    r = client.post("/api/auth/register", json={
        "full_name": name, "email": email, "password": "password123",
        "role": role, "company_name": f"{name} Co", "phone": "999",
    })
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def buyer(client):
    return _register(client, "buyer@test.com", "BUYER", "Buyer One")


@pytest.fixture
def supplier_user(client):
    return _register(client, "supplier1@test.com", "SUPPLIER", "Supplier One")


@pytest.fixture
def supplier2_user(client):
    return _register(client, "supplier2@test.com", "SUPPLIER", "Supplier Two")


@pytest.fixture
def supplier3_user(client):
    return _register(client, "supplier3@test.com", "SUPPLIER", "Supplier Three")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def supplier(db, supplier_user):
    return db.query(Supplier).filter(Supplier.user_id == supplier_user["user"]["id"]).one()


@pytest.fixture
def supplier2(db, supplier2_user):
    return db.query(Supplier).filter(Supplier.user_id == supplier2_user["user"]["id"]).one()


@pytest.fixture
def supplier3(db, supplier3_user):
    return db.query(Supplier).filter(Supplier.user_id == supplier3_user["user"]["id"]).one()


def make_rfq(client, buyer, *, start_offset_min=-60, close_offset_min=60,
             force_offset_min=120, trigger_window=10, extension=5,
             trigger_type="BID_RECEIVED", ref="RFQ-001"):
    now = datetime.now(timezone.utc)
    r = client.post("/api/rfqs", headers=auth(buyer["access_token"]), json={
        "name": "Test RFQ", "reference_id": ref,
        "description": "d", "pickup_location": "Mumbai",
        "destination_location": "Delhi",
        "service_date": (now + timedelta(days=5)).isoformat(),
        "bid_start_time": (now + timedelta(minutes=start_offset_min)).isoformat(),
        "bid_close_time": (now + timedelta(minutes=close_offset_min)).isoformat(),
        "forced_close_time": (now + timedelta(minutes=force_offset_min)).isoformat(),
        "auction_config": {
            "trigger_window_minutes": trigger_window,
            "extension_duration_minutes": extension,
            "trigger_type": trigger_type,
        },
    })
    assert r.status_code == 201, r.text
    return r.json()


def submit_quote(client, tok, rfq_id, freight=40000, origin=5000, dest=5000, carrier="Carrier"):
    r = client.post(f"/api/rfqs/{rfq_id}/quotes", headers=auth(tok), json={
        "carrier_name": carrier, "freight_charges": freight,
        "origin_charges": origin, "destination_charges": dest,
        "transit_time": "3 days",
        "validity_of_quote": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
    })
    return r
