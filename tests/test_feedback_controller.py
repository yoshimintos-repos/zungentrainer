"""Tests fuer die zentrale Feedback-Logik."""

from services.feedback_controller import FeedbackController, FeedbackMode


class FakeSound:
    def __init__(self):
        self.beeps = 0
        self.loop_started = 0
        self.loop_stopped = 0

    def beep(self):
        self.beeps += 1

    def start_alarm_loop(self):
        self.loop_started += 1

    def stop_alarm_loop(self):
        self.loop_stopped += 1


class FakeMpris:
    def __init__(self, paused_players=None):
        self.paused_players = paused_players or []
        self.pause_calls = 0
        self.resume_calls = 0

    def pause_all(self):
        self.pause_calls += 1
        return self.paused_players

    def resume_paused(self):
        self.resume_calls += 1


def test_alarm_pauses_media_when_player_is_playing():
    sound = FakeSound()
    mpris = FakeMpris(paused_players=["org.mpris.MediaPlayer2.test"])
    feedback = FeedbackController(sound, mpris)

    mode = feedback.start_alarm()

    assert mode == FeedbackMode.MEDIA_PAUSED
    assert sound.beeps == 1
    assert sound.loop_started == 0
    assert mpris.pause_calls == 1

    feedback.end_alarm()
    assert mpris.resume_calls == 1
    assert sound.loop_stopped == 0
    assert feedback.mode == FeedbackMode.IDLE


def test_alarm_starts_loop_when_no_media_is_playing():
    sound = FakeSound()
    mpris = FakeMpris(paused_players=[])
    feedback = FeedbackController(sound, mpris)

    mode = feedback.start_alarm()

    assert mode == FeedbackMode.NO_MEDIA_AUDIO
    assert sound.beeps == 1
    assert sound.loop_started == 1
    assert mpris.pause_calls == 1

    feedback.end_alarm()
    assert sound.loop_stopped == 1
    assert mpris.resume_calls == 0
    assert feedback.mode == FeedbackMode.IDLE


def test_alarm_starts_loop_when_media_pause_is_disabled():
    sound = FakeSound()
    mpris = FakeMpris(paused_players=["org.mpris.MediaPlayer2.test"])
    feedback = FeedbackController(sound, mpris, pause_media=False)

    mode = feedback.start_alarm()

    assert mode == FeedbackMode.NO_MEDIA_AUDIO
    assert sound.beeps == 1
    assert sound.loop_started == 1
    assert mpris.pause_calls == 0


def test_alarm_is_not_restarted_while_active():
    sound = FakeSound()
    mpris = FakeMpris(paused_players=[])
    feedback = FeedbackController(sound, mpris)

    feedback.start_alarm()
    feedback.start_alarm()

    assert sound.beeps == 1
    assert sound.loop_started == 1
    assert mpris.pause_calls == 1


def test_cancel_stops_all_feedback_paths():
    sound = FakeSound()
    mpris = FakeMpris(paused_players=["player"])
    feedback = FeedbackController(sound, mpris)

    feedback.start_alarm()
    feedback.cancel()

    assert sound.loop_stopped == 1
    assert mpris.resume_calls == 1
    assert feedback.mode == FeedbackMode.IDLE
