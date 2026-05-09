# ZungenTrainer v2 — Phase 1+2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Funktionsfaehige Trainings-App mit HSV-basierter Zungenerkennung, Session-Management, Mediensteuerung und adaptiver Schwierigkeit.

**Architecture:** Window-Mediator-Pattern (bewaehrt aus alter App). CameraService als Daemon-Thread, alles andere auf GTK-Main-Thread. Neue HSV-Erkennung statt Blendshape-Ansatz. Vereinfachte Zustandsmaschine (kein WARNING-Zwischenschritt). Alte App (`old_apps/zungentrainer/`) dient als Code-Quelle fuer bewaehrte Services.

**Tech Stack:** Python 3.13+, GTK 4.0, Libadwaita 1, OpenCV (headless), MediaPipe (>=0.10.30), NumPy, GStreamer 1.0, GLib/Gio (D-Bus MPRIS2)

**Referenzen:**
- Design-Spec: `docs/superpowers/specs/2026-04-09-zungentrainer-v2-design.md`
- Alte App (Code-Quelle): `old_apps/zungentrainer/src/`
- HIG-Review-Skill: `skills/gnome-hig-review/`

---

## Dateistruktur

```
zungentrainer/
├── bin/zungentrainer              # Flatpak/lokaler Launcher
├── run.sh                         # Lokaler Schnellstart
├── data/
│   └── face_landmarker.task       # MediaPipe-Modell (~4MB)
├── src/
│   ├── main.py                    # Adw.Application Entry Point
│   ├── window.py                  # Mediator: DataStore, Profile, AdaptiveDifficulty, MilestoneSystem
│   ├── models/
│   │   ├── user_data.py           # UserProfile, SessionRecord, Milestone (Dataclasses)
│   │   └── persistence.py         # DataStore: JSON load/save, Schema-Versionierung
│   ├── services/
│   │   ├── camera_service.py      # Threaded OpenCV Capture (1080p)
│   │   ├── detector_service.py    # MediaPipe Landmarks -> HSV -> tongue_out (NEU)
│   │   ├── session_service.py     # Zustandsmaschine IDLE->RUNNING->DETECTED->COOLDOWN
│   │   ├── sound_service.py       # GStreamer Piepton
│   │   └── mpris_service.py       # D-Bus MPRIS2 Mediensteuerung
│   ├── detection/
│   │   ├── hsv_detector.py        # HSV-Farbsegmentierung im Mund-ROI (NEU)
│   │   ├── calibration.py         # Baseline + Zungenfarbe Kalibrierung (NEU)
│   │   └── one_euro_filter.py     # Adaptive Signal-Glaettung (NEU)
│   ├── systems/
│   │   ├── adaptive_difficulty.py # Flow-Zone Algorithmus (NEU)
│   │   └── milestone_system.py    # Einfache Achievements (NEU)
│   ├── pages/
│   │   ├── training_page.py       # Kamera + OSD + Session-Steuerung
│   │   ├── progress_page.py       # Wochenstatistiken + Meilensteine (NEU)
│   │   └── settings_page.py       # AdwPreferencesPage + Eltern-Bereich
│   └── utils/
│       └── camera_paintable.py    # Gdk.Paintable fuer OpenCV Frames
└── tests/
    ├── test_one_euro_filter.py
    ├── test_hsv_detector.py
    ├── test_calibration.py
    ├── test_session_service.py
    ├── test_adaptive_difficulty.py
    ├── test_milestone_system.py
    └── test_user_data.py
```

---

## PHASE 1: Erkennungs-Pipeline (Standalone)

### Task 1: Projekt-Grundstruktur + Git

**Files:**
- Create: `run.sh`, `bin/zungentrainer`, `src/main.py`, `.gitignore`

- [ ] **Step 1: Git-Repo initialisieren**

```bash
cd /home/yoshimintos/Projekte/ClaudeCode/zungentrainer
git init
git remote add origin git@github.com:yoshimintos-repos/zungentrainer.git
```

- [ ] **Step 2: .gitignore erstellen**

```gitignore
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.flatpak-builder/
*.flatpak
data/face_landmarker.task
.repo/
```

- [ ] **Step 3: Verzeichnisstruktur anlegen**

```bash
mkdir -p src/{models,services,detection,systems,pages,utils} tests data bin
```

- [ ] **Step 4: run.sh von alter App kopieren und anpassen**

Lies `old_apps/zungentrainer/run.sh` und kopiere nach `run.sh`. Inhalt ist identisch:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export ZUNGENTRAINER_DATA_DIR="$SCRIPT_DIR/data"
exec python3 "$SCRIPT_DIR/src/main.py" "$@"
```

```bash
chmod +x run.sh
```

- [ ] **Step 5: bin/zungentrainer von alter App kopieren**

Lies `old_apps/zungentrainer/bin/zungentrainer` und kopiere identisch nach `bin/zungentrainer`.

```bash
chmod +x bin/zungentrainer
```

- [ ] **Step 6: Minimales main.py als Platzhalter**

```python
#!/usr/bin/env python3
"""ZungenTrainer v2 — Zungen-Haltungstrainer mit Webcam-Erkennung."""

import sys
import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Adw, Gio, Gst

Gst.init(None)

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class ZungenTrainerApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="de.yoshimintos.ZungenTrainer",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = Adw.ApplicationWindow(application=self)
            win.set_title("ZungenTrainer")
            win.set_default_size(480, 700)
            label = Gtk.Label(label="ZungenTrainer v2 — Platzhalter")
            win.set_content(label)
        win.present()


def main():
    app = ZungenTrainerApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 7: Testen und committen**

```bash
./run.sh  # Fenster mit Platzhalter-Text sollte erscheinen
```

```bash
git add .gitignore run.sh bin/zungentrainer src/main.py
git commit -m "feat: Projekt-Grundstruktur mit GTK4/Libadwaita Skeleton"
```

---

### Task 2: One-Euro-Filter

**Files:**
- Create: `src/detection/one_euro_filter.py`
- Test: `tests/test_one_euro_filter.py`

- [ ] **Step 1: Failing Test schreiben**

```python
# tests/test_one_euro_filter.py
"""Tests fuer den One-Euro-Filter (adaptive Signalglaettung)."""

import pytest
from detection.one_euro_filter import OneEuroFilter


def test_initial_value_passthrough():
    """Erster Wert wird direkt durchgereicht."""
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    result = f.filter(5.0, timestamp=0.0)
    assert result == 5.0


def test_smoothing_reduces_noise():
    """Filter glaettet verrauschte Signale."""
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    f.filter(0.0, timestamp=0.0)
    # Sprung von 0 auf 10 — gefilterter Wert sollte dazwischen liegen
    result = f.filter(10.0, timestamp=0.033)
    assert 0.0 < result < 10.0


def test_high_beta_tracks_fast_changes():
    """Hoher beta-Wert folgt schnellen Aenderungen besser."""
    slow = OneEuroFilter(min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    fast = OneEuroFilter(min_cutoff=1.0, beta=10.0, d_cutoff=1.0)

    slow.filter(0.0, timestamp=0.0)
    fast.filter(0.0, timestamp=0.0)

    slow_result = slow.filter(10.0, timestamp=0.033)
    fast_result = fast.filter(10.0, timestamp=0.033)

    # Hoher beta = naeher am tatsaechlichen Wert
    assert fast_result > slow_result


def test_reset_clears_state():
    """Nach Reset verhält sich der Filter wie neu."""
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    f.filter(100.0, timestamp=0.0)
    f.filter(100.0, timestamp=0.033)
    f.reset()
    result = f.filter(5.0, timestamp=1.0)
    assert result == 5.0
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

```bash
cd /home/yoshimintos/Projekte/ClaudeCode/zungentrainer
PYTHONPATH=src python3 -m pytest tests/test_one_euro_filter.py -v
```

Expected: ModuleNotFoundError

- [ ] **Step 3: One-Euro-Filter implementieren**

```python
# src/detection/one_euro_filter.py
"""One-Euro-Filter: Adaptive Signalglaettung.

Glaettet stark bei Ruhe (weniger Fehlalarme) und reagiert schnell bei
Bewegung (niedrige Latenz). Ideal fuer Echtzeit-Score-Glaettung.

Referenz: Casiez et al., "1€ Filter: A Simple Speed-based Low-pass Filter
for Noisy Input in Interactive Systems", CHI 2012.
"""

import math


class OneEuroFilter:
    """Adaptiver Low-Pass-Filter mit geschwindigkeitsabhaengiger Cutoff-Frequenz."""

    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.007,
                 d_cutoff: float = 1.0):
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    def filter(self, x: float, timestamp: float) -> float:
        """Filtert einen neuen Wert. Gibt den geglaetteten Wert zurueck."""
        if self._t_prev is None:
            self._x_prev = x
            self._t_prev = timestamp
            self._dx_prev = 0.0
            return x

        dt = timestamp - self._t_prev
        if dt <= 0:
            return self._x_prev

        # Ableitung schaetzen und glaetten
        dx = (x - self._x_prev) / dt
        alpha_d = self._smoothing_factor(dt, self._d_cutoff)
        dx_hat = alpha_d * dx + (1 - alpha_d) * self._dx_prev

        # Adaptive Cutoff-Frequenz
        cutoff = self._min_cutoff + self._beta * abs(dx_hat)

        # Signal glaetten
        alpha = self._smoothing_factor(dt, cutoff)
        x_hat = alpha * x + (1 - alpha) * self._x_prev

        self._x_prev = x_hat
        self._dx_prev = dx_hat
        self._t_prev = timestamp
        return x_hat

    def reset(self):
        """Setzt den Filter-Zustand zurueck."""
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    @staticmethod
    def _smoothing_factor(dt: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)
```

Erstelle auch `src/detection/__init__.py` (leer).

- [ ] **Step 4: Tests ausfuehren — muessen bestehen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_one_euro_filter.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/detection/ tests/test_one_euro_filter.py
git commit -m "feat: One-Euro-Filter fuer adaptive Score-Glaettung"
```

---

### Task 3: Kalibrierung

**Files:**
- Create: `src/detection/calibration.py`
- Test: `tests/test_calibration.py`

- [ ] **Step 1: Failing Test schreiben**

```python
# tests/test_calibration.py
"""Tests fuer die Kalibrierung (Baseline + Zungenfarbe)."""

import numpy as np
import pytest
from detection.calibration import Calibration, CalibrationState


def _make_hsv_roi(h: int, s: int, v: int, size: int = 50) -> np.ndarray:
    """Erzeugt ein einfarbiges HSV-Bild."""
    roi = np.zeros((size, size, 3), dtype=np.uint8)
    roi[:, :, 0] = h
    roi[:, :, 1] = s
    roi[:, :, 2] = v
    return roi


def test_initial_state_is_idle():
    cal = Calibration()
    assert cal.state == CalibrationState.IDLE


def test_start_begins_baseline():
    cal = Calibration()
    cal.start()
    assert cal.state == CalibrationState.BASELINE


def test_baseline_collects_frames():
    """Nach genug Frames wechselt Baseline zu TONGUE_PROMPT."""
    cal = Calibration(baseline_frames=5)
    cal.start()
    roi = _make_hsv_roi(10, 100, 150)
    for _ in range(5):
        cal.feed_frame(roi, mouth_open=False)
    assert cal.state == CalibrationState.TONGUE_PROMPT


def test_tongue_phase_collects_and_completes():
    """Nach genug Zungenfarbe-Frames ist Kalibrierung fertig."""
    cal = Calibration(baseline_frames=3, tongue_frames=3)
    cal.start()
    lip_roi = _make_hsv_roi(10, 100, 150)
    for _ in range(3):
        cal.feed_frame(lip_roi, mouth_open=False)
    assert cal.state == CalibrationState.TONGUE_PROMPT

    tongue_roi = _make_hsv_roi(0, 180, 200)
    for _ in range(3):
        cal.feed_frame(tongue_roi, mouth_open=True)
    assert cal.state == CalibrationState.DONE


def test_done_provides_ranges():
    """Nach Abschluss sind HSV-Ranges verfuegbar."""
    cal = Calibration(baseline_frames=3, tongue_frames=3)
    cal.start()
    lip_roi = _make_hsv_roi(10, 100, 150)
    for _ in range(3):
        cal.feed_frame(lip_roi, mouth_open=False)
    tongue_roi = _make_hsv_roi(0, 180, 200)
    for _ in range(3):
        cal.feed_frame(tongue_roi, mouth_open=True)

    ranges = cal.get_tongue_hsv_range()
    assert ranges is not None
    assert "lower" in ranges and "upper" in ranges
    assert len(ranges["lower"]) == 3
    assert len(ranges["upper"]) == 3


def test_silent_recalibration():
    """Stille Rekalibrierung aktualisiert nur Baseline, nicht Zungenfarbe."""
    cal = Calibration(baseline_frames=3, tongue_frames=3)
    cal.start()
    lip_roi = _make_hsv_roi(10, 100, 150)
    for _ in range(3):
        cal.feed_frame(lip_roi, mouth_open=False)
    tongue_roi = _make_hsv_roi(0, 180, 200)
    for _ in range(3):
        cal.feed_frame(tongue_roi, mouth_open=True)

    old_ranges = cal.get_tongue_hsv_range()

    # Stille Rekalibrierung mit anderem Licht
    cal.start_silent(baseline_frames=3)
    new_lip = _make_hsv_roi(15, 90, 140)
    for _ in range(3):
        cal.feed_frame(new_lip, mouth_open=False)

    assert cal.state == CalibrationState.DONE
    # Zungenfarbe unveraendert
    assert cal.get_tongue_hsv_range() == old_ranges
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_calibration.py -v
```

- [ ] **Step 3: Kalibrierung implementieren**

```python
# src/detection/calibration.py
"""Kalibrierung: Baseline-Lippen + Zungenfarbe erfassen.

Zwei Modi:
- Interaktiv (erster Start): BASELINE -> TONGUE_PROMPT -> DONE
- Still (Folge-Sessions): nur BASELINE neu erfassen, Zungenfarbe aus Profil
"""

from enum import Enum, auto
import numpy as np
import cv2


class CalibrationState(Enum):
    IDLE = auto()
    BASELINE = auto()
    TONGUE_PROMPT = auto()
    DONE = auto()


class Calibration:
    """Erfasst personalisierte HSV-Ranges fuer Lippen und Zunge."""

    def __init__(self, baseline_frames: int = 60, tongue_frames: int = 60):
        self._baseline_target = baseline_frames
        self._tongue_target = tongue_frames
        self.state = CalibrationState.IDLE

        self._baseline_samples: list[np.ndarray] = []
        self._tongue_samples: list[np.ndarray] = []

        self._lip_hsv_mean: np.ndarray | None = None
        self._lip_hsv_std: np.ndarray | None = None
        self._tongue_hsv_lower: np.ndarray | None = None
        self._tongue_hsv_upper: np.ndarray | None = None

    def start(self):
        """Startet interaktive Kalibrierung (Baseline + Zunge)."""
        self._baseline_samples.clear()
        self._tongue_samples.clear()
        self.state = CalibrationState.BASELINE

    def start_silent(self, baseline_frames: int = 60):
        """Startet stille Rekalibrierung (nur Baseline, Zunge bleibt)."""
        self._baseline_samples.clear()
        self._baseline_target_silent = baseline_frames
        self.state = CalibrationState.BASELINE
        self._silent_mode = True

    def feed_frame(self, hsv_roi: np.ndarray, mouth_open: bool):
        """Fuettert einen Frame in die Kalibrierung.

        Args:
            hsv_roi: Mund-ROI bereits in HSV konvertiert.
            mouth_open: Ob der Mund geoeffnet ist (fuer Zungenphase).
        """
        if self.state == CalibrationState.BASELINE:
            self._baseline_samples.append(hsv_roi.copy())
            target = getattr(self, "_baseline_target_silent", self._baseline_target)
            if len(self._baseline_samples) >= target:
                self._compute_baseline()
                if getattr(self, "_silent_mode", False):
                    self.state = CalibrationState.DONE
                    self._silent_mode = False
                else:
                    self.state = CalibrationState.TONGUE_PROMPT

        elif self.state == CalibrationState.TONGUE_PROMPT:
            self._tongue_samples.append(hsv_roi.copy())
            if len(self._tongue_samples) >= self._tongue_target:
                self._compute_tongue_range()
                self.state = CalibrationState.DONE

    def _compute_baseline(self):
        """Berechnet Lippen-HSV Statistiken aus Baseline-Samples."""
        all_pixels = np.concatenate(
            [s.reshape(-1, 3) for s in self._baseline_samples], axis=0
        )
        self._lip_hsv_mean = np.mean(all_pixels, axis=0).astype(np.float32)
        self._lip_hsv_std = np.std(all_pixels, axis=0).astype(np.float32)

    def _compute_tongue_range(self):
        """Berechnet Zungen-HSV-Range aus Zungenfarbe-Samples.

        Range = Median ± 2*MAD pro Kanal, mit Mindest-Spread.
        """
        all_pixels = np.concatenate(
            [s.reshape(-1, 3) for s in self._tongue_samples], axis=0
        )
        median = np.median(all_pixels, axis=0)
        mad = np.median(np.abs(all_pixels - median), axis=0)
        spread = np.maximum(mad * 2, np.array([8, 30, 30]))

        self._tongue_hsv_lower = np.clip(median - spread, 0, 255).astype(np.uint8)
        self._tongue_hsv_upper = np.clip(median + spread, 0, 255).astype(np.uint8)

    def get_tongue_hsv_range(self) -> dict | None:
        """Gibt kalibrierte HSV-Range fuer Zungenerkennung zurueck."""
        if self._tongue_hsv_lower is None:
            return None
        return {
            "lower": self._tongue_hsv_lower.tolist(),
            "upper": self._tongue_hsv_upper.tolist(),
        }

    def get_lip_stats(self) -> dict | None:
        """Gibt Lippen-HSV-Statistiken zurueck."""
        if self._lip_hsv_mean is None:
            return None
        return {
            "mean": self._lip_hsv_mean.tolist(),
            "std": self._lip_hsv_std.tolist(),
        }

    def load_tongue_range(self, lower: list[int], upper: list[int]):
        """Laedt gespeicherte Zungen-HSV-Range (fuer Folge-Sessions)."""
        self._tongue_hsv_lower = np.array(lower, dtype=np.uint8)
        self._tongue_hsv_upper = np.array(upper, dtype=np.uint8)
```

- [ ] **Step 4: Tests ausfuehren — muessen bestehen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_calibration.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/detection/calibration.py tests/test_calibration.py
git commit -m "feat: Kalibrierung (Baseline + Zungenfarbe HSV-Ranges)"
```

---

### Task 4: HSV-Detektor

**Files:**
- Create: `src/detection/hsv_detector.py`
- Test: `tests/test_hsv_detector.py`

- [ ] **Step 1: Failing Test schreiben**

```python
# tests/test_hsv_detector.py
"""Tests fuer HSV-basierte Zungenerkennung im Mund-ROI."""

import numpy as np
import cv2
import pytest
from detection.hsv_detector import HsvDetector


def _make_bgr_roi(h: int, s: int, v: int, size: int = 100) -> np.ndarray:
    """Erzeugt ein einfarbiges BGR-Bild aus HSV-Werten."""
    hsv = np.zeros((size, size, 3), dtype=np.uint8)
    hsv[:, :] = [h, s, v]
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def test_no_tongue_returns_zero():
    """Lippen-farbiger ROI ohne Zunge ergibt Score ~0."""
    det = HsvDetector()
    # Kalibrierte Range: Zunge ist rot (H=0, S=180, V=200)
    det.set_tongue_range([0, 150, 170], [10, 210, 230])

    # Lippen-farbiger ROI (H=15, S=100, V=150) — kein Rot
    lip_roi = _make_bgr_roi(15, 100, 150)
    result = det.detect(lip_roi, mouth_area=100 * 100)
    assert result["tongue_ratio"] < 0.05


def test_tongue_returns_high_score():
    """ROI mit Zungenfarbe ergibt hohen Score."""
    det = HsvDetector()
    det.set_tongue_range([0, 150, 170], [10, 210, 230])

    # ROI komplett in Zungenfarbe
    tongue_roi = _make_bgr_roi(5, 180, 200)
    result = det.detect(tongue_roi, mouth_area=100 * 100)
    assert result["tongue_ratio"] > 0.5


def test_mixed_roi_partial_score():
    """ROI mit Teilbereich Zungenfarbe ergibt mittleren Score."""
    det = HsvDetector()
    det.set_tongue_range([0, 150, 170], [10, 210, 230])

    # Obere Haelfte Lippen, untere Haelfte Zunge
    lip_part = _make_bgr_roi(15, 100, 150, size=50)
    tongue_part = _make_bgr_roi(5, 180, 200, size=50)
    roi = np.vstack([lip_part, tongue_part])

    result = det.detect(roi, mouth_area=100 * 50)
    assert 0.2 < result["tongue_ratio"] < 0.8


def test_detect_without_calibration_returns_zero():
    """Ohne Kalibrierung ist tongue_ratio immer 0."""
    det = HsvDetector()
    roi = _make_bgr_roi(5, 180, 200)
    result = det.detect(roi, mouth_area=100 * 100)
    assert result["tongue_ratio"] == 0.0
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_hsv_detector.py -v
```

- [ ] **Step 3: HSV-Detektor implementieren**

```python
# src/detection/hsv_detector.py
"""HSV-Farbsegmentierung zur Zungenerkennung im Mund-ROI.

Pipeline: BGR -> CLAHE -> HSV -> Maske -> Morphologie -> Kontur -> Score.
"""

import cv2
import numpy as np


class HsvDetector:
    """Erkennt Zungenfarbe im Mund-ROI mittels HSV-Segmentierung."""

    def __init__(self):
        self._tongue_lower: np.ndarray | None = None
        self._tongue_upper: np.ndarray | None = None
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        # Morphologie-Kernel
        self._kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    def set_tongue_range(self, lower: list[int], upper: list[int]):
        """Setzt kalibrierte HSV-Range fuer Zungenfarbe."""
        self._tongue_lower = np.array(lower, dtype=np.uint8)
        self._tongue_upper = np.array(upper, dtype=np.uint8)

    def detect(self, bgr_roi: np.ndarray, mouth_area: float) -> dict:
        """Erkennt Zunge im BGR Mund-ROI.

        Args:
            bgr_roi: Ausgeschnittener Mund-Bereich in BGR.
            mouth_area: Flaeche der Mundoeffnung in Pixeln (fuer Normalisierung).

        Returns:
            dict mit tongue_ratio (0.0-1.0) und tongue_tip_y (relative Position).
        """
        if self._tongue_lower is None or mouth_area <= 0:
            return {"tongue_ratio": 0.0, "tongue_tip_y": 0.0, "mask": None}

        # CLAHE auf L-Kanal (Helligkeitsanpassung)
        lab = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = self._clahe.apply(lab[:, :, 0])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # HSV-Konvertierung
        hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)

        # Zungen-Maske erstellen
        # Spezialbehandlung fuer Rot-Wrap-Around im H-Kanal
        if self._tongue_lower[0] > self._tongue_upper[0]:
            mask1 = cv2.inRange(
                hsv,
                np.array([self._tongue_lower[0], self._tongue_lower[1], self._tongue_lower[2]]),
                np.array([179, self._tongue_upper[1], self._tongue_upper[2]]),
            )
            mask2 = cv2.inRange(
                hsv,
                np.array([0, self._tongue_lower[1], self._tongue_lower[2]]),
                self._tongue_upper,
            )
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv, self._tongue_lower, self._tongue_upper)

        # Morphologie: Rauschen entfernen
        mask = cv2.erode(mask, self._kernel, iterations=1)
        mask = cv2.dilate(mask, self._kernel, iterations=2)

        # Groesste Kontur finden
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {"tongue_ratio": 0.0, "tongue_tip_y": 0.0, "mask": mask}

        largest = max(contours, key=cv2.contourArea)
        tongue_area = cv2.contourArea(largest)
        tongue_ratio = tongue_area / mouth_area

        # Zungenspitze: unterster Punkt der Kontur relativ zur ROI-Hoehe
        h = bgr_roi.shape[0]
        bottommost = max(largest, key=lambda p: p[0][1])
        tongue_tip_y = bottommost[0][1] / h if h > 0 else 0.0

        return {
            "tongue_ratio": float(tongue_ratio),
            "tongue_tip_y": float(tongue_tip_y),
            "mask": mask,
        }
```

- [ ] **Step 4: Tests ausfuehren — muessen bestehen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_hsv_detector.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/detection/hsv_detector.py tests/test_hsv_detector.py
git commit -m "feat: HSV-Farbsegmentierung fuer Zungenerkennung im Mund-ROI"
```

---

### Task 5: CameraService (von alter App, 1080p)

**Files:**
- Create: `src/services/camera_service.py`, `src/services/__init__.py`

- [ ] **Step 1: CameraService von alter App kopieren**

Lies `old_apps/zungentrainer/src/services/camera_service.py` und kopiere nach `src/services/camera_service.py`. Erstelle leere `src/services/__init__.py`.

- [ ] **Step 2: Aufloesung auf 1080p aendern**

Aendere in `_capture_loop` die Zeilen:

```python
# ALT:
self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# NEU:
self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
```

- [ ] **Step 3: Commit**

```bash
git add src/services/
git commit -m "feat: CameraService mit 1080p (von alter App portiert)"
```

---

### Task 6: DetectorService (MediaPipe + HSV-Pipeline)

**Files:**
- Create: `src/services/detector_service.py`

Der DetectorService ist die zentrale Integrationsklasse: MediaPipe Landmarks -> Mund-ROI -> Kalibrierung/HSV-Detektion -> One-Euro-Filter -> tongue_out.

- [ ] **Step 1: MediaPipe-Modell bereitstellen**

```bash
# face_landmarker.task herunterladen (falls noch nicht vorhanden)
cd /home/yoshimintos/Projekte/ClaudeCode/zungentrainer
wget -O data/face_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
```

- [ ] **Step 2: DetectorService implementieren**

```python
# src/services/detector_service.py
"""Zungenerkennung: MediaPipe Landmarks -> Mund-ROI -> HSV -> Score -> tongue_out.

Integriert MediaPipe FaceLandmarker (VIDEO-Modus), Kalibrierung,
HSV-Farbsegmentierung, One-Euro-Filter und Entscheidungslogik.
"""

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
# Aeussere Lippen-Kontur
OUTER_LIP_INDICES = [
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291,
    409, 270, 269, 267, 0, 37, 39, 40, 185,
]
# Innere Lippen (fuer Mundoeffnungsflaeche)
INNER_LIP_INDICES = [
    78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308,
    415, 310, 311, 312, 13, 82, 81, 80, 191,
]

# Schwellwerte
TONGUE_RATIO_THRESHOLD = 0.08  # Mindest-Zungenflaeche relativ zur Mundoeffnung
TONGUE_TIP_THRESHOLD = 0.6     # Zungenspitze muss unterhalb 60% der ROI-Hoehe sein
MOUTH_OPEN_THRESHOLD = 0.02    # Mindest-Mundoeffnung (relativ zur Gesichtshoehe)


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
        self.sensitivity = 1.0  # Multiplikator fuer Schwellwert

        self._init_mediapipe()

    def _init_mediapipe(self):
        """Initialisiert MediaPipe FaceLandmarker."""
        if mp is None:
            self.init_error = "MediaPipe nicht installiert"
            return

        data_dir = os.environ.get("ZUNGENTRAINER_DATA_DIR", "")
        model_path = os.path.join(data_dir, "face_landmarker.task")
        if not os.path.exists(model_path):
            # Fallback: relativ zum src-Verzeichnis
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
        """Erkennt Zunge in einem BGR-Frame.

        Returns:
            dict mit: face_detected, calibrated, tongue_out, confidence,
                      tongue_ratio, calibration_state
        """
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

        # MediaPipe braucht RGB + monoton steigende Timestamps
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms += 33  # ~30 FPS

        try:
            face_result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)
        except Exception:
            return result

        if not face_result.face_landmarks:
            return result

        result["face_detected"] = True
        landmarks = face_result.face_landmarks[0]
        h, w = frame.shape[:2]

        # Mund-ROI extrahieren
        roi, mouth_area, mouth_open = self._extract_mouth_roi(landmarks, frame, h, w)
        if roi is None or roi.size == 0:
            return result

        result["debug_roi"] = roi

        # Kalibrierung fuettern
        if self._calibration.state in (CalibrationState.BASELINE, CalibrationState.TONGUE_PROMPT):
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            self._calibration.feed_frame(hsv_roi, mouth_open)
            result["calibration_state"] = self._calibration.state

            # Nach Kalibrierung HSV-Range an Detektor uebergeben
            if self._calibration.state == CalibrationState.DONE:
                ranges = self._calibration.get_tongue_hsv_range()
                if ranges:
                    self._hsv_detector.set_tongue_range(ranges["lower"], ranges["upper"])
                result["calibrated"] = True
            return result

        if not result["calibrated"]:
            return result

        # HSV-Erkennung
        detection = self._hsv_detector.detect(roi, mouth_area)
        tongue_ratio = detection["tongue_ratio"]
        tongue_tip_y = detection["tongue_tip_y"]
        result["tongue_ratio"] = tongue_ratio
        result["debug_mask"] = detection["mask"]

        # Score: tongue_ratio gewichtet mit Position
        raw_score = tongue_ratio
        if tongue_tip_y > TONGUE_TIP_THRESHOLD:
            raw_score *= 1.5  # Bonus wenn Zunge deutlich raushaengt

        # One-Euro-Filter
        t = self._timestamp_ms / 1000.0
        smoothed = self._score_filter.filter(raw_score, t)
        result["smoothed_score"] = smoothed

        # Entscheidung
        threshold = TONGUE_RATIO_THRESHOLD / self.sensitivity
        result["tongue_out"] = (
            smoothed > threshold
            and mouth_open
        )
        result["confidence"] = min(smoothed / threshold, 1.0) if threshold > 0 else 0.0

        return result

    def _extract_mouth_roi(self, landmarks, frame, h, w):
        """Extrahiert den Mund-ROI aus den Landmarks.

        Returns:
            (roi_bgr, mouth_area_px, mouth_is_open)
        """
        # Aeussere Lippen-Punkte fuer ROI-Bounding-Box
        outer_pts = np.array([
            [int(landmarks[i].x * w), int(landmarks[i].y * h)]
            for i in OUTER_LIP_INDICES
        ])

        # ROI mit Padding
        x_min, y_min = outer_pts.min(axis=0)
        x_max, y_max = outer_pts.max(axis=0)
        pad_x = int((x_max - x_min) * 0.2)
        pad_y = int((y_max - y_min) * 0.3)
        x_min = max(0, x_min - pad_x)
        y_min = max(0, y_min - pad_y)
        x_max = min(w, x_max + pad_x)
        y_max = min(h, y_max + pad_y)

        roi = frame[y_min:y_max, x_min:x_max]

        # Innere Lippen-Flaeche (Mundoeffnung)
        inner_pts = np.array([
            [int(landmarks[i].x * w), int(landmarks[i].y * h)]
            for i in INNER_LIP_INDICES
        ])
        mouth_area = cv2.contourArea(inner_pts)

        # Mundoeffnung relativ zur Gesichtshoehe
        face_h = max(1, int(landmarks[152].y * h) - int(landmarks[10].y * h))
        inner_h = inner_pts[:, 1].max() - inner_pts[:, 1].min()
        mouth_open = (inner_h / face_h) > MOUTH_OPEN_THRESHOLD

        return roi, mouth_area, mouth_open

    def start_calibration(self):
        """Startet interaktive Kalibrierung."""
        self._calibration.start()
        self._score_filter.reset()

    def start_silent_calibration(self):
        """Startet stille Rekalibrierung (nur Baseline)."""
        self._calibration.start_silent()

    def load_calibration(self, tongue_range: dict):
        """Laedt gespeicherte Kalibrierung aus dem Profil."""
        if tongue_range:
            self._calibration.load_tongue_range(
                tongue_range["lower"], tongue_range["upper"]
            )
            self._hsv_detector.set_tongue_range(
                tongue_range["lower"], tongue_range["upper"]
            )
            self._calibration.state = CalibrationState.DONE

    def reset(self):
        """Setzt den Detektor zurueck (fuer neue Session)."""
        self._score_filter.reset()
        self._frame_count = 0

    def cleanup(self):
        """Gibt Ressourcen frei."""
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None
```

- [ ] **Step 3: Commit**

```bash
git add src/services/detector_service.py
git commit -m "feat: DetectorService mit MediaPipe + HSV-Pipeline"
```

---

### Task 7: Standalone Debug-Skript

**Files:**
- Create: `src/debug_detector.py`

Dieses Skript ermoeglicht das Testen der Erkennung ohne GTK-App.

- [ ] **Step 1: Debug-Skript implementieren**

```python
#!/usr/bin/env python3
"""Standalone-Test der Erkennungs-Pipeline mit OpenCV Debug-Fenster.

Startet Kamera, fuehrt Kalibrierung durch, und zeigt Erkennung live.
Druecke 'q' zum Beenden, 'r' fuer Re-Kalibrierung.
"""

import sys
import os
import cv2
import numpy as np

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

os.environ.setdefault(
    "ZUNGENTRAINER_DATA_DIR",
    os.path.join(os.path.dirname(SRC_DIR), "data"),
)

from services.detector_service import DetectorService
from detection.calibration import CalibrationState


def main():
    detector = DetectorService()
    if detector.init_error:
        print(f"Fehler: {detector.init_error}")
        return 1

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    if not cap.isOpened():
        print("Fehler: Kamera nicht verfuegbar")
        return 1

    detector.start_calibration()
    print("=== Kalibrierung ===")
    print("Phase 1: Mund geschlossen halten (2 Sekunden)")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        result = detector.detect(frame)
        display = frame.copy()

        # Status-Text
        cal_state = result["calibration_state"]
        if cal_state == CalibrationState.BASELINE:
            text = "KALIBRIERUNG: Mund zu, normal schauen"
            color = (0, 255, 255)
        elif cal_state == CalibrationState.TONGUE_PROMPT:
            text = "KALIBRIERUNG: Zeig die Zunge!"
            color = (0, 165, 255)
        elif result["tongue_out"]:
            text = f"ZUNGE ERKANNT! Score: {result['smoothed_score']:.3f}"
            color = (0, 0, 255)
        elif result["face_detected"]:
            text = f"OK - Score: {result['smoothed_score']:.3f}"
            color = (0, 255, 0)
        else:
            text = "Kein Gesicht"
            color = (128, 128, 128)

        cv2.putText(display, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        # Tongue Ratio Balken
        if result["calibrated"]:
            bar_w = int(result["tongue_ratio"] * 400)
            cv2.rectangle(display, (20, 70), (20 + bar_w, 90), color, -1)
            cv2.rectangle(display, (20, 70), (420, 90), (255, 255, 255), 1)

        # Debug: Mund-ROI und Maske anzeigen
        if result["debug_roi"] is not None:
            roi = result["debug_roi"]
            roi_h = min(200, roi.shape[0])
            roi_w = int(roi.shape[1] * roi_h / roi.shape[0])
            roi_small = cv2.resize(roi, (roi_w, roi_h))
            display[100:100 + roi_h, 20:20 + roi_w] = roi_small

        if result["debug_mask"] is not None:
            mask = result["debug_mask"]
            mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            mask_h = min(200, mask.shape[0])
            mask_w = int(mask.shape[1] * mask_h / mask.shape[0])
            mask_small = cv2.resize(mask_color, (mask_w, mask_h))
            x_offset = 40 + (roi_w if result["debug_roi"] is not None else 0)
            display[100:100 + mask_h, x_offset:x_offset + mask_w] = mask_small

        # Anzeige (skaliert fuer Bildschirm)
        display_small = cv2.resize(display, (960, 540))
        cv2.imshow("ZungenTrainer Debug", display_small)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            detector.start_calibration()
            print("Re-Kalibrierung gestartet")

    cap.release()
    cv2.destroyAllWindows()
    detector.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Testen**

```bash
cd /home/yoshimintos/Projekte/ClaudeCode/zungentrainer
python3 src/debug_detector.py
```

Erwartetes Verhalten:
1. Kamera startet, "Mund zu" wird angezeigt (2s)
2. "Zeig die Zunge" wird angezeigt (2s)
3. Danach: Normales Sprechen → "OK", Zunge raus → "ZUNGE ERKANNT!"
4. Debug-ROI und Maske werden eingeblendet
5. 'q' beendet, 'r' kalibriert neu

- [ ] **Step 3: Commit**

```bash
git add src/debug_detector.py
git commit -m "feat: Standalone Debug-Skript fuer Erkennungs-Pipeline"
```

---

## PHASE 2: Minimale App

### Task 8: SoundService + MprisService (von alter App)

**Files:**
- Create: `src/services/sound_service.py`, `src/services/mpris_service.py`

- [ ] **Step 1: Dateien von alter App kopieren**

Lies und kopiere identisch:
- `old_apps/zungentrainer/src/services/sound_service.py` → `src/services/sound_service.py`
- `old_apps/zungentrainer/src/services/mpris_service.py` → `src/services/mpris_service.py`

Diese Services sind unveraendert wiederverwendbar.

- [ ] **Step 2: Commit**

```bash
git add src/services/sound_service.py src/services/mpris_service.py
git commit -m "feat: SoundService + MprisService (von alter App portiert)"
```

---

### Task 9: SessionService (vereinfacht)

**Files:**
- Create: `src/services/session_service.py`
- Test: `tests/test_session_service.py`

Die neue SessionService hat keinen WARNING-Zustand — Piep und Pause kommen gleichzeitig.

- [ ] **Step 1: Failing Test schreiben**

```python
# tests/test_session_service.py
"""Tests fuer die vereinfachte Session-Zustandsmaschine."""

import time
import pytest
from unittest.mock import MagicMock
from services.session_service import SessionService, SessionState, CONFIRM_FRAMES


def test_initial_state_is_idle():
    s = SessionService()
    assert s.state == SessionState.IDLE


def test_start_transitions_to_running():
    s = SessionService()
    s.start()
    assert s.state == SessionState.RUNNING


def test_tongue_needs_confirm_frames():
    """Einzelner tongue_out Frame reicht nicht fuer DETECTED."""
    s = SessionService()
    s.start()
    s.update(True)
    assert s.state == SessionState.RUNNING


def test_confirmed_tongue_triggers_detected():
    """CONFIRM_FRAMES tongue_out-Frames loesen DETECTED aus."""
    s = SessionService()
    s.on_alarm = MagicMock()
    s.start()
    for _ in range(CONFIRM_FRAMES):
        s.update(True)
    assert s.state == SessionState.DETECTED
    assert s.incident_count == 1
    s.on_alarm.assert_called_once()


def test_tongue_back_during_confirmation_resets():
    """Zunge zurueck vor Bestaetigung setzt Zaehler zurueck."""
    s = SessionService()
    s.start()
    s.update(True)
    s.update(True)
    s.update(False)  # Reset
    assert s.state == SessionState.RUNNING
    # Nochmal 2 Frames reicht nicht
    s.update(True)
    s.update(True)
    assert s.state == SessionState.RUNNING


def test_detected_to_cooldown_on_tongue_back():
    """Nach DETECTED: Zunge zurueck + resume_delay -> COOLDOWN."""
    s = SessionService()
    s.resume_delay = 0.0  # Sofort
    s.on_alarm_end = MagicMock()
    s.start()
    for _ in range(CONFIRM_FRAMES):
        s.update(True)
    assert s.state == SessionState.DETECTED
    s.update(False)
    assert s.state == SessionState.COOLDOWN
    s.on_alarm_end.assert_called_once()


def test_stop_returns_result():
    s = SessionService()
    s.start()
    result = s.stop()
    assert "duration" in result
    assert "incidents" in result
    assert "success" in result
    assert s.state == SessionState.IDLE
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_session_service.py -v
```

- [ ] **Step 3: SessionService implementieren**

Lies `old_apps/zungentrainer/src/services/session_service.py` als Basis. Die neue Version entfernt den WARNING-Zustand — der Uebergang geht direkt RUNNING -> DETECTED (Piep + Pause gleichzeitig):

```python
# src/services/session_service.py
"""Sitzungs-Zustandsmaschine fuer das Training.

Vereinfachtes Alarm-System (kein WARNING-Zwischenschritt):
  RUNNING -> tongue_out fuer CONFIRM_FRAMES -> DETECTED (Piep + Medienpause)
  DETECTED -> Zunge zurueck + resume_delay -> COOLDOWN
  COOLDOWN -> cooldown_time -> RUNNING

Multi-Frame-Bestaetigung: CONFIRM_FRAMES aufeinanderfolgende tongue_out-Frames
vor DETECTED. Sofortiger Reset bei Zunge-zurueck (rohes Signal).
"""

import time
from enum import Enum, auto


CONFIRM_FRAMES = 3  # ~100ms bei 30 FPS


class SessionState(Enum):
    IDLE = auto()
    RUNNING = auto()
    DETECTED = auto()
    COOLDOWN = auto()


class SessionService:
    """Verwaltet den Trainings-Sitzungszustand.

    Zustandsuebergaenge:
        IDLE -> RUNNING (start)
        RUNNING -> DETECTED (Zunge bestaetigt -> Piep + Medienpause)
        DETECTED -> COOLDOWN (resume_delay + Zunge zurueck)
        COOLDOWN -> RUNNING (cooldown_time)
        alle -> IDLE (stop)
    """

    def __init__(self):
        self.state = SessionState.IDLE

        # Schwierigkeitsparameter (von AdaptiveDifficulty gesetzt)
        self.resume_delay = 0.0
        self.cooldown_time = 5.0
        self.max_incidents = 0
        self.required_session_time = 600.0

        # Interner Zustand
        self._detected_time = None
        self._cooldown_start = None
        self._session_start = None
        self._incident_count = 0
        self._confirm_count = 0

        # Callbacks
        self.on_alarm = None       # Piep + Medienpause
        self.on_alarm_end = None   # Mediaresume
        self.on_state_change = None

    @property
    def session_duration(self) -> float:
        if self._session_start is None:
            return 0.0
        return time.monotonic() - self._session_start

    @property
    def incident_count(self) -> int:
        return self._incident_count

    @property
    def session_successful(self) -> bool:
        return self.session_duration >= self.required_session_time

    @property
    def remaining_cooldown(self) -> float:
        if self.state != SessionState.COOLDOWN or self._cooldown_start is None:
            return 0.0
        return max(0.0, self.cooldown_time - (time.monotonic() - self._cooldown_start))

    @property
    def remaining_resume(self) -> float:
        if self.state != SessionState.DETECTED or self._detected_time is None:
            return 0.0
        return max(0.0, self.resume_delay - (time.monotonic() - self._detected_time))

    @property
    def session_failed(self) -> bool:
        if self.max_incidents <= 0:
            return False
        return self._incident_count >= self.max_incidents

    def start(self):
        self.state = SessionState.RUNNING
        self._session_start = time.monotonic()
        self._detected_time = None
        self._cooldown_start = None
        self._incident_count = 0
        self._confirm_count = 0
        self._notify_state_change()

    def stop(self) -> dict:
        duration = self.session_duration
        incidents = self._incident_count
        success = self.session_successful and not self.session_failed
        self.state = SessionState.IDLE
        self._session_start = None
        self._detected_time = None
        self._cooldown_start = None
        self._confirm_count = 0
        self._notify_state_change()
        return {"duration": duration, "incidents": incidents, "success": success}

    def update(self, tongue_out: bool):
        """Wird jeden Frame aufgerufen mit dem Erkennungsergebnis."""
        now = time.monotonic()

        if tongue_out:
            self._confirm_count += 1
        else:
            self._confirm_count = 0
        confirmed = self._confirm_count >= CONFIRM_FRAMES

        if self.state == SessionState.RUNNING:
            if confirmed:
                # Direkt zu DETECTED (Piep + Pause gleichzeitig)
                self._incident_count += 1
                self.state = SessionState.DETECTED
                self._detected_time = now
                self._confirm_count = 0
                self._notify_state_change()
                if self.on_alarm:
                    self.on_alarm()

        elif self.state == SessionState.DETECTED:
            # Rohes Signal fuer schnelle Reaktion
            time_elapsed = (now - self._detected_time) >= self.resume_delay
            if time_elapsed and not tongue_out:
                self.state = SessionState.COOLDOWN
                self._cooldown_start = now
                self._notify_state_change()
                if self.on_alarm_end:
                    self.on_alarm_end()

        elif self.state == SessionState.COOLDOWN:
            if (now - self._cooldown_start) >= self.cooldown_time:
                self.state = SessionState.RUNNING
                self._notify_state_change()

    def _notify_state_change(self):
        if self.on_state_change:
            self.on_state_change(self.state)
```

- [ ] **Step 4: Tests ausfuehren — muessen bestehen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_session_service.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/services/session_service.py tests/test_session_service.py
git commit -m "feat: Vereinfachte SessionService (kein WARNING-Zwischenschritt)"
```

---

### Task 10: User-Datenmodell + Persistenz

**Files:**
- Create: `src/models/user_data.py`, `src/models/persistence.py`, `src/models/__init__.py`
- Test: `tests/test_user_data.py`

- [ ] **Step 1: Failing Test schreiben**

```python
# tests/test_user_data.py
"""Tests fuer UserProfile Serialisierung."""

from models.user_data import UserProfile, SessionRecord


def test_roundtrip_empty_profile():
    p = UserProfile()
    d = p.to_dict()
    p2 = UserProfile.from_dict(d)
    assert p2.name == p.name
    assert p2.total_sessions == 0
    assert p2.sessions == []


def test_roundtrip_with_sessions():
    p = UserProfile(name="Anouk")
    p.sessions.append(SessionRecord(
        timestamp="2026-05-09T10:00:00",
        duration=600.0,
        incidents=2,
        success=True,
    ))
    d = p.to_dict()
    p2 = UserProfile.from_dict(d)
    assert len(p2.sessions) == 1
    assert p2.sessions[0].duration == 600.0


def test_unknown_fields_ignored():
    """Unbekannte Felder aus neueren Versionen werden ignoriert."""
    d = {"name": "Test", "unknown_future_field": 42, "schema_version": 1}
    p = UserProfile.from_dict(d)
    assert p.name == "Test"


def test_settings_defaults():
    p = UserProfile()
    assert p.settings["camera_index"] == 0
    assert p.settings["volume"] == 0.5


def test_difficulty_params_roundtrip():
    p = UserProfile()
    p.difficulty_params["reaction_time"] = 1.5
    d = p.to_dict()
    p2 = UserProfile.from_dict(d)
    assert p2.difficulty_params["reaction_time"] == 1.5
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_user_data.py -v
```

- [ ] **Step 3: user_data.py implementieren**

Basiert auf `old_apps/zungentrainer/src/models/user_data.py`, entfernt Gamification (Level, XP, Badges, Creatures), fuegt adaptive Schwierigkeit und Wochen-Streak hinzu:

```python
# src/models/user_data.py
"""Datenklassen fuer Benutzerprofil und Trainingshistorie."""

import dataclasses
from dataclasses import dataclass, field


def _filter_fields(cls, data: dict) -> dict:
    """Gibt nur bekannte Felder einer Dataclass aus einem dict zurueck."""
    known = {f.name for f in dataclasses.fields(cls)}
    return {k: v for k, v in data.items() if k in known}


@dataclass
class SessionRecord:
    """Aufzeichnung einer Trainingssitzung."""
    timestamp: str = ""
    duration: float = 0.0
    incidents: int = 0
    success: bool = False


@dataclass
class Milestone:
    """Ein erreichter Meilenstein."""
    milestone_id: str = ""
    name: str = ""
    reached_date: str = ""


@dataclass
class UserProfile:
    """Benutzerprofil mit Trainingshistorie und Einstellungen."""
    name: str = "Anouk"
    total_sessions: int = 0
    successful_sessions: int = 0
    total_training_time: float = 0.0
    total_incidents: int = 0
    weekly_streak: int = 0
    best_weekly_streak: int = 0
    last_session_date: str = ""
    sessions: list = field(default_factory=list)
    milestones: list = field(default_factory=list)
    settings: dict = field(default_factory=lambda: {
        "camera_index": 0,
        "volume": 0.5,
        "beep_frequency": 800,
    })
    difficulty_params: dict = field(default_factory=lambda: {
        "reaction_time": 3.0,
        "resume_delay": 0.0,
        "sensitivity": 1.0,
        "cooldown": 5.0,
    })
    calibration: dict = field(default_factory=dict)
    trainings_per_week: int = 2
    min_session_duration: int = 10

    def to_dict(self) -> dict:
        from models.persistence import CURRENT_SCHEMA
        return {
            "schema_version": CURRENT_SCHEMA,
            "name": self.name,
            "total_sessions": self.total_sessions,
            "successful_sessions": self.successful_sessions,
            "total_training_time": self.total_training_time,
            "total_incidents": self.total_incidents,
            "weekly_streak": self.weekly_streak,
            "best_weekly_streak": self.best_weekly_streak,
            "last_session_date": self.last_session_date,
            "sessions": [
                {f.name: getattr(s, f.name) for f in dataclasses.fields(s)}
                for s in self.sessions
            ],
            "milestones": [
                {f.name: getattr(m, f.name) for f in dataclasses.fields(m)}
                for m in self.milestones
            ],
            "settings": self.settings,
            "difficulty_params": self.difficulty_params,
            "calibration": self.calibration,
            "trainings_per_week": self.trainings_per_week,
            "min_session_duration": self.min_session_duration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        profile = cls()
        simple_fields = (
            "name", "total_sessions", "successful_sessions",
            "total_training_time", "total_incidents", "weekly_streak",
            "best_weekly_streak", "last_session_date",
            "trainings_per_week", "min_session_duration",
        )
        for key in simple_fields:
            if key in data:
                setattr(profile, key, data[key])

        profile.sessions = [
            SessionRecord(**_filter_fields(SessionRecord, s))
            for s in data.get("sessions", [])
        ]
        profile.milestones = [
            Milestone(**_filter_fields(Milestone, m))
            for m in data.get("milestones", [])
        ]
        if "settings" in data:
            profile.settings.update(data["settings"])
        if "difficulty_params" in data:
            profile.difficulty_params.update(data["difficulty_params"])
        if "calibration" in data:
            profile.calibration = data["calibration"]
        return profile
```

- [ ] **Step 4: persistence.py von alter App kopieren und anpassen**

Lies `old_apps/zungentrainer/src/models/persistence.py` und kopiere nach `src/models/persistence.py`. Der Code ist identisch, da `UserProfile.from_dict` und `UserProfile.to_dict` die Unterschiede kapseln.

Erstelle leere `src/models/__init__.py`.

- [ ] **Step 5: Tests ausfuehren — muessen bestehen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_user_data.py -v
```

Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add src/models/ tests/test_user_data.py
git commit -m "feat: Datenmodell und Persistenz (UserProfile ohne Gamification)"
```

---

### Task 11: Adaptive Schwierigkeit

**Files:**
- Create: `src/systems/adaptive_difficulty.py`, `src/systems/__init__.py`
- Test: `tests/test_adaptive_difficulty.py`

- [ ] **Step 1: Failing Test schreiben**

```python
# tests/test_adaptive_difficulty.py
"""Tests fuer den Flow-Zone Algorithmus."""

from systems.adaptive_difficulty import AdaptiveDifficulty


def test_initial_params():
    ad = AdaptiveDifficulty()
    params = ad.get_params()
    assert "reaction_time" in params
    assert "resume_delay" in params
    assert "sensitivity" in params
    assert "cooldown" in params


def test_low_incident_rate_increases_difficulty():
    """Wenige Vorfaelle -> schwieriger."""
    ad = AdaptiveDifficulty()
    initial = ad.get_params()["reaction_time"]
    # 0.1 Vorfaelle/min (< 0.2 -> schwieriger)
    ad.adjust_after_session(incidents=1, duration_minutes=10.0)
    assert ad.get_params()["reaction_time"] < initial


def test_high_incident_rate_decreases_difficulty():
    """Viele Vorfaelle -> leichter."""
    ad = AdaptiveDifficulty()
    initial = ad.get_params()["reaction_time"]
    # 2.0 Vorfaelle/min (> 1.0 -> leichter)
    ad.adjust_after_session(incidents=20, duration_minutes=10.0)
    assert ad.get_params()["reaction_time"] > initial


def test_flow_zone_no_change():
    """Vorfallsrate in Flow-Zone -> keine Aenderung."""
    ad = AdaptiveDifficulty()
    initial = ad.get_params()
    # 0.5 Vorfaelle/min (0.2-1.0 -> Flow-Zone)
    ad.adjust_after_session(incidents=5, duration_minutes=10.0)
    assert ad.get_params()["reaction_time"] == initial["reaction_time"]


def test_params_stay_in_bounds():
    """Parameter ueberschreiten nicht die Grenzen."""
    ad = AdaptiveDifficulty()
    # 50 Sessions mit extremen Werten
    for _ in range(50):
        ad.adjust_after_session(incidents=0, duration_minutes=10.0)
    params = ad.get_params()
    assert params["reaction_time"] >= 0.3
    assert params["sensitivity"] <= 2.0


def test_from_dict_roundtrip():
    ad = AdaptiveDifficulty()
    ad.adjust_after_session(incidents=1, duration_minutes=10.0)
    d = ad.to_dict()
    ad2 = AdaptiveDifficulty.from_dict(d)
    assert ad2.get_params() == ad.get_params()
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_adaptive_difficulty.py -v
```

- [ ] **Step 3: AdaptiveDifficulty implementieren**

```python
# src/systems/adaptive_difficulty.py
"""Adaptive Schwierigkeit (Flow-Zone Algorithmus).

Passt nach jeder Session die Schwierigkeitsparameter an:
- rate < 0.2/min: schwieriger (kleine Schritte)
- rate 0.2-1.0/min: Flow-Zone (keine Aenderung)
- rate > 1.0/min: leichter (groessere Schritte)

Alle Anpassungen per EMA (nie sprunghaft).
"""


# Parameter-Grenzen
BOUNDS = {
    "reaction_time": (0.3, 3.0),    # Sekunden bis Piep + Pause
    "resume_delay": (0.0, 20.0),     # Sekunden Medienpause
    "sensitivity": (0.5, 2.0),       # Detektor-Empfindlichkeit
    "cooldown": (3.0, 5.0),          # Sekunden nach Alarm
}

# Schrittgroessen
HARDER_STEP = {
    "reaction_time": -0.1,
    "resume_delay": 1.0,
    "sensitivity": 0.05,
    "cooldown": -0.1,
}
EASIER_STEP = {
    "reaction_time": 0.2,
    "resume_delay": -1.5,
    "sensitivity": -0.1,
    "cooldown": 0.2,
}

FLOW_ZONE_LOW = 0.2   # Vorfaelle/min
FLOW_ZONE_HIGH = 1.0


class AdaptiveDifficulty:
    """Passt Schwierigkeitsparameter automatisch an."""

    def __init__(self):
        self._params = {
            "reaction_time": 3.0,
            "resume_delay": 0.0,
            "sensitivity": 1.0,
            "cooldown": 5.0,
        }

    def get_params(self) -> dict:
        return self._params.copy()

    def adjust_after_session(self, incidents: int, duration_minutes: float):
        """Passt Schwierigkeit basierend auf Vorfallsrate an."""
        if duration_minutes <= 0:
            return

        rate = incidents / duration_minutes

        if rate < FLOW_ZONE_LOW:
            steps = HARDER_STEP
        elif rate > FLOW_ZONE_HIGH:
            steps = EASIER_STEP
        else:
            return  # Flow-Zone

        for key, step in steps.items():
            low, high = BOUNDS[key]
            self._params[key] = max(low, min(high, self._params[key] + step))

    def to_dict(self) -> dict:
        return self._params.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "AdaptiveDifficulty":
        ad = cls()
        for key in ad._params:
            if key in data:
                ad._params[key] = data[key]
        return ad
```

Erstelle leere `src/systems/__init__.py`.

- [ ] **Step 4: Tests ausfuehren — muessen bestehen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_adaptive_difficulty.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/systems/ tests/test_adaptive_difficulty.py
git commit -m "feat: Adaptive Schwierigkeit (Flow-Zone Algorithmus)"
```

---

### Task 12: CameraPaintable (von alter App)

**Files:**
- Create: `src/utils/camera_paintable.py`, `src/utils/__init__.py`

- [ ] **Step 1: Datei von alter App kopieren**

Lies `old_apps/zungentrainer/src/utils/camera_paintable.py` und kopiere identisch nach `src/utils/camera_paintable.py`. Erstelle leere `src/utils/__init__.py`.

- [ ] **Step 2: Commit**

```bash
git add src/utils/
git commit -m "feat: CameraPaintable (von alter App portiert)"
```

---

### Task 13: Window + ViewStack (3 Views)

**Files:**
- Modify: `src/main.py`
- Create: `src/window.py`
- Create: Platzhalter fuer `src/pages/training_page.py`, `src/pages/progress_page.py`, `src/pages/settings_page.py`

- [ ] **Step 1: Platzhalter-Pages erstellen**

```python
# src/pages/__init__.py
# (leer)
```

```python
# src/pages/training_page.py
"""Trainings-Seite (Platzhalter)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class TrainingPage(Gtk.Box):
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window
        label = Adw.StatusPage(
            title="Training",
            description="Kamera-Feed und Erkennung",
            icon_name="camera-video-symbolic",
        )
        self.append(label)

    def cleanup(self):
        pass
```

```python
# src/pages/progress_page.py
"""Fortschritts-Seite (Platzhalter)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class ProgressPage(Gtk.Box):
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window
        label = Adw.StatusPage(
            title="Fortschritt",
            description="Wochenstatistiken und Meilensteine",
            icon_name="starred-symbolic",
        )
        self.append(label)

    def refresh(self):
        pass
```

```python
# src/pages/settings_page.py
"""Einstellungs-Seite (Platzhalter)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw


class SettingsPage(Adw.PreferencesPage):
    def __init__(self, main_window):
        super().__init__()
        self._window = main_window
        group = Adw.PreferencesGroup(title="Einstellungen")
        group.set_description("Platzhalter")
        self.add(group)

    def refresh(self):
        pass
```

- [ ] **Step 2: Window implementieren**

Basiert auf `old_apps/zungentrainer/src/window.py`. Entfernt Gamification, 3 Views statt 4, `starred-symbolic` statt `go-up-symbolic`:

```python
# src/window.py
"""Hauptfenster mit ViewStack-Navigation (3 Views)."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from pages.training_page import TrainingPage
from pages.progress_page import ProgressPage
from pages.settings_page import SettingsPage
from models.persistence import DataStore
from systems.adaptive_difficulty import AdaptiveDifficulty


class ZungenTrainerWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("ZungenTrainer")
        self.set_default_size(480, 700)

        self.data_store = DataStore()
        self.profile = self.data_store.load()
        self.adaptive_difficulty = AdaptiveDifficulty.from_dict(
            self.profile.difficulty_params
        )

        self._build_ui()
        self.connect("close-request", self._on_close)

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        self.view_stack = Adw.ViewStack()
        self.view_stack.set_vexpand(True)
        toolbar_view.set_content(self.view_stack)

        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self.view_stack)
        toolbar_view.add_bottom_bar(switcher_bar)

        switcher_title = Adw.ViewSwitcherTitle()
        switcher_title.set_stack(self.view_stack)
        switcher_title.set_title("ZungenTrainer")
        header.set_title_widget(switcher_title)

        switcher_title.connect(
            "notify::title-visible",
            lambda st, _: switcher_bar.set_reveal(st.get_title_visible()),
        )

        self.training_page = TrainingPage(self)
        self.progress_page = ProgressPage(self)
        self.settings_page = SettingsPage(self)

        self.view_stack.add_titled_with_icon(
            self.training_page, "training", "Training", "camera-video-symbolic"
        )
        self.view_stack.add_titled_with_icon(
            self.progress_page, "progress", "Fortschritt", "starred-symbolic"
        )
        self.view_stack.add_titled_with_icon(
            self.settings_page, "settings", "Einstellungen", "preferences-system-symbolic"
        )

    def save_profile(self):
        try:
            self.data_store.save(self.profile)
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")

    def refresh_pages(self):
        self.progress_page.refresh()
        self.settings_page.refresh()

    def _on_close(self, *args):
        self.training_page.cleanup()
        self.save_profile()
        return False
```

- [ ] **Step 3: main.py aktualisieren**

Ersetze den Platzhalter in `src/main.py` — aendere `do_activate`:

```python
    def do_activate(self):
        from window import ZungenTrainerWindow

        win = self.props.active_window
        if not win:
            win = ZungenTrainerWindow(application=self)
        win.present()
```

- [ ] **Step 4: Testen**

```bash
./run.sh
```

Erwartetes Ergebnis: Fenster mit 3 Tabs (Training, Fortschritt, Einstellungen), ViewSwitcher im Header, Platzhalter-Inhalte.

- [ ] **Step 5: Commit**

```bash
git add src/main.py src/window.py src/pages/
git commit -m "feat: Window mit 3-View ViewStack (Training, Fortschritt, Einstellungen)"
```

---

### Task 14: TrainingPage (Kamera + OSD + Session)

**Files:**
- Modify: `src/pages/training_page.py`

Dies ist die zentrale Seite. Basiert auf `old_apps/zungentrainer/src/pages/training_page.py`, angepasst fuer:
- Vereinfachte SessionService (kein WARNING)
- HSV-DetectorService
- OSD-Overlays statt fester Info-Zeilen
- View-Wechsel pausiert Training
- `.pill` + `.suggested-action` fuer Start-Button

- [ ] **Step 1: TrainingPage implementieren**

Lies `old_apps/zungentrainer/src/pages/training_page.py` als Vorlage. Schreibe die neue Version:

```python
# src/pages/training_page.py
"""Trainings-Seite mit Kamera-Feed, OSD-Overlays und Session-Steuerung."""

from datetime import datetime
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from services.camera_service import CameraService
from services.detector_service import DetectorService
from services.sound_service import SoundService
from services.mpris_service import MprisService
from services.session_service import SessionService, SessionState
from utils.camera_paintable import CameraPaintable
from models.user_data import SessionRecord
from detection.calibration import CalibrationState


class TrainingPage(Gtk.Box):
    """Hauptseite: Kamera-Feed mit OSD-Overlays fuer Training."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._window = main_window
        self._polling_id = None
        self._paused_by_view_switch = False

        # Services
        profile = main_window.profile
        self._camera = CameraService(profile.settings.get("camera_index", 0))
        self._detector = DetectorService()
        self._sound = SoundService(
            frequency=profile.settings.get("beep_frequency", 800)
        )
        self._sound.volume = profile.settings.get("volume", 0.5)
        self._mpris = MprisService()
        self._session = SessionService()
        self._paintable = CameraPaintable()

        # Gespeicherte Kalibrierung laden
        if profile.calibration:
            self._detector.load_calibration(profile.calibration)

        # Session-Callbacks
        self._session.on_alarm = self._on_alarm
        self._session.on_alarm_end = self._on_alarm_end
        self._session.on_state_change = self._on_state_change

        self._apply_difficulty()
        self._build_ui()

    def _apply_difficulty(self):
        params = self._window.adaptive_difficulty.get_params()
        self._session.resume_delay = params["resume_delay"]
        self._session.cooldown_time = params["cooldown"]
        self._session.required_session_time = self._window.profile.min_session_duration * 60.0
        self._detector.sensitivity = params["sensitivity"]

    def _build_ui(self):
        # Toast-Overlay fuer transiente Meldungen
        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_vexpand(True)
        self.append(self._toast_overlay)

        # Overlay fuer OSD ueber dem Kamera-Feed
        overlay = Gtk.Overlay()
        self._toast_overlay.set_child(overlay)

        # Kamera-Bild
        self._picture = Gtk.Picture()
        self._picture.set_paintable(self._paintable)
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self._picture.set_vexpand(True)
        overlay.set_child(self._picture)

        # Banner (persistenter Alarm-Status)
        self._banner = Adw.Banner()
        self._banner.set_revealed(False)
        overlay.add_overlay(self._banner)

        # OSD: Timer oben rechts
        self._timer_label = Gtk.Label(label="00:00")
        self._timer_label.add_css_class("title-2")
        self._timer_label.add_css_class("numeric")
        self._timer_label.set_halign(Gtk.Align.END)
        self._timer_label.set_valign(Gtk.Align.START)
        self._timer_label.set_margin_top(12)
        self._timer_label.set_margin_end(12)
        self._timer_label.set_visible(False)
        self._timer_label.set_tooltip_text("Trainingszeit")
        overlay.add_overlay(self._timer_label)

        # OSD: Statusleiste unten
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_box.set_halign(Gtk.Align.CENTER)
        bottom_box.set_valign(Gtk.Align.END)
        bottom_box.set_margin_bottom(12)

        self._incident_label = Gtk.Label(label="0 Vorfaelle")
        self._incident_label.add_css_class("dim-label")
        self._incident_label.set_visible(False)
        bottom_box.append(self._incident_label)

        self._stop_button = Gtk.Button(icon_name="media-playback-stop-symbolic")
        self._stop_button.set_tooltip_text("Training beenden")
        self._stop_button.add_css_class("circular")
        self._stop_button.add_css_class("destructive-action")
        self._stop_button.set_visible(False)
        self._stop_button.connect("clicked", lambda _: self.stop_training())
        bottom_box.append(self._stop_button)

        overlay.add_overlay(bottom_box)

        # Start-Button (im Zentrum, sichtbar wenn nicht trainiert)
        self._start_button = Gtk.Button(label="Training starten")
        self._start_button.add_css_class("suggested-action")
        self._start_button.add_css_class("pill")
        self._start_button.set_halign(Gtk.Align.CENTER)
        self._start_button.set_valign(Gtk.Align.CENTER)
        self._start_button.set_tooltip_text("Training starten")
        self._start_button.connect("clicked", lambda _: self.start_training())
        overlay.add_overlay(self._start_button)

        # Status-Label unter dem Overlay
        self._status_label = Gtk.Label(label="Bereit zum Training")
        self._status_label.add_css_class("dim-label")
        self._status_label.set_margin_top(8)
        self._status_label.set_margin_bottom(8)
        self.append(self._status_label)

    def start_training(self):
        if self._detector.init_error:
            self._banner.set_title(
                f"Fehler: {self._detector.init_error}"
            )
            self._banner.set_revealed(True)
            return

        self._apply_difficulty()

        # Kalibrierung: entweder still (Folge-Session) oder interaktiv
        if self._detector._calibration.state == CalibrationState.DONE:
            self._detector.start_silent_calibration()
        else:
            self._detector.start_calibration()

        self._detector.reset()
        self._camera.start()
        self._session.start()
        self._paused_by_view_switch = False

        # UI umschalten
        self._start_button.set_visible(False)
        self._timer_label.set_visible(True)
        self._incident_label.set_visible(True)
        self._stop_button.set_visible(True)
        self._banner.set_revealed(False)
        self._status_label.set_label("Kalibrierung \u2013 Mund bitte geschlossen halten")

        self._polling_id = GLib.timeout_add(33, self._poll_frame)

    def stop_training(self):
        if self._session.state == SessionState.IDLE:
            return

        if self._polling_id:
            GLib.source_remove(self._polling_id)
            self._polling_id = None

        result = self._session.stop()
        self._camera.stop()
        self._mpris.resume_paused()

        # UI zuruecksetzen
        self._start_button.set_visible(True)
        self._timer_label.set_visible(False)
        self._incident_label.set_visible(False)
        self._stop_button.set_visible(False)
        self._banner.set_revealed(False)
        self._status_label.set_label("Bereit zum Training")

        if result["duration"] > 10:
            self._finish_session(result)

    def pause_training(self):
        """Pausiert Training bei View-Wechsel."""
        if self._session.state == SessionState.IDLE:
            return
        if self._polling_id:
            GLib.source_remove(self._polling_id)
            self._polling_id = None
        self._camera.stop()
        self._mpris.resume_paused()
        self._paused_by_view_switch = True
        self._status_label.set_label("Training pausiert")

    def resume_training(self):
        """Setzt pausiertes Training fort."""
        if not self._paused_by_view_switch:
            return
        self._paused_by_view_switch = False
        self._camera.start()
        self._status_label.set_label("Training laeuft")
        self._polling_id = GLib.timeout_add(33, self._poll_frame)

    def _poll_frame(self) -> bool:
        frame = self._camera.get_frame()
        if frame is None:
            return True

        self._paintable.set_frame(frame)

        try:
            detection = self._detector.detect(frame)
        except Exception as e:
            print(f"Detektor-Fehler: {e}")
            return True

        if detection["face_detected"]:
            self._session.update(detection["tongue_out"])

            cal_state = detection["calibration_state"]
            if cal_state == CalibrationState.BASELINE:
                self._status_label.set_label("Kalibrierung \u2013 Mund bitte geschlossen halten")
            elif cal_state == CalibrationState.TONGUE_PROMPT:
                self._status_label.set_label("Zeig mal kurz die Zunge!")
            elif cal_state == CalibrationState.DONE and not detection["calibrated"]:
                # Gerade fertig kalibriert — HSV-Ranges speichern
                ranges = self._detector._calibration.get_tongue_hsv_range()
                if ranges:
                    self._window.profile.calibration = ranges
                    self._window.save_profile()
            elif self._session.state == SessionState.RUNNING:
                self._status_label.set_label("Training laeuft")
            elif self._session.state == SessionState.DETECTED:
                remaining = self._session.remaining_resume
                if remaining > 0:
                    self._status_label.set_label(
                        f"Film pausiert\u2026 noch {int(remaining)}\u202fs"
                    )
                else:
                    self._status_label.set_label("Zunge rein!")
            elif self._session.state == SessionState.COOLDOWN:
                remaining = self._session.remaining_cooldown
                self._status_label.set_label(f"Abklingzeit\u2026 {int(remaining)}\u202fs")
        else:
            self._session.update(False)
            if self._session.state == SessionState.RUNNING:
                self._status_label.set_label("Kein Gesicht erkannt")

        # Timer + Vorfaelle
        d = self._session.session_duration
        self._timer_label.set_label(f"{int(d) // 60:02d}:{int(d) % 60:02d}")
        self._incident_label.set_label(f"{self._session.incident_count} Vorfaelle")

        if self._session.session_failed:
            self._polling_id = None
            GLib.timeout_add(100, lambda: self.stop_training() or False)
            return False

        return True

    def _on_alarm(self):
        self._sound.beep()
        self._mpris.pause_all()
        self._banner.set_title("Zunge erkannt \u2014 Film pausiert")
        self._banner.set_revealed(True)

    def _on_alarm_end(self):
        self._mpris.resume_paused()
        self._banner.set_revealed(False)

    def _on_state_change(self, new_state):
        if new_state == SessionState.DETECTED:
            self._banner.set_title("Zunge erkannt \u2014 Film pausiert")
            self._banner.set_revealed(True)
        elif new_state in (SessionState.COOLDOWN, SessionState.RUNNING):
            self._banner.set_revealed(False)
        elif new_state == SessionState.IDLE:
            self._banner.set_revealed(False)

    def _finish_session(self, result: dict):
        profile = self._window.profile
        record = SessionRecord(
            timestamp=datetime.now().isoformat(),
            duration=result["duration"],
            incidents=result["incidents"],
            success=result["success"],
        )
        profile.sessions.append(record)
        profile.total_sessions += 1
        profile.total_training_time += result["duration"]
        profile.total_incidents += result["incidents"]
        if result["success"]:
            profile.successful_sessions += 1

        # Adaptive Schwierigkeit anpassen
        self._window.adaptive_difficulty.adjust_after_session(
            incidents=result["incidents"],
            duration_minutes=result["duration"] / 60.0,
        )
        profile.difficulty_params = self._window.adaptive_difficulty.to_dict()

        self._window.save_profile()
        self._window.refresh_pages()

        # Toast statt Dialog
        toast = Adw.Toast(
            title=f"Training beendet \u2014 {result['incidents']} Vorfaelle"
        )
        toast.set_timeout(3)
        self._toast_overlay.add_toast(toast)

    def cleanup(self):
        self.stop_training()
        self._sound.cleanup()
        self._detector.cleanup()

    def update_settings(self):
        profile = self._window.profile
        self._camera.camera_index = profile.settings.get("camera_index", 0)
        self._sound.volume = profile.settings.get("volume", 0.5)
        self._sound.frequency = profile.settings.get("beep_frequency", 800)
```

- [ ] **Step 2: View-Wechsel-Handling in Window ergaenzen**

In `src/window.py` nach dem Erstellen der Pages, fuege hinzu:

```python
        # View-Wechsel: Training pausieren/fortsetzen
        self.view_stack.connect(
            "notify::visible-child",
            self._on_visible_child_changed,
        )

    def _on_visible_child_changed(self, stack, _param):
        visible = stack.get_visible_child()
        if visible == self.training_page:
            self.training_page.resume_training()
        else:
            self.training_page.pause_training()
```

- [ ] **Step 3: Testen**

```bash
./run.sh
```

Erwartetes Ergebnis: Training starten → Kamera-Feed → Kalibrierung → Erkennung → Alarm mit Piep + Banner. View-Wechsel pausiert Training.

- [ ] **Step 4: Commit**

```bash
git add src/pages/training_page.py src/window.py
git commit -m "feat: TrainingPage mit Kamera, OSD, Session und View-Wechsel-Pause"
```

---

### Task 15: SettingsPage (Einstellungen + Eltern-Bereich Platzhalter)

**Files:**
- Modify: `src/pages/settings_page.py`

- [ ] **Step 1: SettingsPage implementieren**

Basiert auf `old_apps/zungentrainer/src/pages/settings_page.py`, vereinfacht (kein Test-Modus, kein Level-Display), mit Platzhalter fuer Eltern-Bereich:

```python
# src/pages/settings_page.py
"""Einstellungs-Seite mit AdwPreferencesPage."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class SettingsPage(Adw.PreferencesPage):
    """Einstellungen fuer Kamera, Ton und Name."""

    def __init__(self, main_window):
        super().__init__()
        self._window = main_window
        self._build_ui()

    def _build_ui(self):
        profile = self._window.profile

        # Kamera
        camera_group = Adw.PreferencesGroup(title="Kamera")
        self.add(camera_group)

        camera_row = Adw.SpinRow.new_with_range(0, 10, 1)
        camera_row.set_title("Kamera-Index")
        camera_row.set_subtitle("0 = Standard-Webcam")
        camera_row.set_value(profile.settings.get("camera_index", 0))
        camera_row.connect("notify::value", self._on_camera_changed)
        camera_group.add(camera_row)

        # Ton
        sound_group = Adw.PreferencesGroup(title="Ton")
        self.add(sound_group)

        volume_row = Adw.ActionRow(title="Lautstaerke")
        self._volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 5
        )
        self._volume_scale.set_value(profile.settings.get("volume", 0.5) * 100)
        self._volume_scale.set_size_request(200, -1)
        self._volume_scale.set_valign(Gtk.Align.CENTER)
        self._volume_scale.connect("value-changed", self._on_volume_changed)
        volume_row.add_suffix(self._volume_scale)
        sound_group.add(volume_row)

        # Profil
        profile_group = Adw.PreferencesGroup(title="Profil")
        self.add(profile_group)

        name_row = Adw.EntryRow(title="Name")
        name_row.set_text(profile.name)
        name_row.connect("changed", self._on_name_changed)
        profile_group.add(name_row)

        # Kalibrierung
        cal_group = Adw.PreferencesGroup(title="Erkennung")
        self.add(cal_group)

        recal_row = Adw.ButtonRow(title="Neu kalibrieren")
        recal_row.set_start_icon_name("view-refresh-symbolic")
        recal_row.connect("activated", self._on_recalibrate)
        cal_group.add(recal_row)

        # Eltern-Bereich (Platzhalter — Polkit kommt in Phase 3)
        parent_group = Adw.PreferencesGroup(title="Eltern-Bereich")
        parent_group.set_description("Erweiterte Einstellungen (Phase 3: Polkit)")
        self.add(parent_group)

        parent_row = Adw.ButtonRow(title="Eltern-Bereich oeffnen")
        parent_row.set_start_icon_name("system-lock-screen-symbolic")
        parent_row.set_end_icon_name("go-next-symbolic")
        parent_row.set_sensitive(False)
        parent_group.add(parent_row)

        # Daten zuruecksetzen
        reset_group = Adw.PreferencesGroup()
        self.add(reset_group)

        reset_row = Adw.ButtonRow(title="Fortschritt zuruecksetzen")
        reset_row.add_css_class("destructive-action")
        reset_row.connect("activated", self._on_reset)
        reset_group.add(reset_row)

    def _on_camera_changed(self, row, _param):
        self._window.profile.settings["camera_index"] = int(row.get_value())
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_volume_changed(self, scale):
        self._window.profile.settings["volume"] = scale.get_value() / 100.0
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_name_changed(self, row):
        self._window.profile.name = row.get_text()
        self._window.save_profile()

    def _on_recalibrate(self, *args):
        self._window.profile.calibration = {}
        self._window.save_profile()
        toast = Adw.Toast(title="Kalibrierung zurueckgesetzt")
        # Toast via Window oder TrainingPage
        self._window.training_page._toast_overlay.add_toast(toast)

    def _on_reset(self, *args):
        dialog = Adw.AlertDialog()
        dialog.set_heading("Fortschritt zuruecksetzen?")
        dialog.set_body(
            "Alle Trainingsdaten und Meilensteine werden geloescht. "
            "Das kann nicht rueckgaengig gemacht werden!"
        )
        dialog.add_response("cancel", "Abbrechen")
        dialog.add_response("reset", "Zuruecksetzen")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.choose(self._window, None, self._on_reset_response)

    def _on_reset_response(self, dialog, result):
        response = dialog.choose_finish(result)
        if response == "reset":
            from models.user_data import UserProfile
            settings = self._window.profile.settings.copy()
            self._window.profile = UserProfile()
            self._window.profile.settings = settings
            self._window.save_profile()
            self._window.refresh_pages()

    def refresh(self):
        pass
```

- [ ] **Step 2: Testen**

```bash
./run.sh
```

Einstellungen-Tab pruefen: Kamera-Index, Lautstaerke, Name aendern, Neu kalibrieren, Reset-Dialog.

- [ ] **Step 3: Commit**

```bash
git add src/pages/settings_page.py
git commit -m "feat: SettingsPage mit Kamera, Ton, Profil und Reset"
```

---

### Task 16: MilestoneSystem

**Files:**
- Create: `src/systems/milestone_system.py`
- Test: `tests/test_milestone_system.py`

- [ ] **Step 1: Failing Test schreiben**

```python
# tests/test_milestone_system.py
"""Tests fuer das Meilenstein-System."""

from systems.milestone_system import MilestoneSystem
from models.user_data import UserProfile, SessionRecord


def test_first_training_milestone():
    ms = MilestoneSystem()
    profile = UserProfile(total_sessions=1)
    new = ms.check_milestones(profile)
    assert any(m.milestone_id == "first_training" for m in new)


def test_no_duplicate_milestones():
    ms = MilestoneSystem()
    profile = UserProfile(total_sessions=1)
    new1 = ms.check_milestones(profile)
    profile.milestones.extend(new1)
    new2 = ms.check_milestones(profile)
    assert not any(m.milestone_id == "first_training" for m in new2)


def test_ten_trainings_milestone():
    ms = MilestoneSystem()
    profile = UserProfile(total_sessions=10)
    new = ms.check_milestones(profile)
    assert any(m.milestone_id == "ten_trainings" for m in new)


def test_perfect_session_milestone():
    ms = MilestoneSystem()
    profile = UserProfile(total_sessions=1)
    profile.sessions = [SessionRecord(incidents=0, success=True, duration=600)]
    new = ms.check_milestones(profile)
    assert any(m.milestone_id == "perfect_session" for m in new)
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_milestone_system.py -v
```

- [ ] **Step 3: MilestoneSystem implementieren**

```python
# src/systems/milestone_system.py
"""Meilenstein-System: Einfache Achievements basierend auf echtem Fortschritt."""

from datetime import datetime
from models.user_data import UserProfile, Milestone

# Meilenstein-Definitionen: (id, name, check_function)
_MILESTONE_DEFS = [
    ("first_training", "Erstes Training",
     lambda p: p.total_sessions >= 1),
    ("ten_trainings", "10 Trainings",
     lambda p: p.total_sessions >= 10),
    ("fifty_trainings", "50 Trainings",
     lambda p: p.total_sessions >= 50),
    ("first_week", "Erste Woche geschafft",
     lambda p: p.weekly_streak >= 1),
    ("four_weeks", "4 Wochen in Folge",
     lambda p: p.weekly_streak >= 4),
    ("perfect_session", "Ganze Session ohne Vorfall",
     lambda p: any(s.incidents == 0 and s.success for s in p.sessions)),
    ("five_min_clean", "5 Minuten ohne Vorfall",
     lambda p: _longest_clean_stretch(p) >= 300),
    ("fifteen_min_clean", "15 Minuten ohne Vorfall",
     lambda p: _longest_clean_stretch(p) >= 900),
]


def _longest_clean_stretch(profile: UserProfile) -> float:
    """Laengste Session ohne Vorfall in Sekunden."""
    clean = [s.duration for s in profile.sessions if s.incidents == 0 and s.success]
    return max(clean) if clean else 0.0


class MilestoneSystem:
    """Prueft und vergibt Meilensteine."""

    def check_milestones(self, profile: UserProfile) -> list[Milestone]:
        """Prueft welche neuen Meilensteine erreicht wurden."""
        existing_ids = {m.milestone_id for m in profile.milestones}
        new_milestones = []

        for mid, name, check_fn in _MILESTONE_DEFS:
            if mid not in existing_ids and check_fn(profile):
                new_milestones.append(Milestone(
                    milestone_id=mid,
                    name=name,
                    reached_date=datetime.now().isoformat(),
                ))

        return new_milestones
```

- [ ] **Step 4: Tests ausfuehren — muessen bestehen**

```bash
PYTHONPATH=src python3 -m pytest tests/test_milestone_system.py -v
```

Expected: 4 passed

- [ ] **Step 5: MilestoneSystem in Window integrieren**

In `src/window.py`: Import hinzufuegen und im `__init__` erstellen:

```python
from systems.milestone_system import MilestoneSystem

# Im __init__ nach adaptive_difficulty:
self.milestone_system = MilestoneSystem()
```

- [ ] **Step 6: Meilenstein-Check in TrainingPage._finish_session ergaenzen**

In `src/pages/training_page.py`, in `_finish_session` nach dem Adaptive-Difficulty-Block:

```python
        # Meilensteine pruefen
        new_milestones = self._window.milestone_system.check_milestones(profile)
        for ms in new_milestones:
            profile.milestones.append(ms)
            toast = Adw.Toast(title=f"Meilenstein: {ms.name}")
            toast.set_timeout(5)
            self._toast_overlay.add_toast(toast)
```

- [ ] **Step 7: Commit**

```bash
git add src/systems/milestone_system.py tests/test_milestone_system.py src/window.py src/pages/training_page.py
git commit -m "feat: MilestoneSystem mit 8 Achievements und Toast-Benachrichtigungen"
```

---

### Task 17: ProgressPage (Basisversion)

**Files:**
- Modify: `src/pages/progress_page.py`

- [ ] **Step 1: ProgressPage implementieren**

```python
# src/pages/progress_page.py
"""Fortschritts-Seite mit Wochenstatistiken und Meilensteinen."""

from datetime import datetime, timedelta
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class ProgressPage(Gtk.Box):
    """Zeigt Trainingsfortschritt: Wochenuebersicht und Meilensteine."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window

        scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(scroll)

        self._clamp = Adw.Clamp(maximum_size=600)
        scroll.set_child(self._clamp)

        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self._content.set_margin_top(24)
        self._content.set_margin_bottom(24)
        self._content.set_margin_start(12)
        self._content.set_margin_end(12)
        self._clamp.set_child(self._content)

        self._build_empty_state()

    def _build_empty_state(self):
        self._status_page = Adw.StatusPage(
            title="Noch keine Trainings",
            description="Starte dein erstes Training um Fortschritt zu sehen",
            icon_name="starred-symbolic",
        )
        self._content.append(self._status_page)

    def refresh(self):
        """Aktualisiert die Ansicht mit aktuellen Daten."""
        profile = self._window.profile

        # Content leeren
        while child := self._content.get_first_child():
            self._content.remove(child)

        if profile.total_sessions == 0:
            self._build_empty_state()
            return

        # Wochenuebersicht
        week_group = Adw.PreferencesGroup(title="Diese Woche")
        self._content.append(week_group)

        sessions_this_week = self._count_sessions_this_week()
        target = profile.trainings_per_week

        progress_row = Adw.ActionRow(
            title=f"{sessions_this_week}/{target} Trainings geschafft"
        )
        week_group.add(progress_row)

        if profile.total_sessions > 0:
            clean_pct = (profile.successful_sessions / profile.total_sessions) * 100
            clean_row = Adw.ActionRow(
                title=f"{clean_pct:.0f}% erfolgreich"
            )
            week_group.add(clean_row)

        total_min = int(profile.total_training_time / 60)
        time_row = Adw.ActionRow(title=f"{total_min} Minuten trainiert (gesamt)")
        week_group.add(time_row)

        # Streak
        if profile.weekly_streak > 0:
            streak_group = Adw.PreferencesGroup(title="Wochen-Streak")
            self._content.append(streak_group)
            streak_row = Adw.ActionRow(
                title=f"{profile.weekly_streak} Wochen in Folge",
                subtitle=f"Bester: {profile.best_weekly_streak} Wochen",
            )
            streak_group.add(streak_row)

        # Meilensteine
        if profile.milestones:
            ms_group = Adw.PreferencesGroup(title="Meilensteine")
            self._content.append(ms_group)
            for ms in profile.milestones:
                row = Adw.ActionRow(title=ms.name)
                row.set_subtitle(ms.reached_date[:10] if ms.reached_date else "")
                row.add_prefix(
                    Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                )
                ms_group.add(row)

    def _count_sessions_this_week(self) -> int:
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        count = 0
        for s in self._window.profile.sessions:
            try:
                ts = datetime.fromisoformat(s.timestamp)
                if ts >= week_start:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count
```

- [ ] **Step 2: Testen**

```bash
./run.sh
```

Fortschritt-Tab: Zeigt "Noch keine Trainings" initial. Nach einem Training: Wochenuebersicht mit Statistiken und Meilensteinen.

- [ ] **Step 3: Commit**

```bash
git add src/pages/progress_page.py
git commit -m "feat: ProgressPage mit Wochenstatistiken und Meilensteinen"
```

---

### Task 18: Keyboard-Shortcuts + Abschluss Phase 2

**Files:**
- Modify: `src/main.py`, `src/window.py`

- [ ] **Step 1: Keyboard-Shortcuts in main.py**

In `ZungenTrainerApp.do_activate` oder als separate Methode, nach `win.present()`:

```python
    def do_activate(self):
        from window import ZungenTrainerWindow

        win = self.props.active_window
        if not win:
            win = ZungenTrainerWindow(application=self)
            self._setup_shortcuts(win)
        win.present()

    def _setup_shortcuts(self, win):
        # Ctrl+Q: Beenden
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

        # Space: Training starten/stoppen
        toggle_action = Gio.SimpleAction.new("toggle-training", None)
        toggle_action.connect("activate", lambda *_: win.toggle_training())
        win.add_action(toggle_action)
        self.set_accels_for_action("win.toggle-training", ["space"])

        # Escape: Training abbrechen
        stop_action = Gio.SimpleAction.new("stop-training", None)
        stop_action.connect("activate", lambda *_: win.training_page.stop_training())
        win.add_action(stop_action)
        self.set_accels_for_action("win.stop-training", ["Escape"])
```

- [ ] **Step 2: toggle_training in Window**

In `src/window.py`:

```python
    def toggle_training(self):
        """Space-Taste: Training starten oder stoppen."""
        from services.session_service import SessionState
        if self.training_page._session.state == SessionState.IDLE:
            self.view_stack.set_visible_child(self.training_page)
            self.training_page.start_training()
        else:
            self.training_page.stop_training()
```

- [ ] **Step 3: Testen**

```bash
./run.sh
```

- Ctrl+Q beendet die App
- Space startet/stoppt das Training
- Escape stoppt das Training

- [ ] **Step 4: Commit**

```bash
git add src/main.py src/window.py
git commit -m "feat: Keyboard-Shortcuts (Ctrl+Q, Space, Escape)"
```

---

## Self-Review Checklist

**Spec-Abdeckung:**
- [x] Erkennungs-Pipeline (HSV, Kalibrierung, One-Euro-Filter, CLAHE) → Tasks 2-6
- [x] 3 Views mit ViewSwitcher → Task 13
- [x] TrainingPage mit OSD → Task 14
- [x] Alarm-System (vereinfacht, kein WARNING) → Task 9
- [x] Hintergrund-Modus → nicht in Phase 2 (Phase 3)
- [x] Adaptive Schwierigkeit → Task 11
- [x] Meilensteine → Task 16
- [x] Einstellungen mit Reset → Task 15
- [x] Persistenz (JSON, atomar) → Task 10
- [x] View-Wechsel pausiert Training → Task 14
- [x] Tastaturkuerzel → Task 18
- [ ] Onboarding → Phase 3
- [ ] Eltern-Bereich (Polkit) → Phase 3
- [ ] Trainingsplan + Wochen-Streak → Phase 3
- [ ] Fortschritts-Trend (Balkendiagramm) → Phase 3
- [ ] Flatpak-Build → Phase 3
- [ ] App-Icon → Phase 3

**Placeholder-Scan:** Keine TBDs, TODOs oder "implement later" gefunden. Alle Code-Bloecke sind vollstaendig.

**Typ-Konsistenz:** `AdaptiveDifficulty.get_params()` → dict mit keys `reaction_time`, `resume_delay`, `sensitivity`, `cooldown` — konsistent in Tasks 11, 14. `SessionService` States: IDLE, RUNNING, DETECTED, COOLDOWN — konsistent in Tasks 9, 14. `UserProfile.calibration` dict mit `lower`/`upper` keys — konsistent in Tasks 6, 10, 14, 15.
