# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt

ZungenTrainer v2 — GTK 4 / Libadwaita App (Python), erkennt per Webcam Zungenprotrusion und pausiert Medienplayer + Piepton. Hilft Kindern, sich die Gewohnheit abzugewoehnen.

UI-Sprache ist Deutsch (Labels, Statusmeldungen, Kommentare, Docstrings).

App-ID: `de.yoshimintos.ZungenTrainer`. Lizenz: GPL-3.0-or-later.

## Befehle

```bash
# Lokal starten
./run.sh

# Erkennung standalone testen (OpenCV Debug-Fenster)
python3 src/debug_detector.py

# Tests
PYTHONPATH=src python3 -m pytest tests/ -v

# Flatpak bauen und installieren
./build-flatpak.sh

# Flatpak starten
flatpak run de.yoshimintos.ZungenTrainer
```

## Architektur

### Window als Mediator

`ZungenTrainerWindow` besitzt DataStore, UserProfile, AdaptiveDifficulty, MilestoneSystem, StreakSystem. Pages referenzieren Window und greifen ueber es auf gemeinsamen Zustand zu.

### Erkennungs-Pipeline

MediaPipe Face Landmarker (VIDEO-Modus, NUR fuer Landmarks) -> Mund-ROI -> CLAHE -> HSV-Farbsegmentierung -> One-Euro-Filter -> tongue_out. Blendshapes werden NICHT fuer Zungenerkennung genutzt.

### Services

| Service | Datei | Aufgabe |
|---------|-------|---------|
| CameraService | `src/services/camera_service.py` | Daemon-Thread, 1080p OpenCV, Lock-basierter Frame-Handoff |
| DetectorService | `src/services/detector_service.py` | MediaPipe + HSV Pipeline -> tongue_out |
| SessionService | `src/services/session_service.py` | IDLE -> RUNNING -> DETECTED -> COOLDOWN |
| SoundService | `src/services/sound_service.py` | GStreamer Piepton |
| MprisService | `src/services/mpris_service.py` | D-Bus MPRIS2 Mediensteuerung |

### Threading

CameraService = Daemon-Thread. Alles andere auf GTK-Main-Thread. Frame-Handoff ueber `threading.Lock`. Trainings-Loop: `GLib.timeout_add(33, ...)` (~30 FPS).

### Alarm-System

Kein WARNING-Zwischenschritt. Piep + Medienpause gleichzeitig bei DETECTED. Multi-Frame-Bestaetigung (3 Frames) vor Transition. Sofortiger Reset bei Zunge-zurueck.

### Datenpersistenz

`$XDG_DATA_HOME/zungentrainer/profile.json`. Atomares Schreiben (temp + `os.replace()`). Schema-Versionierung mit append-only Migrations. `ZUNGENTRAINER_DATA_DIR` Override fuer lokale Entwicklung.

## Technische Constraints

- MediaPipe VIDEO-Modus: Timestamps MUESSEN monoton steigend sein
- Kein `tongueOut`-Blendshape in MediaPipe
- Import-Konvention: `src/` in `sys.path`, flache Imports (`from services.camera_service import CameraService`)
- Flatpak: `--device=all` fuer Kamera, `--talk-name=org.mpris.MediaPlayer2.*`

## GNOME HIG Compliance

HIG-Review-Skill unter `skills/gnome-hig-review/` — nach UI-Aenderungen laufen lassen. Wichtigste Regeln:
- AdwBanner fuer persistente Zustaende, AdwToast fuer transiente Events
- Max 1 `.suggested-action` oder `.destructive-action` pro View
- Alle Header-Bar-Controls brauchen Tooltips
- Accessible Names auf allen nicht-textuellen Elementen
- Unicode korrekt: Gedankenstrich (U+2014), Ellipsis (U+2026), NNBSP (U+202F) vor Einheiten

## Tech-Stack

Python 3.13+, GTK 4.0, Libadwaita 1, OpenCV (headless), MediaPipe (>=0.10.30), NumPy, GStreamer 1.0, GLib/Gio (D-Bus MPRIS2). Flatpak Runtime: GNOME Platform/SDK 49.
