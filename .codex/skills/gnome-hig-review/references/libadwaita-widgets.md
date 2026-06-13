# Libadwaita Widget-Referenz fuer HIG-Reviews

Schnellreferenz: Welches Widget fuer welchen Zweck. Falsche Widget-Wahl ist einer der haeufigsten HIG-Verstoesse.

## Container & Fenster

| Widget | Zweck | Hinweis |
|--------|-------|---------|
| `AdwApplicationWindow` | Hauptfenster | Immer statt GtkApplicationWindow |
| `AdwToolbarView` | Container fuer Header Bar + Inhalt | Standardstruktur fuer Views |
| `AdwHeaderBar` | Fenster-Header | Statt GtkHeaderBar |
| `AdwClamp` | Inhaltsbreite begrenzen | Gegen zu lange Zeilen auf breiten Bildschirmen |
| `AdwBreakpoint` | Adaptive Layout-Umschaltung | Fuer responsive Designs |

## Navigation

| Widget | Zweck | Wann verwenden |
|--------|-------|----------------|
| `AdwViewStack` | Container fuer gleichwertige Views | 3-5 Views |
| `AdwViewSwitcher` | View-Umschalter in Header Bar | Primaere Navigation |
| `AdwViewSwitcherBar` | View-Umschalter am unteren Rand | Responsive Companion zu ViewSwitcher |
| `AdwNavigationSplitView` | Sidebar-Navigation | > 5 Views oder dynamische Listen |
| `AdwNavigationView` | Stack-basierte hierarchische Navigation | Drill-Down in Details |
| `AdwCarousel` | Horizontales Swipen durch Seiten | Onboarding, Tutorials |

## Feedback

| Widget | Zweck | Wann verwenden |
|--------|-------|----------------|
| `AdwToastOverlay` | Container fuer Toasts | In jede View einbauen die Toasts braucht |
| `AdwToast` | Transiente Nachricht + optionaler Button | Reaktionen auf Nutzeraktionen, Undo |
| `AdwBanner` | Persistente Statusnachricht | Andauernde Zustaende, Warnungen |
| `AdwStatusPage` | Grosses Icon + Titel + Beschreibung | Leere Zustaende, Willkommen, Fehler |
| `AdwAlertDialog` | Bestaetigungs-/Fehlerdialog | Nur wenn noetig (Undo bevorzugen) |
| `AdwSpinner` | Lade-Indikator | Wenn Inhalt geladen wird |

## Einstellungen

| Widget | Zweck | NICHT verwenden |
|--------|-------|----|
| `AdwPreferencesDialog` | Einstellungsfenster | Seit Libadwaita 1.5 |
| `AdwPreferencesPage` | Thematische Einstellungsseite | |
| `AdwPreferencesGroup` | Gruppe verwandter Einstellungen | |
| ~~`AdwPreferencesWindow`~~ | ~~Einstellungsfenster~~ | **DEPRECATED** seit 1.6 |

## Listen-Zeilen (fuer Boxed Lists / Preferences)

| Widget | Zweck | Typischer Einsatz |
|--------|-------|-------------------|
| `AdwActionRow` | Titel + Untertitel + beliebiger Control | Allzweck-Zeile |
| `AdwSwitchRow` | Titel + Untertitel + Switch | Boolean-Einstellungen |
| `AdwComboRow` | Dropdown-Auswahl | Einzelauswahl aus Liste |
| `AdwEntryRow` | Texteingabe | Namen, Pfade, Werte |
| `AdwSpinRow` | Zahleneingabe mit +/- | Numerische Einstellungen |
| `AdwExpanderRow` | Aufklappbar mit Unter-Zeilen | Gruppierte Sub-Einstellungen |
| `AdwButtonRow` | Klickbare Zeile mit Icon | Aktionen in Listen |
| `AdwPropertyRow` | Property-Name + Wert | Informationsanzeige |

## Buttons (Style-Klassen)

| Style-Klasse | Zweck | Regel |
|--------------|-------|-------|
| `.suggested-action` | Affirmative/empfohlene Aktion | Max 1 pro View |
| `.destructive-action` | Gefaehrliche/zerstoererische Aktion | Max 1 pro View |
| `.pill` | Primaere View-Aktion im offenen Raum | Einladenderes Klickziel |
| `.circular` | Kleine runde Buttons | Mehrere kleine Buttons nah beieinander |
| `.flat` | Ohne sichtbaren Hintergrund | Standard in Header Bars |

## Listen (Style-Klassen)

| Style-Klasse | Zweck |
|--------------|-------|
| `.boxed-list` | Einstellungs-/Optionslisten |
| `.boxed-list-separate` | Visuell getrennte Zeilen |
| `.navigation-sidebar` | Sidebar-Navigation |
| `.rich-list` | Listen mit groesseren Zeilen |

## Typografie (CSS-Klassen)

| CSS-Klasse | Zweck |
|------------|-------|
| `body` | Standard-UI-Text, Labels |
| `heading` | UI-Ueberschriften, Fenstertitel |
| `caption` | Kleiner Begleittext |
| `caption-heading` | Kleine Ueberschrift |
| `title-1` bis `title-4` | Display-Ueberschriften (1 = groesste) |
| `large-title` | Groesste Ueberschrift (selten, nur mit viel Whitespace) |
| `dim-label` | Abgedimmter/sekundaerer Text |
| `numeric` | Tabular-Ziffern fuer Zahlenkolonnen |

## GNOME Farbpalette (Referenz)

Fuer App-Icons und Illustrationen. 5 Intensitaetsstufen pro Farbfamilie:

| Farbe | Hell → Dunkel |
|-------|---------------|
| Blau | #99c1f1, #62a0ea, #3584e4, #1c71d8, #1a5fb4 |
| Gruen | #8ff0a4, #57e389, #33d17a, #2ec27e, #26a269 |
| Gelb | #f9f06b, #f8e45c, #f6d32d, #f5c211, #e5a50a |
| Orange | #ffbe6f, #ffa348, #ff7800, #e66100, #c64600 |
| Rot | #f66151, #ed333b, #e01b24, #c01c28, #a51d2d |
| Lila | #dc8add, #c061cb, #9141ac, #813d9c, #613583 |
| Braun | #cdab8f, #b5835a, #986a44, #865e3c, #63452c |
| Hell-Neutral | #ffffff, #f6f5f4, #deddda, #c0bfbc, #9a9996 |
| Dunkel-Neutral | #77767b, #5e5c64, #3d3846, #241f31, #000000 |
