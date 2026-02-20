# ZungenTrainer

Zungen-Haltungstrainer mit Webcam-Erkennung. Die App erkennt per Webcam, wenn die Zunge aus dem Mund hängt, gibt einen Piepton aus und pausiert laufende Musik. Ein Gamification-System mit Leveln, Abzeichen und sammelbaren Kreaturen ("Zungenfreunde") motiviert zum regelmäßigen Training.

Gedacht als Unterstützung bei myofunktioneller Therapie (Logopädie / Kieferorthopädie).

![Screenshot](https://raw.githubusercontent.com/yoshimintos/zungentrainer/main/data/icons/hicolor/scalable/apps/de.yoshimintos.ZungenTrainer.svg)

## Funktionen

### Echtzeit-Zungenerkennung

- Webcam-basierte Gesichtsanalyse mit [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker) Face Landmarks
- Kombiniert ~10 Signale (innere/äußere Lippenlücke, Mundfläche, Kieferöffnung, Blendshapes) zu einem gewichteten Composite-Score
- Dynamische Baseline-Kalibrierung: Die ersten ~2 Sekunden jeder Sitzung messen den Ruhezustand des Gesichts. Danach wird nur die Abweichung vom persönlichen Ruhewert als Auslöser verwendet
- 5-Frame zeitliche Glättung gegen Flackern

### Alarm-System

- Konfigurierbarer Piepton über GStreamer (Frequenz und Lautstärke einstellbar)
- Automatische Pausierung aller laufenden Medienplayer über D-Bus MPRIS2 (Spotify, Firefox, VLC, etc.) bei Erkennung, mit Wiederaufnahme nach Abklingzeit

### 10-Stufen Schwierigkeitssystem

Auslöse-Dauer (Zunge draußen bis Alarm) und Abklingzeit sind fest auf **5 Sekunden** gesetzt. Die Schwierigkeit skaliert über Erkennungspause, Empfindlichkeit und erlaubte Vorfälle:

| Parameter | Level 1 (leicht) | Level 10 (schwer) |
|-----------|------------------:|-------------------:|
| Erkennungspause nach Vorfall | 0 s | 20 s |
| Reaktionsverzögerung | 3.0 s | 0 s |
| Empfindlichkeits-Multiplikator | 3.5x | 1.2x |
| Max. erlaubte Vorfälle | unbegrenzt | 3 |
| Mindest-Sitzungsdauer | 10 min | 30 min |

XP-Vergabe: 1 XP pro Trainingsminute, Boni für wenige Vorfälle und erfolgreiche Sitzungen, Level-Multiplikator für höhere Stufen.

### Sammelbare Zungenfreunde

12 Kreaturen (Schnecki, Fröschli, Chameli, Eulchen, Drachi, Pingui, Koali, Foxie, Phoenix, Einhorn, Sternchen, Regenbogi), die durch Level-Aufstiege, Streaks und perfekte Sitzungen freigeschaltet werden. Jede Kreatur wird prozedural mit Cairo gezeichnet. Goldene Varianten werden bei Streak-Meilensteinen (alle 7 Tage) vergeben.

### 15 Abzeichen

Freischaltbar durch Sitzungsanzahl, Erfolgsserien, perfekte Sitzungen (0 Vorfälle), Streak-Tage und Trainingszeit-Meilensteine.

### Vier App-Seiten

- **Training**: Kamera-Feed mit Start/Stop, Timer, Vorfalls-Zähler und Score-Anzeige
- **Fortschritt**: Level, XP-Balken, aktuelle Schwierigkeitsparameter und Gesamtstatistiken
- **Sammlung**: Zungenfreunde-Galerie und Abzeichen-Übersicht
- **Einstellungen**: Kamera-Auswahl, Piepton-Konfiguration, Test-Modus (Auslöse-Dauer einmalig überschreiben), Name ändern, Fortschritt zurücksetzen

## Technischer Aufbau

### Überblick

```
bin/zungentrainer          # Launcher (erkennt Flatpak vs. lokale Entwicklung)
src/
  main.py                  # Adw.Application, Entry Point
  window.py                # Zentraler Mediator: hält DataStore, Profile, Gamification-Systeme
  services/
    camera_service.py      # Threaded OpenCV-Capture mit Lock-basiertem Frame-Zugriff
    detector_service.py    # MediaPipe FaceLandmarker → Composite-Score + Baseline-Kalibrierung
    session_service.py     # Zustandsmaschine (IDLE → RUNNING → DETECTED → COOLDOWN)
    sound_service.py       # GStreamer audiotestsrc Piepton
    mpris_service.py       # D-Bus MPRIS2 Mediensteuerung
  gamification/
    level_system.py        # 10 Level mit XP-Tabelle und Schwierigkeitsparametern
    badge_system.py        # 15 Abzeichen mit Lambda-Freischaltbedingungen
    creature_system.py     # 12 Kreaturen mit Cairo-Zeichenfunktionen
  pages/
    training_page.py       # Kamera-Feed, Trainingssteuerung, Sitzungsauswertung
    progress_page.py       # Level/XP/Statistik-Anzeige
    collection_page.py     # Zungenfreunde- und Abzeichen-Galerie
    settings_page.py       # Einstellungen mit AdwPreferencesPage
  models/
    user_data.py           # Dataclasses: UserProfile, SessionRecord, Badge, Creature
    persistence.py         # JSON-Speicherung mit atomarem Schreiben (temp + rename)
  utils/
    camera_paintable.py    # Gdk.Paintable-Subklasse für OpenCV→GTK4 Frame-Anzeige
data/
  face_landmarker.task     # MediaPipe-Modell (~4 MB)
  de.yoshimintos.ZungenTrainer.desktop
  de.yoshimintos.ZungenTrainer.metainfo.xml
  icons/                   # App-Icons (SVG)
```

### Architektur-Muster

**Window als Mediator:** `ZungenTrainerWindow` besitzt den `DataStore`, das `UserProfile` und alle drei Gamification-Systeme. Jede Page bekommt eine Referenz auf das Window und greift darüber auf gemeinsamen Zustand zu (`self._window.profile`, `self._window.level_system`, etc.).

**Trainings-Loop:** `TrainingPage` startet einen `GLib.timeout_add(33, ...)` Callback (~30 FPS), der auf dem GTK-Main-Thread läuft. Jeder Tick: Frame von `CameraService` holen → durch `DetectorService` analysieren → `SessionService.update()` mit Ergebnis füttern → UI aktualisieren.

**Kamera-Threading:** `CameraService` läuft in einem Daemon-Thread mit `cv2.VideoCapture`. Frames werden über einen `threading.Lock` thread-sicher an den GTK-Main-Thread übergeben. `CameraPaintable` konvertiert BGR→RGB und erzeugt `Gdk.MemoryTexture` für die Anzeige.

**Erkennungs-Pipeline:** `DetectorService` extrahiert Signale aus MediaPipe Face Landmarks und Blendshapes, berechnet einen gewichteten Score, kalibriert eine Baseline über die ersten 60 Frames (Median), und vergleicht den geglätteten Score gegen `baseline + baseline * sensitivity_multiplier`.

**Sitzungs-Zustandsmaschine:** `SessionService` durchläuft IDLE → RUNNING → DETECTED → COOLDOWN → PAUSED → RUNNING. Der PAUSED-State setzt die Erkennung für `detection_pause` Sekunden aus (Level-abhängig, 0–20 s). Löst Callbacks für Alarm-Start (`on_alarm`) und Alarm-Ende (`on_alarm_end`) aus. TrainingPage verdrahtet diese mit SoundService und MprisService.

**Datenpersistenz:** JSON-Profil unter `$XDG_DATA_HOME/zungentrainer/profile.json`. Atomares Schreiben über temporäre Datei + `os.replace()`. Beim lokalen Entwickeln setzt `run.sh` die Umgebungsvariable `ZUNGENTRAINER_DATA_DIR` auf das lokale `data/`-Verzeichnis.

**Schema-Versionierung:** Jedes gespeicherte Profil enthält ein `schema_version`-Feld. Beim Laden prüft `persistence.py`, ob Migrationen nötig sind, erstellt ein Backup (`profile.v{alt}.json.bak`) und wendet die Migrationskette sequenziell an. So bleiben Profildaten bei App-Updates erhalten, auch wenn sich das Datenformat ändert.

## Installation

### Option 1: Flatpak bauen und installieren (empfohlen)

Voraussetzungen installieren:

```bash
# Flathub-Repository hinzufügen (falls noch nicht vorhanden)
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# GNOME Runtime, SDK und Flatpak-Builder installieren
flatpak install flathub org.gnome.Platform//49
flatpak install flathub org.gnome.Sdk//49
flatpak install flathub org.flatpak.Builder

# pip3 wird zum Herunterladen der Python-Wheels benötigt
# (auf Fedora/Ubuntu ist es normalerweise schon installiert)
# Fedora: sudo dnf install python3-pip
# Ubuntu: sudo apt install python3-pip
```

Bauen und installieren:

```bash
git clone https://github.com/yoshimintos/zungentrainer.git
cd zungentrainer
./build-flatpak.sh
```

Das Skript lädt automatisch die Python-Abhängigkeiten (MediaPipe, NumPy, OpenCV) als Wheels herunter, baut das Flatpak und installiert es für den aktuellen Benutzer.

Starten:

```bash
flatpak run de.yoshimintos.ZungenTrainer
```

### Option 2: Flatpak-Bundle weitergeben

```bash
./build-flatpak.sh bundle
```

Erzeugt eine `ZungenTrainer.flatpak`-Datei. Auf dem Zielrechner:

```bash
# Einmalig: GNOME Runtime installieren
flatpak install flathub org.gnome.Platform//49

# Bundle installieren
flatpak install ZungenTrainer.flatpak
```

### Option 3: Lokal ohne Flatpak ausführen

Voraussetzungen:

- Python 3.11+
- GTK 4 und Libadwaita 1 (Systempakete)
- GStreamer 1.0 (Systempakete)

```bash
# Systempakete (Fedora)
sudo dnf install gtk4-devel libadwaita-devel gstreamer1-devel \
    gstreamer1-plugins-base python3-gobject

# Systempakete (Ubuntu/Debian)
sudo apt install libgtk-4-dev libadwaita-1-dev gstreamer1.0-tools \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 \
    gir1.2-gst-1.0

# Python-Abhängigkeiten
pip install numpy opencv-python mediapipe

# Starten
git clone https://github.com/yoshimintos/zungentrainer.git
cd zungentrainer
./run.sh
```

Das Profil wird bei lokaler Ausführung unter `./data/profile.json` gespeichert (nicht in `~/.local/share`).

### Kamera-Zugriff

Die App benötigt Zugriff auf eine Webcam. Falls die Standardkamera (Index 0) nicht funktioniert, kann der Kamera-Index in den Einstellungen geändert werden. Der CameraService probiert bei Fehlschlag automatisch die Indizes 0–4 durch.

Im Flatpak ist Kamera-Zugriff über `--device=all` in den Finish-Args freigegeben.

## Update

Das Benutzerprofil (`profile.json`) liegt in `$XDG_DATA_HOME/zungentrainer/` und überlebt App-Updates. Wenn sich das Datenformat zwischen Versionen ändert, migriert die App das Profil beim nächsten Start automatisch:

1. Backup der alten Datei als `profile.v{alte_version}.json.bak`
2. Sequenzielle Anwendung aller nötigen Migrationsschritte
3. Speicherung des aktualisierten Profils

### Flatpak aktualisieren

```bash
# Neu bauen und installieren (überschreibt die vorherige Version)
cd PFAD_WOHIN_GEPULLT_WURDE
git pull
./build-flatpak.sh
```

Oder bei Nutzung eines `.flatpak`-Bundles: Einfach das neue Bundle installieren — Flatpak aktualisiert die App, das Profil bleibt erhalten.

## Lizenz

GPL-3.0-or-later
