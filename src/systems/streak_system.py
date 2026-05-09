"""Wochen-Streak: Zaehlt Wochen mit erfuelltem Trainingsplan.

- Woche mit x/x Trainings = Streak +1
- Woche mit mind. 1 Training = Streak bleibt
- Woche mit 0 Trainings = Streak reset
"""

from datetime import datetime, timedelta
from models.user_data import UserProfile


class StreakSystem:
    """Verwaltet den Wochen-Streak und Erinnerungen."""

    def update_streak(self, profile: UserProfile):
        """Aktualisiert den Streak basierend auf der aktuellen Woche."""
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        week_key = week_start.strftime("%Y-%m-%d")

        if profile.last_week_checked == week_key:
            return  # Diese Woche bereits geprueft

        # Letzte Woche pruefen (nur wenn es eine vorherige Woche gab)
        if profile.last_week_checked:
            last_checked = datetime.strptime(profile.last_week_checked, "%Y-%m-%d")
            prev_week_start = week_start - timedelta(weeks=1)

            if last_checked < prev_week_start:
                # Mehr als eine Woche ohne Check — Wochen dazwischen pruefen
                sessions_prev = self._count_sessions_in_week(profile, prev_week_start)
                if sessions_prev == 0:
                    profile.weekly_streak = 0
                elif sessions_prev >= profile.trainings_per_week:
                    profile.weekly_streak += 1

        # Aktuelle Woche
        sessions_now = self._count_sessions_in_week(profile, week_start)
        if sessions_now >= profile.trainings_per_week:
            # Nur inkrementieren wenn noch nicht fuer diese Woche gezaehlt
            if profile.last_week_checked != week_key:
                profile.weekly_streak += 1

        profile.last_week_checked = week_key
        profile.best_weekly_streak = max(
            profile.best_weekly_streak, profile.weekly_streak
        )

    def remaining_this_week(self, profile: UserProfile) -> int:
        """Wie viele Trainings fehlen noch diese Woche."""
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        done = self._count_sessions_in_week(profile, week_start)
        return max(0, profile.trainings_per_week - done)

    def get_reminder_text(self, profile: UserProfile) -> str | None:
        """Gibt Erinnerungstext zurueck, oder None wenn keine noetig."""
        if not profile.reminders_enabled:
            return None
        remaining = self.remaining_this_week(profile)
        if remaining <= 0:
            return None
        now = datetime.now()
        weekday = now.weekday()
        if weekday >= 4 and remaining == profile.trainings_per_week:
            # Freitag+ und noch kein Training → dringend
            return "Letzte Chance diese Woche!"
        if weekday >= 2 and remaining > 0:
            # Mittwoch+ → Erinnerung
            return f"Noch {remaining} Training{'s' if remaining > 1 else ''} diese Woche"
        return None

    def _count_sessions_in_week(self, profile: UserProfile,
                                 week_start: datetime) -> int:
        """Zaehlt Sessions innerhalb einer Kalenderwoche."""
        week_end = week_start + timedelta(weeks=1)
        count = 0
        for s in profile.sessions:
            try:
                ts = datetime.fromisoformat(s.timestamp)
                if week_start <= ts < week_end:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count
