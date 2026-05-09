"""Tests fuer HSV-basierte Zungenerkennung im Mund-ROI."""
import numpy as np
import cv2
import pytest
from detection.hsv_detector import HsvDetector

def _make_bgr_roi(h: int, s: int, v: int, size: int = 100) -> np.ndarray:
    hsv = np.zeros((size, size, 3), dtype=np.uint8)
    hsv[:, :] = [h, s, v]
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def test_no_tongue_returns_zero():
    det = HsvDetector()
    det.set_tongue_range([0, 150, 170], [10, 210, 230])
    lip_roi = _make_bgr_roi(15, 100, 150)
    result = det.detect(lip_roi, mouth_area=100 * 100)
    assert result["tongue_ratio"] < 0.05

def test_tongue_returns_high_score():
    det = HsvDetector()
    det.set_tongue_range([0, 150, 170], [10, 210, 230])
    tongue_roi = _make_bgr_roi(5, 180, 200)
    result = det.detect(tongue_roi, mouth_area=100 * 100)
    assert result["tongue_ratio"] > 0.5

def test_mixed_roi_partial_score():
    det = HsvDetector()
    det.set_tongue_range([0, 150, 170], [10, 210, 230])
    lip_part = _make_bgr_roi(15, 100, 150, size=50)
    tongue_part = _make_bgr_roi(5, 180, 200, size=50)
    roi = np.vstack([lip_part, tongue_part])
    result = det.detect(roi, mouth_area=100 * 50)
    assert 0.2 < result["tongue_ratio"] < 0.8

def test_detect_without_calibration_returns_zero():
    det = HsvDetector()
    roi = _make_bgr_roi(5, 180, 200)
    result = det.detect(roi, mouth_area=100 * 100)
    assert result["tongue_ratio"] == 0.0
