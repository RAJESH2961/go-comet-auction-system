import jwt
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import SessionLocal
from .models.rfq import RFQ
from .models.supplier import Supplier
from .models.user import User, UserRole
from .routers import auth, auction, bid, quote, rfq, supplier
from .scheduler.auction_scheduler import AuctionScheduler
from .utils.security import decode_token
from .websocket.manager import manager

scheduler = AuctionScheduler(interval_seconds=5.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    manager.loop = asyncio.get_running_loop()
    scheduler.start()  # reconciles overdue auctions on startup too
    yield
    await scheduler.stop()


app = FastAPI(title="RFQ British Auction Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rfq.router)
app.include_router(supplier.router)
app.include_router(quote.router)
app.include_router(bid.router)
app.include_router(auction.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws/auctions/{rfq_id}")
async def auction_ws(websocket: WebSocket, rfq_id: int, token: str = ""):
    # Authenticate
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("bad type")
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        rfq = db.get(RFQ, rfq_id)
        if user is None or not user.is_active or rfq is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        # Authorization: buyers monitor only their own RFQs;
        # suppliers may monitor RFQs (competitive info only).
        if user.role == UserRole.BUYER and rfq.buyer_id != user.id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        db.close()

    await websocket.accept()
    await manager.connect(rfq_id, websocket)
    try:
        while True:
            # keepalive: client may send pings; we ignore payloads
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(rfq_id, websocket)
