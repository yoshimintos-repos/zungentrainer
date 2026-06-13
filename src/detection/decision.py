"""Fachliche Erkennungsentscheidung fuer Zungenprotrusion."""

from dataclasses import dataclass, field
from enum import Enum


class DetectionState(Enum):
    CLEAR = "clear"
    UNCERTAIN = "uncertain"
    TONGUE_OUT = "tongue_out"


@dataclass(frozen=True)
class DetectionDecision:
    """Resultat der fachlichen Erkennung.

    Nur TONGUE_OUT darf Feedback ausloesen. UNCERTAIN bedeutet bewusst: nicht
    nerven, weil die Erkennungslage nicht gut genug ist.
    """

    state: DetectionState
    confidence: float = 0.0
    reason: str = ""
    signals: dict = field(default_factory=dict)

    @property
    def tongue_out(self) -> bool:
        return self.state == DetectionState.TONGUE_OUT


def decision_from_legacy_detection(detection: dict) -> DetectionDecision:
    """Erzeugt eine v3-Entscheidung aus dem aktuellen Detektor-Dict."""
    if not detection.get("face_detected", False):
        return DetectionDecision(
            state=DetectionState.UNCERTAIN,
            confidence=0.0,
            reason="no_face",
        )

    if not detection.get("calibrated", False):
        return DetectionDecision(
            state=DetectionState.UNCERTAIN,
            confidence=0.0,
            reason="not_calibrated",
        )

    signals = {
        "tongue_ratio": detection.get("tongue_ratio", 0.0),
        "smoothed_score": detection.get("smoothed_score", 0.0),
    }

    if detection.get("tongue_out", False):
        return DetectionDecision(
            state=DetectionState.TONGUE_OUT,
            confidence=detection.get("confidence", 0.0),
            reason="legacy_detector_positive",
            signals=signals,
        )

    return DetectionDecision(
        state=DetectionState.CLEAR,
        confidence=1.0 - detection.get("confidence", 0.0),
        reason="legacy_detector_clear",
        signals=signals,
    )
