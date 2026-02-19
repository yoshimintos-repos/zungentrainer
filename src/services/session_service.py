"""Sitzungs-Zustandsmaschine für das Training."""

import time
from enum import Enum, auto


class SessionState(Enum):
    IDLE = auto()
    RUNNING = auto()
    DETECTED = auto()
    COOLDOWN = auto()


class SessionService:
    """Verwaltet den Trainings-Sitzungszustand.

    Zustandsübergänge:
        IDLE → RUNNING (start)
        RUNNING → DETECTED (Zunge erkannt für trigger_duration)
        DETECTED → COOLDOWN (nach reaction_delay)
        COOLDOWN → RUNNING (nach cooldown)
        RUNNING/DETECTED/COOLDOWN → IDLE (stop)
    """

    def __init__(self):
        self.state = SessionState.IDLE

        # Schwierigkeitsparameter (werden vom LevelSystem gesetzt)
        self.trigger_duration = 45.0   # Sekunden Zunge draußen bis Alarm
        self.cooldown_time = 300.0     # Sekunden Pause zwischen Erkennungen
        self.reaction_delay = 3.0      # Sekunden Verzögerung nach Erkennung
        self.max_incidents = 0         # 0 = unbegrenzt
        self.required_session_time = 600.0  # Sekunden Mindest-Trainingszeit

        # Interner Zustand
        self._tongue_start = None      # Zeitpunkt ab dem Zunge erkannt
        self._detection_time = None    # Zeitpunkt der Auslösung
        self._cooldown_start = None
        self._session_start = None
        self._incident_count = 0

        # Callbacks
        self.on_alarm = None           # Wird bei Erkennung aufgerufen
        self.on_alarm_end = None       # Wird bei Alarm-Ende aufgerufen
        self.on_state_change = None

    @property
    def session_duration(self) -> float:
        """Aktuelle Sitzungsdauer in Sekunden."""
        if self._session_start is None:
            return 0.0
        return time.monotonic() - self._session_start

    @property
    def incident_count(self) -> int:
        return self._incident_count

    @property
    def session_successful(self) -> bool:
        """Ob die Sitzung die Mindestdauer erreicht hat."""
        return self.session_duration >= self.required_session_time

    @property
    def remaining_cooldown(self) -> float:
        """Verbleibende Abklingzeit in Sekunden."""
        if self.state != SessionState.COOLDOWN or self._cooldown_start is None:
            return 0.0
        elapsed = time.monotonic() - self._cooldown_start
        return max(0.0, self.cooldown_time - elapsed)

    @property
    def session_failed(self) -> bool:
        """Ob zu viele Vorfälle aufgetreten sind."""
        if self.max_incidents <= 0:
            return False
        return self._incident_count >= self.max_incidents

    def start(self):
        self.state = SessionState.RUNNING
        self._session_start = time.monotonic()
        self._tongue_start = None
        self._detection_time = None
        self._cooldown_start = None
        self._incident_count = 0
        self._notify_state_change()

    def stop(self):
        """Stoppt die Sitzung und gibt Ergebnis zurück."""
        duration = self.session_duration
        incidents = self._incident_count
        success = self.session_successful and not self.session_failed
        self.state = SessionState.IDLE
        self._session_start = None
        self._tongue_start = None
        self._detection_time = None
        self._cooldown_start = None
        self._notify_state_change()
        return {
            "duration": duration,
            "incidents": incidents,
            "success": success,
        }

    def update(self, tongue_out: bool):
        """Wird jeden Frame aufgerufen mit dem Erkennungsergebnis."""
        now = time.monotonic()

        if self.state == SessionState.RUNNING:
            if tongue_out:
                if self._tongue_start is None:
                    self._tongue_start = now
                elif (now - self._tongue_start) >= self.trigger_duration:
                    # Zunge war lang genug draußen → Erkennung!
                    self.state = SessionState.DETECTED
                    self._detection_time = now
                    self._incident_count += 1
                    self._notify_state_change()
                    if self.on_alarm:
                        self.on_alarm()
            else:
                self._tongue_start = None

        elif self.state == SessionState.DETECTED:
            if (now - self._detection_time) >= self.reaction_delay:
                # Reaktionszeit vorbei → Cooldown
                self.state = SessionState.COOLDOWN
                self._cooldown_start = now
                self._tongue_start = None
                self._notify_state_change()
                if self.on_alarm_end:
                    self.on_alarm_end()

        elif self.state == SessionState.COOLDOWN:
            if (now - self._cooldown_start) >= self.cooldown_time:
                self.state = SessionState.RUNNING
                self._tongue_start = None
                self._notify_state_change()

    def _notify_state_change(self):
        if self.on_state_change:
            self.on_state_change(self.state)
