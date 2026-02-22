"""Level-System mit XP-Progression und Schwierigkeitsskalierung."""

import math


# XP benötigt pro Level (kumulativ)
# Level 1→2: 100 XP, Level 2→3: 250 XP, etc.
XP_TABLE = [0, 0, 100, 250, 500, 800, 1200, 1700, 2400, 3200, 4200]

# Schwierigkeitsparameter pro Level [Level 1 ... Level 10]
# (beep_delay_s, pause_delay_s, resume_delay_s, cooldown_s,
#  sensitivity_multiplier, max_incidents, required_session_time_s)
#
# beep_delay: Sekunden bis Piep-Warnung (schneller = schwerer)
# pause_delay: Sekunden bis Medienpause ab Zungenstart (schneller = schwerer)
# resume_delay: Wie lange Medien pausiert bleiben = "Erkennungspause" (länger = schwerer)
# sensitivity_multiplier: Wie viel der Score über der Baseline liegen muss.
#   Höher = weniger empfindlich = einfacher (Level 1).
#   Niedriger = empfindlicher = schwerer (Level 10).
DIFFICULTY = [
    None,  # Index 0 nicht genutzt
    # beep  pause  resume  cool   sens   max_inc  session_time
    (1.0,   3.0,    0.0,   5.0,   2.5,   0,       600.0),   # Level 1
    (0.9,   2.7,    2.0,   5.0,   2.3,   0,       660.0),   # Level 2
    (0.8,   2.4,    4.0,   4.5,   2.1,   0,       720.0),   # Level 3
    (0.7,   2.0,    7.0,   4.5,   1.9,   10,      780.0),   # Level 4
    (0.5,   1.7,    9.0,   4.0,   1.7,   8,       900.0),   # Level 5
    (0.4,   1.4,   11.0,   4.0,   1.5,   7,      1020.0),   # Level 6
    (0.3,   1.1,   13.0,   3.5,   1.3,   6,      1140.0),   # Level 7
    (0.2,   0.8,   16.0,   3.5,   1.1,   5,      1320.0),   # Level 8
    (0.1,   0.5,   18.0,   3.0,   0.9,   4,      1500.0),   # Level 9
    (0.0,   0.3,   20.0,   3.0,   0.8,   3,      1800.0),   # Level 10
]

MAX_LEVEL = 10


class LevelSystem:
    """Verwaltet XP-Vergabe, Level-Aufstiege und Schwierigkeitsstufen."""

    def xp_for_next_level(self, current_level: int) -> int:
        """XP die für den nächsten Level-Aufstieg benötigt werden."""
        if current_level >= MAX_LEVEL:
            return 0
        return XP_TABLE[current_level + 1] - XP_TABLE[current_level]

    def xp_in_current_level(self, current_level: int, total_xp: int) -> int:
        """XP-Fortschritt innerhalb des aktuellen Levels."""
        if current_level >= MAX_LEVEL:
            return 0
        return max(0, total_xp - XP_TABLE[current_level])

    def calculate_level(self, total_xp: int) -> int:
        """Berechnet das Level basierend auf Gesamt-XP."""
        for lvl in range(MAX_LEVEL, 0, -1):
            if total_xp >= XP_TABLE[lvl]:
                return lvl
        return 1

    def award_session_xp(self, level: int, duration: float, incidents: int,
                          success: bool) -> int:
        """Berechnet XP für eine abgeschlossene Sitzung.

        Args:
            level: Aktuelles Level
            duration: Sitzungsdauer in Sekunden
            incidents: Anzahl Vorfälle
            success: Ob die Sitzung erfolgreich war

        Returns:
            Verdiente XP
        """
        # Basis-XP: 1 XP pro Minute Training
        base_xp = int(duration / 60)

        # Bonus für wenige Vorfälle
        if incidents == 0:
            base_xp = int(base_xp * 2.0)
        elif incidents <= 2:
            base_xp = int(base_xp * 1.5)

        # Erfolgsbonus
        if success:
            base_xp += 10 + level * 2

        # Level-Multiplikator (höhere Level geben mehr XP)
        multiplier = 1.0 + (level - 1) * 0.1
        return max(1, int(base_xp * multiplier))

    def get_difficulty(self, level: int) -> dict:
        """Gibt die Schwierigkeitsparameter für ein Level zurück."""
        level = max(1, min(MAX_LEVEL, level))
        t = DIFFICULTY[level]
        return {
            "beep_delay": t[0],
            "pause_delay": t[1],
            "resume_delay": t[2],
            "cooldown_time": t[3],
            "sensitivity": t[4],
            "max_incidents": t[5],
            "required_session_time": t[6],
        }

    def check_level_up(self, profile) -> list[int]:
        """Prüft und führt Level-Aufstiege durch. Gibt Liste neuer Level zurück."""
        new_levels = []
        new_level = self.calculate_level(profile.total_xp)
        while new_level > profile.level and profile.level < MAX_LEVEL:
            profile.level += 1
            new_levels.append(profile.level)
        return new_levels
