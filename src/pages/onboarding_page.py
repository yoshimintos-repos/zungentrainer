# src/pages/onboarding_page.py
"""Onboarding: 5-Schritt-Assistent beim ersten Start (HIG-konform)."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib


class OnboardingPage(Adw.ToolbarView):
    """AdwCarousel-basiertes Onboarding mit 5 Schritten.

    Jeder Schritt ist eine AdwStatusPage mit konsistenter Struktur:
    Icon, Titel, Beschreibung und optionalem Child-Widget.
    Navigation ueber Weiter-Buttons (.suggested-action .pill).
    """

    def __init__(self, main_window):
        super().__init__()
        self._window = main_window
        self._build_ui()

    # -- Aufbau ---------------------------------------------------------

    def _build_ui(self):
        # Header Bar (leer, nur fuer Fenster-Dragging und konsistentes Look)
        header = Adw.HeaderBar()
        header.set_show_title(False)
        self.add_top_bar(header)

        # Hauptcontainer
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Carousel
        self._carousel = Adw.Carousel()
        self._carousel.set_vexpand(True)
        self._carousel.set_allow_long_swipes(True)
        self._carousel.set_allow_scroll_wheel(False)
        self._carousel.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Einrichtungsassistent"]
        )
        main_box.append(self._carousel)

        # Indikator-Punkte am unteren Rand
        indicator = Adw.CarouselIndicatorDots()
        indicator.set_carousel(self._carousel)
        indicator.set_margin_top(6)
        indicator.set_margin_bottom(12)
        main_box.append(indicator)

        # Schritte aufbauen
        self._build_welcome_step()
        self._build_camera_step()
        self._build_calibration_step()
        self._build_name_step()
        self._build_finish_step()

    # -- Schritt 1: Willkommen ------------------------------------------

    def _build_welcome_step(self):
        btn = self._make_next_button("Weiter", 1)
        page = Adw.StatusPage(
            title="Willkommen beim ZungenTrainer",
            description=(
                "Diese App hilft dir, die Zunge drin zu behalten \u2013 "
                "mit Kamera, Spielen und Belohnungen"
            ),
            icon_name="de.yoshimintos.ZungenTrainer",
            child=btn,
        )
        page.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Willkommen beim ZungenTrainer"],
        )
        self._carousel.append(page)

    # -- Schritt 2: Kamera ----------------------------------------------

    def _build_camera_step(self):
        btn = self._make_next_button("Weiter", 2)
        page = Adw.StatusPage(
            title="Deine Kamera",
            description="Die Webcam erkennt automatisch, ob deine Zunge drau\u00dfen ist",
            icon_name="camera-video-symbolic",
            child=btn,
        )
        page.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Kamera-Erkl\u00e4rung"],
        )
        self._carousel.append(page)

    # -- Schritt 3: Kalibrierung ----------------------------------------

    def _build_calibration_step(self):
        btn = self._make_next_button("Weiter", 3)
        page = Adw.StatusPage(
            title="Kalibrierung",
            description=(
                "Beim ersten Training zeigst du kurz die Zunge, "
                "damit die App sie kennenlernt"
            ),
            icon_name="system-run-symbolic",
            child=btn,
        )
        page.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Kalibrierung"],
        )
        self._carousel.append(page)

    # -- Schritt 4: Name ------------------------------------------------

    def _build_name_step(self):
        # Eingabefeld in AdwClamp + PreferencesGroup
        self._name_entry = Adw.EntryRow(title="Dein Name")
        self._name_entry.set_text(self._window.profile.name)
        self._name_entry.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Name eingeben"],
        )

        group = Adw.PreferencesGroup()
        group.add(self._name_entry)

        clamp = Adw.Clamp(maximum_size=360)
        clamp.set_child(group)

        btn = Gtk.Button(label="Weiter")
        btn.add_css_class("suggested-action")
        btn.add_css_class("pill")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_tooltip_text("N\u00e4chster Schritt")
        btn.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Weiter zu Schritt 5"],
        )
        btn.connect("clicked", self._on_name_next)

        # Vertikaler Container fuer Clamp + Button
        child_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=24,
            halign=Gtk.Align.CENTER,
        )
        child_box.append(clamp)
        child_box.append(btn)

        page = Adw.StatusPage(
            title="Wie hei\u00dft du?",
            icon_name="avatar-default-symbolic",
            child=child_box,
        )
        page.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Name eingeben"],
        )
        self._carousel.append(page)

    # -- Schritt 5: Los geht's ------------------------------------------

    def _build_finish_step(self):
        btn = Gtk.Button(label="Los geht\u2019s!")
        btn.add_css_class("suggested-action")
        btn.add_css_class("pill")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_tooltip_text("Erstes Training starten")
        btn.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Training starten"],
        )
        btn.connect("clicked", self._on_finish)

        page = Adw.StatusPage(
            title="Alles Bereit!",
            description="Starte jetzt dein erstes Training",
            icon_name="starred-symbolic",
            child=btn,
        )
        page.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Alles bereit"],
        )
        self._carousel.append(page)

    # -- Hilfsfunktionen ------------------------------------------------

    def _make_next_button(self, label: str, target_index: int) -> Gtk.Button:
        """Erzeugt einen einheitlichen Weiter-Button (.suggested-action .pill)."""
        btn = Gtk.Button(label=label)
        btn.add_css_class("suggested-action")
        btn.add_css_class("pill")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_tooltip_text("N\u00e4chster Schritt")
        btn.update_property(
            [Gtk.AccessibleProperty.LABEL],
            [f"Weiter zu Schritt {target_index + 1}"],
        )
        btn.connect("clicked", lambda _b: self._go_to(target_index))
        return btn

    def _go_to(self, index: int):
        """Scrollt zur Carousel-Seite mit dem gegebenen Index."""
        page = self._carousel.get_nth_page(index)
        self._carousel.scroll_to(page, True)

    def _on_name_next(self, _btn):
        """Speichert den Namen und geht zum naechsten Schritt."""
        self._save_name()
        self._go_to(4)

    def _save_name(self):
        """Speichert den eingegebenen Namen im Profil."""
        name = self._name_entry.get_text().strip()
        if name:
            self._window.profile.name = name

    def _on_finish(self, _btn):
        """Schliesst das Onboarding ab und wechselt zur Hauptansicht."""
        # Namen nochmal sichern, falls im letzten Schritt geaendert
        self._save_name()
        self._window.profile.onboarding_done = True
        self._window.save_profile()
        self._window.finish_onboarding()
