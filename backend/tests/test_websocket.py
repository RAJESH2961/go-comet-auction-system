import json

from tests.conftest import auth, make_rfq, submit_quote
from tests.test_bidding import bid


def test_websocket_requires_auth(client, buyer):
    rfq = make_rfq(client, buyer, ref="W-0")
    try:
        with client.websocket_connect(f"/ws/auctions/{rfq['id']}?token=bad"):
            pass
        assert False, "should have been closed"
    except Exception:
        pass


def test_websocket_broadcasts_bid_and_rankings(client, buyer, supplier_user):
    rfq = make_rfq(client, buyer, ref="W-1")
    submit_quote(client, supplier_user["access_token"], rfq["id"])
    with client.websocket_connect(
            f"/ws/auctions/{rfq['id']}?token={buyer['access_token']}") as ws:
        r = bid(client, supplier_user["access_token"], rfq["id"], 40000)
        assert r.status_code == 201
        events = set()
        for _ in range(2):  # new_bid + rankings
            msg = json.loads(ws.receive_text())
            events.add(msg["event"])
        assert "new_bid" in events
        assert "rankings" in events


def test_websocket_extension_notification(client, buyer, supplier_user):
    rfq = make_rfq(client, buyer, ref="W-2", close_offset_min=8,
                   force_offset_min=60, trigger_window=10, extension=5)
    submit_quote(client, supplier_user["access_token"], rfq["id"])
    with client.websocket_connect(
            f"/ws/auctions/{rfq['id']}?token={supplier_user['access_token']}") as ws:
        bid(client, supplier_user["access_token"], rfq["id"], 40000)
        events = set()
        for _ in range(3):  # new_bid + rankings + auction_extended
            msg = json.loads(ws.receive_text())
            events.add(msg["event"])
        assert "auction_extended" in events
