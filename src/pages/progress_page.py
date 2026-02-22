"""Fortschritts-Seite mit Level, XP und Statistiken."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from gamification.level_system import MAX_LEVEL


class ProgressPage(Gtk.Box):
    """Zeigt Level-Fortschritt, XP-Balken und Trainingsstatistiken."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._window = main_window
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroll)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        scroll.set_child(clamp)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(16)
        content.set_margin_end(16)
        clamp.set_child(content)

        # Level-Anzeige (eigenständig, nicht in PreferencesGroup)
        level_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        level_box.set_halign(Gtk.Align.CENTER)

        self._level_label = Gtk.Label()
        self._level_label.add_css_class("title-1")
        level_box.append(self._level_label)

        # XP-Balken
        xp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        self._xp_label = Gtk.Label()
        self._xp_label.add_css_class("caption")
        self._xp_label.add_css_class("dim-label")
        xp_box.append(self._xp_label)

        self._xp_bar = Gtk.ProgressBar()
        self._xp_bar.set_show_text(False)
        xp_box.append(self._xp_bar)

        level_box.append(xp_box)
        content.append(level_box)

        # Schwierigkeit
        diff_group = Adw.PreferencesGroup()
        diff_group.set_title("Aktuelle Schwierigkeit")
        content.append(diff_group)

        self._beep_row = Adw.ActionRow(title="Piep-Verzögerung")
        diff_group.add(self._beep_row)
        self._pause_row = Adw.ActionRow(title="Medienpausen-Auslösung")
        diff_group.add(self._pause_row)
        self._resume_row = Adw.ActionRow(title="Medienpausen-Dauer")
        diff_group.add(self._resume_row)
        self._cooldown_row = Adw.ActionRow(title="Abklingzeit")
        diff_group.add(self._cooldown_row)
        self._sensitivity_row = Adw.ActionRow(title="Empfindlichkeit")
        diff_group.add(self._sensitivity_row)
        self._max_inc_row = Adw.ActionRow(title="Max. Vorfälle")
        diff_group.add(self._max_inc_row)
        self._session_time_row = Adw.ActionRow(title="Min. Sitzungsdauer")
        diff_group.add(self._session_time_row)

        # Statistiken
        stats_group = Adw.PreferencesGroup()
        stats_group.set_title("Statistiken")
        content.append(stats_group)

        self._sessions_row = Adw.ActionRow(title="Sitzungen")
        stats_group.add(self._sessions_row)
        self._success_row = Adw.ActionRow(title="Erfolgreiche Sitzungen")
        stats_group.add(self._success_row)
        self._time_row = Adw.ActionRow(title="Gesamte Trainingszeit")
        stats_group.add(self._time_row)
        self._incidents_row = Adw.ActionRow(title="Gesamte Vorfälle")
        stats_group.add(self._incidents_row)
        self._streak_row = Adw.ActionRow(title="Aktueller Streak")
        stats_group.add(self._streak_row)
        self._best_streak_row = Adw.ActionRow(title="Bester Streak")
        stats_group.add(self._best_streak_row)

    def refresh(self):
        """Aktualisiert die Anzeige mit aktuellen Profildaten."""
        profile = self._window.profile
        level_sys = self._window.level_system

        # Level
        self._level_label.set_label(f"Level {profile.level}")

        # XP
        if profile.level >= MAX_LEVEL:
            self._xp_label.set_label("Maximales Level erreicht!")
            self._xp_bar.set_fraction(1.0)
        else:
            xp_in_level = level_sys.xp_in_current_level(profile.level, profile.total_xp)
            xp_needed = level_sys.xp_for_next_level(profile.level)
            self._xp_label.set_label(f"{xp_in_level} / {xp_needed} XP")
            fraction = xp_in_level / xp_needed if xp_needed > 0 else 0
            self._xp_bar.set_fraction(max(0.0, min(1.0, fraction)))

        # Schwierigkeit
        diff = level_sys.get_difficulty(profile.level)
        self._beep_row.set_subtitle(f"{diff['beep_delay']:.1f} Sekunden")
        self._pause_row.set_subtitle(f"{diff['pause_delay']:.1f} Sekunden")
        resume = diff['resume_delay']
        if resume == 0:
            self._resume_row.set_subtitle("Aus (nur Piep)")
        else:
            self._resume_row.set_subtitle(f"{resume:.0f} Sekunden")
        self._cooldown_row.set_subtitle(f"{diff['cooldown_time']:.1f} Sekunden")
        self._sensitivity_row.set_subtitle(f"{diff['sensitivity']:.1f}x über Baseline")
        max_inc = diff["max_incidents"]
        self._max_inc_row.set_subtitle("Unbegrenzt" if max_inc <= 0 else str(max_inc))
        mins = int(diff["required_session_time"]) // 60
        self._session_time_row.set_subtitle(f"{mins} Minuten")

        # Statistiken
        self._sessions_row.set_subtitle(str(profile.total_sessions))
        self._success_row.set_subtitle(str(profile.successful_sessions))

        total_mins = int(profile.total_training_time) // 60
        hours = total_mins // 60
        mins = total_mins % 60
        self._time_row.set_subtitle(f"{hours}h {mins}min")

        self._incidents_row.set_subtitle(str(profile.total_incidents))
        self._streak_row.set_subtitle(f"{profile.current_streak} Tage")
        self._best_streak_row.set_subtitle(f"{profile.best_streak} Tage")
