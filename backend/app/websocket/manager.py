"""In-memory WebSocket connection manager for auction rooms."""
import asyncio
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from fastapi import WebSocket


def _default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, Decimal):
        return float(o)
    return str(o)


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, rfq_id: int, ws: WebSocket):
        async with self._lock:
            self.rooms[rfq_id].add(ws)

    async def disconnect(self, rfq_id: int, ws: WebSocket):
        async with self._lock:
            self.rooms[rfq_id].discard(ws)
            if not self.rooms[rfq_id]:
                self.rooms.pop(rfq_id, None)

    async def broadcast(self, rfq_id: int, event: str, data: dict):
        async with self._lock:
            sockets = list(self.rooms.get(rfq_id, ()))
        if not sockets:
            return
        payload = json.dumps({"event": event, "data": data}, default=_default)
        dead = []
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self.rooms[rfq_id].discard(ws)


manager = ConnectionManager()


def broadcast_threadsafe(rfq_id: int, event: str, data: dict):
    """Schedule a broadcast from sync code (post-commit) onto the app loop."""
    loop = manager.loop
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(rfq_id, event, data), loop)
