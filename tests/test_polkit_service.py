"""Tests fuer Polkit-Helfer ohne echte D-Bus-Autorisierung."""

import os

import pytest

gi = pytest.importorskip("gi")

from services import polkit_service


def test_process_start_time_is_int():
    start_time = polkit_service._process_start_time_ticks(os.getpid())
    assert isinstance(start_time, int)
    assert start_time >= 0


def test_unix_process_subject_uses_real_pid():
    subject_type, details = polkit_service._unix_process_subject()

    assert subject_type == "unix-process"
    assert details["pid"].unpack() == os.getpid()
    assert isinstance(details["start-time"].unpack(), int)


def test_dev_fallback_is_explicit(monkeypatch):
    monkeypatch.delenv("ZUNGENTRAINER_POLKIT_DEV_FALLBACK", raising=False)
    assert polkit_service._dev_fallback_enabled() is False

    monkeypatch.setenv("ZUNGENTRAINER_POLKIT_DEV_FALLBACK", "1")
    assert polkit_service._dev_fallback_enabled() is True
