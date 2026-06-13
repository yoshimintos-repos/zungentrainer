# ZungenTrainer

Trainings-App die per Webcam erkennt wenn die Zunge heraushaengt und dann Medienplayer pausiert + einen Piepton gibt. Hilft Kindern, sich die Gewohnheit der Zungenprotrusion abzugewoehnen.

## Installation

### Auf diesem Rechner (Entwicklung)

```bash
# Voraussetzungen
pip install numpy opencv-python-headless mediapipe

# Starten
./run.sh
```

### Als Flatpak (empfohlen)

```bash
# Voraussetzungen: Flatpak + GNOME Runtime
flatpak install flathub org.gnome.Platform//49
flatpak install flathub org.gnome.Sdk//49
flatpak install flathub org.flatpak.Builder

# Bauen und installieren
./build-flatpak.sh build

# Python-Wheel-Cache bei Dependency-Aenderungen neu erstellen
./build-flatpak.sh deps-refresh

# Starten
flatpak run de.yoshimintos.ZungenTrainer
```

### Auf einem anderen Geraet installieren

1. Bundle erstellen:
   ```bash
   ./build-flatpak.sh bundle
   ```

2. `ZungenTrainer.flatpak` + `install-remote.sh` auf das Zielgeraet kopieren (USB-Stick, Netzwerk, etc.)

3. Auf dem Zielgeraet:
   ```bash
   chmod +x install-remote.sh
   ./install-remote.sh ZungenTrainer.flatpak
   ```

   Das Skript installiert automatisch die GNOME Runtime falls noetig.

4. Starten ueber die App-Uebersicht oder:
   ```bash
   flatpak run de.yoshimintos.ZungenTrainer
   ```

## Funktionen

- **Zungenerkennung** per Webcam (HSV-Farbsegmentierung + geometrische Analyse)
- **Mediensteuerung** — pausiert Spotify, Firefox etc. bei Zungenprotrusion
- **Piepton-Alarm** bei erkannter Zunge
- **Adaptive Schwierigkeit** — passt sich automatisch dem Trainingsfortschritt an
- **Meilensteine** — Achievements fuer regelmaessiges Training
- **Wochen-Streak** — trackt Trainingsplan-Erfuellung
- **Onboarding** — 5-Schritt-Assistent beim ersten Start
- **Eltern-Bereich** — Polkit-geschuetzte Einstellungen fuer Trainingsplan und Schwierigkeit

## Tastaturkuerzel

| Kuerzel | Funktion |
|---------|----------|
| Space | Training starten / stoppen |
| Escape | Training abbrechen |
| Ctrl+Q | App beenden |

## Entwicklung & Debugging

Der Live-Test der Erkennung ist in [docs/debug-workflow.md](docs/debug-workflow.md)
beschrieben. Unit-Tests laufen mit:

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

## Lizenz

GPL-3.0-or-later
