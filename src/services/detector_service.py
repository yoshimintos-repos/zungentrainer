"""MediaPipe FaceLandmarker-basierte Zungen-Erkennung.

Nutzt eine Kombination aus:
1. Face-Blendshapes (jawOpen, mouthClose, mouthLowerDown, mouthUpperUp)
2. Multi-Landmark Mund-Analyse (innere Lippenkontur, Mundbereich-Fläche)
3. Dynamische Baseline-Kalibrierung (passt sich an jedes Gesicht an)
4. Zeitliche Glättung (verhindert Flackern)
"""

import os
import collections
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ── Landmark-Indizes ──────────────────────────────────────────────
FOREHEAD = 10
CHIN = 152
UPPER_INNER_LIP_CENTER = 13
LOWER_INNER_LIP_CENTER = 14
UPPER_OUTER_LIP_CENTER = 0
LOWER_OUTER_LIP_CENTER = 17
MOUTH_LEFT = 61
MOUTH_RIGHT = 291

# Innere Lippenkontur (obere Hälfte + untere Hälfte)
INNER_LIP_TOP = [82, 13, 312]
INNER_LIP_BOTTOM = [87, 14, 317]

# Vollständige innere Lippenkontur für Flächenberechnung
INNER_LIP_CONTOUR = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415,
                      308, 324, 318, 402, 317, 14, 87, 178, 88, 95]

# Kalibrierungskonstanten
CALIBRATION_FRAMES = 60      # ~2 Sekunden bei 30 FPS
SMOOTHING_WINDOW = 5         # Frames für zeitliche Glättung
MIN_FACE_HEIGHT = 0.001      # Minimum normalisierte Gesichtshöhe


class DetectorService:
    """Erkennt Zungenfehlstellung mittels Multi-Signal-Analyse.

    Die Erkennung kombiniert mehrere Signale zu einem Composite-Score:
    - jawOpen Blendshape: Direktes ML-Signal für Kieferöffnung
    - Innere Lippenlücke: Geometrischer Abstand obere/untere Innenlippe
    - Mundöffnungs-Fläche: Fläche der inneren Lippenkontur
    - Unterlippenabsenkung: Wie weit die Unterlippe zum Kinn wandert
    - mouthClose (invertiert): Niedrig wenn Mund offen

    Dynamische Kalibrierung: Die ersten ~2 Sekunden jeder Sitzung
    messen die Ruhewerte. Danach wird die Abweichung vom Ruhezustand
    als Auslöser verwendet.
    """

    def __init__(self, model_path: str = None):
        if model_path is None:
            # Zuerst Umgebungsvariable prüfen (Flatpak/installiert)
            data_dir = os.environ.get("ZUNGENTRAINER_DATA_DIR")
            if data_dir is None:
                # Fallback: relativ zum Source-Verzeichnis
                data_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "..", "data",
                )
            model_path = os.path.join(data_dir, "face_landmarker.task")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1,
            output_face_blendshapes=True,
        )
        self._detector = vision.FaceLandmarker.create_from_options(options)

        # Schwellwert-Multiplikator (wird vom Level-System gesetzt)
        # Höher = weniger empfindlich (einfacher)
        # Ein Wert von 2.0 bedeutet: Score muss 2x über Baseline sein
        self._sensitivity_multiplier = 2.5

        # Absoluter Fallback-Schwellwert (ohne Kalibrierung)
        self._absolute_threshold = 0.35

        # Kalibrierung
        self._calibration_buffer: list[dict] = []
        self._baseline: dict | None = None
        self._calibrated = False

        # Zeitliche Glättung
        self._score_history = collections.deque(maxlen=SMOOTHING_WINDOW)

    @property
    def sensitivity_multiplier(self):
        return self._sensitivity_multiplier

    @sensitivity_multiplier.setter
    def sensitivity_multiplier(self, value: float):
        self._sensitivity_multiplier = max(1.2, min(5.0, value))

    def reset_calibration(self):
        """Setzt die Kalibrierung zurück (bei neuem Training-Start)."""
        self._calibration_buffer.clear()
        self._baseline = None
        self._calibrated = False
        self._score_history.clear()

    def detect(self, frame: np.ndarray) -> dict:
        """Analysiert einen BGR-Frame.

        Returns:
            dict mit:
                - face_detected: bool
                - score: float (Composite-Score, 0.0 wenn kein Gesicht)
                - smoothed_score: float (geglätteter Score)
                - tongue_out: bool
                - calibrated: bool
                - debug: dict (Detail-Werte für UI-Anzeige)
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self._detector.detect(mp_image)

        no_face = {
            "face_detected": False,
            "score": 0.0,
            "smoothed_score": 0.0,
            "tongue_out": False,
            "calibrated": self._calibrated,
            "debug": {},
        }

        if not result.face_landmarks:
            return no_face

        landmarks = result.face_landmarks[0]
        blendshapes = {}
        if result.face_blendshapes:
            blendshapes = {
                s.category_name: s.score
                for s in result.face_blendshapes[0]
            }

        # ── Signale extrahieren ─────────────────────────────
        signals = self._extract_signals(landmarks, blendshapes)
        if signals is None:
            return no_face

        # ── Composite-Score berechnen ───────────────────────
        score = self._compute_score(signals)

        # ── Kalibrierung ────────────────────────────────────
        if not self._calibrated:
            self._calibration_buffer.append(score)
            if len(self._calibration_buffer) >= CALIBRATION_FRAMES:
                self._finish_calibration()

        # ── Zeitliche Glättung ──────────────────────────────
        self._score_history.append(score)
        smoothed = sum(self._score_history) / len(self._score_history)

        # ── Entscheidung ────────────────────────────────────
        tongue_out = self._is_tongue_out(smoothed)

        return {
            "face_detected": True,
            "score": score,
            "smoothed_score": smoothed,
            "tongue_out": tongue_out,
            "calibrated": self._calibrated,
            "debug": signals,
        }

    def _extract_signals(self, landmarks, blendshapes: dict) -> dict | None:
        """Extrahiert alle Erkennungssignale aus Landmarks und Blendshapes."""
        forehead = landmarks[FOREHEAD]
        chin = landmarks[CHIN]
        face_h = abs(chin.y - forehead.y)

        if face_h < MIN_FACE_HEIGHT:
            return None

        # 1. Innere Lippenlücke (Durchschnitt aus 3 Punktpaaren)
        top_y = sum(landmarks[i].y for i in INNER_LIP_TOP) / len(INNER_LIP_TOP)
        bot_y = sum(landmarks[i].y for i in INNER_LIP_BOTTOM) / len(INNER_LIP_BOTTOM)
        inner_gap = abs(bot_y - top_y) / face_h

        # 2. Äußere Lippenlücke
        outer_gap = abs(
            landmarks[LOWER_OUTER_LIP_CENTER].y -
            landmarks[UPPER_OUTER_LIP_CENTER].y
        ) / face_h

        # 3. Innere Mundfläche (Shoelace-Formel)
        pts = [landmarks[i] for i in INNER_LIP_CONTOUR]
        area = 0.0
        n = len(pts)
        for j in range(n):
            k = (j + 1) % n
            area += pts[j].x * pts[k].y
            area -= pts[k].x * pts[j].y
        norm_area = abs(area) / 2.0 / (face_h * face_h)

        # 4. Unterlippenabstand zum Kinn (kleiner = Lippe weiter unten)
        lip_chin = abs(chin.y - landmarks[LOWER_INNER_LIP_CENTER].y) / face_h

        # 5. Mundbreite
        mouth_w = abs(
            landmarks[MOUTH_RIGHT].x - landmarks[MOUTH_LEFT].x
        )
        # Mund-Aspektverhältnis (vertikal / horizontal)
        mouth_aspect = inner_gap / (mouth_w / face_h) if mouth_w > 0 else 0

        # 6. Blendshapes
        jaw_open = blendshapes.get("jawOpen", 0.0)
        mouth_close = blendshapes.get("mouthClose", 0.0)
        mouth_lower_down = (
            blendshapes.get("mouthLowerDownLeft", 0.0) +
            blendshapes.get("mouthLowerDownRight", 0.0)
        ) / 2.0
        mouth_upper_up = (
            blendshapes.get("mouthUpperUpLeft", 0.0) +
            blendshapes.get("mouthUpperUpRight", 0.0)
        ) / 2.0
        mouth_stretch = (
            blendshapes.get("mouthStretchLeft", 0.0) +
            blendshapes.get("mouthStretchRight", 0.0)
        ) / 2.0

        return {
            "inner_gap": inner_gap,
            "outer_gap": outer_gap,
            "norm_area": norm_area,
            "lip_chin": lip_chin,
            "mouth_aspect": mouth_aspect,
            "jaw_open": jaw_open,
            "mouth_close": mouth_close,
            "mouth_lower_down": mouth_lower_down,
            "mouth_upper_up": mouth_upper_up,
            "mouth_stretch": mouth_stretch,
        }

    def _compute_score(self, signals: dict) -> float:
        """Berechnet den gewichteten Composite-Score.

        Gewichte basierend auf Signal-Zuverlässigkeit und Diskriminierungskraft:
        - inner_gap: Sehr zuverlässig, großer Unterschied Ruhe↔Zunge
        - jaw_open: Direkte ML-Schätzung der Kieferöffnung
        - norm_area: Fläche korreliert stark mit Mundöffnung
        - mouth_lower_down: Unterlippe wird durch Zunge nach unten gedrückt
        - mouth_upper_up: Oberlippe hebt sich
        - mouth_close: Invertiert — niedrig wenn Mund offen
        """
        score = (
            signals["inner_gap"] * 5.0
            + signals["jaw_open"] * 3.0
            + signals["norm_area"] * 25.0
            + signals["mouth_lower_down"] * 2.0
            + signals["mouth_upper_up"] * 1.5
            + signals["mouth_stretch"] * 1.0
            - signals["mouth_close"] * 2.0
        )
        return max(0.0, score)

    def _finish_calibration(self):
        """Berechnet die Baseline aus dem Kalibrierungspuffer."""
        if not self._calibration_buffer:
            return

        # Median statt Mittelwert für Robustheit gegen Ausreißer
        scores = sorted(self._calibration_buffer)
        mid = len(scores) // 2
        self._baseline = scores[mid]
        self._calibrated = True

    def cleanup(self):
        """Gibt MediaPipe-Ressourcen frei."""
        if self._detector:
            self._detector.close()
            self._detector = None

    def _is_tongue_out(self, smoothed_score: float) -> bool:
        """Entscheidet ob die Zunge draußen ist."""
        if self._calibrated and self._baseline is not None:
            # Kalibrierter Modus: Score muss deutlich über Baseline liegen
            # Baseline + (Baseline * Multiplikator) = Schwellwert
            # Bei Ruhewert ~0.16 und Multiplikator 2.5: Schwelle ≈ 0.56
            threshold = self._baseline + (self._baseline * self._sensitivity_multiplier)
            # Mindest-Schwellwert um Fehlauslösungen bei sehr kleiner Baseline zu vermeiden
            threshold = max(threshold, 0.20)
            return smoothed_score > threshold
        else:
            # Vor Kalibrierung: absoluter Schwellwert
            return smoothed_score > self._absolute_threshold
