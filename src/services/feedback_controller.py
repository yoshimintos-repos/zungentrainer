"""Zentrale Feedback-Logik fuer Zungenalarme."""

from enum import Enum, auto


class FeedbackMode(Enum):
    IDLE = auto()
    MEDIA_PAUSED = auto()
    NO_MEDIA_AUDIO = auto()


class FeedbackController:
    """Steuert Piepton, Medienpause und No-Media-Audioschleife.

    Die Produktregel ist: Nur beim Uebergang in den Alarm stoeren. Danach wird
    entweder ein von uns pausierter Medienplayer gehalten oder eine Audioschleife
    abgespielt, bis die Zunge wieder drin ist.
    """

    def __init__(self, sound_service, mpris_service):
        self._sound = sound_service
        self._mpris = mpris_service
        self.mode = FeedbackMode.IDLE

    def start_alarm(self) -> FeedbackMode:
        """Startet Feedback fuer einen neuen Zungenalarm."""
        if self.mode != FeedbackMode.IDLE:
            return self.mode

        self._sound.beep()
        paused_players = self._mpris.pause_all()
        if paused_players:
            self.mode = FeedbackMode.MEDIA_PAUSED
        else:
            self._sound.start_alarm_loop()
            self.mode = FeedbackMode.NO_MEDIA_AUDIO
        return self.mode

    def end_alarm(self):
        """Beendet Feedback, wenn die Zunge wieder stabil drin ist."""
        if self.mode == FeedbackMode.MEDIA_PAUSED:
            self._mpris.resume_paused()
        elif self.mode == FeedbackMode.NO_MEDIA_AUDIO:
            self._sound.stop_alarm_loop()
        self.mode = FeedbackMode.IDLE

    def cancel(self):
        """Bricht jedes aktive Feedback sofort ab."""
        self._sound.stop_alarm_loop()
        self._mpris.resume_paused()
        self.mode = FeedbackMode.IDLE
