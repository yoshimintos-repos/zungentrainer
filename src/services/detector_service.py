"""MediaPipe FaceLandmarker-basierte Zungen-Erkennung.

Nutzt eine Kombination aus:
1. Face-Blendshapes (jawOpen, mouthClose, mouthLowerDown, mouthUpperUp, mouthShrugLower)
2. Multi-Landmark Mund-Analyse (innere Lippenkontur, Mundbereich-Fläche)
3. Dynamische Baseline-Kalibrierung (passt sich an jedes Gesicht an)
4. Adaptive Glättung (One-Euro-Filter für minimale Latenz bei schneller Reaktion)
5. Laufende Baseline-Adaption (EMA bei Ruhe für Drift-Ausgleich)
"""

import os
import math
import time
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
MIN_FACE_HEIGHT = 0.001      # Minimum normalisierte Gesichtshöhe

# One-Euro-Filter-Parameter
OEF_MIN_CUTOFF = 0.7         # Minimale Cutoff-Frequenz (Hz) — Glättung bei Ruhe
OEF_BETA = 0.007             # Geschwindigkeits-Koeffizient — Reaktion bei Bewegung
OEF_D_CUTOFF = 1.0           # Cutoff für Ableitung

# Baseline-Adaption
BASELINE_EMA_ALPHA = 0.005   # Langsame Anpassung bei Ruhe


class OneEuroFilter:
    """Adaptiver Rauschfilter nach Casiez et al. 2012.

    Glättet stark bei langsamer Bewegung (weniger Fehlalarme),
    reagiert schnell bei schneller Bewegung (weniger Latenz).
    """

    def __init__(self, min_cutoff=OEF_MIN_CUTOFF, beta=OEF_BETA,
                 d_cutoff=OEF_D_CUTOFF):
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    def reset(self):
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    @staticmethod
    def _smoothing_factor(te, cutoff):
        r = 2.0 * math.pi * cutoff * te
        return r / (r + 1.0)

    def __call__(self, x, t=None):
        if t is None:
            t = time.monotonic()

        if self._t_prev is None:
            self._x_prev = x
            self._dx_prev = 0.0
            self._t_prev = t
            return x

        te = t - self._t_prev
        if te <= 0:
            return self._x_prev if self._x_prev is not None else x
        self._t_prev = t

        # Ableitung filtern
        a_d = self._smoothing_factor(te, self._d_cutoff)
        dx = (x - self._x_prev) / te
        dx_hat = a_d * dx + (1.0 - a_d) * self._dx_prev
        self._dx_prev = dx_hat

        # Adaptive Cutoff-Frequenz
        cutoff = self._min_cutoff + self._beta * abs(dx_hat)

        # Signal filtern
        a = self._smoothing_factor(te, cutoff)
        x_hat = a * x + (1.0 - a) * self._x_prev
        self._x_prev = x_hat

        return x_hat


class DetectorService:
    """Erkennt Zungenfehlstellung mittels Multi-Signal-Analyse.

    Die Erkennung kombiniert mehrere Signale zu einem Composite-Score:
    - tongueOut Blendshape: Direktes ML-Signal für Zungenprotrusion (stärkstes Signal)
    - jawOpen Blendshape: Direktes ML-Signal für Kieferöffnung
    - Innere Lippenlücke: Geometrischer Abstand obere/untere Innenlippe
    - Mundöffnungs-Fläche: Fläche der inneren Lippenkontur
    - Unterlippenabsenkung: Wie weit die Unterlippe zum Kinn wandert
    - mouthClose (invertiert): Niedrig wenn Mund offen
    - mouthShrugLower: Aktiviert wenn Zunge gegen Unterlippe drückt

    Dynamische Kalibrierung: Die ersten ~2 Sekunden jeder Sitzung
    messen die Ruhewerte. Danach wird die Abweichung vom Ruhezustand
    als Auslöser verwendet. Laufende Baseline-Adaption gleicht Drift aus.
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

        self._model_path = model_path
        self._init_error: str | None = None

        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"MediaPipe-Modell nicht gefunden: {model_path}"
                )
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1,
                output_face_blendshapes=True,
                min_face_detection_confidence=0.4,
                min_face_presence_confidence=0.4,
                min_tracking_confidence=0.4,
            )
            self._detector = vision.FaceLandmarker.create_from_options(options)
        except Exception as e:
            self._detector = None
            self._init_error = str(e)
            print(f"DetectorService: Initialisierung fehlgeschlagen: {e}")

        self._frame_timestamp_ms = 0

        # Schwellwert-Multiplikator (wird vom Level-System gesetzt)
        # Höher = weniger empfindlich (einfacher)
        # Ein Wert von 2.0 bedeutet: Score muss 2x über Baseline sein
        self._sensitivity_multiplier = 2.5

        # Absoluter Fallback-Schwellwert (ohne Kalibrierung)
        self._absolute_threshold = 0.35

        # Kalibrierung
        self._calibration_buffer: list[float] = []
        self._baseline: float | None = None
        self._calibrated = False

        # One-Euro-Filter für adaptive Glättung
        self._score_filter = OneEuroFilter()

    @property
    def sensitivity_multiplier(self):
        return self._sensitivity_multiplier

    @sensitivity_multiplier.setter
    def sensitivity_multiplier(self, value: float):
        self._sensitivity_multiplier = max(0.5, min(5.0, value))

    def reset_calibration(self):
        """Setzt die Kalibrierung zurück (bei neuem Training-Start).

        WICHTIG: _frame_timestamp_ms wird NICHT zurückgesetzt!
        MediaPipe VIDEO-Modus verlangt monoton steigende Timestamps
        über die gesamte Lebensdauer des Detektors.
        """
        self._calibration_buffer.clear()
        self._baseline = None
        self._calibrated = False
        self._score_filter.reset()

    @property
    def init_error(self) -> str | None:
        """Fehlermeldung wenn die Initialisierung fehlgeschlagen ist."""
        return self._init_error

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
        if self._detector is None:
            return {
                "face_detected": False,
                "score": 0.0,
                "smoothed_score": 0.0,
                "tongue_out": False,
                "calibrated": False,
                "debug": {},
            }

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # VIDEO-Modus: aufsteigende Timestamps erforderlich
        self._frame_timestamp_ms += 33  # ~30 FPS
        result = self._detector.detect_for_video(
            mp_image, self._frame_timestamp_ms
        )

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

        # ── Adaptive Glättung (One-Euro-Filter) ─────────────
        smoothed = self._score_filter(score)

        # ── Entscheidung ────────────────────────────────────
        tongue_out = self._is_tongue_out(smoothed)

        # ── Laufende Baseline-Adaption ──────────────────────
        if self._calibrated and self._baseline is not None and not tongue_out:
            self._baseline = (
                (1.0 - BASELINE_EMA_ALPHA) * self._baseline
                + BASELINE_EMA_ALPHA * score
            )

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
        mouth_shrug_lower = blendshapes.get("mouthShrugLower", 0.0)
        tongue_out_bs = blendshapes.get("tongueOut", 0.0)

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
            "mouth_shrug_lower": mouth_shrug_lower,
            "tongue_out_bs": tongue_out_bs,
        }

    def _compute_score(self, signals: dict) -> float:
        """Berechnet den gewichteten Composite-Score.

        Gewichte basierend auf Signal-Zuverlässigkeit und Diskriminierungskraft:
        - tongue_out_bs: Direktes ML-Signal für Zungenprotrusion (ARKit tongueOut)
        - inner_gap: Sehr zuverlässig, großer Unterschied Ruhe↔Zunge
        - jaw_open: Direkte ML-Schätzung der Kieferöffnung
        - norm_area: Fläche korreliert stark mit Mundöffnung
        - mouth_lower_down: Unterlippe wird durch Zunge nach unten gedrückt
        - mouth_upper_up: Oberlippe hebt sich
        - mouth_close: Invertiert — niedrig wenn Mund offen
        - mouth_shrug_lower: Zunge drückt gegen Unterlippe
        """
        score = (
            signals["tongue_out_bs"] * 8.0
            + signals["inner_gap"] * 5.0
            + signals["jaw_open"] * 3.0
            + signals["norm_area"] * 25.0
            + signals["mouth_lower_down"] * 2.0
            + signals["mouth_upper_up"] * 1.5
            + signals["mouth_stretch"] * 1.0
            + signals["mouth_shrug_lower"] * 2.0
            - signals["mouth_close"] * 2.0
        )
        return max(0.0, score)

    def _finish_calibration(self):
        """Berechnet die Baseline aus dem Kalibrierungspuffer."""
        if not self._calibration_buffer:
            return

        # Korrekter Median: bei gerader Anzahl Durchschnitt der mittleren zwei Werte
        scores = sorted(self._calibration_buffer)
        n = len(scores)
        mid = n // 2
        if n % 2 == 0:
            self._baseline = (scores[mid - 1] + scores[mid]) / 2.0
        else:
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
            threshold = self._baseline + (self._baseline * self._sensitivity_multiplier)
            # Mindest-Schwellwert um Fehlauslösungen bei sehr kleiner Baseline zu vermeiden
            threshold = max(threshold, 0.15)
            return smoothed_score > threshold
        else:
            # Vor Kalibrierung: absoluter Schwellwert
            return smoothed_score > self._absolute_threshold
