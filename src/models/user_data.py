"""Datenklassen fuer Benutzerprofil und Trainingshistorie."""
import dataclasses
from dataclasses import dataclass, field

def _filter_fields(cls, data: dict) -> dict:
    known = {f.name for f in dataclasses.fields(cls)}
    return {k: v for k, v in data.items() if k in known}

@dataclass
class SessionRecord:
    timestamp: str = ""
    duration: float = 0.0
    incidents: int = 0
    success: bool = False

@dataclass
class Milestone:
    milestone_id: str = ""
    name: str = ""
    reached_date: str = ""

@dataclass
class UserProfile:
    name: str = "Anouk"
    total_sessions: int = 0
    successful_sessions: int = 0
    total_training_time: float = 0.0
    total_incidents: int = 0
    weekly_streak: int = 0
    best_weekly_streak: int = 0
    last_session_date: str = ""
    sessions: list = field(default_factory=list)
    milestones: list = field(default_factory=list)
    settings: dict = field(default_factory=lambda: {
        "camera_index": 0, "volume": 0.5, "beep_frequency": 800,
        "pause_media": True,
    })
    difficulty_params: dict = field(default_factory=lambda: {
        "reaction_time": 3.0, "resume_delay": 0.0, "sensitivity": 1.0, "cooldown": 5.0,
    })
    calibration: dict = field(default_factory=dict)
    trainings_per_week: int = 2
    min_session_duration: int = 10
    onboarding_done: bool = False
    reminders_enabled: bool = True
    last_week_checked: str = ""

    def to_dict(self) -> dict:
        from models.persistence import CURRENT_SCHEMA
        return {
            "schema_version": CURRENT_SCHEMA,
            "name": self.name,
            "total_sessions": self.total_sessions,
            "successful_sessions": self.successful_sessions,
            "total_training_time": self.total_training_time,
            "total_incidents": self.total_incidents,
            "weekly_streak": self.weekly_streak,
            "best_weekly_streak": self.best_weekly_streak,
            "last_session_date": self.last_session_date,
            "sessions": [
                {f.name: getattr(s, f.name) for f in dataclasses.fields(s)}
                for s in self.sessions
            ],
            "milestones": [
                {f.name: getattr(m, f.name) for f in dataclasses.fields(m)}
                for m in self.milestones
            ],
            "settings": self.settings,
            "difficulty_params": self.difficulty_params,
            "calibration": self.calibration,
            "trainings_per_week": self.trainings_per_week,
            "min_session_duration": self.min_session_duration,
            "onboarding_done": self.onboarding_done,
            "reminders_enabled": self.reminders_enabled,
            "last_week_checked": self.last_week_checked,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        profile = cls()
        simple_fields = (
            "name", "total_sessions", "successful_sessions",
            "total_training_time", "total_incidents", "weekly_streak",
            "best_weekly_streak", "last_session_date",
            "trainings_per_week", "min_session_duration",
            "onboarding_done", "reminders_enabled", "last_week_checked",
        )
        for key in simple_fields:
            if key in data:
                setattr(profile, key, data[key])
        profile.sessions = [
            SessionRecord(**_filter_fields(SessionRecord, s))
            for s in data.get("sessions", [])
        ]
        profile.milestones = [
            Milestone(**_filter_fields(Milestone, m))
            for m in data.get("milestones", [])
        ]
        if "settings" in data:
            profile.settings.update(data["settings"])
        if "difficulty_params" in data:
            profile.difficulty_params.update(data["difficulty_params"])
        if "calibration" in data:
            profile.calibration = data["calibration"]
        return profile
