"""Tests fuer die vereinfachte Session-Zustandsmaschine."""
import time
import pytest
from unittest.mock import MagicMock
from services.session_service import SessionService, SessionState, CONFIRM_FRAMES

def test_initial_state_is_idle():
    s = SessionService()
    assert s.state == SessionState.IDLE

def test_start_transitions_to_running():
    s = SessionService()
    s.start()
    assert s.state == SessionState.RUNNING

def test_tongue_needs_confirm_frames():
    s = SessionService()
    s.start()
    s.update(True)
    assert s.state == SessionState.RUNNING

def test_confirmed_tongue_triggers_detected():
    s = SessionService()
    s.on_alarm = MagicMock()
    s.start()
    for _ in range(CONFIRM_FRAMES):
        s.update(True)
    assert s.state == SessionState.DETECTED
    assert s.incident_count == 1
    s.on_alarm.assert_called_once()

def test_tongue_back_during_confirmation_resets():
    s = SessionService()
    s.start()
    s.update(True)
    s.update(True)
    s.update(False)
    assert s.state == SessionState.RUNNING
    s.update(True)
    s.update(True)
    assert s.state == SessionState.RUNNING

def test_detected_to_cooldown_on_tongue_back():
    s = SessionService()
    s.resume_delay = 0.0
    s.on_alarm_end = MagicMock()
    s.start()
    for _ in range(CONFIRM_FRAMES):
        s.update(True)
    assert s.state == SessionState.DETECTED
    s.update(False)
    assert s.state == SessionState.COOLDOWN
    s.on_alarm_end.assert_called_once()

def test_stop_returns_result():
    s = SessionService()
    s.start()
    result = s.stop()
    assert "duration" in result
    assert "incidents" in result
    assert "success" in result
    assert s.state == SessionState.IDLE
