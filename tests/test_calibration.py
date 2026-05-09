"""Tests fuer die Kalibrierung (Baseline + Zungenfarbe)."""
import numpy as np
import pytest
from detection.calibration import Calibration, CalibrationState

def _make_hsv_roi(h: int, s: int, v: int, size: int = 50) -> np.ndarray:
    roi = np.zeros((size, size, 3), dtype=np.uint8)
    roi[:, :, 0] = h
    roi[:, :, 1] = s
    roi[:, :, 2] = v
    return roi

def test_initial_state_is_idle():
    cal = Calibration()
    assert cal.state == CalibrationState.IDLE

def test_start_begins_baseline():
    cal = Calibration()
    cal.start()
    assert cal.state == CalibrationState.BASELINE

def test_baseline_collects_frames():
    cal = Calibration(baseline_frames=5)
    cal.start()
    roi = _make_hsv_roi(10, 100, 150)
    for _ in range(5):
        cal.feed_frame(roi, mouth_open=False)
    assert cal.state == CalibrationState.TONGUE_PROMPT

def test_tongue_phase_collects_and_completes():
    cal = Calibration(baseline_frames=3, tongue_frames=3)
    cal.start()
    lip_roi = _make_hsv_roi(10, 100, 150)
    for _ in range(3):
        cal.feed_frame(lip_roi, mouth_open=False)
    assert cal.state == CalibrationState.TONGUE_PROMPT
    tongue_roi = _make_hsv_roi(0, 180, 200)
    for _ in range(3):
        cal.feed_frame(tongue_roi, mouth_open=True)
    assert cal.state == CalibrationState.DONE

def test_done_provides_ranges():
    cal = Calibration(baseline_frames=3, tongue_frames=3)
    cal.start()
    lip_roi = _make_hsv_roi(10, 100, 150)
    for _ in range(3):
        cal.feed_frame(lip_roi, mouth_open=False)
    tongue_roi = _make_hsv_roi(0, 180, 200)
    for _ in range(3):
        cal.feed_frame(tongue_roi, mouth_open=True)
    ranges = cal.get_tongue_hsv_range()
    assert ranges is not None
    assert "lower" in ranges and "upper" in ranges
    assert len(ranges["lower"]) == 3
    assert len(ranges["upper"]) == 3

def test_silent_recalibration():
    cal = Calibration(baseline_frames=3, tongue_frames=3)
    cal.start()
    lip_roi = _make_hsv_roi(10, 100, 150)
    for _ in range(3):
        cal.feed_frame(lip_roi, mouth_open=False)
    tongue_roi = _make_hsv_roi(0, 180, 200)
    for _ in range(3):
        cal.feed_frame(tongue_roi, mouth_open=True)
    old_ranges = cal.get_tongue_hsv_range()
    cal.start_silent(baseline_frames=3)
    new_lip = _make_hsv_roi(15, 90, 140)
    for _ in range(3):
        cal.feed_frame(new_lip, mouth_open=False)
    assert cal.state == CalibrationState.DONE
    assert cal.get_tongue_hsv_range() == old_ranges
