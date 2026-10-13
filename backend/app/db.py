"""Storage layer: Firestore Emulator if running, otherwise in-memory fallback."""
import os
import socket
import threading

from . import config


def _port_open(hostport: str) -> bool:
    host, port = hostport.split(":")
    try:
        with socket.create_connection((host, int(port)), timeout=1):
            return True
    except OSError:
        return False


class MemoryStore:
    kind = "memory"

    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def add(self, col, doc):
        with self._lock:
            items = self._data.setdefault(col, {})
            items[doc["id"]] = doc
            if len(items) > 2000:
                for k in list(items)[:500]:
                    items.pop(k)

    def upsert(self, col, doc_id, doc):
        with self._lock:
            self._data.setdefault(col, {}).setdefault(doc_id, {}).update(doc)

    def recent(self, col, limit=50):
        with self._lock:
            docs = list(self._data.get(col, {}).values())
        return sorted(docs, key=lambda d: d.get("ts", ""), reverse=True)[:limit]

    def all(self, col):
        with self._lock:
            return list(self._data.get(col, {}).values())


class FirestoreStore:
    kind = "firestore-emulator"

    def __init__(self):
        os.environ["FIRESTORE_EMULATOR_HOST"] = config.FIRESTORE_EMULATOR_HOST
        from google.cloud import firestore  # anonymous creds in emulator mode

        self._fs = firestore
        self.db = firestore.Client(project=config.FIREBASE_PROJECT_ID)

    def add(self, col, doc):
        self.db.collection(col).document(doc["id"]).set(doc)

    def upsert(self, col, doc_id, doc):
        self.db.collection(col).document(doc_id).set(doc, merge=True)

    def recent(self, col, limit=50):
        q = (self.db.collection(col)
             .order_by("ts", direction=self._fs.Query.DESCENDING)
             .limit(limit))
        return [d.to_dict() for d in q.stream()]

    def all(self, col):
        return [d.to_dict() for d in self.db.collection(col).stream()]


def get_store():
    if _port_open(config.FIRESTORE_EMULATOR_HOST):
        try:
            store = FirestoreStore()
            print(f"[db] Using Firestore Emulator at {config.FIRESTORE_EMULATOR_HOST}")
            return store
        except Exception as e:  # noqa: BLE001
            print(f"[db] Firestore init failed ({e}); using in-memory store")
    else:
        print("[db] Firestore Emulator not running; using in-memory store")
    return MemoryStore()
