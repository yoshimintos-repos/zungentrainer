# ZungenTrainer v3 Spec

## Leitidee

ZungenTrainer ist ein unauffaelliger Hintergrund-Trainer gegen unbewusste
Zungenprotrusion. Die App laeuft waehrend normaler Bildschirmzeit mit und stoert
nur dann, wenn die Zunge draussen ist.

Die wichtigste Produktregel:

> Die App darf nur nerven, wenn die Zunge draussen ist.

Gleichzeitig muss sie auch minimale Protrusion erkennen. Die Loesung ist nicht
eine global empfindlichere Erkennung, sondern eine praezise, personalisierte und
anatomisch eng begrenzte Erkennung.

## Ziel

Menschen, die ihre Zunge unbewusst leicht oder deutlich aus dem Mund haengen
lassen, sollen direktes Feedback bekommen, um diese Gewohnheit abzubauen.
Typischer Kontext ist Sitzen vor dem Bildschirm, zum Beispiel beim Schauen von
Filmen, Musikhoeren, Arbeiten oder Lernen.

Die App ist kein medizinisches Diagnose- oder Therapieprodukt. Sie unterstuetzt
Gewohnheitstraining und ersetzt keine logopaedische, kieferorthopaedische oder
aerztliche Behandlung.

## Produktprinzipien

- Nur stoeren, wenn die Zunge draussen ist.
- Bei Unsicherheit nicht stoeren.
- Kleine Protrusion ist relevant und muss erkannt werden.
- Die App soll im Alltag fast unsichtbar sein.
- Wenige Einstellungen. Gute Defaults statt Nutzer-Regler.
- Kamera- und Erkennungsdaten bleiben lokal.
- Keine Gamification, keine Abzeichen, keine Sammelobjekte.
- GNOME HIG und Libadwaita-Konventionen haben Vorrang vor eigener UI-Erfindung.

## Zielplattform

- Python
- GTK 4
- Libadwaita
- Flatpak
- GNOME Desktop als primaere Umgebung

Andere Sprachen oder native Module sind erlaubt, wenn sie fuer die Erkennung
oder Performance nachweislich sinnvoll sind. Die App-Schale bleibt GTK 4 /
Libadwaita.

## Verhaltensmodell

### Normalbetrieb

Die App laeuft im Hintergrund und analysiert die Webcam.

Wenn keine Zunge erkannt wird:

- kein Ton
- keine Benachrichtigung
- keine sichtbare Unterbrechung
- kein periodischer Reminder

Wenn die Zunge sicher draussen erkannt wird:

1. Ein kurzer Piepton wird abgespielt.
2. Falls ein Medienplayer aktiv spielt, wird dieser pausiert.
3. Falls kein Medieninhalt laeuft, startet eine kleine stoerende Audioschleife.

Wenn die Zunge wieder drin ist:

- Die stoerende Audioschleife stoppt sofort.
- Pausierte Medien werden erst fortgesetzt, wenn die Zunge mindestens 3 Sekunden
  stabil drin ist.

Der Piepton wird nur beim Uebergang in den Alarmzustand abgespielt, nicht in
jedem Frame und nicht dauerhaft.

### Medienlogik

Die App unterscheidet:

- `MEDIA_PLAYING`: Mindestens ein MPRIS-Player spielt.
- `NO_MEDIA`: Kein MPRIS-Player spielt.

Bei `MEDIA_PLAYING`:

- piepen
- alle aktuell spielenden Player pausieren
- nur von der App pausierte Player merken
- nach stabiler Rueckkehr der Zunge plus 3 Sekunden wieder starten

Bei `NO_MEDIA`:

- piepen
- stoerende Audioschleife starten
- Audioschleife stoppen, sobald Zunge wieder drin ist

Die Audioschleife braucht keine eigene Testfunktion in der UI.

## UI-Konzept

### Hauptfenster

Die App hat eine Hauptseite: `Training` oder `Ueberwachung`.

Diese Seite zeigt nur, was fuer Verstaendnis und Vertrauen noetig ist:

- Aktiv/Inaktiv-Zustand
- Kamera-/Erkennungsstatus
- Start/Stop-Schalter
- optional: letzter Alarm oder heutige Alarmzahl, sehr dezent

Keine Fortschrittsseite als zentrales Produktfeature. Keine Meilensteinseite.
Keine Level.

### Menue

Die drei Striche in der Header Bar enthalten:

- Einstellungen
- Ueber ZungenTrainer

### Einstellungen

Nur notwendige Einstellungen:

- Kamera
- Lautstaerke
- Medien pausieren: an/aus
- Beim Anmelden starten: an/aus, wenn technisch sauber moeglich
- Neu kalibrieren

Keine normalen Nutzer-Regler fuer Sensitivity, Schwellenwerte, Filterstaerken,
Cooldowns oder Modellparameter.

Erweiterte Debug-Optionen duerfen existieren, aber nicht in der normalen
Produktoberflaeche. Sie gehoeren hoechstens in einen expliziten Debug-Modus.

### Onboarding

Das Onboarding ist kurz und zweckorientiert:

1. Erklaeren, was die App tut.
2. Kamera und Datenschutz erklaeren: Verarbeitung lokal.
3. Kalibrierung starten.
4. Ergebnis zeigen: bereit oder Kalibrierung wiederholen.

Keine Tontests, keine Nervmusiktests, keine Gamification-Erklaerungen.

## Kalibrierung

Die Kalibrierung darf ungefaehr 1 Minute dauern. Sie ist entscheidend fuer
Qualitaet und darf deshalb sorgfaeltig sein.

Ziel: Die App lernt nicht nur, wie Zunge aussieht, sondern auch, wie normale
Nicht-Zunge-Zustaende der Person aussehen.

### Ablauf

Vorgeschlagener Ablauf:

| Zeit | Phase | Ziel |
| --- | --- | --- |
| 0-10 s | Kamera, Gesicht, Licht pruefen | Sicherstellen, dass das Setup verwendbar ist |
| 10-25 s | Mund geschlossen, normal schauen | Baseline fuer Lippen, Haut, Licht |
| 25-35 s | Normale Mundbewegung ohne Zunge draussen | Negative Beispiele fuer Sprechen/Bewegen |
| 35-45 s | Minimale Zunge draussen | Positive Beispiele fuer Micro-Protrusion |
| 45-55 s | Deutliche Zunge draussen | Positive Beispiele fuer klare Protrusion |
| 55-60 s | Validierung | Trennbarkeit pruefen |

Die App darf waehrend der Kalibrierung klare Anweisungen zeigen. Nach der
Kalibrierung soll sie wieder unauffaellig sein.

### Qualitaetspruefung

Die Kalibrierung gilt nur als gut, wenn:

- Gesicht und Mundlandmarks stabil erkannt werden.
- Die Helligkeit nicht zu dunkel oder ueberbelichtet ist.
- Negative und positive Beispiele unterscheidbar sind.
- Micro-Protrusion nicht mit normaler Mundbewegung verwechselt wird.

Wenn die Qualitaet schlecht ist, soll die App eine konkrete Korrektur nennen:

- Mehr Licht
- Gesicht naeher zur Kamera
- Kamera stabiler ausrichten
- Kalibrierung wiederholen

## Erkennung

### Grundsatz

Die Erkennung arbeitet mit drei Ergebniszustaenden:

- `CLEAR`: sicher keine Zunge draussen
- `UNCERTAIN`: unsicher, nichts tun
- `TONGUE_OUT`: Zunge sicher draussen

Nur `TONGUE_OUT` darf Feedback ausloesen. `UNCERTAIN` ist ein bewusstes
Nicht-Handeln und kein Fehler.

### Zielkonflikt

Die App muss auch kleine Protrusion erkennen, darf aber nicht bei Schatten,
Lippen, Sprechen oder schlechtem Licht nerven.

Deshalb ist die Erkennung:

- lokal statt global
- anatomisch begrenzt
- personalisiert
- zeitlich stabilisiert
- konservativ bei Unsicherheit

### Pipeline

```text
Kamera-Frame
-> Face/Mouth Landmarks
-> Landmark-Qualitaet pruefen
-> Mund-zu-Gate
-> Praeziser innerer Lippenspalt-ROI
-> Baseline-Vergleich
-> Farbsignal
-> Geometriesignal
-> Textur/ML-Signal, spaeter
-> Fusion zu CLEAR / UNCERTAIN / TONGUE_OUT
-> temporale State Machine
-> Feedback Controller
```

### Gates

Die App darf nur dann ueberhaupt in Richtung Alarm entscheiden, wenn:

- Gesicht erkannt ist
- Mundlandmarks stabil genug sind
- der relevante Lippenspalt sichtbar ist
- die Erkennung nicht durch schlechtes Licht unbrauchbar ist

Wenn diese Gates nicht erfuellt sind, ist das Ergebnis `UNCERTAIN` oder `CLEAR`,
nicht `TONGUE_OUT`.

### Micro-Protrusion

Kleine Protrusion wird nicht primaer ueber grosse Flaeche erkannt, sondern ueber
eine kleine stabile Veraenderung genau im inneren Lippenspalt.

Wichtige Signale:

- neue zungenartige Farbe im zentralen Lippenspalt
- Veraenderung gegenueber persoenlicher Baseline
- zentrale Oeffnung anders als Seitenoeffnung
- kleine Lippenverformung durch die Zunge
- plausible Position an der Lippenkante
- zeitliche Stabilitaet ueber mehrere Frames

### Schlechte Lichtbedingungen

Die App muss mit gutem und schlechtem Licht umgehen, aber sie darf schlechte
Lichtqualitaet nicht durch falsches Nerven kompensieren.

Strategie:

- Helligkeit und Kontrast im Mund-ROI messen.
- Ueberbelichtung und Unterbelichtung erkennen.
- Farbsignale normalisieren, zum Beispiel durch CLAHE oder aehnliche Verfahren.
- Persoenliche Kalibrierungsdaten pro Lichtbereich erheben, soweit moeglich.
- Bei unbrauchbarem Licht nicht alarmieren.
- Im sichtbaren Fenster dezent anzeigen, wenn die Erkennung eingeschraenkt ist.

Langfristig sollte die Kalibrierung Beispiele bei mehreren Lichtniveaus sammeln
oder die Nutzerin gezielt bitten, die Kalibrierung bei normalem Alltagslicht zu
machen.

### Entscheidungslogik

Ein Alarm wird nur ausgeloest, wenn:

- anatomische Gates bestanden sind
- mehrere Signale fuer Protrusion sprechen
- das Ergebnis nicht `UNCERTAIN` ist
- die Erkennung fuer eine kurze Mindestzeit stabil ist

Vorgeschlagen:

- Micro-Protrusion: kuerzere Reaktionszeit moeglich, aber nur bei sehr guter
  Kalibrierungsqualitaet
- deutliche Protrusion: schnellere Erkennung
- unsicher: kein Feedback

Die konkrete Reaktionszeit ist ein interner Parameter und keine normale
Einstellung.

## Datensammlung und ML-Ausbau

Kurzfristig kann die App regelbasiert mit HSV, Geometrie und Baseline-Vergleich
arbeiten.

Fuer robuste Erkennung in vielen Lichtbedingungen ist mittelfristig ein kleines
lokales Modell wahrscheinlich sinnvoll.

Trainingsklassen:

- `clear_closed`
- `clear_moving`
- `clear_speaking`
- `micro_protrusion`
- `strong_protrusion`
- `bad_light`
- `no_face`

Das Modell soll nicht allein entscheiden. Es liefert ein weiteres Signal in der
Fusion. Anatomische Gates und temporale Logik bleiben davor und danach erhalten.

Alle Trainingsdaten bleiben lokal. Ein Export fuer Entwicklung oder Debugging
darf nur explizit erfolgen.

## Datenschutz

- Kamera-Auswertung lokal.
- Keine Uploads.
- Keine Cloud-Abhaengigkeit.
- Gespeicherte Kalibrierungsdaten liegen lokal im Nutzerprofil.
- Optional gespeicherte ROI-Bilder duerfen nur in einem Debug-/Entwicklungsmodus
  gesammelt werden.

In der UI muss klar werden: Die Kamera wird lokal verarbeitet.

## Packaging und Distribution

Primaeres Paketformat ist Flatpak.

Verteilwege:

1. Lokales Bundle fuer einzelne Tester.
2. Beta-Flatpak-Repository ueber GitHub Pages.
3. Spaeter Flathub, wenn App, Datenschutztexte, Metadaten und Permissions reif
   sind.

GitHub-Pages-Beta darf zuerst ohne GPG fuer enge Tester existieren. Fuer breitere
Verteilung soll das Repository signiert werden.

## Nicht-Ziele

- Keine Therapie-Diagnose.
- Keine Gamification.
- Keine detaillierten Fortschritts-Dashboards.
- Keine vielen Einstellungen.
- Kein Cloud-Training.
- Keine Ton- oder Nervmusik-Testbuttons.
- Keine App, die wegen schlechter Erkennung dauernd Aufmerksamkeit verlangt.

## Offene Entscheidungen

- Heisst die Hauptseite `Training`, `Ueberwachung` oder anders?
- Soll die App automatisch beim Login starten?
- Wie genau wird `NO_MEDIA` zuverlaessig erkannt?
- Welche stoerende Audioschleife ist wirksam, aber nicht unangemessen?
- Wie viel Debug-Datensammlung ist fuer reale Verbesserung noetig?
- Ab wann ist ein ML-Modell notwendig statt optional?
- Welche Datenschutz- und Haftungstexte braucht eine oeffentliche Version?
