#!/usr/bin/env python3
"""Standalone-Test der Erkennungs-Pipeline mit OpenCV Debug-Fenster.

Startet Kamera, fuehrt Kalibrierung durch, und zeigt Erkennung live.
Druecke 'q' zum Beenden, 'r' fuer Re-Kalibrierung.
"""

import sys
import os
import cv2
import numpy as np

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

os.environ.setdefault(
    "ZUNGENTRAINER_DATA_DIR",
    os.path.join(os.path.dirname(SRC_DIR), "data"),
)

from services.detector_service import DetectorService
from detection.calibration import CalibrationState


def main():
    detector = DetectorService()
    if detector.init_error:
        print(f"Fehler: {detector.init_error}")
        return 1

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    if not cap.isOpened():
        print("Fehler: Kamera nicht verfuegbar")
        return 1

    detector.start_calibration()
    print("=== Kalibrierung ===")
    print("Phase 1: Mund geschlossen halten (2 Sekunden)")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        result = detector.detect(frame)
        display = frame.copy()

        cal_state = result["calibration_state"]
        if cal_state == CalibrationState.BASELINE:
            text = "KALIBRIERUNG: Mund zu, normal schauen"
            color = (0, 255, 255)
        elif cal_state == CalibrationState.TONGUE_PROMPT:
            text = "KALIBRIERUNG: Zeig die Zunge!"
            color = (0, 165, 255)
        elif result["tongue_out"]:
            text = f"ZUNGE ERKANNT! Score: {result['smoothed_score']:.3f}"
            color = (0, 0, 255)
        elif result["face_detected"]:
            text = f"OK - Score: {result['smoothed_score']:.3f}"
            color = (0, 255, 0)
        else:
            text = "Kein Gesicht"
            color = (128, 128, 128)

        cv2.putText(display, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        if result["calibrated"]:
            bar_w = int(result["tongue_ratio"] * 400)
            cv2.rectangle(display, (20, 70), (20 + bar_w, 90), color, -1)
            cv2.rectangle(display, (20, 70), (420, 90), (255, 255, 255), 1)

        if result["debug_roi"] is not None:
            roi = result["debug_roi"]
            roi_h = min(200, roi.shape[0])
            roi_w = int(roi.shape[1] * roi_h / roi.shape[0])
            roi_small = cv2.resize(roi, (roi_w, roi_h))
            display[100:100 + roi_h, 20:20 + roi_w] = roi_small

        if result["debug_mask"] is not None:
            mask = result["debug_mask"]
            mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            mask_h = min(200, mask.shape[0])
            mask_w = int(mask.shape[1] * mask_h / mask.shape[0])
            mask_small = cv2.resize(mask_color, (mask_w, mask_h))
            x_offset = 40 + (roi_w if result["debug_roi"] is not None else 0)
            display[100:100 + mask_h, x_offset:x_offset + mask_w] = mask_small

        display_small = cv2.resize(display, (960, 540))
        cv2.imshow("ZungenTrainer Debug", display_small)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            detector.start_calibration()
            print("Re-Kalibrierung gestartet")

    cap.release()
    cv2.destroyAllWindows()
    detector.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
