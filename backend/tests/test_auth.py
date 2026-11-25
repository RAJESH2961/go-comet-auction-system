from tests.conftest import _register, auth, make_rfq


def test_buyer_registration(client, buyer):
    assert buyer["user"]["role"] == "BUYER"
    assert buyer["access_token"]


def test_supplier_registration(client, supplier_user):
    assert supplier_user["user"]["role"] == "SUPPLIER"
    assert supplier_user["user"]["supplier_id"] is not None


def test_successful_login(client, buyer):
    r = client.post("/api/auth/login", json={
        "email": "buyer@test.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "buyer@test.com"


def test_invalid_password(client, buyer):
    r = client.post("/api/auth/login", json={
        "email": "buyer@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_duplicate_email(client, buyer):
    r = client.post("/api/auth/register", json={
        "full_name": "X", "email": "buyer@test.com",
        "password": "password123", "role": "SUPPLIER"})
    assert r.status_code == 409


def test_expired_or_invalid_jwt(client):
    r = client.get("/api/auth/me", headers=auth("not.a.token"))
    assert r.status_code == 401


def test_unauthorized_access(client):
    assert client.get("/api/auth/me").status_code in (401, 403)
    assert client.get("/api/rfqs").status_code in (401, 403)


def test_buyer_cannot_access_supplier_apis(client, buyer):
    r = client.get("/api/suppliers/me", headers=auth(buyer["access_token"]))
    assert r.status_code == 403


def test_supplier_cannot_create_rfq(client, supplier_user):
    r = client.post("/api/rfqs", headers=auth(supplier_user["access_token"]), json={})
    assert r.status_code == 403


def test_refresh_token(client, buyer):
    r = client.post("/api/auth/refresh", json={"refresh_token": buyer["refresh_token"]})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_refresh_rejects_access_token(client, buyer):
    r = client.post("/api/auth/refresh", json={"refresh_token": buyer["access_token"]})
    assert r.status_code == 401
