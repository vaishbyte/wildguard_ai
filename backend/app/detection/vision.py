"""Webcam -> YOLOv8: detects humans and animals, classifies species (COCO classes)."""
import os
import threading
import time

from .. import config

# COCO class ids used by pretrained YOLOv8
HUMAN_ID = 0
ANIMALS = {14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep",
           19: "cow", 20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe"}


class VisionMonitor(threading.Thread):
    def __init__(self, bus):
        super().__init__(daemon=True, name="vision")
        self.bus = bus
        self.status = "starting"
        self.counts = {}qq
        self.fps = 0.0
        self._jpeg = None
        self._lock = threading.Lock()
        self._running = True

    def latest_jpeg(self):
        with self._lock:
            return self._jpeg

    def stop(self):
        self._running = False

    def run(self):
        try:
            import cv2
            from ultralytics import YOLO
        except ImportError as e:
            self.status = f"missing package: {e}"
            return

        self.status = "loading model"
        model = YOLO(config.YOLO_MODEL)  # auto-downloads yolov8n.pt on first run

        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        cap = cv2.VideoCapture(config.CAMERA_INDEX, backend)
        if not cap.isOpened():
            self.status = f"camera {config.CAMERA_INDEX} not found"
            return

        self.status = "running"
        classes = [HUMAN_ID] + list(ANIMALS)
        t0, frames = time.time(), 0
        while self._running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.1)
                continue

            result = model(frame, conf=config.VISION_CONFIDENCE,
                           classes=classes, verbose=False)[0]
            counts = {}
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                if cls == HUMAN_ID:
                    label, category = "human", "human"
                else:
                    label, category = ANIMALS[cls], "animal"
                counts[label] = counts.get(label, 0) + 1
                self.bus.emit(category, label, conf, "camera-1",
                              extra={"count": counts[label]})
            self.counts = counts

            annotated = result.plot()
            ok, buf = cv2.imencode(".jpg", annotated,
                                   [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ok:
                with self._lock:
                    self._jpeg = buf.tobytes()

            frames += 1
            if time.time() - t0 >= 2:
                self.fps = round(frames / (time.time() - t0), 1)
                t0, frames = time.time(), 0

        cap.release()
        self.status = "stopped"
