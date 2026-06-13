# GNOME HIG — Vollstaendige Review-Checkliste

Dieses Dokument enthaelt alle pruefbaren Regeln aus den GNOME Human Interface Guidelines, organisiert nach Kategorie. Jede Regel hat eine ID fuer die Referenzierung im Report.

## Inhaltsverzeichnis

1. [Design-Prinzipien](#1-design-prinzipien)
2. [App-Identitaet](#2-app-identitaet)
3. [Navigation](#3-navigation)
4. [Header Bars](#4-header-bars)
5. [Buttons](#5-buttons)
6. [Boxed Lists](#6-boxed-lists)
7. [Preferences](#7-preferences)
8. [Toasts & Banners](#8-toasts--banners)
9. [Dialoge](#9-dialoge)
10. [Schreibstil](#10-schreibstil)
11. [Typografie](#11-typografie)
12. [Icons](#12-icons)
13. [Barrierefreiheit](#13-barrierefreiheit)
14. [Adaptive Gestaltung](#14-adaptive-gestaltung)
15. [Tastatur](#15-tastatur)
16. [Zeiger & Touch](#16-zeiger--touch)
17. [UI-Styling](#17-ui-styling)

---

## 1. Design-Prinzipien

| ID | Regel | Schwere |
|----|-------|---------|
| P1 | App macht EINE Sache gut — kein Feature-Overload | Major |
| P2 | Progressive Disclosure: haeufige Aktionen nah, seltene weiter weg | Major |
| P3 | Nicht zu viele Elemente auf einmal anzeigen | Major |
| P4 | Automatisieren was automatisierbar ist | Minor |
| P5 | Schritte minimieren fuer haeufige Aufgaben | Minor |
| P6 | Merkaufwand reduzieren (Tabs, zuletzt verwendet, Vorschlaege) | Minor |
| P7 | Fehler antizipieren und verhindern | Major |
| P8 | Undo statt Bestaetigungsdialoge wo moeglich | Major |
| P9 | Zeit und Aufmerksamkeit respektieren — nicht unnoetig unterbrechen | Major |

---

## 2. App-Identitaet

### App-Name

| ID | Regel | Schwere |
|----|-------|---------|
| N1 | 1-2 einfache Substantive | Minor |
| N2 | Bezug zur App-Domaene | Minor |
| N3 | Unter 15 Zeichen | Minor |
| N4 | Leicht auszusprechen | Minor |
| N5 | Header Capitalization (z.B. "Icon Preview" nicht "Icon preview") | Minor |
| N6 | Kein "G"-Praefix, keine Marken anderer Projekte | Major |
| N7 | Keine ungewoehnliche Interpunktion oder Whitespace (z.B. "SuperWriter") | Minor |

### App-Icon

| ID | Regel | Schwere |
|----|-------|---------|
| I1 | Eigenes, einzigartiges App-Icon — keine Wiederverwendung existierender Icons | Kritisch |
| I2 | Einfache, erkennbare Metapher mit Bezug zum App-Namen | Major |
| I3 | Gezeichnet in 128x128px Canvas, fuellt den Raum nicht komplett | Major |
| I4 | Keine extremen Seitenverhaeltnisse (zu schmal/breit) | Minor |
| I5 | Nicht flach — subtile Tiefe durch "Vorderseite" Profil | Minor |
| I6 | Standard-GNOME-Farbpalette als Basis | Minor |
| I7 | Flache Farben fuer gerade Flaechen, Gradienten nur fuer gekruemmte | Minor |
| I8 | Keine Schatten ausserhalb der Silhouette | Minor |
| I9 | 2px-Raster einhalten, nicht zu viel Detail (skaliert bis 32x32) | Minor |
| I10 | Symbolische Version des App-Icons vorhanden | Major |
| I11 | Keine Maskottchen, Charaktere oder stilabhaengige Logos | Minor |

---

## 3. Navigation

| ID | Regel | Schwere |
|----|-------|---------|
| NAV1 | ViewSwitcher: 3-5 Views | Kritisch |
| NAV2 | ViewSwitcher-Labels: Substantive (nicht Verben), Header Capitalization | Major |
| NAV3 | ViewSwitcher-Labels: aehnliche Laenge | Minor |
| NAV4 | ViewSwitcher muss bei schmalen Fenstern nach unten wechseln (AdwViewSwitcherBar) | Kritisch |
| NAV5 | Keine View-uebergreifenden Abhaengigkeiten (Controls in View A beeinflussen View B) | Major |
| NAV6 | In-Window-Navigation bevorzugen ueber sekundaere Fenster | Major |
| NAV7 | Hierarchie-Tiefe maximal 1 Level | Major |
| NAV8 | Jede View hat klaren Fokus/Thema | Major |
| NAV9 | Inhaltsmenge pro View verdaulich — nicht ueberladen | Major |
| NAV10 | Standard-Tastaturkuerzel fuer Navigation unterstuetzen | Major |
| NAV11 | Sidebar statt ViewSwitcher wenn > 5 Views noetig | Major |

---

## 4. Header Bars

| ID | Regel | Schwere |
|----|-------|---------|
| HB1 | Wenige Controls — Primaerfunktion sofort erkennbar | Major |
| HB2 | Freier Platz fuer Fenster-Dragging | Major |
| HB3 | ALLE Controls muessen Tooltips haben | Major |
| HB4 | Keine reinen Text-Label-Buttons (immer Icon dabei) | Major |
| HB5 | Kein `.suggested-action` / `.destructive-action` in primaeren Header Bars | Kritisch |
| HB6 | Keine verlinkten (linked) Button-Gruppen — `.spacer` fuer Gruppierung | Major |
| HB7 | Header Bar Controls aktualisieren sich bei View-/Moduswechsel | Major |
| HB8 | Hauptaktions-Buttons am Anfang/links | Minor |
| HB9 | Menues am Ende/rechts | Minor |
| HB10 | Split Buttons fuer zusammengehoerige Button-Dropdown-Kombinationen | Minor |

---

## 5. Buttons

| ID | Regel | Schwere |
|----|-------|---------|
| BTN1 | Maximal EIN `.suggested-action` oder `.destructive-action` Button pro View | Kritisch |
| BTN2 | Labels: imperative Verben mit Header Capitalization | Major |
| BTN3 | Labels kurz halten (Lokalisierung beachten) | Minor |
| BTN4 | Ausserhalb Header Bars: entweder Icon ODER Label, nicht beides | Major |
| BTN5 | Keine Aktionen exklusiv auf Doppelklick oder Rechtsklick | Kritisch |
| BTN6 | Ungueltige Buttons insensitiv machen (nicht Fehler nach Klick) | Major |
| BTN7 | Max 1-2 verschiedene Button-Breiten im selben Fenster | Minor |
| BTN8 | Nebeneinanderliegende Buttons gleich breit | Minor |
| BTN9 | `.pill` Style fuer primaere View-Aktionen im offenen Raum | Minor |
| BTN10 | `.circular` Style fuer mehrere kleine Buttons in enger Naehe | Minor |
| BTN11 | Toggle Buttons fuer offensichtlich binaere Modi/Einstellungen | Minor |

---

## 6. Boxed Lists

| ID | Regel | Schwere |
|----|-------|---------|
| BL1 | `GtkListBox` mit `.boxed-list` Style fuer Einstellungslisten | Major |
| BL2 | Nur fuer relativ kleine, statische Listen — `GtkListView`/`GtkColumnView` fuer grosse/dynamische | Major |
| BL3 | Semantisch organisieren | Minor |
| BL4 | Max 1-2 Controls pro Zeile | Major |
| BL5 | Klick auf Zeilen-Hintergrund loest den Control aus | Minor |
| BL6 | Controls fokussierbar, Listenzeile selbst NICHT fokussierbar | Major |
| BL7 | Navigations-Zeilen mit `go-next-symbolic` Pfeil am Ende | Major |
| BL8 | Mehrere Textelemente durch Groesse/Gewicht/Farbe differenzieren | Minor |
| BL9 | Icons im symbolischen Stil | Minor |
| BL10 | Minimal- und Maximalbreite fuer adaptives Scaling | Major |
| BL11 | Drag-Handles am Zeilenanfang fuer umordbare Listen | Minor |
| BL12 | Korrekte Libadwaita Row-Typen verwenden (AdwSwitchRow, AdwComboRow, etc.) | Major |

---

## 7. Preferences

| ID | Regel | Schwere |
|----|-------|---------|
| PREF1 | `AdwPreferencesDialog` verwenden (NICHT das veraltete `AdwPreferencesWindow`) | Kritisch |
| PREF2 | Seiten fuer thematisch getrennte Bereiche | Major |
| PREF3 | Gruppen (AdwPreferencesGroup) fuer verwandte Einstellungen | Major |
| PREF4 | Titel und Beschreibungen in Groups sinnvoll benennen (wichtig fuer Suche) | Major |
| PREF5 | Suche aktivieren | Minor |
| PREF6 | Subpages fuer progressive Offenlegung fortgeschrittener Einstellungen | Minor |
| PREF7 | Toasts fuer Echtzeit-Feedback bei Einstellungsaenderungen | Minor |

---

## 8. Toasts & Banners

| ID | Regel | Schwere |
|----|-------|---------|
| TB1 | AdwToast NUR fuer transiente Ereignisse / Reaktionen auf Nutzeraktionen | Major |
| TB2 | AdwBanner fuer andauernde Zustaende | Major |
| TB3 | Toast-Button nur wenn direkt relevant zur Nachricht | Minor |
| TB4 | Toast-Titel: informeller Heading-Stil | Minor |
| TB5 | Toasts am unteren Rand, horizontal zentriert | Minor |
| TB6 | Notifications (GNotification) wenn App inaktiv und Nachricht trotzdem sichtbar sein soll | Major |
| TB7 | Undo-Button in Toasts nach destruktiven Aktionen (bevorzugt ueber Bestaetigungsdialog) | Major |

---

## 9. Dialoge

| ID | Regel | Schwere |
|----|-------|---------|
| DLG1 | `AdwAlertDialog` fuer Bestaetigungen und Fehler | Major |
| DLG2 | Undo ist BESSER als Bestaetigungsdialog | Major |
| DLG3 | Affirmativer Button: spezifisches imperatives Verb ("Speichern"), NICHT generisch ("OK", "Fertig") | Kritisch |
| DLG4 | Abbrechen-Button zuerst (links in LTR) | Major |
| DLG5 | Enter → affirmativer Button (AUSNAHME: irreversibel/destruktiv) | Major |
| DLG6 | Escape → Abbrechen | Major |
| DLG7 | Niemals unerwartet anzeigen — nur als Reaktion auf bewusste Nutzeraktion | Kritisch |
| DLG8 | Immer modal zum Elternfenster | Major |
| DLG9 | Initialer Tastaturfokus auf die Komponente, die der Nutzer zuerst bedient | Minor |
| DLG10 | Affirmativen Button deaktivieren bis alle erforderlichen Optionen gewaehlt | Major |
| DLG11 | Fehler-Dialoge vermeiden wo moeglich — Toasts fuer nicht-kritische Fehler | Major |
| DLG12 | Action-Dialoge brauchen Header Bar mit aktionsbeschreibender Ueberschrift | Major |
| DLG13 | Kein Stapeln sekundaerer Fenster | Major |

---

## 10. Schreibstil

| ID | Regel | Schwere |
|----|-------|---------|
| WS1 | Header Capitalization fuer: Ueberschriften, Header Bar Titel, Tab-Titel, Button-Labels, Menue-Items, Tooltips | Major |
| WS2 | Sentence Capitalization fuer: Checkbox/Radio/Slider-Labels, Body-Text, Feld-Labels, ComboBox-Labels | Major |
| WS3 | Keine Punkte (.) am Ende von Labels, Ueberschriften, Beschreibungen | Minor |
| WS4 | Punkte nur in Mehrfachsatz-Absaetzen | Minor |
| WS5 | Ellipsis (Unicode U+2026) wenn Aktion weitere Eingabe braucht ("Speichern unter\u2026") | Minor |
| WS6 | Keine Ellipsis bei Labels wie "Einstellungen" oder "Eigenschaften" | Minor |
| WS7 | Neutraler Ton — kein "du"/"mein", "Ihre/Ihre" wenn Besitz noetig | Minor |
| WS8 | Keine lateinischen Abkuerzungen (i.e., e.g.) — volle Woerter | Minor |
| WS9 | Keine Saetze ueber mehrere Controls hinweg konstruieren (Uebersetzungsproblem) | Major |
| WS10 | Ueberschriften: Hilfsverben und Artikel weglassen ("Drei Dokumente aktualisiert") | Minor |
| WS11 | Text kurz und praegnant — wenigste Woerter die Bedeutung klar vermitteln | Minor |
| WS12 | Domaenenspezifische Terminologie statt System-Jargon | Minor |

**Hinweis zu deutscher UI-Sprache:** Die Capitalization-Regeln (WS1, WS2) beziehen sich auf englische UI-Texte. In deutschen UIs gelten die deutschen Rechtschreibregeln. Die Prinzipien (kurz, klar, neutral, keine Punkte am Ende) gelten trotzdem.

---

## 11. Typografie

| ID | Regel | Schwere |
|----|-------|---------|
| TYP1 | System-Schriftart verwenden (Adwaita Sans / Inter) | Major |
| TYP2 | KEIN Kursiv/Oblique | Major |
| TYP3 | KEINE Grossbuchstaben fuer komplette Woerter (ALL CAPS) | Major |
| TYP4 | KEINE hart-codierten Schriftgroessen — CSS-Klassen verwenden | Kritisch |
| TYP5 | Standard-CSS-Klassen: `body`, `heading`, `caption`, `caption-heading`, `title-1` bis `title-4`, `large-title` | Major |
| TYP6 | Wenige verschiedene Groessen/Gewichte — nicht uebertreiben | Minor |
| TYP7 | Leichterer/kleinerer Text fuer sekundaere Info, schwerer fuer wichtiges | Minor |
| TYP8 | Kein Text ueber grafischen Hintergruenden oder Texturen | Major |
| TYP9 | Unicode korrekt: typografische Anfuehrungszeichen, Auslassungszeichen (U+2026), Gedankenstrich (U+2013), schmales geschuetztes Leerzeichen vor Einheiten (U+202F) | Minor |

---

## 12. Icons

### UI-Icons

| ID | Regel | Schwere |
|----|-------|---------|
| ICN1 | Symbolischer Stil (16x16 SVG, monochrom) fuer UI-Icons | Major |
| ICN2 | Groessen: 16, 32, 64, 128px — andere Groessen vermeiden (unscharfes Rendering) | Minor |
| ICN3 | Controls: entweder Icon ODER Label, nicht beides (Ausnahme: Sidebar, ViewSwitcher) | Major |
| ICN4 | Icons nur verwenden wenn Nutzer sie erkennen — im Zweifel Text-Label | Major |
| ICN5 | Manche Icons funktionieren nur als Set (Stop, Remove) | Minor |
| ICN6 | Existierende GTK/Icon Dev Kit Icons wiederverwenden statt eigene erstellen | Minor |
| ICN7 | Eigene Icons: 16x16, 2px Striche, am Pixelraster ausgerichtet, monochrom | Minor |

---

## 13. Barrierefreiheit

| ID | Regel | Schwere |
|----|-------|---------|
| A11Y1 | ALLE Interface-Elemente haben beschreibende Accessible Names | Kritisch |
| A11Y2 | Funktioniert mit High-Contrast-Modus | Kritisch |
| A11Y3 | Funktioniert mit grossem Text (Large Text Mode) | Kritisch |
| A11Y4 | Vollstaendig per Tastatur bedienbar | Kritisch |
| A11Y5 | Funktioniert mit Screen Reader (alle Elemente werden vorgelesen) | Kritisch |
| A11Y6 | Funktioniert mit On-Screen-Keyboard | Major |
| A11Y7 | Farbe nicht als einziges Unterscheidungsmerkmal | Kritisch |
| A11Y8 | Keine blinkenden/blitzenden Elemente | Kritisch |
| A11Y9 | Klickziele gross genug fuer verschiedene Faehigkeiten | Major |
| A11Y10 | Hover darf nicht einzige Methode fuer Aktionen/Info sein | Major |
| A11Y11 | Accessible Names kurz und beschreibend | Minor |
| A11Y12 | Standard-GTK-Beschreibungen wo noetig mit app-spezifischen ueberschreiben | Minor |

---

## 14. Adaptive Gestaltung

| ID | Regel | Schwere |
|----|-------|---------|
| AD1 | Minimale Desktop-Groesse: 1024x600px unterstuetzt | Kritisch |
| AD2 | Minimale Telefon-Groesse (wenn anwendbar): 360x294px | Major |
| AD3 | AdwBreakpoint fuer Layout-Umschaltungen verwenden | Major |
| AD4 | Inhalte in Containern mit Maximalbreite (gegen zu lange Textzeilen) | Major |
| AD5 | Glattes Resizing — keine springenden Widgets | Major |
| AD6 | Design von kleinster Groesse aufwaerts | Minor |
| AD7 | Container-Breiten muessen bei jeder Fenstergroesse gut aussehen | Major |
| AD8 | Sidebars nie uebermaessig breit oder schmal im Verhaeltnis zum Hauptbereich | Minor |
| AD9 | Listen-Patterns bevorzugen (skalieren gut bei schmalen und breiten Views) | Minor |
| AD10 | Keine Aufteilung in viele kleine Panels (schwer adaptiv zu machen) | Major |

---

## 15. Tastatur

| ID | Regel | Schwere |
|----|-------|---------|
| KB1 | Jede Aktion muss per Tastatur moeglich sein | Kritisch |
| KB2 | Standard-GNOME-Shortcuts fuer Standardfunktionen verwenden | Major |
| KB3 | Tab-Reihenfolge logisch und vollstaendig | Major |
| KB4 | Ctrl+Buchstabe fuer eigene Shortcuts (mnemonisch wo moeglich) | Minor |
| KB5 | Shift+Ctrl+Buchstabe fuer Umkehr-/Erweiterungs-Shortcuts | Minor |
| KB6 | KEIN Alt fuer Shortcuts (Konflikt mit Access Keys) | Major |
| KB7 | KEIN Super (System reserviert) | Major |
| KB8 | Unbequeme Griffe vermeiden (Einhand-Bedienung bevorzugen) | Minor |
| KB9 | Access Keys (Mnemonics) fuer alle beschrifteten Controls | Minor |
| KB10 | Alert-Sound wenn Tab den Fokus nicht bewegen kann | Minor |
| KB11 | Control-Labels direkt vor ihrem Control in der Fokus-Reihenfolge | Minor |
| KB12 | Pfeiltasten fuer direktionale Navigation wo sinnvoll | Minor |
| KB13 | Esc bricht laufende Pointer-Operationen ab | Minor |

### Standard-Navigationstasten (muessen funktionieren)

| Taste | Funktion |
|-------|----------|
| Tab | Naechstes Control |
| Shift+Tab | Vorheriges Control |
| Return | Fokussiertes Control aktivieren |
| Space | Zustand umschalten |
| F10 | Primaer-/Sekundaermenue oeffnen |
| Menu / Shift+F10 | Kontextmenue |
| Esc | Transiente Container schliessen |

---

## 16. Zeiger & Touch

| ID | Regel | Schwere |
|----|-------|---------|
| PT1 | Klickziele gross genug fuer verschiedene Eingabegeraete | Major |
| PT2 | Kein Doppelklick oder Chord (mehrere Tasten gleichzeitig) fuer wesentliche Aktionen | Kritisch |
| PT3 | Hover nicht als einzige Methode fuer Aktionen/Info | Major |
| PT4 | Alle Pointer-Aktionen auch per Tastatur moeglich | Kritisch |
| PT5 | Sekundaeraktion (Rechtsklick) nur fuer Kontextmenue, nicht fuer alternative Aktionen | Major |
| PT6 | Kontextmenue auch per Tastatur erreichbar | Major |
| PT7 | Keine 3- oder 4-Finger-Gesten (System reserviert) | Major |
| PT8 | Esc bricht laufende Pointer-Operationen ab | Minor |
| PT9 | Eingabegeraet-agnostische Formulierungen in der UI (nicht "Maus bewegen") | Minor |
| PT10 | Scroll-Views: Scroll + Ctrl+Scroll/Pinch fuer Zoom | Minor |
| PT11 | Pan-Views: Click+Drag/Finger-Drag fuer Pan, Scroll/Pinch fuer Zoom | Minor |

---

## 17. UI-Styling

| ID | Regel | Schwere |
|----|-------|---------|
| STY1 | Light + Dark Style unterstuetzen (AdwStyleManager) | Major |
| STY2 | System-Style-Praeferenz folgen | Major |
| STY3 | Per-App Style-Praeferenz: Light, Dark, System folgen (3 Optionen) | Minor |
| STY4 | High-Contrast-Modus getestet und korrekt gerendert | Kritisch |
| STY5 | Minimale eigene CSS — Libadwaita Style-Klassen und Farbvariablen nutzen | Major |
| STY6 | Eigenes Styling muss mit Light, Dark UND High-Contrast funktionieren | Kritisch |
| STY7 | Style-Klassen und Variablen nicht ausserhalb ihres vorgesehenen Zwecks verwenden | Major |
| STY8 | Farbe nicht als einziges Unterscheidungsmerkmal (Form, Position, Text zusaetzlich) | Kritisch |

---

## Zusammenfassung: Haeufigste Verstoesse

Die folgenden Regeln werden am haeufigsten verletzt und sollten bei jedem Review priorisiert werden:

1. **PREF1** — `AdwPreferencesWindow` statt `AdwPreferencesDialog`
2. **HB5** — Suggested/Destructive Styles in Header Bars
3. **BTN1** — Mehrere Suggested/Destructive Buttons pro View
4. **DLG3** — Generische Button-Labels ("OK", "Fertig")
5. **TYP4** — Hart-codierte Schriftgroessen
6. **A11Y1** — Fehlende Accessible Names
7. **NAV4** — ViewSwitcher wechselt nicht nach unten bei schmalem Fenster
8. **KB1** — Aktionen nur per Maus erreichbar
9. **HB3** — Fehlende Tooltips
10. **AD1** — Minimale Fenstergroesse nicht unterstuetzt
