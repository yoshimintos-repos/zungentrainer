# src/pages/onboarding_page.py
"""Onboarding: 5-Schritt-Assistent beim ersten Start."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib


class OnboardingPage(Gtk.Box):
    """AdwCarousel-basiertes Onboarding mit 5 Schritten."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window
        self._build_ui()

    def _build_ui(self):
        self._carousel = Adw.Carousel()
        self._carousel.set_vexpand(True)
        self.append(self._carousel)

        # Carousel-Indikator
        indicator = Adw.CarouselIndicatorDots()
        indicator.set_carousel(self._carousel)
        indicator.set_margin_bottom(12)
        self.append(indicator)

        # Schritt 1: Willkommen
        welcome = Adw.StatusPage(
            title="Willkommen bei ZungenTrainer",
            description="Diese App hilft dir, die Zunge nicht mehr rauszustrecken",
            icon_name="de.yoshimintos.ZungenTrainer",
        )
        next_btn_1 = Gtk.Button(label="Weiter")
        next_btn_1.add_css_class("suggested-action")
        next_btn_1.add_css_class("pill")
        next_btn_1.set_halign(Gtk.Align.CENTER)
        next_btn_1.set_margin_bottom(24)
        next_btn_1.connect("clicked", lambda _: self._go_to(1))
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        welcome_box.append(welcome)
        welcome_box.append(next_btn_1)
        self._carousel.append(welcome_box)

        # Schritt 2: Kamera
        camera = Adw.StatusPage(
            title="Kamera",
            description="Die App nutzt deine Webcam um die Zunge zu erkennen. Die Kamera wird automatisch erkannt",
            icon_name="camera-video-symbolic",
        )
        next_btn_2 = Gtk.Button(label="Weiter")
        next_btn_2.add_css_class("suggested-action")
        next_btn_2.add_css_class("pill")
        next_btn_2.set_halign(Gtk.Align.CENTER)
        next_btn_2.set_margin_bottom(24)
        next_btn_2.connect("clicked", lambda _: self._go_to(2))
        camera_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        camera_box.append(camera)
        camera_box.append(next_btn_2)
        self._carousel.append(camera_box)

        # Schritt 3: Kalibrierung
        cal = Adw.StatusPage(
            title="Kalibrierung",
            description="Beim ersten Training zeigst du kurz die Zunge, damit die App deine Zungenfarbe lernt",
            icon_name="system-run-symbolic",
        )
        next_btn_3 = Gtk.Button(label="Weiter")
        next_btn_3.add_css_class("suggested-action")
        next_btn_3.add_css_class("pill")
        next_btn_3.set_halign(Gtk.Align.CENTER)
        next_btn_3.set_margin_bottom(24)
        next_btn_3.connect("clicked", lambda _: self._go_to(3))
        cal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cal_box.append(cal)
        cal_box.append(next_btn_3)
        self._carousel.append(cal_box)

        # Schritt 4: Name
        name_page = Adw.StatusPage(
            title="Wie heisst du?",
            icon_name="avatar-default-symbolic",
        )
        name_group = Adw.PreferencesGroup()
        name_group.set_halign(Gtk.Align.CENTER)
        name_group.set_margin_start(48)
        name_group.set_margin_end(48)
        self._name_entry = Adw.EntryRow(title="Name")
        self._name_entry.set_text(self._window.profile.name)
        name_group.add(self._name_entry)
        next_btn_4 = Gtk.Button(label="Weiter")
        next_btn_4.add_css_class("suggested-action")
        next_btn_4.add_css_class("pill")
        next_btn_4.set_halign(Gtk.Align.CENTER)
        next_btn_4.set_margin_top(24)
        next_btn_4.set_margin_bottom(24)
        next_btn_4.connect("clicked", self._on_name_next)
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_box.append(name_page)
        name_box.append(name_group)
        name_box.append(next_btn_4)
        self._carousel.append(name_box)

        # Schritt 5: Los geht's
        start = Adw.StatusPage(
            title="Alles bereit!",
            description="Starte dein erstes Training",
            icon_name="emblem-ok-symbolic",
        )
        start_btn = Gtk.Button(label="Training starten")
        start_btn.add_css_class("suggested-action")
        start_btn.add_css_class("pill")
        start_btn.set_halign(Gtk.Align.CENTER)
        start_btn.set_margin_bottom(24)
        start_btn.connect("clicked", self._on_finish)
        start_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        start_box.append(start)
        start_box.append(start_btn)
        self._carousel.append(start_box)

    def _go_to(self, index: int):
        page = self._carousel.get_nth_page(index)
        self._carousel.scroll_to(page, True)

    def _on_name_next(self, _btn):
        name = self._name_entry.get_text().strip()
        if name:
            self._window.profile.name = name
        self._go_to(4)

    def _on_finish(self, _btn):
        self._window.profile.onboarding_done = True
        self._window.save_profile()
        self._window.finish_onboarding()
