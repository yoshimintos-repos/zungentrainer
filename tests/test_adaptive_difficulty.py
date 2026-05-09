"""Tests fuer den Flow-Zone Algorithmus."""
from systems.adaptive_difficulty import AdaptiveDifficulty

def test_initial_params():
    ad = AdaptiveDifficulty()
    params = ad.get_params()
    assert "reaction_time" in params
    assert "resume_delay" in params
    assert "sensitivity" in params
    assert "cooldown" in params

def test_low_incident_rate_increases_difficulty():
    ad = AdaptiveDifficulty()
    initial = ad.get_params()["reaction_time"]
    ad.adjust_after_session(incidents=1, duration_minutes=10.0)
    assert ad.get_params()["reaction_time"] < initial

def test_high_incident_rate_decreases_difficulty():
    ad = AdaptiveDifficulty()
    initial = ad.get_params()["reaction_time"]
    ad.adjust_after_session(incidents=20, duration_minutes=10.0)
    assert ad.get_params()["reaction_time"] > initial

def test_flow_zone_no_change():
    ad = AdaptiveDifficulty()
    initial = ad.get_params()
    ad.adjust_after_session(incidents=5, duration_minutes=10.0)
    assert ad.get_params()["reaction_time"] == initial["reaction_time"]

def test_params_stay_in_bounds():
    ad = AdaptiveDifficulty()
    for _ in range(50):
        ad.adjust_after_session(incidents=0, duration_minutes=10.0)
    params = ad.get_params()
    assert params["reaction_time"] >= 0.3
    assert params["sensitivity"] <= 2.0

def test_from_dict_roundtrip():
    ad = AdaptiveDifficulty()
    ad.adjust_after_session(incidents=1, duration_minutes=10.0)
    d = ad.to_dict()
    ad2 = AdaptiveDifficulty.from_dict(d)
    assert ad2.get_params() == ad.get_params()
