"""Tests fuer das Meilenstein-System."""
from systems.milestone_system import MilestoneSystem
from models.user_data import UserProfile, SessionRecord

def test_first_training_milestone():
    ms = MilestoneSystem()
    profile = UserProfile(total_sessions=1)
    new = ms.check_milestones(profile)
    assert any(m.milestone_id == "first_training" for m in new)

def test_no_duplicate_milestones():
    ms = MilestoneSystem()
    profile = UserProfile(total_sessions=1)
    new1 = ms.check_milestones(profile)
    profile.milestones.extend(new1)
    new2 = ms.check_milestones(profile)
    assert not any(m.milestone_id == "first_training" for m in new2)

def test_ten_trainings_milestone():
    ms = MilestoneSystem()
    profile = UserProfile(total_sessions=10)
    new = ms.check_milestones(profile)
    assert any(m.milestone_id == "ten_trainings" for m in new)

def test_perfect_session_milestone():
    ms = MilestoneSystem()
    profile = UserProfile(total_sessions=1)
    profile.sessions = [SessionRecord(incidents=0, success=True, duration=600)]
    new = ms.check_milestones(profile)
    assert any(m.milestone_id == "perfect_session" for m in new)
