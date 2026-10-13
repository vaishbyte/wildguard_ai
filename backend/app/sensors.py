"""Rule engine for field sensor nodes (Wokwi ESP32 or Python simulator)."""
from pydantic import BaseModel, Field

from .events import now_iso


class SensorReading(BaseModel):
    node_id: str
    lat: float
    lon: float
    motion: bool = False
    sound_db: float = Field(0, ge=0, le=140)
    vibration: float = Field(0, ge=0, le=1)   # 0..1 normalised tree vibration
    battery: float = Field(100, ge=0, le=100)


def process_reading(r: SensorReading, store, bus):
    store.upsert("sensor_nodes", r.node_id, {**r.model_dump(), "ts": now_iso()})
    alerts = []
    src = f"sensor:{r.node_id}"
    if r.vibration >= 0.6 and r.sound_db >= 80:
        conf = min(1.0, (r.vibration + r.sound_db / 110) / 2)
        alerts.append(bus.emit("chainsaw", "vibration+noise pattern", conf, src,
                               r.lat, r.lon, extra=r.model_dump()))
    elif r.sound_db >= 75:
        alerts.append(bus.emit("loud_noise", "possible engine", r.sound_db / 110, src,
                               r.lat, r.lon, extra=r.model_dump()))
    if r.motion:
        alerts.append(bus.emit("intrusion", "PIR motion", 0.7, src, r.lat, r.lon,
                               extra=r.model_dump()))
    return [a for a in alerts if a]
