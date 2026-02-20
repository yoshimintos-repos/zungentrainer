"""Sitzungs-Zustandsmaschine für das Training.

Zwei-Stufen-Alarm-System:
1. WARNING: Piep-Warnung nach beep_delay (Zunge zurück → kein Vorfall)
2. DETECTED: Medienpause nach pause_delay (Vorfall gezählt)
3. COOLDOWN: Medien bleiben pausiert für resume_delay, dann Abklingzeit
"""

import time
from enum import Enum, auto


class SessionState(Enum):
    IDLE = auto()
    RUNNING = auto()
    WARNING = auto()
    DETECTED = auto()
    COOLDOWN = auto()


class SessionService:
    """Verwaltet den Trainings-Sitzungszustand.

    Zustandsübergänge:
        IDLE → RUNNING (start)
        RUNNING → WARNING (Zunge erkannt für beep_delay → Piep)
        WARNING → RUNNING (Zunge zurück → kein Vorfall, Timer zurückgesetzt)
        WARNING → DETECTED (Zunge weiterhin draußen, pause_delay total erreicht → Medienpause)
        DETECTED → COOLDOWN (nach resume_delay → Medien wieder abspielen)
        COOLDOWN → RUNNING (nach cooldown_time)
        alle → IDLE (stop)
    """

    def __init__(self):
        self.state = SessionState.IDLE

        # Schwierigkeitsparameter (werden vom LevelSystem gesetzt)
        self.beep_delay = 1.0          # Sekunden bis Piep-Warnung
        self.pause_delay = 3.0         # Sekunden bis Medienpause (ab Zungenstart)
        self.resume_delay = 0.0        # Sekunden wie lange Medien pausiert bleiben
        self.cooldown_time = 5.0       # Sekunden Abklingzeit nach Mediaresume
        self.max_incidents = 0         # 0 = unbegrenzt
        self.required_session_time = 600.0  # Sekunden Mindest-Trainingszeit

        # Interner Zustand
        self._tongue_start = None      # Zeitpunkt ab dem Zunge erkannt
        self._detected_time = None     # Zeitpunkt des DETECTED-Übergangs
        self._cooldown_start = None
        self._session_start = None
        self._incident_count = 0

        # Callbacks
        self.on_warning = None         # Wird bei Piep-Warnung aufgerufen
        self.on_alarm = None           # Wird bei Medienpause aufgerufen
        self.on_alarm_end = None       # Wird bei Mediaresume aufgerufen
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
    def remaining_resume(self) -> float:
        """Verbleibende Medienpausen-Dauer in Sekunden."""
        if self.state != SessionState.DETECTED or self._detected_time is None:
            return 0.0
        elapsed = time.monotonic() - self._detected_time
        return max(0.0, self.resume_delay - elapsed)

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
        self._detected_time = None
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
        self._detected_time = None
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
                elif (now - self._tongue_start) >= self.beep_delay:
                    # Piep-Warnung auslösen
                    self.state = SessionState.WARNING
                    self._notify_state_change()
                    if self.on_warning:
                        self.on_warning()
            else:
                self._tongue_start = None

        elif self.state == SessionState.WARNING:
            if tongue_out:
                # Prüfen ob pause_delay erreicht (ab Zungenstart gemessen)
                if self._tongue_start and (now - self._tongue_start) >= self.pause_delay:
                    # Vorfall! Medienpause auslösen
                    self._incident_count += 1
                    self.state = SessionState.DETECTED
                    self._detected_time = now
                    self._notify_state_change()
                    # Nur Medien pausieren wenn resume_delay > 0
                    if self.resume_delay > 0 and self.on_alarm:
                        self.on_alarm()
            else:
                # Zunge zurück → kein Vorfall, zurück zu RUNNING
                self._tongue_start = None
                self.state = SessionState.RUNNING
                self._notify_state_change()

        elif self.state == SessionState.DETECTED:
            if (now - self._detected_time) >= self.resume_delay:
                # Medien wieder abspielen, Cooldown starten
                self.state = SessionState.COOLDOWN
                self._cooldown_start = now
                self._tongue_start = None
                self._notify_state_change()
                if self.resume_delay > 0 and self.on_alarm_end:
                    self.on_alarm_end()

        elif self.state == SessionState.COOLDOWN:
            if (now - self._cooldown_start) >= self.cooldown_time:
                self.state = SessionState.RUNNING
                self._tongue_start = None
                self._notify_state_change()

    def _notify_state_change(self):
        if self.on_state_change:
            self.on_state_change(self.state)
