"""Zungenerkennung: MediaPipe Landmarks -> Mund-ROI -> HSV -> Score -> tongue_out."""

import os
import time
import cv2
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
except ImportError:
    mp = None

from detection.calibration import Calibration, CalibrationState
from detection.hsv_detector import HsvDetector
from detection.one_euro_filter import OneEuroFilter

# Mund-Landmark-Indizes (MediaPipe Face Mesh)
OUTER_LIP_INDICES = [
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291,
    409, 270, 269, 267, 0, 37, 39, 40, 185,
]
INNER_LIP_INDICES = [
    78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308,
    415, 310, 311, 312, 13, 82, 81, 80, 191,
]

TONGUE_RATIO_THRESHOLD = 0.15
TONGUE_TIP_THRESHOLD = 0.6
MOUTH_OPEN_THRESHOLD = 0.04
GRACE_PERIOD_FRAMES = 30  # ~1 Sekunde nach Kalibrierung keine Erkennung
MIN_MOUTH_AREA = 100  # Pixel² — unter diesem Wert ist der Mund geschlossen


class DetectorService:
    """Erkennt Zungenprotrusion per HSV-Farbanalyse im Mund-ROI."""

    def __init__(self):
        self.init_error: str | None = None
        self._landmarker = None
        self._hsv_detector = HsvDetector()
        self._calibration = Calibration()
        self._score_filter = OneEuroFilter(min_cutoff=1.0, beta=0.007)
        self._timestamp_ms = 0
        self._frame_count = 0
        self._grace_frames_remaining = 0
        self.sensitivity = 1.0
        self._roi_save_interval = 5.0  # Sekunden
        self._last_roi_save = 0.0
        self._roi_save_dir = None

        self._init_mediapipe()

    def _init_mediapipe(self):
        if mp is None:
            self.init_error = "MediaPipe nicht installiert"
            return

        data_dir = os.environ.get("ZUNGENTRAINER_DATA_DIR", "")
        model_path = os.path.join(data_dir, "face_landmarker.task")
        if not os.path.exists(model_path):
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(os.path.dirname(src_dir), "data", "face_landmarker.task")

        if not os.path.exists(model_path):
            self.init_error = f"Modell nicht gefunden: {model_path}"
            return

        try:
            options = vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=model_path),
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=False,
            )
            self._landmarker = vision.FaceLandmarker.create_from_options(options)
        except Exception as e:
            self.init_error = str(e)

    def detect(self, frame: np.ndarray) -> dict:
        result = {
            "face_detected": False,
            "calibrated": self._calibration.state == CalibrationState.DONE,
            "tongue_out": False,
            "confidence": 0.0,
            "tongue_ratio": 0.0,
            "smoothed_score": 0.0,
            "calibration_state": self._calibration.state,
            "debug_roi": None,
            "debug_mask": None,
        }

        if self._landmarker is None:
            return result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms += 33

        try:
            face_result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)
        except Exception:
            return result

        if not face_result.face_landmarks:
            return result

        result["face_detected"] = True
        landmarks = face_result.face_landmarks[0]
        h, w = frame.shape[:2]

        roi, mouth_area, mouth_open = self._extract_mouth_roi(landmarks, frame, h, w)
        if roi is None or roi.size == 0:
            return result

        result["debug_roi"] = roi

        prev_cal_state = self._calibration.state
        if self._calibration.state in (CalibrationState.BASELINE, CalibrationState.TONGUE_PROMPT):
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            self._calibration.feed_frame(hsv_roi, mouth_open)
            result["calibration_state"] = self._calibration.state

            # State-Transition loggen
            if self._calibration.state != prev_cal_state:
                print(f"[Detektor] Kalibrierung: {prev_cal_state.name} -> {self._calibration.state.name}")

            if self._calibration.state == CalibrationState.DONE:
                ranges = self._calibration.get_tongue_hsv_range()
                if ranges:
                    self._hsv_detector.set_tongue_range(ranges["lower"], ranges["upper"])
                result["calibrated"] = True
                # Grace-Period starten: nach Kalibrierung kurz keine Erkennung
                self._grace_frames_remaining = GRACE_PERIOD_FRAMES
                self._score_filter.reset()
                print(f"[Detektor] Kalibrierung abgeschlossen, Grace-Period: {GRACE_PERIOD_FRAMES} Frames")
            return result

        if not result["calibrated"]:
            return result

        # Grace-Period: nach Kalibrierung kurz keine Erkennung
        if self._grace_frames_remaining > 0:
            self._grace_frames_remaining -= 1
            if self._grace_frames_remaining % 10 == 0:
                print(f"[Detektor] Grace-Period: noch {self._grace_frames_remaining} Frames")
            return result

        # Fix 3: Bei geschlossenem Mund HSV-Detektor ueberspringen
        if not mouth_open:
            t = self._timestamp_ms / 1000.0
            self._score_filter.filter(0.0, t)
            result["smoothed_score"] = 0.0
            # Fix 4: Nur alle 30 Frames loggen bei geschlossenem Mund
            if self._frame_count % 30 == 0:
                print(f"[Detektor] ZU score_reset")
            return result

        detection = self._hsv_detector.detect(roi, mouth_area)
        tongue_ratio = detection["tongue_ratio"]
        tongue_tip_y = detection["tongue_tip_y"]
        result["tongue_ratio"] = tongue_ratio
        result["debug_mask"] = detection["mask"]

        raw_score = tongue_ratio
        if tongue_tip_y > TONGUE_TIP_THRESHOLD:
            raw_score *= 1.5

        t = self._timestamp_ms / 1000.0
        smoothed = self._score_filter.filter(raw_score, t)
        result["smoothed_score"] = smoothed

        threshold = TONGUE_RATIO_THRESHOLD / self.sensitivity
        result["tongue_out"] = smoothed > threshold
        result["confidence"] = min(smoothed / threshold, 1.0) if threshold > 0 else 0.0

        # Fix 4: Besseres Logging
        print(f"[Detektor] OFFEN ratio={tongue_ratio:.3f} smooth={smoothed:.3f} "
              f"thr={threshold:.3f} → {'ZUNGE' if result['tongue_out'] else 'ok'}")

        # ROI-Datensammlung
        if self._roi_save_dir:
            now = time.monotonic()
            if now - self._last_roi_save >= self._roi_save_interval:
                self._last_roi_save = now
                self._save_roi(roi, tongue_ratio)

        return result

    def enable_roi_saving(self, save_dir: str):
        """Aktiviert ROI-Datensammlung fuer spaeteres ML."""
        self._roi_save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def disable_roi_saving(self):
        """Deaktiviert ROI-Datensammlung."""
        self._roi_save_dir = None

    def _save_roi(self, roi, score: float):
        """Speichert einen Mund-ROI-Crop mit Score im Dateinamen."""
        timestamp = int(time.time() * 1000)
        score_str = f"{score:.3f}"
        filename = f"roi_{timestamp}_s{score_str}.png"
        path = os.path.join(self._roi_save_dir, filename)
        try:
            cv2.imwrite(path, roi)
        except Exception:
            pass  # Nicht-kritisch, still fehlschlagen

    def _extract_mouth_roi(self, landmarks, frame, h, w):
        outer_pts = np.array([
            [int(landmarks[i].x * w), int(landmarks[i].y * h)]
            for i in OUTER_LIP_INDICES
        ])

        x_min, y_min = outer_pts.min(axis=0)
        x_max, y_max = outer_pts.max(axis=0)
        pad_x = int((x_max - x_min) * 0.2)
        pad_y = int((y_max - y_min) * 0.3)
        x_min = max(0, x_min - pad_x)
        y_min = max(0, y_min - pad_y)
        x_max = min(w, x_max + pad_x)
        y_max = min(h, y_max + pad_y)

        roi = frame[y_min:y_max, x_min:x_max]

        inner_pts = np.array([
            [int(landmarks[i].x * w), int(landmarks[i].y * h)]
            for i in INNER_LIP_INDICES
        ])
        mouth_area = cv2.contourArea(inner_pts)

        face_h = max(1, int(landmarks[152].y * h) - int(landmarks[10].y * h))
        inner_h = inner_pts[:, 1].max() - inner_pts[:, 1].min()
        mouth_open = (inner_h / face_h) > MOUTH_OPEN_THRESHOLD

        # Fix 1: Mindestflaeche — bei zu kleiner Mundoeffnung gilt Mund als geschlossen
        if mouth_area < MIN_MOUTH_AREA:
            mouth_open = False
            mouth_area = 0

        # Fix 5: Diagnostik-Log alle 30 Frames
        self._frame_count += 1
        if self._frame_count % 30 == 0:
            print(f"[Detektor] face_h={face_h} inner_h={inner_h} "
                  f"ratio={inner_h / face_h:.3f} mouth_area={mouth_area:.0f}")

        return roi, mouth_area, mouth_open

    def start_calibration(self):
        self._calibration.start()
        self._score_filter.reset()

    def start_silent_calibration(self):
        self._calibration.start_silent()

    def load_calibration(self, tongue_range: dict):
        if tongue_range:
            self._calibration.load_tongue_range(tongue_range["lower"], tongue_range["upper"])
            self._hsv_detector.set_tongue_range(tongue_range["lower"], tongue_range["upper"])
            self._calibration.state = CalibrationState.DONE

    def reset(self):
        self._score_filter.reset()
        self._frame_count = 0
        self._grace_frames_remaining = 0

    def cleanup(self):
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None
