# RFQ British Auction Platform

A full-stack Request-for-Quotation system with British (reverse) auction bidding:
buyers create RFQs, suppliers submit quotations and compete by lowering bids,
with automatic time-extension triggers and a hard forced-close deadline.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy 2, PostgreSQL, Alembic, WebSockets, Argon2, JWT
- **Frontend:** React 18, Vite, Tailwind CSS, React Router, Axios, Lucide
- **No Redis / no external services** — in-process asyncio scheduler + in-memory WS manager.

## Quick Start

### 1. Database

```bash
createdb rfq_auction
# edit backend/.env if your PG user/password differs
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # adjust DATABASE_URL
alembic upgrade head
python seed.py                # optional demo data
uvicorn app.main:app --reload # http://localhost:8000  (docs: /docs)
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxies /api & /ws to :8000)
```

### 4. Tests

```bash
cd backend
createdb rfq_auction_test     # once
pytest tests -q               # 40 tests
```

## Demo Accounts (after `seed.py`)

| Role | Email | Password |
|---|---|---|
| Buyer | buyer@demo.com | password123 |
| Supplier | supplier1@demo.com … supplier3@demo.com | password123 |

## Architecture

```
backend/app/
  auction_engine/     # core logic — NOT in route handlers
    validation.py     # bid eligibility checks
    ranking.py        # L1..Ln from latest valid bid per supplier (tie: earliest bid)
    extension.py      # BID_RECEIVED / ANY_RANK_CHANGE / L1_RANK_CHANGE triggers
    closing.py        # status computation, forced-close reconciliation
    engine.py         # place_bid(): SELECT FOR UPDATE → validate → insert → rank → extend
  routers/            # thin HTTP layer
  services/           # business services
  websocket/manager.py# per-RFQ rooms; broadcasts AFTER commit via run_coroutine_threadsafe
  scheduler/          # 5s asyncio loop closing due auctions; reconciles on restart
```

### Concurrency

Every bid runs in one transaction that takes `SELECT ... FOR UPDATE` on the RFQ
row, so simultaneous bids serialize; rankings and extensions are computed under
the lock and broadcasts go out only after `COMMIT`.

### Extension rule

`new_close = MIN(current_close + extension_minutes, forced_close)` applied only
when the configured trigger fires within `[current_close - window, current_close)`.
`FORCE_CLOSED` is set when the forced boundary is reached.

## Security Notes

- Argon2id password hashing; JWT access + refresh tokens; role-based guards.
- Supplier/buyer identity is always derived from the JWT — never trusted from the client.
- Suppliers see only their own quotation rows; buyers only their own RFQs.
- For production: serve over HTTPS, move tokens to HttpOnly Secure cookies with
  SameSite=strict + CSRF tokens, and add a refresh-token rotation/blocklist.

## ER Diagram

```
users (1)──< suppliers           users (1)──< rfqs
   │                                  │
   │                                  ├──1── auction_configs
   │                                  ├──<── supplier_quotes >── suppliers
   └──────────────< (bids.actor)      ├──<── bids >── suppliers
                                      └──<── auction_activity_logs

users:            id, full_name, email*, password_hash, role, company_name, phone, is_active, ts
suppliers:        id, user_id*(fk), company_name, contact_name, phone, ts
rfqs:             id, buyer_id(fk), name, reference_id*, description, pickup/destination,
                  service_date, bid_start, bid_close, current_close, forced_close, status, ts
auction_configs:  id, rfq_id*(fk), trigger_window_minutes, extension_duration_minutes, trigger_type
supplier_quotes:  id, rfq_id, supplier_id, carrier_name, freight/origin/destination/total (NUMERIC),
                  transit_time, validity_of_quote  UNIQUE(rfq_id, supplier_id)
bids:             id, rfq_id, supplier_id, amount NUMERIC(14,2), created_at   (immutable)
activity_logs:    id, rfq_id, event_type, actor_user_id, supplier_id, message, metadata JSONB
```
