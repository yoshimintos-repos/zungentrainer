"""Zungenerkennung: MediaPipe Landmarks -> Mund-ROI -> HSV -> Score -> tongue_out."""

import os
import time
import logging
import cv2
import numpy as np

# Log-Datei neben Terminal-Ausgabe
_log = logging.getLogger("zungentrainer.detektor")
if not _log.handlers:
    _log.setLevel(logging.DEBUG)
    _log.addHandler(logging.StreamHandler())  # Terminal
    _data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    _log_dir = os.path.join(_data_home, "zungentrainer")
    os.makedirs(_log_dir, exist_ok=True)
    _fh = logging.FileHandler(os.path.join(_log_dir, "detektor.log"), encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _log.addHandler(_fh)

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
except ImportError:
    mp = None

from detection.calibration import Calibration, CalibrationState
from detection.decision import decision_from_legacy_detection
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

TONGUE_RATIO_THRESHOLD = 0.08
TONGUE_TIP_THRESHOLD = 0.6
MOUTH_OPEN_THRESHOLD = 0.025
GRACE_PERIOD_FRAMES = 30  # ~1 Sekunde nach Kalibrierung keine Erkennung
MIN_MOUTH_AREA = 100  # Pixel² — unter diesem Wert ist der Mund geschlossen


class DetectorService:
    """Erkennt Zungenprotrusion per HSV-Farbanalyse im Mund-ROI."""

    def __init__(self):
        self.init_error: str | None = None
        self._landmarker = None
        self._hsv_detector = HsvDetector()
        self._calibration = Calibration()
        self._score_filter = OneEuroFilter(min_cutoff=1.0, beta=0.02)
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
            "decision": None,
            "debug_roi": None,
            "debug_mask": None,
        }

        if self._landmarker is None:
            result["decision"] = decision_from_legacy_detection(result)
            return result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms += 33

        try:
            face_result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)
        except Exception:
            result["decision"] = decision_from_legacy_detection(result)
            return result

        if not face_result.face_landmarks:
            result["decision"] = decision_from_legacy_detection(result)
            return result

        result["face_detected"] = True
        landmarks = face_result.face_landmarks[0]
        h, w = frame.shape[:2]

        roi, mouth_area, mouth_open = self._extract_mouth_roi(landmarks, frame, h, w)
        if roi is None or roi.size == 0:
            result["decision"] = decision_from_legacy_detection(result)
            return result

        result["debug_roi"] = roi

        prev_cal_state = self._calibration.state
        if self._calibration.state in (CalibrationState.BASELINE, CalibrationState.TONGUE_PROMPT):
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            self._calibration.feed_frame(hsv_roi, mouth_open)
            result["calibration_state"] = self._calibration.state

            # State-Transition loggen
            if self._calibration.state != prev_cal_state:
                _log.info(f"[Detektor] Kalibrierung: {prev_cal_state.name} -> {self._calibration.state.name}")

            if self._calibration.state == CalibrationState.DONE:
                ranges = self._calibration.get_tongue_hsv_range()
                if ranges:
                    self._hsv_detector.set_tongue_range(ranges["lower"], ranges["upper"])
                result["calibrated"] = True
                # Grace-Period starten: nach Kalibrierung kurz keine Erkennung
                self._grace_frames_remaining = GRACE_PERIOD_FRAMES
                self._score_filter.reset()
                _log.info(f"[Detektor] Kalibrierung abgeschlossen, Grace-Period: {GRACE_PERIOD_FRAMES} Frames")
            result["decision"] = decision_from_legacy_detection(result)
            return result

        if not result["calibrated"]:
            result["decision"] = decision_from_legacy_detection(result)
            return result

        # Grace-Period: nach Kalibrierung kurz keine Erkennung
        if self._grace_frames_remaining > 0:
            self._grace_frames_remaining -= 1
            if self._grace_frames_remaining % 10 == 0:
                _log.info(f"[Detektor] Grace-Period: noch {self._grace_frames_remaining} Frames")
            result["decision"] = decision_from_legacy_detection(result)
            return result

        # Fix 3: Bei geschlossenem Mund HSV-Detektor ueberspringen
        if not mouth_open:
            t = self._timestamp_ms / 1000.0
            self._score_filter.filter(0.0, t)
            result["smoothed_score"] = 0.0
            # Fix 4: Nur alle 30 Frames loggen bei geschlossenem Mund
            if self._frame_count % 30 == 0:
                _log.info(f"[Detektor] ZU score_reset")
            result["decision"] = decision_from_legacy_detection(result)
            return result

        # HSV auf dem fokussierten Lippenspalt-ROI
        lip_gap_roi = self._extract_lip_gap_roi(landmarks, frame, h, w)
        if lip_gap_roi is not None and lip_gap_roi.size > 0:
            gap_detection = self._hsv_detector.detect(lip_gap_roi, lip_gap_roi.shape[0] * lip_gap_roi.shape[1])
            gap_ratio = gap_detection["tongue_ratio"]
            result["debug_mask"] = gap_detection["mask"]
        else:
            gap_ratio = 0.0

        result["tongue_ratio"] = gap_ratio

        # Geometrisches Signal: Lip-Bulge
        lip_bulge = self._compute_lip_bulge(landmarks, h)
        bulge_confirmed = lip_bulge > 0.1

        raw_score = gap_ratio
        # Bonus wenn Geometrie bestaetigt
        if bulge_confirmed:
            raw_score *= 1.3

        t = self._timestamp_ms / 1000.0
        smoothed = self._score_filter.filter(raw_score, t)
        result["smoothed_score"] = smoothed

        # Effektiver Threshold: halbiert wenn Lip-Bulge bestaetigt
        threshold = TONGUE_RATIO_THRESHOLD / self.sensitivity
        effective_threshold = threshold * (0.5 if bulge_confirmed else 1.0)

        result["tongue_out"] = smoothed > effective_threshold
        result["confidence"] = min(smoothed / effective_threshold, 1.0) if effective_threshold > 0 else 0.0

        _log.info(f"[Detektor] OFFEN gap={gap_ratio:.3f} bulge={lip_bulge:.3f}{'*' if bulge_confirmed else ''} "
              f"smooth={smoothed:.3f} thr={effective_threshold:.3f} → {'ZUNGE' if result['tongue_out'] else 'ok'}")

        # ROI-Datensammlung
        if self._roi_save_dir:
            now = time.monotonic()
            if now - self._last_roi_save >= self._roi_save_interval:
                self._last_roi_save = now
                self._save_roi(roi, gap_ratio)

        result["decision"] = decision_from_legacy_detection(result)
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
            _log.info(f"[Detektor] face_h={face_h} inner_h={inner_h} "
                  f"ratio={inner_h / face_h:.3f} mouth_area={mouth_area:.0f}")

        return roi, mouth_area, mouth_open

    def _extract_lip_gap_roi(self, landmarks, frame, h, w):
        """Extrahiert nur den schmalen Bereich zwischen den inneren Lippen."""
        upper_center_y = int(landmarks[13].y * h)
        lower_center_y = int(landmarks[14].y * h)

        # Links-Rechts-Ausdehnung der inneren Lippen
        left_x = int(landmarks[78].x * w)
        right_x = int(landmarks[308].x * w)

        # Kleines Padding
        pad = max(3, int((lower_center_y - upper_center_y) * 0.3))

        y_min = max(0, upper_center_y - pad)
        y_max = min(h, lower_center_y + pad)
        x_min = max(0, left_x)
        x_max = min(w, right_x)

        if y_max <= y_min or x_max <= x_min:
            return None

        return frame[y_min:y_max, x_min:x_max]

    def _compute_lip_bulge(self, landmarks, h) -> float:
        """Berechnet wie stark die Lippenmitte weiter offen ist als die Seiten.

        Positiver Wert = Mitte weiter offen (Zunge drueckt Lippen auseinander).
        """
        # Vertikaler Spalt in der Mitte
        center_gap = abs(landmarks[14].y - landmarks[13].y) * h

        # Vertikaler Spalt an den Seiten (Durchschnitt links + rechts)
        left_gap = abs(landmarks[87].y - landmarks[82].y) * h
        right_gap = abs(landmarks[317].y - landmarks[312].y) * h
        side_gap = (left_gap + right_gap) / 2

        # Tongue-Bulge: Mitte weiter offen als Seiten
        lip_bulge = (center_gap - side_gap) / max(1.0, center_gap)
        return lip_bulge

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
