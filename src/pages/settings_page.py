"""Einstellungs-Seite (Platzhalter)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw

class SettingsPage(Adw.PreferencesPage):
    def __init__(self, main_window):
        super().__init__()
        self._window = main_window
        group = Adw.PreferencesGroup(title="Einstellungen")
        group.set_description("Platzhalter")
        self.add(group)

    def refresh(self):
        pass
