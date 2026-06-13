# ZungenTrainer

Unauffaelliger Hintergrund-Trainer, der per Webcam erkennt wenn die Zunge
heraushaengt. Bei erkannter Zunge piept die App und pausiert laufende Medien.
Wenn keine Medien laufen, spielt sie einen stoerenden Ton, bis die Zunge wieder
drin ist.

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
- **Stoerender Ton** wenn keine Medien laufen
- **Minimale Oberflaeche** — eine Ueberwachungsseite plus Einstellungen im Menue
- **Onboarding** — 5-Schritt-Assistent beim ersten Start

## Tastaturkuerzel

| Kuerzel | Funktion |
|---------|----------|
| Space | Ueberwachung starten / stoppen |
| Escape | Ueberwachung abbrechen |
| Ctrl+Q | App beenden |

## Entwicklung & Debugging

Der Live-Test der Erkennung ist in [docs/debug-workflow.md](docs/debug-workflow.md)
beschrieben. Unit-Tests laufen mit:

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

## Lizenz

GPL-3.0-or-later
