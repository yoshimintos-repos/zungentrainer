"""Einstellungs-Seite mit AdwPreferencesPage."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class SettingsPage(Adw.PreferencesPage):
    """Einstellungen für Kamera, Ton und Empfindlichkeit."""

    def __init__(self, main_window):
        super().__init__()
        self._window = main_window
        self._build_ui()

    def _build_ui(self):
        profile = self._window.profile

        # Kamera-Gruppe
        camera_group = Adw.PreferencesGroup()
        camera_group.set_title("Kamera")
        camera_group.set_description("Webcam-Einstellungen")
        self.add(camera_group)

        # Kamera-Index
        camera_row = Adw.SpinRow.new_with_range(0, 10, 1)
        camera_row.set_title("Kamera-Index")
        camera_row.set_subtitle("0 = Standard-Webcam")
        camera_row.set_value(profile.settings.get("camera_index", 0))
        camera_row.connect("notify::value", self._on_camera_changed)
        camera_group.add(camera_row)

        # Ton-Gruppe
        sound_group = Adw.PreferencesGroup()
        sound_group.set_title("Ton")
        sound_group.set_description("Piepton-Einstellungen")
        self.add(sound_group)

        # Lautstärke
        volume_row = Adw.ActionRow()
        volume_row.set_title("Lautstärke")
        self._volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 5
        )
        self._volume_scale.set_value(profile.settings.get("volume", 0.5) * 100)
        self._volume_scale.set_size_request(200, -1)
        self._volume_scale.set_valign(Gtk.Align.CENTER)
        self._volume_scale.connect("value-changed", self._on_volume_changed)
        volume_row.add_suffix(self._volume_scale)
        sound_group.add(volume_row)

        # Frequenz
        freq_row = Adw.SpinRow.new_with_range(200, 2000, 50)
        freq_row.set_title("Piepton-Frequenz")
        freq_row.set_subtitle("Hz")
        freq_row.set_value(profile.settings.get("beep_frequency", 800))
        freq_row.connect("notify::value", self._on_freq_changed)
        sound_group.add(freq_row)

        # Erkennung
        detect_group = Adw.PreferencesGroup()
        detect_group.set_title("Erkennung")
        detect_group.set_description(
            "Die Empfindlichkeit wird automatisch durch das Level angepasst"
        )
        self.add(detect_group)

        # Empfindlichkeits-Anzeige (nur lesen)
        diff = self._window.level_system.get_difficulty(profile.level)
        self._sens_row = Adw.ActionRow()
        self._sens_row.set_title("Empfindlichkeits-Multiplikator")
        self._sens_row.set_subtitle(
            f"{diff['sensitivity']:.1f}x über Baseline (Level {profile.level})"
        )
        detect_group.add(self._sens_row)

        # Test-Modus
        test_group = Adw.PreferencesGroup()
        test_group.set_title("Test-Modus")
        self.add(test_group)

        self._pause_expander = Adw.ExpanderRow()
        self._pause_expander.set_title("Medienpausen-Auslösung überschreiben")
        self._pause_expander.set_subtitle(
            "Einmalig für die nächste Sitzung, wird danach zurückgesetzt"
        )
        self._pause_expander.set_enable_expansion(False)
        self._pause_expander.set_expanded(False)
        self._pause_expander.set_show_enable_switch(True)
        self._pause_expander.connect(
            "notify::enable-expansion", self._on_pause_override_toggled
        )
        test_group.add(self._pause_expander)

        self._pause_spin = Adw.SpinRow.new_with_range(0, 120, 1)
        self._pause_spin.set_title("Dauer in Sekunden")
        self._pause_spin.set_subtitle(
            f"Level-Standard: {diff['pause_delay']:.1f}s"
        )
        self._pause_spin.set_value(diff["pause_delay"])
        self._pause_spin.connect("notify::value", self._on_pause_value_changed)
        self._pause_expander.add_row(self._pause_spin)

        # Daten-Gruppe
        data_group = Adw.PreferencesGroup()
        data_group.set_title("Daten")
        self.add(data_group)

        # Name
        name_row = Adw.EntryRow()
        name_row.set_title("Name")
        name_row.set_text(profile.name)
        name_row.connect("changed", self._on_name_changed)
        data_group.add(name_row)

        # Reset-Button
        reset_row = Adw.ActionRow()
        reset_row.set_title("Fortschritt zurücksetzen")
        reset_row.set_subtitle("Löscht alle Daten unwiderruflich")

        reset_btn = Gtk.Button(label="Zurücksetzen")
        reset_btn.add_css_class("destructive-action")
        reset_btn.set_valign(Gtk.Align.CENTER)
        reset_btn.connect("clicked", self._on_reset)
        reset_row.add_suffix(reset_btn)
        data_group.add(reset_row)

    def _on_camera_changed(self, row, _param):
        self._window.profile.settings["camera_index"] = int(row.get_value())
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_volume_changed(self, scale):
        self._window.profile.settings["volume"] = scale.get_value() / 100.0
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_freq_changed(self, row, _param):
        self._window.profile.settings["beep_frequency"] = int(row.get_value())
        self._window.save_profile()
        self._window.training_page.update_settings()

    def refresh(self):
        """Aktualisiert die Empfindlichkeits-Anzeige nach Level-Änderung."""
        profile = self._window.profile
        diff = self._window.level_system.get_difficulty(profile.level)
        self._sens_row.set_subtitle(
            f"{diff['sensitivity']:.1f}x über Baseline (Level {profile.level})"
        )
        self._pause_spin.set_subtitle(
            f"Level-Standard: {diff['pause_delay']:.1f}s"
        )

    def reset_pause_override(self):
        """Setzt den Test-Modus zurück (nach Sitzungsende)."""
        self._pause_expander.set_enable_expansion(False)
        self._pause_expander.set_expanded(False)

    def _on_pause_override_toggled(self, expander, _param):
        active = expander.get_enable_expansion()
        if active:
            self._window.pause_delay_override = self._pause_spin.get_value()
        else:
            self._window.pause_delay_override = None

    def _on_pause_value_changed(self, row, _param):
        if self._pause_expander.get_enable_expansion():
            self._window.pause_delay_override = row.get_value()

    def _on_name_changed(self, row):
        self._window.profile.name = row.get_text()
        self._window.save_profile()

    def _on_reset(self, button):
        dialog = Adw.AlertDialog()
        dialog.set_heading("Fortschritt zurücksetzen?")
        dialog.set_body(
            "Alle Level, XP, Abzeichen und Zungenfreunde werden gelöscht. "
            "Das kann nicht rückgängig gemacht werden!"
        )
        dialog.add_response("cancel", "Abbrechen")
        dialog.add_response("reset", "Zurücksetzen")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.choose(self._window, None, self._on_reset_response)

    def _on_reset_response(self, dialog, result):
        response = dialog.choose_finish(result)
        if response == "reset":
            from models.user_data import UserProfile
            settings = self._window.profile.settings.copy()
            self._window.profile = UserProfile()
            self._window.profile.settings = settings
            self._window.save_profile()
            self._window.refresh_pages()
