"""Trainings-Seite (Platzhalter)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class TrainingPage(Gtk.Box):
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window
        label = Adw.StatusPage(
            title="Training",
            description="Kamera-Feed und Erkennung",
            icon_name="camera-video-symbolic",
        )
        self.append(label)

    def cleanup(self):
        pass

    def pause_training(self):
        pass

    def resume_training(self):
        pass

    def update_settings(self):
        pass
