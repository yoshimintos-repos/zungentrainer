# AGENTS.md

Codex project guidance for this repository. Treat this file as the canonical
agent entry point. `CLAUDE.md` is kept only as a compatibility pointer.

## Project

ZungenTrainer v2 is a GTK 4 / Libadwaita app written in Python. It detects
tongue protrusion through the webcam and then pauses media players plus plays a
short beep. The app is intended to help children unlearn the habit of tongue
protrusion.

UI language is German. User-facing labels, status messages, comments, and
docstrings should stay German unless a surrounding file clearly uses English for
technical context.

App ID: `de.yoshimintos.ZungenTrainer`
License: `GPL-3.0-or-later`

## Working Rules

- Do not change application code when the task is only about Codex, agent files,
  docs, or workflow metadata.
- Keep edits small and aligned with the existing Python/GTK style.
- Use `rg`/`rg --files` for discovery.
- Do not touch generated build output such as `.flatpak-repo/`,
  `.flatpak-builder/`, `build/`, `dist/`, or `*.flatpak`.
- `docs/superpowers/` contains historical Claude/Superpowers planning artifacts.
  Use them as context only; they are not active workflow instructions unless the
  user explicitly asks to resume one of those plans.
- Keep `CLAUDE.md` as a compatibility file only. Put durable repo guidance in
  this `AGENTS.md`.

## Commands

```bash
# Run locally
./run.sh

# Test detection standalone with OpenCV debug window
python3 src/debug_detector.py

# Run tests
PYTHONPATH=src python3 -m pytest tests/ -v

# Build and install Flatpak
./build-flatpak.sh build

# Refresh pinned Python wheels after Flatpak dependency changes
./build-flatpak.sh deps-refresh

# Run Flatpak
flatpak run de.yoshimintos.ZungenTrainer
```

## Verification

- For non-UI Python logic, run the focused relevant tests first, then the full
  suite when the change touches shared systems or services:
  `PYTHONPATH=src python3 -m pytest tests/ -v`
- For UI changes, also inspect the GTK/Libadwaita behavior manually where
  possible and run the project skill `gnome-hig-review`.
- For Flatpak, use `./build-flatpak.sh build` when packaging files, app metadata,
  permissions, or runtime dependencies change.
- After changing `flatpak/requirements.txt`, run `./build-flatpak.sh deps-refresh`
  before building.

## Architecture

### Window as Mediator

`ZungenTrainerWindow` owns `DataStore`, `UserProfile`, `AdaptiveDifficulty`,
`MilestoneSystem`, and `StreakSystem`. Pages reference the window and access
shared state through it.

### Detection Pipeline

MediaPipe Face Landmarker in VIDEO mode is used only for landmarks:

`MediaPipe Face Landmarker -> mouth ROI -> CLAHE -> HSV color segmentation -> One-Euro filter -> tongue_out`

Blendshapes are not used for tongue detection.

### Services

| Service | File | Responsibility |
| --- | --- | --- |
| `CameraService` | `src/services/camera_service.py` | Daemon thread, 1080p OpenCV, lock-based frame handoff |
| `DetectorService` | `src/services/detector_service.py` | MediaPipe + HSV pipeline -> `tongue_out` |
| `SessionService` | `src/services/session_service.py` | `IDLE -> RUNNING -> DETECTED -> COOLDOWN` |
| `SoundService` | `src/services/sound_service.py` | GStreamer beep |
| `MprisService` | `src/services/mpris_service.py` | D-Bus MPRIS2 media control |

### Threading

`CameraService` runs as a daemon thread. Everything else should remain on the
GTK main thread. Frame handoff uses `threading.Lock`. The training loop uses
`GLib.timeout_add(33, ...)` for roughly 30 FPS.

### Alarm System

There is no intermediate WARNING state. Beep and media pause happen together on
`DETECTED`. A three-frame confirmation is required before transition. Reset
immediately when the tongue is back.

### Persistence

User data lives at `$XDG_DATA_HOME/zungentrainer/profile.json`. Writes are atomic
via temp file plus `os.replace()`. Schema migrations are append-only.
`ZUNGENTRAINER_DATA_DIR` overrides the location for local development and tests.

## Technical Constraints

- MediaPipe VIDEO mode timestamps must be monotonically increasing.
- MediaPipe has no usable `tongueOut` blendshape for this app.
- Import convention: `src/` is on `sys.path`; use flat imports such as
  `from services.camera_service import CameraService`.
- Flatpak needs `--device=all` for the camera and
  `--talk-name=org.mpris.MediaPlayer2.*` for media players.

## GNOME HIG

The project-local Codex skill lives at `.codex/skills/gnome-hig-review/`. Use it
after UI changes and for GNOME design reviews. The older copy under
`skills/gnome-hig-review/` is kept for compatibility with prior tooling.

Key rules to preserve:

- Use `AdwBanner` for persistent states and `AdwToast` for transient events.
- Use at most one `.suggested-action` or `.destructive-action` per view.
- Header-bar controls need tooltips.
- Non-textual elements need accessible names.
- Use correct Unicode in user-facing German text: em dash where intended,
  ellipsis `...` only when the existing file is ASCII-only, otherwise Unicode
  ellipsis, and narrow no-break space before units where the file already uses
  Unicode typography.

## Tech Stack

Python 3.13+, GTK 4.0, Libadwaita 1, OpenCV headless, MediaPipe >= 0.10.30,
NumPy, GStreamer 1.0, GLib/Gio for D-Bus MPRIS2. Flatpak runtime:
GNOME Platform/SDK 49.
