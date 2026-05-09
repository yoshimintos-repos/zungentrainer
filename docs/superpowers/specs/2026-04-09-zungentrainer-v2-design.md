# ZungenTrainer v2 — Design-Spezifikation

## Kontext

ZungenTrainer ist eine GTK 4 / Libadwaita App (Python), die per Webcam erkennt wenn die Zunge heraushaengt und dann Medienplayer pausiert + einen Piepton gibt. Die App hilft Kindern (und anderen), sich die Gewohnheit abzugewoehnen, die Zunge raushängen zu lassen.

Die alte Version (in `old_apps/zungentrainer/`) hatte eine unzuverlaessige Zungenerkennung basierend auf MediaPipe-Blendshapes. Trotz mehrerer Iterationen (gewichteter Composite-Score, Suppressoren, 3-Signal-Ansatz mit Korroboration + Veto) war die Erkennung zu unzuverlaessig — zu viele False Positives bei Sprechen/Gaehnen und False Negatives bei subtiler Zungenprotrusion.

Dieser Neustart ersetzt die Erkennung durch einen Hybrid-Ansatz (HSV-Farbsegmentierung + spaeteres ML-Modell), vereinfacht die App (keine Gamification, adaptive Schwierigkeit statt Level), und folgt strikt den GNOME Human Interface Guidelines.

## Zielgruppe

Primaer: Kinder im Schulalter (ab ca. 10 Jahre) mit myofunktioneller Therapie-Indikation.
Sekundaer: Jeder der die Gewohnheit der Zungenprotrusion abgewoehnen moechte.

Die App wird von Kindern bedient, aber von Eltern eingerichtet und konfiguriert.

---

## 1. Erkennungs-Pipeline

### 1.1 Uebersicht

```
Webcam (1080p, 30 FPS)
  -> MediaPipe Face Landmarker (VIDEO-Modus)
  -> Mund-Landmarks extrahieren
  -> Mund-ROI ausschneiden
  -> CLAHE (adaptive Kontrastverbesserung)
  -> Erkennungs-Backend (austauschbar):
     Phase 1: HSV-Farbsegmentierung
     Phase 2: CNN (MobileNet-Lite)
  -> Score berechnen (tongue_ratio + Position)
  -> One-Euro-Filter (adaptive Glaettung)
  -> Entscheidung: tongue_out (bool) + confidence (float)
```

### 1.2 Kameraaufloesung: 1080p

1080p statt 720p (alte App). Grund: Der Mund-ROI hat bei 1080p ca. 150-300px Breite vs. 100-200px bei 720p. Mehr Pixel im Mund-ROI = bessere Farb-Segmentierung und mehr Detail fuer ML-Features. MediaPipe laeuft auf moderner Hardware problemlos mit 1080p.

### 1.3 Kalibrierung

Zwei Schritte, beim ersten Start interaktiv, danach automatisch:

**Schritt 1 — Baseline (2 Sekunden):**
- Anweisung: "Mund zu, ganz normal schauen"
- Erfasst: Baseline-HSV der Lippen, Mundform in Ruhe (Landmark-Abstaende), Beleuchtungsniveau

**Schritt 2 — Zungenfarbe (2 Sekunden):**
- Anweisung: "Zeig mal kurz die Zunge"
- Erfasst: HSV-Range der Zunge (personalisiert), Differenz Zunge vs. Lippen
- Daraus: Erkennungsschwellwert berechnen

Bei Folge-Sessions: HSV-Ranges der Zunge aus dem Profil laden. Baseline (Lippen-HSV, Mundform) wird in den ersten 2 Sekunden still neu erfasst (gleicher Algorithmus wie Schritt 1, ohne UI-Anweisung). Die Zungenfarbe wird NICHT automatisch rekalibriert — nur ueber explizite Neukalibrierung im Einstellungs-Menue.

### 1.4 Phase 1: HSV-Farbsegmentierung

1. Mund-ROI aus Landmarks ausschneiden
2. CLAHE auf den ROI anwenden
3. In HSV konvertieren
4. Maske fuer kalibrierte Zungenfarbe erstellen
5. Morphologische Operationen (Erosion/Dilation) zum Entrauschen
6. Konturfindung — groesste Kontur = Zunge
7. Score: `tongue_ratio = zungenflaeche / mundoeffnung_flaeche`
8. Position der Zungenspitze relativ zur Lippenlinie

### 1.5 Phase 2: CNN-Upgrade (MobileNet-Lite)

Gleiche Schnittstelle: Mund-ROI rein, Score raus. Drop-in-Ersatz fuer HSV.

Vorteile gegenueber HSV:
- Lernt Textur (Zunge = feucht/glaenzend vs. Lippen = matt) und Form, nicht nur Farbe
- Beleuchtungsunabhaengiger
- Personalisierbar auf individuelle Muster
- Forschungsergebnisse: SVM ~90%, YOLOv5 97% mAP

Datensammlung: Waehrend Phase-1-Trainings werden Mund-ROI-Crops automatisch gespeichert (alle paar Sekunden, mit HSV-Score als Vor-Label). Spaetere Kuratierung durch groesseres Modell. Bilder bleiben lokal — Eltern koennen sie im Eltern-Bereich einsehen und loeschen.

### 1.6 Laufende Anpassung

- **Baseline-Adaption:** EMA (alpha=0.005), nur wenn keine Zunge erkannt. Kompensiert Drift.
- **CLAHE:** Auf jedem Frame, macht Farbsegmentierung beleuchtungsunabhaengiger.
- **One-Euro-Filter:** Adaptive Glaettung — stark bei Ruhe (weniger Fehlalarme), reaktionsschnell bei Bewegung.

### 1.7 MediaPipe-Constraints

- VIDEO-Modus: Timestamps muessen monoton steigend sein (nie zuruecksetzen)
- Kein `tongueOut`-Blendshape verfuegbar (bekannter Bug seit 2023)
- MediaPipe wird NUR fuer Gesichtserkennung und Mund-Landmarks verwendet, NICHT fuer Blendshape-basierte Zungenerkennung

---

## 2. App-Architektur

### 2.1 Navigation: 3 Views

AdwViewStack + AdwViewSwitcher mit 3 Views:

| View | Icon (symbolic) | Inhalt |
|------|----------------|--------|
| Training | camera-video-symbolic | Kamera-Feed + OSD-Overlays, Start/Stop |
| Fortschritt | starred-symbolic | Wochenstatistiken, Trends, Meilensteine |
| Einstellungen | preferences-system-symbolic | Kamera, Lautstaerke, Name, Eltern-Bereich |

Keine Sammlungs-Seite, keine Level-Seite. Minimal, GNOME-konform.

### 2.2 Trainings-View (Hybrid-Layout)

Kamera fuellt die gesamte Flaeche. Dezente, immer sichtbare OSD-Overlays:

- **Oben rechts:** Timer als Pill (halbtransparent)
- **Unten:** Halbtransparente Statusleiste mit Vorfalls-Zaehler und Stop-Button
- **Banner (AdwBanner):** Bei Alarm — "Zunge erkannt — Film pausiert"

Zwei Zustaende:
- **Bereit:** Kamera-Vorschau + "Training starten" Button (`.suggested-action` + `.pill`)
- **Aktiv:** Vollbild-Kamera + OSD-Overlays

**View-Wechsel waehrend Training:** Wechsel zu einer anderen View pausiert das laufende Training automatisch. Rueckkehr zur Trainings-View zeigt den pausierten Zustand mit "Fortsetzen"-Button. Vermeidet unsichtbare Zustandsaenderungen in anderen Views.

### 2.3 Alarm-System (vereinfacht)

Kein Zwei-Stufen-Alarm. Piep und Medienpause kommen gleichzeitig:

```
RUNNING -> tongue_out fuer CONFIRM_FRAMES (3 Frames, ~100ms)
  -> DETECTED: Piep + MPRIS2 Medienpause + Vorfall zaehlen
  -> Zunge zurueck: Film geht weiter nach Erkennungspause
  -> COOLDOWN (adaptiv 3-5s)
  -> RUNNING
```

Multi-Frame-Bestaetigung (3 Frames) vor DETECTED. Sofortiger Reset bei Zunge-zurueck.

### 2.4 Hintergrund-Modus

Automatischer Wechsel:
- **Fenster offen:** Kamera-Ansicht mit OSD-Overlays
- **Fenster nicht sichtbar (minimiert oder anderer Workspace):** Kamera laeuft weiter, Erkennung aktiv, Feedback ueber System-Benachrichtigungen (GNotification) + Piepton + MPRIS2-Pause. Erkennung ueber `GtkWindow.is_active()` bzw. Window-State-Events.

**GNotification-Strategie:** Max. eine aktive Benachrichtigung gleichzeitig (gleiche Notification-ID fuer replace). Text: "Zunge erkannt \u2014 Film pausiert". Wird entfernt wenn Zunge zurueck. Rate-Limit: max. 1 Benachrichtigung pro 10 Sekunden, um die Benachrichtigungsleiste nicht zu fluten.

### 2.5 Fortschritts-View

Echte Daten statt Gamification:

- **Wochenuebersicht:** "2/2 Trainings geschafft", "91% ohne Vorfall", Trainingszeit
- **Trend:** Balkendiagramm ueber die letzten 4 Wochen (Verbesserung sichtbar)
- **Meilensteine:** "Erste Woche geschafft", "10 Trainings absolviert", "15 Minuten ohne Vorfall" — mit Animationen gefeiert
- Gesperrte Meilensteine zeigen aktuellen Fortschritt ("Bester Versuch: 12 min")

### 2.6 Einstellungen

AdwPreferencesPage innerhalb des ViewStack (nicht als separater `AdwPreferencesDialog`). Begruendung: Die App hat nur 3 Views — Einstellungen als Dialog auszulagern wuerde den ViewSwitcher auf 2 Views reduzieren (unter dem HIG-Minimum von 3). Die Einstellungen sind zudem einfach genug fuer eine eingebettete Seite. Der Eltern-Bereich wird als Subpage via `AdwNavigationView` push implementiert, nicht als flache Liste im gleichen Scroll-Bereich.

**Fuer das Kind:**
- Kamera waehlen (AdwComboRow, automatische Erkennung als Default)
- Lautstaerke (GtkScale)
- Name aendern (AdwEntryRow)

**Eltern-Bereich (Polkit-geschuetzt):**
- Trainingsplan: Trainings pro Woche (AdwSpinRow)
- Mindest-Trainingsdauer (AdwSpinRow)
- Schwierigkeit manuell uebersteuern
- Erinnerungen konfigurieren (AdwSwitchRow)
- Gesammelte ROI-Bilder einsehen/loeschen
- Profil zuruecksetzen (destructive-action mit AdwAlertDialog)

Zugang: Einstellungen -> "Eltern-Bereich" -> System-Passwort-Abfrage via Polkit (`polkit-agent`). Polkit ist der GNOME-Standard fuer privilegierte Aktionen und funktioniert in Flatpak mit `--talk-name=org.freedesktop.PolicyKit1`. Erfordert eine `.policy`-Datei im Flatpak-Bundle.

**Polkit-Fehlerbehandlung:** Bei Abbruch durch den Nutzer -> zurueck zu den normalen Einstellungen, kein Fehlerdialog, optional Toast "Zugang abgebrochen". Bei falschem Passwort: Polkit-Agent zeigt eigene Fehlermeldung (System-Standard), App wartet passiv.

### 2.7 Onboarding (Erster Start)

AdwCarousel mit 5 Schritten:

1. **Willkommen** — AdwStatusPage (Illustration-Stil): was die App macht (1 Satz)
2. **Kamera** — Automatische Erkennung, Preview, manuell waehlbar falls noetig
3. **Kalibrierung** — "Mund zu" (2s) + "Zeig die Zunge" (2s), visuelles Feedback
4. **Eltern-Setup** — "Hol mal einen Elternteil" -> Polkit -> Trainingsplan, Dauer, Erinnerungen
5. **Los geht's** — Erstes Training starten

---

## 3. Smarte Systeme

### 3.1 Adaptive Schwierigkeit (Flow-Zone)

Statt manueller Level passt die App die Schwierigkeit automatisch an:

**Parameter die sich anpassen:**
- Reaktionszeit bis Piep + Pause (0.3s – 3.0s)
- Erkennungspause — wie lange Film pausiert bleibt (0 – 20s)
- Empfindlichkeit des Detektors
- Cooldown nach Alarm (3 – 5s)

**Algorithmus (nach jeder Session):**
```
vorfallsrate = vorfaelle / dauer_minuten

wenn rate < 0.2/min:  -> schwieriger (kleine Schritte)
wenn rate 0.2 - 1.0/min:  -> nichts aendern (Flow-Zone)
wenn rate > 1.0/min:  -> leichter (groessere Schritte)
```

Anpassung immer per EMA (nie sprunghaft). Beruecksichtigt Trend ueber 5+ Sessions. Eltern koennen im Polkit-Bereich Grenzen setzen.

### 3.2 Trainingsplan & Streak

Wochen-basiert statt taeglich:
- Eltern stellen ein: X Trainings pro Woche (z.B. 2)
- Streak zaehlt **Wochen** mit erfuelltem Ziel
- Woche mit x/x Trainings = Streak +1
- Woche mit mind. 1 Training = Streak bleibt
- Woche mit 0 Trainings = Streak reset

Erinnerungen (freundlich, abschaltbar):
- Mitte der Woche: "Du hast noch X Trainings offen"
- Nach Training: "Geschafft! Noch X diese Woche."
- Ende der Woche: "Letzte Chance" (nur wenn 0 Trainings)

### 3.3 Meilensteine

Einfache Achievements mit Animationen:
- Session-basiert: "Erstes Training", "10 Trainings", "50 Trainings"
- Streak-basiert: "Erste Woche geschafft", "4 Wochen in Folge"
- Leistungs-basiert: "5 Minuten ohne Vorfall", "15 Minuten ohne Vorfall", "Ganze Session ohne Vorfall"

Kein Level-System, keine Sammelkarten, keine Kreaturen. Nur ehrliches Feedback ueber echten Fortschritt.

---

## 4. Interne Architektur

### 4.1 Window als Mediator (bewaehrtes Pattern)

ZungenTrainerWindow besitzt:
- DataStore (JSON-Persistenz)
- UserProfile (Dataclass)
- AdaptiveDifficulty (ersetzt LevelSystem)
- MilestoneSystem (ersetzt Badge/CreatureSystem)

Pages referenzieren Window und greifen ueber es auf gemeinsamen Zustand zu.

### 4.2 Services

| Service | Aufgabe |
|---------|---------|
| CameraService | Daemon-Thread, 1080p OpenCV-Capture, Lock-basierter Frame-Handoff |
| DetectorService | MediaPipe Landmarks -> Mund-ROI -> HSV/CNN -> Score -> tongue_out |
| SessionService | Zustandsmaschine: IDLE -> RUNNING -> DETECTED -> COOLDOWN |
| SoundService | GStreamer audiotestsrc Piepton |
| MprisService | D-Bus MPRIS2 Mediensteuerung (Pause/Resume aller Player) |

### 4.3 Trainings-Loop

TrainingPage startet `GLib.timeout_add(33, ...)` (~30 FPS) auf dem GTK-Main-Thread:
1. Frame von CameraService holen (Lock-geschuetzt)
2. CameraPaintable aktualisieren (Gdk.Paintable fuer OpenCV -> GTK)
3. DetectorService.detect(frame) -> tongue_out + confidence
4. SessionService.update(tongue_out) -> Zustandsuebergaenge + Callbacks
5. OSD-Overlays aktualisieren

### 4.4 Threading

- CameraService: Daemon-Thread mit `cv2.VideoCapture(1080p)`, Frames via `threading.Lock`
- Alles andere: GTK-Main-Thread (Detection, Session, UI)
- Kein Blocking: MediaPipe-Inferenz + HSV-Analyse sind schnell genug fuer 30 FPS

### 4.5 Datenpersistenz

- Speicherort: `$XDG_DATA_HOME/zungentrainer/profile.json`
- Atomares Schreiben: temp-Datei + `os.replace()`
- Schema-Versionierung: `schema_version` Feld, append-only Migrations-Kette, Backup vor Migration
- Lokale Entwicklung: `ZUNGENTRAINER_DATA_DIR` Override via `run.sh`
- ROI-Bilder: `$XDG_DATA_HOME/zungentrainer/training_data/` (fuer spaeteres ML)

---

## 5. Distribution

### 5.1 Eigenes Flatpak-Repo auf GitHub Pages

Kein Flathub (Policy verbietet AI-generierten Code).

**Build-Pipeline:**
1. Code pushen (git push)
2. Flatpak bauen (build-flatpak.sh)
3. `flatpak build-export` in OSTree-Repo
4. Repo auf gh-pages Branch pushen -> GitHub Pages hostet es

**Nutzer-Seite:**
- Erstinstallation: `flatpak remote-add` + `flatpak install` (einmalig)
- Updates: `flatpak update` (automatisch via GNOME Software)
- Profil ueberlebt Updates (in $XDG_DATA_HOME)

### 5.2 Flatpak-Konfiguration

- App-ID: `de.yoshimintos.ZungenTrainer`
- Runtime: org.gnome.Platform 49
- SDK: org.gnome.Sdk 49
- Finish-Args: `--device=all` (Kamera), `--socket=wayland`, `--socket=fallback-x11`, `--socket=pulseaudio`, `--talk-name=org.mpris.MediaPlayer2.*`, `--talk-name=org.freedesktop.DBus`, `--talk-name=org.freedesktop.PolicyKit1` (Polkit fuer Eltern-Bereich)
- Python-Deps als vorgeladene Wheels: mediapipe, numpy, opencv-python-headless

### 5.3 Datenpfad-Aufloesung

**App-Daten** (MediaPipe-Modell, Icons, Metainfo — read-only, im Repo/Flatpak-Bundle):
1. `ZUNGENTRAINER_DATA_DIR` Umgebungsvariable (fuer lokale Entwicklung, gesetzt in `run.sh`)
2. `/app/share/zungentrainer/data/` (Flatpak)
3. Fallback: relative Pfade von `src/`

**User-Daten** (Profil, Trainingshistorie, ROI-Bilder — read-write, pro Nutzer):
- `$XDG_DATA_HOME/zungentrainer/` (typisch: `~/.local/share/zungentrainer/`)
- Im Flatpak automatisch sandboxed unter `~/.var/app/de.yoshimintos.ZungenTrainer/data/zungentrainer/`

---

## 6. GNOME-Konformitaet

### 6.1 Eingehaltene HIG-Prinzipien

- **Eine Sache gut machen:** Zungenerkennung + Feedback. Keine Feature-Ueberladung.
- **Content, not chrome:** Kamera-Feed ist der primaere Inhalt. OSD-Overlays statt permanenter UI-Elemente.
- **Progressive Disclosure:** Einfache Einstellungen sichtbar, Eltern-Bereich hinter Polkit.
- **Reduce User Effort:** Adaptive Schwierigkeit, automatische Kalibrierung, automatischer Hintergrund-Modus.
- **Be Considerate:** Toasts statt Dialoge, freundliche Erinnerungen, positive Meilensteine.

### 6.2 Verwendete Libadwaita-Widgets

- AdwApplicationWindow, AdwToolbarView, AdwHeaderBar
- AdwViewStack + AdwViewSwitcher / AdwViewSwitcherBar
- AdwCarousel (Onboarding)
- AdwStatusPage (Onboarding-Schritte, leere Zustaende)
- AdwPreferencesPage, AdwPreferencesGroup (Einstellungen als ViewStack-Page)
- AdwSwitchRow, AdwComboRow, AdwEntryRow, AdwSpinRow
- AdwBanner (persistenter Alarm-Status)
- AdwToastOverlay + AdwToast (transiente Meldungen, Meilensteine)
- AdwAlertDialog (Profil zuruecksetzen)
- AdwClamp (Inhaltsbreite begrenzen)

### 6.3 Keine Emojis

Ausschliesslich GNOME symbolic icons (z.B. camera-video-symbolic, starred-symbolic, preferences-system-symbolic). Keine Emojis in der App-UI.

### 6.4 Tooltips

Alle Header-Bar-Controls und OSD-Buttons brauchen Tooltips:
- Start-Button: "Training starten"
- Stop-Button (OSD): "Training beenden"
- Timer-Pill (OSD): "Trainingszeit"
- ViewSwitcher-Tabs: ueber die View-Titel automatisch abgedeckt

### 6.5 Tastaturkuerzel

| Kuerzel | Funktion |
|---------|----------|
| Space | Training starten / stoppen |
| Escape | Training abbrechen |
| Ctrl+Q | App beenden |
| Ctrl+, | Einstellungen fokussieren |
| F1 | Ueber-Dialog |

Alle Standard-GNOME-Shortcuts (Ctrl+Q, Ctrl+,) werden uebernommen. Eigene Shortcuts nur fuer die Kern-Interaktion (Space, Escape).

### 6.6 Barrierefreiheit

**Accessible Names:**
- Kamera-Feed: "Kamera-Vorschau" (bzw. "Training aktiv \u2014 Kamera-Vorschau" waehrend Training)
- Timer-Pill: "Trainingszeit: X Minuten Y Sekunden"
- Vorfalls-Zaehler: "X Vorfaelle"
- Balkendiagramm (Fortschritt): ATK-Beschreibung mit den Wochenwerten als Text
- Meilensteine: Status "erreicht" / "noch nicht erreicht, bester Versuch: X"

**Zustandsaenderungen fuer Screen Reader:**
- Training gestartet/gestoppt: `Gtk.Accessible` Status-Update
- Alarm ausgeloest: Ansage "Zunge erkannt" (ueber ATK live-region oder GNotification)

**Getestet werden muss:**
- High-Contrast-Modus (OSD-Overlays muessen lesbar bleiben)
- Large-Text-Modus (OSD-Layout darf nicht brechen)
- Keyboard-only (Training komplett per Tastatur steuerbar)
- Screen Reader (alle Elemente werden vorgelesen)
- On-Screen-Keyboard (Onboarding-Texteingabe fuer Name)

### 6.7 Adaptive Gestaltung

**Minimale Fenstergroesse:** 1024x600px (Desktop). Keine Telefon-Unterstuetzung geplant.

**ViewSwitcher-Breakpoint:** Bei schmalen Fenstern (< ~600px) wechselt der AdwViewSwitcher automatisch zur AdwViewSwitcherBar am unteren Rand (Standard-Verhalten mit `policy=WIDE`).

**OSD-Breakpoints:** Bei schmalen Fenstern wird die Statusleiste kompakter (Vorfalls-Zaehler als Zahl statt Text, kleinere Timer-Pill).

**Maximalbreite:** Fortschritts-View und Einstellungen nutzen `AdwClamp` fuer angemessene Inhaltsbreite auf breiten Bildschirmen.

### 6.8 UI-Styling

Die App folgt der System-Style-Praeferenz (Light/Dark) ueber `AdwStyleManager`. Kein per-App Umschalter — die App zeigt primaer Video-Inhalt, daher ist die System-Einstellung ausreichend. Minimales eigenes CSS: nur fuer halbtransparente OSD-Overlays ueber dem Kamera-Feed. Alle OSD-Styles muessen mit Light, Dark und High-Contrast funktionieren.

### 6.9 App-Icon

**Metapher:** Stilisierter Mund/Lippen (Bezug zum App-Namen und Funktion). Einfach, geometrisch, GNOME-Farbpalette.
- 128x128px Canvas, 2px-Raster
- Subtile Tiefe (dunkler "Vorderseite"-Profil)
- Symbolische Version: vereinfachter Mund als 16x16 Symbolic
- Erstellt mit App Icon Preview Tool
- Umsetzung in Phase 3

### 6.10 Schreibkonventionen

- Keine Punkte am Ende von Labels, Ueberschriften, Toast-/Banner-Texten
- Unicode korrekt: Gedankenstrich (U+2014), Auslassungszeichen (U+2026), schmales geschuetztes Leerzeichen (U+202F) vor Einheiten ("15\u202fmin")
- Erinnerungstexte verwenden bewusst "Du"-Anrede (Zielgruppe Kinder, paedagogisch sinnvoll \u2014 dokumentierte Abweichung von HIG WS7)

---

## 7. Tech-Stack

| Komponente | Technologie |
|-----------|------------|
| Sprache | Python 3.13+ |
| UI-Framework | GTK 4.0 + Libadwaita 1 |
| Gesichtserkennung | MediaPipe Face Landmarker (VIDEO-Modus) |
| Bildverarbeitung | OpenCV (headless) + NumPy |
| Sound | GStreamer 1.0 (audiotestsrc) |
| Mediensteuerung | D-Bus MPRIS2 (GLib/Gio) |
| Persistenz | JSON (atomares Schreiben) |
| Distribution | Flatpak (eigenes Repo auf GitHub Pages) |
| Lizenz | GPL-3.0-or-later |

---

## 8. Implementierungsphasen

### Phase 1: Erkennung (Prioritaet #1)

Standalone-Skript, testbar ohne UI:
- MediaPipe Face Landmarker aufsetzen (1080p)
- Mund-ROI-Extraktion aus Landmarks
- CLAHE + HSV-Farbsegmentierung
- Kalibrierungs-Flow (Baseline + Zungenfarbe)
- One-Euro-Filter + Entscheidungslogik
- Visuelles Debug-Fenster (OpenCV)

### Phase 2: Minimale App

- GTK 4 / Libadwaita Grundstruktur (Window, ViewStack, 3 Pages)
- TrainingPage mit CameraPaintable + OSD-Overlays
- SessionService (vereinfachte Zustandsmaschine: RUNNING -> DETECTED -> COOLDOWN)
- SoundService + MprisService
- Hintergrund-Modus (GNotification bei minimiertem Fenster)
- Adaptive Schwierigkeit (Flow-Zone-Algorithmus)
- JSON-Persistenz (atomares Schreiben, Schema-Versionierung)

### Phase 3: Polieren

- Onboarding (AdwCarousel, 5 Schritte)
- Fortschritts-View (Wochenstatistiken, Trends, Meilensteine)
- Eltern-Bereich (Polkit-geschuetzt)
- Trainingsplan + Wochen-Streak + Erinnerungen
- ROI-Datensammlung fuer spaeteres ML
- Flatpak-Build + GitHub Pages Repo
- Metainfo, Desktop-Entry, Icons

### Phase 4: ML-Upgrade (spaeter)

- Kuratierung der gesammelten ROI-Daten
- MobileNet-Lite Transfer Learning
- Drop-in-Ersatz in der DetectorService-Pipeline
- Evaluation: HSV vs. CNN Vergleich

---

## 9. Verifikation

### Erkennung testen
```bash
cd zungentrainer
python3 src/services/detector_service.py  # Standalone-Test mit Debug-Fenster
```
- Kalibrierung: 2s ruhig, 2s Zunge zeigen
- Normal sprechen -> kein Alarm
- Zunge leicht zwischen Lippen -> Erkennung
- Zunge deutlich raus -> sofortige Erkennung
- Lichtwechsel -> Adaption testen

### App testen
```bash
./run.sh  # Lokaler Start
```
- Onboarding durchlaufen
- Training starten, Fenster minimieren, Film starten
- Zunge raus -> Film pausiert + Piep gleichzeitig
- Zunge rein -> Film geht weiter nach Erkennungspause
- Fortschritts-View pruefen
- Eltern-Bereich (Polkit) testen

### Flatpak testen
```bash
./build-flatpak.sh
flatpak run de.yoshimintos.ZungenTrainer
```
- Kamera-Zugriff im Sandbox-Modus
- Profil-Persistenz ueber App-Neustarts
- MPRIS2 funktioniert (Spotify/Firefox pausieren)
