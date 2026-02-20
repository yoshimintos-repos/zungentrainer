"""Hauptfenster mit ViewStack-Navigation."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from pages.training_page import TrainingPage
from pages.progress_page import ProgressPage
from pages.collection_page import CollectionPage
from pages.settings_page import SettingsPage
from models.persistence import DataStore
from gamification.level_system import LevelSystem
from gamification.badge_system import BadgeSystem
from gamification.creature_system import CreatureSystem


class ZungenTrainerWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("ZungenTrainer")
        self.set_default_size(480, 700)

        # Datenspeicher und Gamification laden
        self.data_store = DataStore()
        self.profile = self.data_store.load()
        self.level_system = LevelSystem()
        self.badge_system = BadgeSystem()
        self.creature_system = CreatureSystem()

        # Test-Modus: einmaliger Override für Medienpausen-Auslösedauer
        self.pause_delay_override = None

        # Hauptlayout
        self._build_ui()

        # Beim Schließen aufräumen
        self.connect("close-request", self._on_close)

    def _build_ui(self):
        # AdwToolbarView für korrektes Header/Content/Bottom-Layout
        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        # Header
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # ViewStack
        self.view_stack = Adw.ViewStack()
        self.view_stack.set_vexpand(True)
        toolbar_view.set_content(self.view_stack)

        # ViewSwitcherBar (unten)
        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self.view_stack)
        toolbar_view.add_bottom_bar(switcher_bar)

        # ViewSwitcherTitle (im Header)
        switcher_title = Adw.ViewSwitcherTitle()
        switcher_title.set_stack(self.view_stack)
        switcher_title.set_title("ZungenTrainer")
        header.set_title_widget(switcher_title)

        # Switcher-Bar bei schmalen Fenstern anzeigen
        switcher_title.connect(
            "notify::title-visible",
            lambda st, _: switcher_bar.set_reveal(st.get_title_visible()),
        )

        # Seiten erstellen
        self.training_page = TrainingPage(self)
        self.progress_page = ProgressPage(self)
        self.collection_page = CollectionPage(self)
        self.settings_page = SettingsPage(self)

        self.view_stack.add_titled_with_icon(
            self.training_page, "training", "Training", "camera-video-symbolic"
        )
        self.view_stack.add_titled_with_icon(
            self.progress_page, "progress", "Fortschritt", "go-up-symbolic"
        )
        self.view_stack.add_titled_with_icon(
            self.collection_page, "collection", "Sammlung", "view-grid-symbolic"
        )
        self.view_stack.add_titled_with_icon(
            self.settings_page, "settings", "Einstellungen", "preferences-system-symbolic"
        )

    def save_profile(self):
        self.data_store.save(self.profile)

    def refresh_pages(self):
        """Alle Seiten nach Datenänderung aktualisieren."""
        self.progress_page.refresh()
        self.collection_page.refresh()
        self.settings_page.refresh()

    def _on_close(self, *args):
        self.training_page.cleanup()
        self.save_profile()
        return False
