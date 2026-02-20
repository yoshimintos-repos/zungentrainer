"""Level-System mit XP-Progression und Schwierigkeitsskalierung."""

import math


# XP benötigt pro Level (kumulativ)
# Level 1→2: 100 XP, Level 2→3: 250 XP, etc.
XP_TABLE = [0, 0, 100, 250, 500, 800, 1200, 1700, 2400, 3200, 4200]

# Schwierigkeitsparameter pro Level [Level 1 ... Level 10]
# (detection_pause_s, reaction_delay_s, sensitivity_multiplier, max_incidents, required_session_time_s)
#
# detection_pause_s: Nach einem Vorfall bleibt die Erkennung so lange aus.
# Level 1: 0s (ständige Überwachung), Level 10: 20s (Selbstdisziplin nötig).
#
# sensitivity_multiplier: Wie viel der Score über der Baseline liegen muss.
# Höher = weniger empfindlich = einfacher (Level 1).
# Niedriger = empfindlicher = schwerer (Level 10).
#
# trigger_duration und cooldown_time sind fest auf 5s gesetzt (siehe get_difficulty).
DIFFICULTY = [
    None,  # Index 0 nicht genutzt
    (0.0,  3.0, 3.5, 0,  600.0),   # Level 1: ständige Überwachung
    (2.0,  2.7, 3.2, 0,  660.0),   # Level 2
    (4.0,  2.4, 2.9, 0,  720.0),   # Level 3
    (7.0,  2.0, 2.6, 10, 780.0),   # Level 4
    (9.0,  1.7, 2.3, 8,  900.0),   # Level 5
    (11.0, 1.3, 2.0, 7,  1020.0),  # Level 6
    (13.0, 1.0, 1.8, 6,  1140.0),  # Level 7
    (16.0, 0.7, 1.6, 5,  1320.0),  # Level 8
    (18.0, 0.3, 1.4, 4,  1500.0),  # Level 9
    (20.0, 0.0, 1.2, 3,  1800.0),  # Level 10: Selbstdisziplin nötig
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
        return total_xp - XP_TABLE[current_level]

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
            "trigger_duration": 5.0,
            "cooldown_time": 5.0,
            "detection_pause": t[0],
            "reaction_delay": t[1],
            "sensitivity": t[2],
            "max_incidents": t[3],
            "required_session_time": t[4],
        }

    def check_level_up(self, profile) -> list[int]:
        """Prüft und führt Level-Aufstiege durch. Gibt Liste neuer Level zurück."""
        new_levels = []
        new_level = self.calculate_level(profile.total_xp)
        while new_level > profile.level and profile.level < MAX_LEVEL:
            profile.level += 1
            new_levels.append(profile.level)
        return new_levels
