"""Meilenstein-System: Einfache Achievements basierend auf echtem Fortschritt."""
from datetime import datetime
from models.user_data import UserProfile, Milestone

_MILESTONE_DEFS = [
    ("first_training", "Erstes Training",
     lambda p: p.total_sessions >= 1),
    ("ten_trainings", "10 Trainings",
     lambda p: p.total_sessions >= 10),
    ("fifty_trainings", "50 Trainings",
     lambda p: p.total_sessions >= 50),
    ("first_week", "Erste Woche geschafft",
     lambda p: p.weekly_streak >= 1),
    ("four_weeks", "4 Wochen in Folge",
     lambda p: p.weekly_streak >= 4),
    ("perfect_session", "Ganze Session ohne Vorfall",
     lambda p: any(s.incidents == 0 and s.success for s in p.sessions)),
    ("five_min_clean", "5 Minuten ohne Vorfall",
     lambda p: _longest_clean_stretch(p) >= 300),
    ("fifteen_min_clean", "15 Minuten ohne Vorfall",
     lambda p: _longest_clean_stretch(p) >= 900),
]

def _longest_clean_stretch(profile: UserProfile) -> float:
    clean = [s.duration for s in profile.sessions if s.incidents == 0 and s.success]
    return max(clean) if clean else 0.0

class MilestoneSystem:
    def check_milestones(self, profile: UserProfile) -> list[Milestone]:
        existing_ids = {m.milestone_id for m in profile.milestones}
        new_milestones = []
        for mid, name, check_fn in _MILESTONE_DEFS:
            if mid not in existing_ids and check_fn(profile):
                new_milestones.append(Milestone(
                    milestone_id=mid, name=name,
                    reached_date=datetime.now().isoformat(),
                ))
        return new_milestones
