"""Einstellungs-Seite mit AdwPreferencesPage."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

# AdwButtonRow ist seit Libadwaita 1.6 verfuegbar.
_HAS_BUTTON_ROW = hasattr(Adw, "ButtonRow")


def _make_button_row(title: str, start_icon: str | None = None,
                     end_icon: str | None = None) -> tuple:
    """Erstellt eine klickbare Zeile.

    Gibt (row, connect_target) zurueck. connect_target ist das Objekt,
    dessen Signal "activated" verbunden werden soll.
    """
    if _HAS_BUTTON_ROW:
        row = Adw.ButtonRow(title=title)
        if start_icon:
            row.set_start_icon_name(start_icon)
        if end_icon:
            row.set_end_icon_name(end_icon)
        return row, row
    else:
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
    """Einstellungen fuer Kamera, Ton und Name."""

    def __init__(self, main_window):
        super().__init__()
        self._window = main_window
        self._build_ui()

    def _build_ui(self):
        profile = self._window.profile

        # --- Kamera ---
        camera_group = Adw.PreferencesGroup(title="Kamera")
        self.add(camera_group)

        camera_row = Adw.SpinRow.new_with_range(0, 10, 1)
        camera_row.set_title("Kamera-Index")
        camera_row.set_subtitle("0 = Standard-Webcam")
        camera_row.set_value(profile.settings.get("camera_index", 0))
        camera_row.connect("notify::value", self._on_camera_changed)
        camera_group.add(camera_row)

        # --- Ton ---
        sound_group = Adw.PreferencesGroup(title="Ton")
        self.add(sound_group)

        volume_row = Adw.ActionRow(title="Lautstaerke")
        self._volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 5
        )
        self._volume_scale.set_value(profile.settings.get("volume", 0.5) * 100)
        self._volume_scale.set_size_request(200, -1)
        self._volume_scale.set_valign(Gtk.Align.CENTER)
        self._volume_scale.connect("value-changed", self._on_volume_changed)
        volume_row.add_suffix(self._volume_scale)
        sound_group.add(volume_row)

        # --- Profil ---
        profile_group = Adw.PreferencesGroup(title="Profil")
        self.add(profile_group)

        name_row = Adw.EntryRow(title="Name")
        name_row.set_text(profile.name)
        name_row.connect("changed", self._on_name_changed)
        profile_group.add(name_row)

        # --- Erkennung / Kalibrierung ---
        cal_group = Adw.PreferencesGroup(title="Erkennung")
        self.add(cal_group)

        recal_row, recal_target = _make_button_row(
            "Neu kalibrieren", start_icon="view-refresh-symbolic"
        )
        recal_target.connect("activated", self._on_recalibrate)
        cal_group.add(recal_row)

        # --- Eltern-Bereich (Platzhalter — Polkit kommt in Phase 3) ---
        parent_group = Adw.PreferencesGroup(title="Eltern-Bereich")
        parent_group.set_description("Erweiterte Einstellungen (Phase 3: Polkit)")
        self.add(parent_group)

        parent_row, _ = _make_button_row(
            "Eltern-Bereich oeffnen",
            start_icon="system-lock-screen-symbolic",
            end_icon="go-next-symbolic" if _HAS_BUTTON_ROW else None,
        )
        parent_row.set_sensitive(False)
        parent_group.add(parent_row)

        # --- Daten zuruecksetzen ---
        reset_group = Adw.PreferencesGroup()
        self.add(reset_group)

        reset_row, reset_target = _make_button_row("Fortschritt zuruecksetzen")
        reset_row.add_css_class("destructive-action")
        reset_target.connect("activated", self._on_reset)
        reset_group.add(reset_row)

    # --- Signal-Handler ---

    def _on_camera_changed(self, row, _param):
        self._window.profile.settings["camera_index"] = int(row.get_value())
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_volume_changed(self, scale):
        self._window.profile.settings["volume"] = scale.get_value() / 100.0
        self._window.save_profile()
        self._window.training_page.update_settings()

    def _on_name_changed(self, row):
        self._window.profile.name = row.get_text()
        self._window.save_profile()

    def _on_recalibrate(self, *args):
        self._window.profile.calibration = {}
        self._window.save_profile()
        toast = Adw.Toast(title="Kalibrierung zurueckgesetzt")
        self._window.training_page._toast_overlay.add_toast(toast)

    def _on_reset(self, *args):
        dialog = Adw.AlertDialog()
        dialog.set_heading("Fortschritt zuruecksetzen?")
        dialog.set_body(
            "Alle Trainingsdaten und Meilensteine werden geloescht. "
            "Das kann nicht rueckgaengig gemacht werden!"
        )
        dialog.add_response("cancel", "Abbrechen")
        dialog.add_response("reset", "Zuruecksetzen")
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

    def refresh(self):
        pass
