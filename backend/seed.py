"""Seed demo data: 1 buyer, 3 suppliers, 1 live RFQ with quotes.

Run: .venv/bin/python seed.py
"""
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models.auction_config import AuctionConfig, TriggerType
from app.models.rfq import RFQ, RFQStatus
from app.models.supplier import Supplier
from app.models.supplier_quote import SupplierQuote
from app.models.user import User, UserRole
from app.utils.security import hash_password

db = SessionLocal()
now = datetime.now(timezone.utc)


def user(email, name, role, company):
    u = db.query(User).filter(User.email == email).first()
    if u:
        return u
    u = User(full_name=name, email=email, password_hash=hash_password("password123"),
             role=role, company_name=company, phone="9876543210")
    db.add(u); db.flush()
    if role == UserRole.SUPPLIER:
        db.add(Supplier(user_id=u.id, company_name=company, contact_name=name, phone=u.phone))
    return u


buyer = user("buyer@demo.com", "Demo Buyer", UserRole.BUYER, "Acme Logistics")
s1 = user("supplier1@demo.com", "Supplier One", UserRole.SUPPLIER, "FastFreight Ltd")
s2 = user("supplier2@demo.com", "Supplier Two", UserRole.SUPPLIER, "CargoKings Pvt")
s3 = user("supplier3@demo.com", "Supplier Three", UserRole.SUPPLIER, "MoveRight Carriers")

rfq = db.query(RFQ).filter(RFQ.reference_id == "RFQ-DEMO-001").first()
if not rfq:
    rfq = RFQ(
        buyer_id=buyer.id, name="Mumbai → Delhi FTL Shipment",
        reference_id="RFQ-DEMO-001",
        description="Full truckload, 9 tonnes, electronic goods.",
        pickup_location="Mumbai, MH", destination_location="Delhi, DL",
        service_date=now + timedelta(days=7),
        bid_start_time=now - timedelta(minutes=30),
        bid_close_time=now + timedelta(minutes=30),
        current_close_time=now + timedelta(minutes=30),
        forced_close_time=now + timedelta(hours=2),
        status=RFQStatus.UPCOMING,
    )
    db.add(rfq); db.flush()
    db.add(AuctionConfig(rfq_id=rfq.id, trigger_window_minutes=10,
                         extension_duration_minutes=5,
                         trigger_type=TriggerType.BID_RECEIVED))
db.flush()

for sup, freight, carrier in ((s1, 52000, "FastFreight"), (s2, 49000, "CargoKings"), (s3, 55000, "MoveRight")):
    sid = db.query(Supplier).filter(Supplier.user_id == sup.id).one().id
    if not db.query(SupplierQuote).filter_by(rfq_id=rfq.id, supplier_id=sid).first():
        db.add(SupplierQuote(
            rfq_id=rfq.id, supplier_id=sid, carrier_name=carrier,
            freight_charges=freight, origin_charges=2500, destination_charges=2500,
            total_amount=freight + 5000, transit_time="3 days"))

db.commit()
print("Seeded. Login with buyer@demo.com / supplier1..3@demo.com — password: password123")
