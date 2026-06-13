# Debug-Workflow

Dieser Ablauf ist fuer reale Tests mit Kamera gedacht. Die Unit-Tests decken die
reine Logik ab, ersetzen aber keinen Live-Test der Erkennung.

## Vorbereitung

```bash
pip install numpy opencv-python-headless mediapipe pytest
```

Das MediaPipe-Modell muss unter `data/face_landmarker.task` liegen. Der lokale
Launcher setzt `ZUNGENTRAINER_DATA_DIR` automatisch auf `data/`.

Fuer `src/debug_detector.py` wird ein OpenCV-Fenster verwendet. Wenn dieser
Standalone-Debugger genutzt wird, installiere statt `opencv-python-headless`
das Paket `opencv-python`.

## Tests

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
python3 -m compileall -q src tests
```

## Live-Test der Erkennung

```bash
./run.sh
```

Beim ersten Training:

1. Baseline abwarten und den Mund geschlossen halten.
2. Bei der Aufforderung kurz die Zunge zeigen.
3. Danach mit geschlossenem Mund, Sprechen, Gaehnen und echter Protrusion testen.
4. Pruefen, dass bei geschlossenem Mund kein Alarm ausloest.
5. Pruefen, dass Piep und Medienpause erst nach durchgehender Erkennung plus
   `reaction_time` ausloesen.

Detektor-Logs liegen unter:

```bash
~/.local/share/zungentrainer/detektor.log
```

Wichtige Log-Muster:

- `ZU score_reset`: Mund gilt als geschlossen, Score wird auf 0 gesetzt.
- `OFFEN gap=... bulge=... smooth=... thr=...`: aktive Erkennung im
  Lippenspalt-ROI.
- `Kalibrierung abgeschlossen`: Danach folgt eine kurze Grace-Period ohne Alarm.

## Standalone-Detektor

```bash
python3 src/debug_detector.py
```

Das ist der schnellste Weg, um Kamera, MediaPipe-Modell und Rohdetektion ohne
die komplette App-Schale zu pruefen.

## Polkit im lokalen Entwicklungsmodus

Der Eltern-Bereich ist standardmaessig fail-closed, wenn Polkit nicht erreichbar
ist oder einen Fehler liefert. Fuer lokale Entwicklung ohne Polkit-Agent kann
der Schutz explizit geoeffnet werden:

```bash
ZUNGENTRAINER_POLKIT_DEV_FALLBACK=1 ./run.sh
```
