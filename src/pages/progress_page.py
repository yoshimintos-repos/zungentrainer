"""Fortschritts-Seite (Platzhalter)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class ProgressPage(Gtk.Box):
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window
        label = Adw.StatusPage(
            title="Fortschritt",
            description="Wochenstatistiken und Meilensteine",
            icon_name="starred-symbolic",
        )
        self.append(label)

    def refresh(self):
        pass
