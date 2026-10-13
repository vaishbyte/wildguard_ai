"""Alert creation, cooldown, storage and WebSocket broadcast."""
import asyncio
import threading
import time
import uuid
from datetime import datetime, timezone

from . import config

SEVERITY = {
    "chainsaw": "critical",
    "gunshot": "critical",
    "engine": "high",
    "human": "high",
    "intrusion": "medium",
    "loud_noise": "medium",
    "animal": "info",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class EventBus:
    def __init__(self, store):
        self.store = store
        self.clients = set()
        self.loop = None
        self._last = {}
        self._lock = threading.Lock()

    def emit(self, category, label, confidence, source, lat=None, lon=None,
             extra=None, severity=None, force=False):
        key = f"{category}:{label}:{source}"
        now = time.time()
        with self._lock:
            if not force and now - self._last.get(key, 0) < config.ALERT_COOLDOWN_SEC:
                return None
            self._last[key] = now

        doc = {
            "id": uuid.uuid4().hex,
            "ts": now_iso(),
            "category": category,
            "label": label,
            "confidence": round(float(confidence), 3),
            "severity": severity or SEVERITY.get(category, "info"),
            "source": source,
            "lat": lat if lat is not None else config.STATION_LAT,
            "lon": lon if lon is not None else config.STATION_LON,
            "extra": extra or {},
        }
        try:
            self.store.add("alerts", doc)
        except Exception as e:  # noqa: BLE001
            print(f"[events] store error: {e}")
        print(f"[ALERT] {doc['severity'].upper():8} {category}/{label} "
              f"conf={doc['confidence']} src={source}")
        self.broadcast({"type": "alert", "data": doc})
        return doc

    def broadcast(self, message):
        if self.loop and self.clients:
            asyncio.run_coroutine_threadsafe(self._send_all(message), self.loop)

    async def _send_all(self, message):
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)
