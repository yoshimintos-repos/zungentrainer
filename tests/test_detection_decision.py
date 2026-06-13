"""Tests fuer die fachliche DetectionDecision-Schnittstelle."""

from detection.decision import (
    DetectionState,
    decision_from_legacy_detection,
)


def test_no_face_is_uncertain():
    decision = decision_from_legacy_detection({"face_detected": False})

    assert decision.state == DetectionState.UNCERTAIN
    assert decision.reason == "no_face"
    assert decision.tongue_out is False


def test_not_calibrated_is_uncertain():
    decision = decision_from_legacy_detection({
        "face_detected": True,
        "calibrated": False,
    })

    assert decision.state == DetectionState.UNCERTAIN
    assert decision.reason == "not_calibrated"


def test_positive_legacy_detection_becomes_tongue_out():
    decision = decision_from_legacy_detection({
        "face_detected": True,
        "calibrated": True,
        "tongue_out": True,
        "confidence": 0.8,
        "tongue_ratio": 0.2,
        "smoothed_score": 0.12,
    })

    assert decision.state == DetectionState.TONGUE_OUT
    assert decision.tongue_out is True
    assert decision.confidence == 0.8
    assert decision.signals["tongue_ratio"] == 0.2


def test_negative_legacy_detection_becomes_clear():
    decision = decision_from_legacy_detection({
        "face_detected": True,
        "calibrated": True,
        "tongue_out": False,
        "confidence": 0.2,
    })

    assert decision.state == DetectionState.CLEAR
    assert decision.tongue_out is False
    assert decision.reason == "legacy_detector_clear"
