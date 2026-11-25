from datetime import datetime, timedelta, timezone

from tests.conftest import auth, make_rfq, submit_quote
from tests.test_bidding import bid, setup_auction


def _rfq(db, rfq_id):
    from app.models.rfq import RFQ
    return db.get(RFQ, rfq_id)


def test_extend_bid_received_trigger(client, db, buyer, supplier_user):
    # closing in 8 min, trigger window 10 -> inside window
    rfq = setup_auction(client, buyer, supplier_user, ref="E-1",
                        close_offset_min=8, force_offset_min=60,
                        trigger_window=10, extension=5,
                        trigger_type="BID_RECEIVED")
    before = rfq["current_close_time"]
    r = bid(client, supplier_user["access_token"], rfq["id"], 40000)
    assert r.status_code == 201
    db.expire_all()
    new_close = _rfq(db, rfq["id"]).current_close_time
    assert new_close.isoformat() > before


def test_no_extension_outside_window(client, db, buyer, supplier_user):
    rfq = setup_auction(client, buyer, supplier_user, ref="E-2",
                        close_offset_min=30, force_offset_min=90,
                        trigger_window=10, extension=5,
                        trigger_type="BID_RECEIVED")
    before = rfq["current_close_time"]
    bid(client, supplier_user["access_token"], rfq["id"], 40000)
    db.expire_all()
    assert _rfq(db, rfq["id"]).current_close_time.isoformat() == before


def test_any_rank_change_extends(client, db, buyer, supplier_user, supplier2_user):
    rfq = setup_auction(client, buyer, supplier_user, supplier2_user, ref="E-3",
                        close_offset_min=8, force_offset_min=60,
                        trigger_window=10, extension=5,
                        trigger_type="ANY_RANK_CHANGE")
    # s1 quote=50000, s2 quote=55000. s2 bids 45000 -> becomes L1, ranks change
    r = bid(client, supplier2_user["access_token"], rfq["id"], 45000)
    assert r.status_code == 201
    db.expire_all()
    new_close = _rfq(db, rfq["id"]).current_close_time
    assert new_close > datetime.fromisoformat(rfq["current_close_time"])


def test_no_extension_when_rank_unchanged(client, db, buyer, supplier_user, supplier2_user):
    rfq = setup_auction(client, buyer, supplier_user, supplier2_user, ref="E-4",
                        close_offset_min=8, force_offset_min=60,
                        trigger_window=10, extension=5,
                        trigger_type="ANY_RANK_CHANGE")
    # s1 (quote 50000, L1) lowers to 48000, stays L1, s2 still L2 -> no rank change
    r = bid(client, supplier_user["access_token"], rfq["id"], 48000)
    assert r.status_code == 201
    db.expire_all()
    assert _rfq(db, rfq["id"]).current_close_time.isoformat() == rfq["current_close_time"]


def test_l1_change_extends(client, db, buyer, supplier_user, supplier2_user):
    rfq = setup_auction(client, buyer, supplier_user, supplier2_user, ref="E-5",
                        close_offset_min=8, force_offset_min=60,
                        trigger_window=10, extension=5,
                        trigger_type="L1_RANK_CHANGE")
    r = bid(client, supplier2_user["access_token"], rfq["id"], 45000)
    assert r.status_code == 201
    db.expire_all()
    assert _rfq(db, rfq["id"]).current_close_time > datetime.fromisoformat(
        rfq["current_close_time"])


def test_l1_same_supplier_no_extend(client, db, buyer, supplier_user, supplier2_user):
    rfq = setup_auction(client, buyer, supplier_user, supplier2_user, ref="E-6",
                        close_offset_min=8, force_offset_min=60,
                        trigger_window=10, extension=5,
                        trigger_type="L1_RANK_CHANGE")
    bid(client, supplier_user["access_token"], rfq["id"], 48000)  # s1 stays L1
    db.expire_all()
    assert _rfq(db, rfq["id"]).current_close_time.isoformat() == rfq["current_close_time"]


def test_never_exceeds_forced_close(client, db, buyer, supplier_user):
    # close in 5 min, force in 8, extension 10 -> capped at force time
    rfq = setup_auction(client, buyer, supplier_user, ref="E-7",
                        close_offset_min=5, force_offset_min=8,
                        trigger_window=10, extension=10,
                        trigger_type="BID_RECEIVED")
    bid(client, supplier_user["access_token"], rfq["id"], 40000)
    db.expire_all()
    r = _rfq(db, rfq["id"])
    assert abs((r.current_close_time - r.forced_close_time).total_seconds()) < 1


def test_extension_logged(client, db, buyer, supplier_user):
    rfq = setup_auction(client, buyer, supplier_user, ref="E-8",
                        close_offset_min=8, force_offset_min=60,
                        trigger_window=10, extension=5)
    bid(client, supplier_user["access_token"], rfq["id"], 40000)
    logs = client.get(f"/api/rfqs/{rfq['id']}/activity",
                      headers=auth(buyer["access_token"])).json()
    ext = [l for l in logs if l["event_type"] == "AUCTION_EXTENDED"]
    assert ext and ext[0]["event_metadata"]["new_close_time"]
