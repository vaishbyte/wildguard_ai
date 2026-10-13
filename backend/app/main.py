"""WildGuard AI - FastAPI backend."""
import asyncio
import time
from collections import Counter
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from . import config
from .db import get_store
from .detection.audio import AudioMonitor
from .detection.vision import VisionMonitor
from .events import EventBus
from .geo.forest import get_forest_data
from .geo.map_builder import build_map
from .sensors import SensorReading, process_reading

store = get_store()
bus = EventBus(store)
vision = VisionMonitor(bus) if config.ENABLE_CAMERA else None
audio = AudioMonitor(bus) if config.ENABLE_MIC else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    bus.loop = asyncio.get_running_loop()
    for mon in (vision, audio):
        if mon:
            mon.start()
    yield
    for mon in (vision, audio):
        if mon:
            mon.stop()


app = FastAPI(title="WildGuard AI", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/status")
def status():
    return {
        "store": store.kind,
        "camera": {"status": vision.status if vision else "disabled",
                   "fps": vision.fps if vision else 0,
                   "counts": vision.counts if vision else {}},
        "mic": {"status": audio.status if audio else "disabled",
                "levels": audio.levels if audio else {},
                "top_sound": audio.top_sound if audio else "",
                "rms": audio.rms if audio else 0},
        "area": {"lat": config.CENTER_LAT, "lon": config.CENTER_LON,
                 "radius_km": config.RADIUS_KM},
    }


@app.get("/api/alerts")
def alerts(limit: int = 50):
    return store.recent("alerts", limit)


@app.get("/api/stats")
def stats():
    recent = store.recent("alerts", 500)
    return {"total": len(recent),
            "by_category": Counter(a["category"] for a in recent),
            "by_severity": Counter(a["severity"] for a in recent),
            "species": Counter(a["label"] for a in recent if a["category"] == "animal")}


class TestAlert(BaseModel):
    category: str = "chainsaw"
    label: str = "manual test"
    confidence: float = 0.9


@app.post("/api/alerts/test")
def test_alert(t: TestAlert):
    """Inject an alert without hardware (no cooldown)."""
    return bus.emit(t.category, t.label, t.confidence, "test", force=True)


@app.get("/api/sensors")
def sensors():
    return store.all("sensor_nodes")


@app.post("/api/sensors/reading")
def sensor_reading(r: SensorReading):
    return {"alerts": process_reading(r, store, bus)}


@app.get("/api/forest")
def forest(refresh: bool = False):
    return get_forest_data(force=refresh)


@app.get("/api/map", response_class=HTMLResponse)
def forest_map():
    return build_map(get_forest_data(), store.recent("alerts", 100), store.all("sensor_nodes"))


def _mjpeg():
    while True:
        frame = vision.latest_jpeg() if vision else None
        if frame:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        time.sleep(0.07)


@app.get("/api/video_feed")
def video_feed():
    return StreamingResponse(_mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    bus.clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive pings from client
    except WebSocketDisconnect:
        bus.clients.discard(websocket)
