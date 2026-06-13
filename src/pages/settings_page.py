"""Reduzierte Einstellungen fuer die v3-Ueberwachung."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


def _make_button_row(title: str, start_icon: str | None = None) -> tuple:
    """Erstellt eine klickbare Zeile mit Libadwaita-Fallback."""
    if hasattr(Adw, "ButtonRow"):
        row = Adw.ButtonRow(title=title)
        if start_icon:
            row.set_start_icon_name(start_icon)
        return row, row

    row = Adw.ActionRow(title=title)
    btn = Gtk.Button()
    if start_icon:
        btn.set_icon_name(start_icon)
    else:
        btn.set_label(title)
    btn.set_valign(Gtk.Align.CENTER)
    btn.add_css_class("flat")
    row.add_suffix(btn)
    row.set_activatable_widget(btn)
    return row, btn


class SettingsPage(Adw.PreferencesPage):
    """Nur die wichtigsten Einstellungen fuer den Alltag."""

    def __init__(self, main_window):
        super().__init__()
        self._window = main_window
        self._build_ui()

    def _build_ui(self):
        profile = self._window.profile

        camera_group = Adw.PreferencesGroup(title="Kamera")
        self.add(camera_group)

        camera_row = Adw.SpinRow.new_with_range(0, 10, 1)
        camera_row.set_title("Kamera")
        camera_row.set_subtitle("0 = Standard-Webcam")
        camera_row.set_value(profile.settings.get("camera_index", 0))
        camera_row.connect("notify::value", self._on_camera_changed)
        camera_group.add(camera_row)

        feedback_group = Adw.PreferencesGroup(title="Feedback")
        self.add(feedback_group)

        volume_row = Adw.ActionRow(title="Lautstaerke")
        self._volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 5
        )
        self._volume_scale.set_value(profile.settings.get("volume", 0.5) * 100)
        self._volume_scale.set_size_request(200, -1)
        self._volume_scale.set_valign(Gtk.Align.CENTER)
        self._volume_scale.connect("value-changed", self._on_volume_changed)
        volume_row.add_suffix(self._volume_scale)
        feedback_group.add(volume_row)

        self._pause_media_row = Adw.SwitchRow(title="Medien pausieren")
        self._pause_media_row.set_subtitle(
            "Laufende Filme, Musik oder Podcasts bei erkannter Zunge pausieren"
        )
        self._pause_media_row.set_active(profile.settings.get("pause_media", True))
        self._pause_media_row.connect("notify::active", self._on_pause_media_changed)
        feedback_group.add(self._pause_media_row)

        detection_group = Adw.PreferencesGroup(title="Erkennung")
        self.add(detection_group)

        recal_row, recal_target = _make_button_row(
            "Neu kalibrieren", start_icon="view-refresh-symbolic"
        )
        recal_target.connect("activated", self._on_recalibrate)
        detection_group.add(recal_row)

    def _on_camera_changed(self, row, _param):
        self._window.profile.settings["camera_index"] = int(row.get_value())
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_volume_changed(self, scale):
        self._window.profile.settings["volume"] = scale.get_value() / 100.0
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_pause_media_changed(self, row, _param):
        self._window.profile.settings["pause_media"] = row.get_active()
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_recalibrate(self, *args):
        self._window.profile.calibration = {}
        self._window.save_profile()
        self._window.show_toast("Kalibrierung zurueckgesetzt")

    def refresh(self):
        pass
