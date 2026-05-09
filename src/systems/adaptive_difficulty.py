"""Adaptive Schwierigkeit (Flow-Zone Algorithmus).

Passt nach jeder Session die Schwierigkeitsparameter an:
- rate < 0.2/min: schwieriger (kleine Schritte)
- rate 0.2-1.0/min: Flow-Zone (keine Aenderung)
- rate > 1.0/min: leichter (groessere Schritte)
"""

BOUNDS = {
    "reaction_time": (0.3, 3.0),
    "resume_delay": (0.0, 20.0),
    "sensitivity": (0.5, 2.0),
    "cooldown": (3.0, 5.0),
}
HARDER_STEP = {"reaction_time": -0.1, "resume_delay": 1.0, "sensitivity": 0.05, "cooldown": -0.1}
EASIER_STEP = {"reaction_time": 0.2, "resume_delay": -1.5, "sensitivity": -0.1, "cooldown": 0.2}
FLOW_ZONE_LOW = 0.2
FLOW_ZONE_HIGH = 1.0

class AdaptiveDifficulty:
    def __init__(self):
        self._params = {"reaction_time": 1.5, "resume_delay": 5.0, "sensitivity": 1.0, "cooldown": 4.0}

    def get_params(self) -> dict:
        return self._params.copy()

    def adjust_after_session(self, incidents: int, duration_minutes: float):
        if duration_minutes <= 0:
            return
        rate = incidents / duration_minutes
        if rate < FLOW_ZONE_LOW:
            steps = HARDER_STEP
        elif rate > FLOW_ZONE_HIGH:
            steps = EASIER_STEP
        else:
            return
        for key, step in steps.items():
            low, high = BOUNDS[key]
            self._params[key] = max(low, min(high, self._params[key] + step))

    def to_dict(self) -> dict:
        return self._params.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "AdaptiveDifficulty":
        ad = cls()
        for key in ad._params:
            if key in data:
                ad._params[key] = data[key]
        return ad
