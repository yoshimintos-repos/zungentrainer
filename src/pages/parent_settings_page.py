"""Eltern-Bereich: Erweiterte Einstellungen hinter Polkit."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class ParentSettingsPage(Gtk.Box):
    """Polkit-geschuetzter Eltern-Bereich mit Trainingsplan-Einstellungen."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window
        self._build_ui()

    def _build_ui(self):
        profile = self._window.profile

        scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(scroll)

        clamp = Adw.Clamp(maximum_size=600)
        scroll.set_child(clamp)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(12)
        content.set_margin_end(12)
        clamp.set_child(content)

        # Trainingsplan
        plan_group = Adw.PreferencesGroup(title="Trainingsplan")
        content.append(plan_group)

        self._trainings_row = Adw.SpinRow.new_with_range(1, 7, 1)
        self._trainings_row.set_title("Trainings pro Woche")
        self._trainings_row.set_value(profile.trainings_per_week)
        self._trainings_row.connect("notify::value", self._on_trainings_changed)
        plan_group.add(self._trainings_row)

        self._duration_row = Adw.SpinRow.new_with_range(5, 60, 5)
        self._duration_row.set_title("Mindest-Trainingsdauer (Minuten)")
        self._duration_row.set_value(profile.min_session_duration)
        self._duration_row.connect("notify::value", self._on_duration_changed)
        plan_group.add(self._duration_row)

        # Erinnerungen
        remind_group = Adw.PreferencesGroup(title="Erinnerungen")
        content.append(remind_group)

        self._remind_row = Adw.SwitchRow(title="Erinnerungen aktiviert")
        self._remind_row.set_subtitle("Freundliche Hinweise wenn Trainings ausstehen")
        self._remind_row.set_active(profile.reminders_enabled)
        self._remind_row.connect("notify::active", self._on_reminders_changed)
        remind_group.add(self._remind_row)

        # Schwierigkeit
        diff_group = Adw.PreferencesGroup(title="Schwierigkeit")
        diff_group.set_description(
            "Die Schwierigkeit passt sich normalerweise automatisch an"
        )
        content.append(diff_group)

        params = self._window.adaptive_difficulty.get_params()
        self._sensitivity_row = Adw.ActionRow(title="Empfindlichkeit")
        sens_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.5, 2.0, 0.1
        )
        sens_scale.set_value(params.get("sensitivity", 1.0))
        sens_scale.set_size_request(200, -1)
        sens_scale.set_valign(Gtk.Align.CENTER)
        sens_scale.connect("value-changed", self._on_sensitivity_changed)
        self._sensitivity_row.add_suffix(sens_scale)
        diff_group.add(self._sensitivity_row)

    def _on_trainings_changed(self, row, _param):
        self._window.profile.trainings_per_week = int(row.get_value())
        self._window.save_profile()

    def _on_duration_changed(self, row, _param):
        self._window.profile.min_session_duration = int(row.get_value())
        self._window.save_profile()

    def _on_reminders_changed(self, row, _param):
        self._window.profile.reminders_enabled = row.get_active()
        self._window.save_profile()

    def _on_sensitivity_changed(self, scale):
        params = self._window.adaptive_difficulty.get_params()
        params["sensitivity"] = round(scale.get_value(), 2)
        self._window.adaptive_difficulty._params = params
        self._window.profile.difficulty_params = params
        self._window.save_profile()
