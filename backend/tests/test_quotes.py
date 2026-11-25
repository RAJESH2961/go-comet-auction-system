from tests.conftest import auth, make_rfq, submit_quote


def test_submit_initial_quote(client, buyer, supplier_user):
    rfq = make_rfq(client, buyer, ref="Q-1")
    r = submit_quote(client, supplier_user["access_token"], rfq["id"],
                     freight=40000, origin=5000, dest=7000)
    assert r.status_code == 201, r.text
    assert float(r.json()["total_amount"]) == 52000.0


def test_duplicate_quote_rejected(client, buyer, supplier_user):
    rfq = make_rfq(client, buyer, ref="Q-2")
    assert submit_quote(client, supplier_user["access_token"], rfq["id"]).status_code == 201
    r = submit_quote(client, supplier_user["access_token"], rfq["id"])
    assert r.status_code == 409


def test_buyer_sees_all_quotes_supplier_sees_own(
        client, buyer, supplier_user, supplier2_user):
    rfq = make_rfq(client, buyer, ref="Q-3")
    submit_quote(client, supplier_user["access_token"], rfq["id"])
    submit_quote(client, supplier2_user["access_token"], rfq["id"], carrier="C2")
    buyer_quotes = client.get(
        f"/api/rfqs/{rfq['id']}/quotes", headers=auth(buyer["access_token"])).json()
    assert len(buyer_quotes) == 2
    sup_quotes = client.get(
        f"/api/rfqs/{rfq['id']}/quotes",
        headers=auth(supplier_user["access_token"])).json()
    assert len(sup_quotes) == 1
