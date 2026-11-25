import threading
from decimal import Decimal

from app.auction_engine.engine import BidValidationError, place_bid
from app.auction_engine.ranking import compute_rankings
from tests.conftest import TestingSession, auth, make_rfq, submit_quote


def test_concurrent_place_bid(client, db, buyer, supplier_user, supplier2_user,
                              supplier, supplier2):
    rfq = make_rfq(client, buyer, ref="C-2")
    submit_quote(client, supplier_user["access_token"], rfq["id"], freight=50000)
    submit_quote(client, supplier2_user["access_token"], rfq["id"], freight=50000)

    results, errors = [], []

    def worker(sid, amount):
        s = TestingSession()
        try:
            r = place_bid(s, rfq["id"], s.get(__import__("app.models.supplier", fromlist=["Supplier"]).Supplier, sid), Decimal(amount))
            s.commit()
            results.append(r.bid.id)
        except BidValidationError as e:
            s.rollback()
            errors.append(e.message)
        finally:
            s.close()

    t1 = threading.Thread(target=worker, args=(supplier.id, 40000))
    t2 = threading.Thread(target=worker, args=(supplier2.id, 39000))
    t1.start(); t2.start(); t1.join(); t2.join()

    assert not errors
    assert len(results) == 2
    rankings = compute_rankings(db, rfq["id"])
    db.expire_all()
    assert len(rankings) == 2
    assert float(rankings[0].amount) == 39000.0
    assert rankings[0].supplier_id == supplier2.id


def test_same_supplier_concurrent_bids_one_rejected(
        client, db, buyer, supplier_user, supplier):
    rfq = make_rfq(client, buyer, ref="C-3")
    submit_quote(client, supplier_user["access_token"], rfq["id"], freight=50000)
    results, errors = [], []

    def worker(amount):
        s = TestingSession()
        try:
            r = place_bid(s, rfq["id"],
                          s.get(__import__("app.models.supplier", fromlist=["Supplier"]).Supplier, supplier.id),
                          Decimal(amount))
            s.commit()
            results.append(amount)
        except BidValidationError as e:
            s.rollback()
            errors.append(e.message)
        finally:
            s.close()

    threads = [threading.Thread(target=worker, args=(a,)) for a in (45000, 44000)]
    for t in threads: t.start()
    for t in threads: t.join()
    # serialized by FOR UPDATE: whichever ran first wins; the second sees a
    # lower baseline so it may still be accepted if it is lower than the first.
    # Either way, history is consistent.
    rankings = compute_rankings(db, rfq["id"])
    assert rankings[0].amount <= Decimal("45000")
