"""Kamera-Service mit Threading für OpenCV Capture."""

import time
import threading
import cv2
import numpy as np


class CameraService:
    """Threaded Webcam-Capture mit Lock-basiertem Frame-Zugriff."""

    def __init__(self, camera_index: int = 0):
        self._camera_index = camera_index
        self._cap = None
        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    @property
    def camera_index(self):
        return self._camera_index

    @camera_index.setter
    def camera_index(self, value: int):
        was_running = self._running
        if was_running:
            self.stop()
        self._camera_index = value
        if was_running:
            self.start()

    def start(self):
        if self._running:
            return
        # Sicherstellen, dass der alte Thread wirklich beendet ist
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        # _cap wird im Thread released; nur als Fallback hier
        with self._lock:
            if self._cap:
                self._cap.release()
                self._cap = None
            self._frame = None

    def get_frame(self) -> np.ndarray | None:
        """Aktuellen Frame thread-sicher abrufen."""
        with self._lock:
            if self._frame is not None:
                return self._frame.copy()
            return None

    def _capture_loop(self):
        self._cap = cv2.VideoCapture(self._camera_index)
        if not self._cap.isOpened():
            # Fallback: andere Kamera-Indizes probieren
            for i in range(5):
                if i == self._camera_index:
                    continue
                self._cap = cv2.VideoCapture(i)
                if self._cap.isOpened():
                    break

        if not self._cap.isOpened():
            self._running = False
            return

        # 720p anfordern für bessere Landmark-Präzision bei Entfernung
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.033)
                continue
            with self._lock:
                self._frame = frame

        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
