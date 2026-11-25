"""Lightweight asyncio scheduler that reconciles auction statuses.

Runs every few seconds inside the FastAPI process — no Redis required.
On startup it immediately reconciles any auctions that passed their
closing time while the app was offline.
"""
import asyncio

from ..auction_engine.closing import close_due_auctions
from ..database import SessionLocal
from ..websocket.manager import manager


class AuctionScheduler:
    def __init__(self, interval_seconds: float = 5.0):
        self.interval = interval_seconds
        self._task: asyncio.Task | None = None
        self._stopped: asyncio.Event | None = None

    async def _loop(self):
        self._stopped = asyncio.Event()
        while not self._stopped.is_set():
            try:
                changed = await asyncio.to_thread(self._reconcile)
                for rfq in changed:
                    await manager.broadcast(rfq.id, "auction_status", {
                        "rfq_id": rfq.id,
                        "status": rfq.status.value,
                        "current_close_time": rfq.current_close_time,
                    })
            except Exception:
                pass  # keep the scheduler alive; errors surface via API validation too
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                continue

    @staticmethod
    def _reconcile():
        db = SessionLocal()
        try:
            return close_due_auctions(db)
        finally:
            db.close()

    def start(self):
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        if self._stopped:
            self._stopped.set()
        if self._task:
            await asyncio.wait([self._task])
