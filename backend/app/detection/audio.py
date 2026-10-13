"""Microphone -> YAMNet (AudioSet, 521 classes): detects chainsaw, vehicle, gunshot."""
import csv
import logging
import threading
import time

from .. import config

log = logging.getLogger("audio_monitor")

SAMPLE_RATE = 16000
WINDOW_SEC = 1.0

# AudioSet display names grouped into our alert categories
TARGETS = {
    "chainsaw": ["Chainsaw"],
    "vehicle": ["Engine", "Engine starting", "Idling", "Light engine (high frequency)",
                "Medium engine (mid frequency)", "Heavy engine (low frequency)",
                "Motor vehicle (road)", "Vehicle", "Truck", "Motorcycle", "Car",
                "Motorboat, speedboat", "Lawn mower"],
    "gunshot": ["Gunshot, gunfire", "Machine gun"],
}


class AudioMonitor(threading.Thread):
    def __init__(self, bus):
        super().__init__(daemon=True, name="audio")
        self.bus = bus
        self.status = "starting"
        self.levels = {k: 0.0 for k in TARGETS}
        self.top_sound = ""
        self.rms = 0.0
        self._running = True

    def stop(self):
        self._running = False

    def _set_status(self, status, exc=None):
        self.status = status
        if exc is not None:
            log.exception(status)
        else:
            log.info(status)

    def run(self):
        try:
            import numpy as np
            import sounddevice as sd
            import tensorflow as tf
            import tensorflow_hub as hub
        except ImportError as e:
            self._set_status(f"missing package: {e}", exc=e)
            return

        # --- Model loading: previously unprotected, so any failure here
        # (no internet, blocked tfhub.dev, bad cache) killed the thread
        # silently and status got stuck on "loading YAMNet" forever. ---
        self._set_status("loading YAMNet")
        try:
            model = hub.load("https://tfhub.dev/google/yamnet/1")
            class_map = model.class_map_path().numpy().decode()
            with tf.io.gfile.GFile(class_map) as f:
                names = [row["display_name"] for row in csv.DictReader(f)]
        except Exception as e:  # noqa: BLE001
            self._set_status(f"model load error: {e}", exc=e)
            return

        idx = {}
        for cat, lst in TARGETS.items():
            found = [names.index(n) for n in lst if n in names]
            missing = [n for n in lst if n not in names]
            if missing:
                log.warning("category %r: names not found in class map: %s", cat, missing)
            if not found:
                log.warning("category %r: NO matching class names found, will never trigger", cat)
            idx[cat] = found

        threshold = getattr(config, "AUDIO_THRESHOLD", None)
        if threshold is None:
            self._set_status("config.AUDIO_THRESHOLD missing, defaulting to 0.3")
            threshold = 0.3

        block = int(SAMPLE_RATE * WINDOW_SEC)
        try:
            stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                     dtype="float32", blocksize=block)
            stream.start()
        except Exception as e:  # noqa: BLE001
            self._set_status(f"microphone error: {e}", exc=e)
            return

        self._set_status("running")
        while self._running:
            try:
                data, overflowed = stream.read(block)
                if overflowed:
                    log.warning("audio input overflowed, samples were dropped")

                wave = data[:, 0]
                self.rms = round(float(np.sqrt(np.mean(wave ** 2))), 4)

                scores, _, _ = model(wave)
                mean = scores.numpy().mean(axis=0)
                self.top_sound = names[int(mean.argmax())]

                for cat, ids in idx.items():
                    if not ids:
                        continue
                    score = float(mean[ids].max())
                    self.levels[cat] = round(score, 3)
                    log.debug("%s: %.3f", cat, score)
                    if score >= threshold:
                        best = names[ids[int(mean[ids].argmax())]]
                        self.bus.emit(cat, best, score, "mic-1",
                                       extra={"rms": self.rms})
            except Exception as e:  # noqa: BLE001
                # Previously any exception here killed the thread permanently
                # with no error surfaced. Now we log it and keep running.
                log.exception("audio loop error: %s", e)
                time.sleep(0.5)
                continue

            time.sleep(0.01)

        stream.stop()
        stream.close()
        self._set_status("stopped")