from datetime import datetime, timedelta, timezone

from tests.conftest import auth, make_rfq


def test_create_rfq(client, buyer):
    rfq = make_rfq(client, buyer)
    fetched = client.get(f"/api/rfqs/{rfq['id']}",
                         headers=auth(buyer["access_token"])).json()
    assert fetched["status"] == "ACTIVE"  # started 60 min ago
    assert rfq["auction_config"]["trigger_type"] == "BID_RECEIVED"


def test_duplicate_reference_id(client, buyer):
    make_rfq(client, buyer, ref="DUP-1")
    import pytest
    now = datetime.now(timezone.utc)
    r = client.post("/api/rfqs", headers=auth(buyer["access_token"]), json={
        "name": "X", "reference_id": "DUP-1",
        "bid_start_time": now.isoformat(),
        "bid_close_time": (now + timedelta(hours=1)).isoformat(),
        "forced_close_time": (now + timedelta(hours=2)).isoformat(),
        "auction_config": {"trigger_window_minutes": 5,
                           "extension_duration_minutes": 5,
                           "trigger_type": "BID_RECEIVED"},
    })
    assert r.status_code == 409


def test_start_before_close_validation(client, buyer):
    now = datetime.now(timezone.utc)
    r = client.post("/api/rfqs", headers=auth(buyer["access_token"]), json={
        "name": "X", "reference_id": "BAD-1",
        "bid_start_time": (now + timedelta(hours=2)).isoformat(),
        "bid_close_time": (now + timedelta(hours=1)).isoformat(),
        "forced_close_time": (now + timedelta(hours=3)).isoformat(),
        "auction_config": {"trigger_window_minutes": 5,
                           "extension_duration_minutes": 5,
                           "trigger_type": "BID_RECEIVED"},
    })
    assert r.status_code == 422


def test_forced_close_after_close_validation(client, buyer):
    now = datetime.now(timezone.utc)
    r = client.post("/api/rfqs", headers=auth(buyer["access_token"]), json={
        "name": "X", "reference_id": "BAD-2",
        "bid_start_time": now.isoformat(),
        "bid_close_time": (now + timedelta(hours=2)).isoformat(),
        "forced_close_time": (now + timedelta(hours=1)).isoformat(),
        "auction_config": {"trigger_window_minutes": 5,
                           "extension_duration_minutes": 5,
                           "trigger_type": "BID_RECEIVED"},
    })
    assert r.status_code == 422


def test_list_and_get_rfq(client, buyer):
    rfq = make_rfq(client, buyer, ref="LIST-1")
    r = client.get("/api/rfqs", headers=auth(buyer["access_token"]))
    assert r.status_code == 200
    assert any(i["reference_id"] == "LIST-1" for i in r.json()["items"])
    r = client.get(f"/api/rfqs/{rfq['id']}", headers=auth(buyer["access_token"]))
    assert r.status_code == 200


def test_buyer_cannot_see_other_buyers_rfq(client, buyer):
    other = client.post("/api/auth/register", json={
        "full_name": "B2", "email": "b2@t.com", "password": "password123",
        "role": "BUYER"}).json()
    rfq = make_rfq(client, buyer, ref="PRIV-1")
    r = client.get(f"/api/rfqs/{rfq['id']}", headers=auth(other["access_token"]))
    assert r.status_code == 403
