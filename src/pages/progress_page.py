"""Fortschritts-Seite mit Wochenstatistiken und Meilensteinen."""
from datetime import datetime, timedelta
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class ProgressPage(Gtk.Box):
    """Zeigt Trainingsfortschritt: Wochenuebersicht und Meilensteine."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window

        scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(scroll)

        self._clamp = Adw.Clamp(maximum_size=600)
        scroll.set_child(self._clamp)

        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self._content.set_margin_top(24)
        self._content.set_margin_bottom(24)
        self._content.set_margin_start(12)
        self._content.set_margin_end(12)
        self._clamp.set_child(self._content)

        self._build_empty_state()

    def _build_empty_state(self):
        self._status_page = Adw.StatusPage(
            title="Noch keine Trainings",
            description="Starte dein erstes Training um Fortschritt zu sehen",
            icon_name="starred-symbolic",
        )
        self._content.append(self._status_page)

    def refresh(self):
        profile = self._window.profile

        # Content leeren
        while child := self._content.get_first_child():
            self._content.remove(child)

        if profile.total_sessions == 0:
            self._build_empty_state()
            return

        # Wochenuebersicht
        week_group = Adw.PreferencesGroup(title="Diese Woche")
        self._content.append(week_group)

        sessions_this_week = self._count_sessions_this_week()
        target = profile.trainings_per_week

        progress_row = Adw.ActionRow(
            title=f"{sessions_this_week}/{target} Trainings geschafft"
        )
        week_group.add(progress_row)

        if profile.total_sessions > 0:
            clean_pct = (profile.successful_sessions / profile.total_sessions) * 100
            clean_row = Adw.ActionRow(
                title=f"{clean_pct:.0f}% erfolgreich"
            )
            week_group.add(clean_row)

        total_min = int(profile.total_training_time / 60)
        time_row = Adw.ActionRow(title=f"{total_min} Minuten trainiert (gesamt)")
        week_group.add(time_row)

        # Streak
        if profile.weekly_streak > 0:
            streak_group = Adw.PreferencesGroup(title="Wochen-Streak")
            self._content.append(streak_group)
            streak_row = Adw.ActionRow(
                title=f"{profile.weekly_streak} Wochen in Folge",
                subtitle=f"Bester: {profile.best_weekly_streak} Wochen",
            )
            streak_group.add(streak_row)

        # Meilensteine
        if profile.milestones:
            ms_group = Adw.PreferencesGroup(title="Meilensteine")
            self._content.append(ms_group)
            for ms in profile.milestones:
                row = Adw.ActionRow(title=ms.name)
                row.set_subtitle(ms.reached_date[:10] if ms.reached_date else "")
                row.add_prefix(
                    Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                )
                ms_group.add(row)

    def _count_sessions_this_week(self) -> int:
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        count = 0
        for s in self._window.profile.sessions:
            try:
                ts = datetime.fromisoformat(s.timestamp)
                if ts >= week_start:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count
