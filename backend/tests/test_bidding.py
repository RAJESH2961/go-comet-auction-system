from tests.conftest import auth, make_rfq, submit_quote


def bid(client, tok, rfq_id, amount):
    return client.post(f"/api/rfqs/{rfq_id}/bids",
                       headers=auth(tok), json={"amount": amount})


def setup_auction(client, buyer, *suppliers, **kw):
    rfq = make_rfq(client, buyer, **kw)
    for i, s in enumerate(suppliers):
        submit_quote(client, s["access_token"], rfq["id"],
                     freight=40000 + i * 5000, carrier=f"C{i}")
    return rfq


def test_reject_bid_before_start(client, buyer, supplier_user):
    rfq = setup_auction(client, buyer, supplier_user,
                        ref="B-1", start_offset_min=30)
    r = bid(client, supplier_user["access_token"], rfq["id"], 40000)
    assert r.status_code == 400


def _insert_quote(db, rfq_id, supplier_id, total=50000):
    from decimal import Decimal
    from app.models.supplier_quote import SupplierQuote
    q = SupplierQuote(rfq_id=rfq_id, supplier_id=supplier_id,
                      carrier_name="C", freight_charges=Decimal(total - 500),
                      origin_charges=Decimal("250"), destination_charges=Decimal("250"),
                      total_amount=Decimal(total), transit_time="3d")
    db.add(q)
    db.commit()
    return q


def test_reject_bid_after_close(client, db, buyer, supplier_user, supplier):
    rfq = make_rfq(client, buyer, ref="B-2",
                   start_offset_min=-180, close_offset_min=-60, force_offset_min=-30)
    _insert_quote(db, rfq["id"], supplier.id)
    r = bid(client, supplier_user["access_token"], rfq["id"], 1000)
    assert r.status_code == 400


def test_reject_bid_after_forced_close(client, db, buyer, supplier_user, supplier):
    rfq = make_rfq(client, buyer, ref="B-3",
                   start_offset_min=-180, close_offset_min=-60, force_offset_min=-10)
    _insert_quote(db, rfq["id"], supplier.id)
    r = bid(client, supplier_user["access_token"], rfq["id"], 1000)
    assert r.status_code == 400


def test_reject_without_quote(client, buyer, supplier_user):
    rfq = make_rfq(client, buyer, ref="B-4")
    r = bid(client, supplier_user["access_token"], rfq["id"], 1000)
    assert r.status_code == 403


def test_reject_non_improving_bid(client, buyer, supplier_user):
    rfq = setup_auction(client, buyer, supplier_user, ref="B-5")  # quote=50000
    r = bid(client, supplier_user["access_token"], rfq["id"], 60000)
    assert r.status_code == 400
    assert bid(client, supplier_user["access_token"], rfq["id"], 49000).status_code == 201
    r = bid(client, supplier_user["access_token"], rfq["id"], 49500)
    assert r.status_code == 400


def test_accept_valid_lower_bids_and_rankings(
        client, buyer, supplier_user, supplier2_user, supplier3_user):
    rfq = setup_auction(client, buyer, supplier_user, supplier2_user, supplier3_user,
                        ref="B-6")
    bid(client, supplier_user["access_token"], rfq["id"], 45000)
    bid(client, supplier2_user["access_token"], rfq["id"], 40000)
    bid(client, supplier3_user["access_token"], rfq["id"], 35000)
    r = client.get(f"/api/rfqs/{rfq['id']}/rankings",
                   headers=auth(buyer["access_token"]))
    ranks = r.json()
    assert [x["rank_label"] for x in ranks] == ["L1", "L2", "L3"]
    assert float(ranks[0]["latest_bid"]) == 35000.0


def test_bid_history_maintained(client, buyer, supplier_user):
    rfq = setup_auction(client, buyer, supplier_user, ref="B-7")
    bid(client, supplier_user["access_token"], rfq["id"], 45000)
    bid(client, supplier_user["access_token"], rfq["id"], 43000)
    hist = client.get(f"/api/rfqs/{rfq['id']}/bids",
                      headers=auth(buyer["access_token"])).json()
    assert len(hist) == 2
    assert float(hist[1]["previous_amount"]) == 45000.0
    mine = client.get(f"/api/rfqs/{rfq['id']}/my-bids",
                      headers=auth(supplier_user["access_token"])).json()
    assert len(mine) == 2
