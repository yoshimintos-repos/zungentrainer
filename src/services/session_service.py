"""Sitzungs-Zustandsmaschine fuer das Training.

Vereinfachtes Alarm-System (kein WARNING-Zwischenschritt):
  RUNNING -> tongue_out fuer CONFIRM_FRAMES -> DETECTED (Piep + Medienpause)
  DETECTED -> Zunge zurueck + resume_delay -> COOLDOWN
  COOLDOWN -> cooldown_time -> RUNNING
"""
import time
from enum import Enum, auto

CONFIRM_FRAMES = 3

class SessionState(Enum):
    IDLE = auto()
    RUNNING = auto()
    DETECTED = auto()
    COOLDOWN = auto()

class SessionService:
    def __init__(self):
        self.state = SessionState.IDLE
        self.reaction_time = 0.0
        self.resume_delay = 0.0
        self.cooldown_time = 5.0
        self.max_incidents = 0
        self.required_session_time = 600.0
        self._detected_time = None
        self._cooldown_start = None
        self._session_start = None
        self._tongue_start = None
        self._incident_count = 0
        self._confirm_count = 0
        self.on_alarm = None
        self.on_alarm_end = None
        self.on_state_change = None

    @property
    def session_duration(self) -> float:
        if self._session_start is None:
            return 0.0
        return time.monotonic() - self._session_start

    @property
    def incident_count(self) -> int:
        return self._incident_count

    @property
    def session_successful(self) -> bool:
        return self.session_duration >= self.required_session_time

    @property
    def remaining_cooldown(self) -> float:
        if self.state != SessionState.COOLDOWN or self._cooldown_start is None:
            return 0.0
        return max(0.0, self.cooldown_time - (time.monotonic() - self._cooldown_start))

    @property
    def remaining_resume(self) -> float:
        if self.state != SessionState.DETECTED or self._detected_time is None:
            return 0.0
        return max(0.0, self.resume_delay - (time.monotonic() - self._detected_time))

    @property
    def session_failed(self) -> bool:
        if self.max_incidents <= 0:
            return False
        return self._incident_count >= self.max_incidents

    def start(self):
        self.state = SessionState.RUNNING
        self._session_start = time.monotonic()
        self._detected_time = None
        self._cooldown_start = None
        self._tongue_start = None
        self._incident_count = 0
        self._confirm_count = 0
        self._notify_state_change()

    def stop(self) -> dict:
        duration = self.session_duration
        incidents = self._incident_count
        success = self.session_successful and not self.session_failed
        self.state = SessionState.IDLE
        self._session_start = None
        self._detected_time = None
        self._cooldown_start = None
        self._tongue_start = None
        self._confirm_count = 0
        self._notify_state_change()
        return {"duration": duration, "incidents": incidents, "success": success}

    def update(self, tongue_out: bool):
        now = time.monotonic()
        if tongue_out:
            if self._tongue_start is None:
                self._tongue_start = now
            self._confirm_count += 1
        else:
            self._tongue_start = None
            self._confirm_count = 0
        confirmed = self._confirm_count >= CONFIRM_FRAMES
        reaction_elapsed = (
            self._tongue_start is not None
            and (now - self._tongue_start) >= self.reaction_time
        )

        if self.state == SessionState.RUNNING:
            if confirmed and reaction_elapsed:
                self._incident_count += 1
                self.state = SessionState.DETECTED
                self._detected_time = now
                self._tongue_start = None
                self._confirm_count = 0
                self._notify_state_change()
                if self.on_alarm:
                    self.on_alarm()
        elif self.state == SessionState.DETECTED:
            time_elapsed = (now - self._detected_time) >= self.resume_delay
            if time_elapsed and not tongue_out:
                self.state = SessionState.COOLDOWN
                self._cooldown_start = now
                self._notify_state_change()
                if self.on_alarm_end:
                    self.on_alarm_end()
        elif self.state == SessionState.COOLDOWN:
            if (now - self._cooldown_start) >= self.cooldown_time:
                self.state = SessionState.RUNNING
                self._notify_state_change()

    def _notify_state_change(self):
        if self.on_state_change:
            self.on_state_change(self.state)
