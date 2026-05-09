"""Tests fuer UserProfile Serialisierung."""
from models.user_data import UserProfile, SessionRecord

def test_roundtrip_empty_profile():
    p = UserProfile()
    d = p.to_dict()
    p2 = UserProfile.from_dict(d)
    assert p2.name == p.name
    assert p2.total_sessions == 0
    assert p2.sessions == []

def test_roundtrip_with_sessions():
    p = UserProfile(name="Anouk")
    p.sessions.append(SessionRecord(
        timestamp="2026-05-09T10:00:00", duration=600.0, incidents=2, success=True,
    ))
    d = p.to_dict()
    p2 = UserProfile.from_dict(d)
    assert len(p2.sessions) == 1
    assert p2.sessions[0].duration == 600.0

def test_unknown_fields_ignored():
    d = {"name": "Test", "unknown_future_field": 42, "schema_version": 1}
    p = UserProfile.from_dict(d)
    assert p.name == "Test"

def test_settings_defaults():
    p = UserProfile()
    assert p.settings["camera_index"] == 0
    assert p.settings["volume"] == 0.5

def test_difficulty_params_roundtrip():
    p = UserProfile()
    p.difficulty_params["reaction_time"] = 1.5
    d = p.to_dict()
    p2 = UserProfile.from_dict(d)
    assert p2.difficulty_params["reaction_time"] == 1.5
