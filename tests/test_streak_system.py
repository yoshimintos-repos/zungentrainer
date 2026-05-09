"""Tests fuer Wochen-Streak-System."""

from datetime import datetime, timedelta
from systems.streak_system import StreakSystem
from models.user_data import UserProfile, SessionRecord


def _profile_with_sessions(dates: list[str]) -> UserProfile:
    """Erzeugt ein Profil mit Sessions an den gegebenen Daten."""
    p = UserProfile(trainings_per_week=2)
    for d in dates:
        p.sessions.append(SessionRecord(timestamp=d, duration=600, success=True))
    p.total_sessions = len(dates)
    return p


def test_no_sessions_no_streak():
    ss = StreakSystem()
    p = UserProfile(trainings_per_week=2)
    ss.update_streak(p)
    assert p.weekly_streak == 0


def test_fulfilled_week_increments_streak():
    ss = StreakSystem()
    now = datetime.now()
    # 2 Sessions diese Woche (Ziel = 2)
    mon = now - timedelta(days=now.weekday())
    p = _profile_with_sessions([
        mon.isoformat(),
        (mon + timedelta(days=1)).isoformat(),
    ])
    ss.update_streak(p)
    assert p.weekly_streak >= 1


def test_zero_sessions_resets_streak():
    ss = StreakSystem()
    p = UserProfile(trainings_per_week=2, weekly_streak=5)
    # Letzte Session war vor 2 Wochen
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).isoformat()
    p.last_session_date = two_weeks_ago[:10]
    p.last_week_checked = two_weeks_ago[:10]
    ss.update_streak(p)
    assert p.weekly_streak == 0


def test_partial_sessions_preserves_streak():
    ss = StreakSystem()
    now = datetime.now()
    mon = now - timedelta(days=now.weekday())
    # 1 Session diese Woche (Ziel = 2) — Streak bleibt
    p = _profile_with_sessions([mon.isoformat()])
    p.weekly_streak = 3
    ss.update_streak(p)
    assert p.weekly_streak == 3


def test_best_streak_tracked():
    ss = StreakSystem()
    p = UserProfile(weekly_streak=10, best_weekly_streak=5)
    ss.update_streak(p)
    assert p.best_weekly_streak == 10


def test_remaining_trainings():
    ss = StreakSystem()
    now = datetime.now()
    mon = now - timedelta(days=now.weekday())
    p = _profile_with_sessions([mon.isoformat()])
    p.trainings_per_week = 3
    assert ss.remaining_this_week(p) == 2
