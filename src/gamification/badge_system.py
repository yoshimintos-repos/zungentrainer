"""Abzeichen-System mit Freischalt-Bedingungen."""

from datetime import datetime
from models.user_data import Badge


# Abzeichen-Definitionen: (id, name, beschreibung, bedingung_fn)
BADGE_DEFS = [
    (
        "first_session",
        "Erste Schritte",
        "Erste Trainings-Sitzung abgeschlossen",
        lambda p: p.total_sessions >= 1,
    ),
    (
        "five_sessions",
        "Fleißig",
        "5 Sitzungen abgeschlossen",
        lambda p: p.total_sessions >= 5,
    ),
    (
        "ten_sessions",
        "Ausdauernd",
        "10 Sitzungen abgeschlossen",
        lambda p: p.total_sessions >= 10,
    ),
    (
        "twentyfive_sessions",
        "Trainingsprofi",
        "25 Sitzungen abgeschlossen",
        lambda p: p.total_sessions >= 25,
    ),
    (
        "first_success",
        "Geschafft!",
        "Erste erfolgreiche Sitzung",
        lambda p: p.successful_sessions >= 1,
    ),
    (
        "five_successes",
        "Zuverlässig",
        "5 erfolgreiche Sitzungen",
        lambda p: p.successful_sessions >= 5,
    ),
    (
        "perfect_session",
        "Perfekt!",
        "Sitzung ohne einen einzigen Vorfall",
        lambda p: any(s.success and s.incidents == 0 for s in p.sessions),
    ),
    (
        "streak_3",
        "Dranbleiber",
        "3 Tage in Folge trainiert",
        lambda p: p.best_streak >= 3,
    ),
    (
        "streak_7",
        "Wochenkrieger",
        "7 Tage in Folge trainiert",
        lambda p: p.best_streak >= 7,
    ),
    (
        "streak_14",
        "Zweiwochenmeister",
        "14 Tage in Folge trainiert",
        lambda p: p.best_streak >= 14,
    ),
    (
        "streak_30",
        "Monatslegende",
        "30 Tage in Folge trainiert",
        lambda p: p.best_streak >= 30,
    ),
    (
        "level_5",
        "Halbzeit",
        "Level 5 erreicht",
        lambda p: p.level >= 5,
    ),
    (
        "level_10",
        "Meister der Zunge",
        "Level 10 erreicht!",
        lambda p: p.level >= 10,
    ),
    (
        "hour_trained",
        "Eine Stunde",
        "Insgesamt 1 Stunde trainiert",
        lambda p: p.total_training_time >= 3600,
    ),
    (
        "five_hours",
        "Zeitinvestor",
        "Insgesamt 5 Stunden trainiert",
        lambda p: p.total_training_time >= 18000,
    ),
]


class BadgeSystem:
    """Prüft und vergibt Abzeichen basierend auf dem Spielerprofil."""

    def check_badges(self, profile) -> list[Badge]:
        """Prüft alle Abzeichen und schaltet neue frei.

        Returns:
            Liste der neu freigeschalteten Abzeichen.
        """
        unlocked_ids = {b.badge_id for b in profile.badges if b.unlocked}
        newly_unlocked = []

        for badge_id, name, description, condition_fn in BADGE_DEFS:
            if badge_id in unlocked_ids:
                continue

            if condition_fn(profile):
                badge = Badge(
                    badge_id=badge_id,
                    name=name,
                    description=description,
                    unlocked=True,
                    unlocked_date=datetime.now().isoformat(),
                )
                profile.badges.append(badge)
                newly_unlocked.append(badge)

        return newly_unlocked

    @staticmethod
    def all_badges() -> list[tuple[str, str, str]]:
        """Gibt alle möglichen Abzeichen zurück (id, name, beschreibung)."""
        return [(bid, name, desc) for bid, name, desc, _ in BADGE_DEFS]
