import os
from dotenv import load_dotenv

load_dotenv()


def _f(name, default):
    return float(os.getenv(name, default))


CENTER_LAT = _f("CENTER_LAT", "21.9497")
CENTER_LON = _f("CENTER_LON", "88.8958")
RADIUS_KM = _f("RADIUS_KM", "25")
STATION_LAT = _f("STATION_LAT", "21.9600")
STATION_LON = _f("STATION_LON", "88.8800")

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "demo-wildguard")
FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")

GFW_API_KEY = os.getenv("GFW_API_KEY", "").strip()

ENABLE_CAMERA = os.getenv("ENABLE_CAMERA", "1") == "1"
ENABLE_MIC = os.getenv("ENABLE_MIC", "1") == "1"
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")
VISION_CONFIDENCE = _f("VISION_CONFIDENCE", "0.45")
AUDIO_THRESHOLD = _f("AUDIO_THRESHOLD", "0.25")
ALERT_COOLDOWN_SEC = _f("ALERT_COOLDOWN_SEC", "10")
