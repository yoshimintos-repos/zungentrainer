"""Datenklassen für Benutzerprofil, Level, Abzeichen und Kreaturen."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionRecord:
    """Aufzeichnung einer Trainingssitzung."""
    timestamp: str = ""
    duration: float = 0.0        # Sekunden
    incidents: int = 0
    success: bool = False
    xp_earned: int = 0
    level_at_time: int = 1


@dataclass
class Badge:
    """Ein freigeschaltetes Abzeichen."""
    badge_id: str = ""
    name: str = ""
    description: str = ""
    unlocked: bool = False
    unlocked_date: str = ""


@dataclass
class Creature:
    """Eine sammelbare Kreatur (Zungenfreund)."""
    creature_id: str = ""
    name: str = ""
    description: str = ""
    unlocked: bool = False
    unlocked_date: str = ""
    golden: bool = False


@dataclass
class UserProfile:
    """Hauptprofil mit allen Spieldaten."""
    name: str = "Anouk"
    level: int = 1
    xp: int = 0
    total_xp: int = 0
    total_sessions: int = 0
    successful_sessions: int = 0
    total_training_time: float = 0.0   # Sekunden
    total_incidents: int = 0
    current_streak: int = 0            # Tage in Folge
    best_streak: int = 0
    last_session_date: str = ""
    badges: list = field(default_factory=list)
    creatures: list = field(default_factory=list)
    sessions: list = field(default_factory=list)
    settings: dict = field(default_factory=lambda: {
        "camera_index": 0,
        "volume": 0.5,
        "beep_frequency": 800,
    })

    def to_dict(self) -> dict:
        from models.persistence import CURRENT_SCHEMA
        return {
            "schema_version": CURRENT_SCHEMA,
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "total_xp": self.total_xp,
            "total_sessions": self.total_sessions,
            "successful_sessions": self.successful_sessions,
            "total_training_time": self.total_training_time,
            "total_incidents": self.total_incidents,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "last_session_date": self.last_session_date,
            "badges": [
                {
                    "badge_id": b.badge_id,
                    "name": b.name,
                    "description": b.description,
                    "unlocked": b.unlocked,
                    "unlocked_date": b.unlocked_date,
                }
                for b in self.badges
            ],
            "creatures": [
                {
                    "creature_id": c.creature_id,
                    "name": c.name,
                    "description": c.description,
                    "unlocked": c.unlocked,
                    "unlocked_date": c.unlocked_date,
                    "golden": c.golden,
                }
                for c in self.creatures
            ],
            "sessions": [
                {
                    "timestamp": s.timestamp,
                    "duration": s.duration,
                    "incidents": s.incidents,
                    "success": s.success,
                    "xp_earned": s.xp_earned,
                    "level_at_time": s.level_at_time,
                }
                for s in self.sessions
            ],
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        profile = cls()
        for key in ("name", "level", "xp", "total_xp", "total_sessions",
                     "successful_sessions", "total_training_time",
                     "total_incidents", "current_streak", "best_streak",
                     "last_session_date"):
            if key in data:
                setattr(profile, key, data[key])

        profile.badges = [
            Badge(**b) for b in data.get("badges", [])
        ]
        profile.creatures = [
            Creature(**c) for c in data.get("creatures", [])
        ]
        profile.sessions = [
            SessionRecord(**s) for s in data.get("sessions", [])
        ]
        if "settings" in data:
            profile.settings.update(data["settings"])
        return profile
