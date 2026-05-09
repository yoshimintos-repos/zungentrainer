"""Kalibrierung: Baseline-Lippen + Zungenfarbe erfassen.

Zwei Modi:
- Interaktiv (erster Start): BASELINE -> TONGUE_PROMPT -> DONE
- Still (Folge-Sessions): nur BASELINE neu erfassen, Zungenfarbe aus Profil
"""
from enum import Enum, auto
import numpy as np
import cv2

class CalibrationState(Enum):
    IDLE = auto()
    BASELINE = auto()
    TONGUE_PROMPT = auto()
    DONE = auto()

class Calibration:
    def __init__(self, baseline_frames: int = 60, tongue_frames: int = 30):
        self._baseline_target = baseline_frames
        self._tongue_target = tongue_frames
        self.state = CalibrationState.IDLE
        self._baseline_samples: list[np.ndarray] = []
        self._tongue_samples: list[np.ndarray] = []
        self._lip_hsv_mean: np.ndarray | None = None
        self._lip_hsv_std: np.ndarray | None = None
        self._tongue_hsv_lower: np.ndarray | None = None
        self._tongue_hsv_upper: np.ndarray | None = None
        self._silent_mode = False
        self._baseline_target_silent = baseline_frames

    def start(self):
        self._baseline_samples.clear()
        self._tongue_samples.clear()
        self._silent_mode = False
        self.state = CalibrationState.BASELINE

    def start_silent(self, baseline_frames: int = 60):
        self._baseline_samples.clear()
        self._baseline_target_silent = baseline_frames
        self._silent_mode = True
        self.state = CalibrationState.BASELINE

    def feed_frame(self, hsv_roi: np.ndarray, mouth_open: bool):
        if self.state == CalibrationState.BASELINE:
            self._baseline_samples.append(hsv_roi.copy())
            target = self._baseline_target_silent if self._silent_mode else self._baseline_target
            if len(self._baseline_samples) >= target:
                self._compute_baseline()
                if self._silent_mode:
                    self.state = CalibrationState.DONE
                    self._silent_mode = False
                else:
                    self.state = CalibrationState.TONGUE_PROMPT
        elif self.state == CalibrationState.TONGUE_PROMPT:
            self._tongue_samples.append(hsv_roi.copy())
            if len(self._tongue_samples) >= self._tongue_target:
                self._compute_tongue_range()
                self.state = CalibrationState.DONE

    def _compute_baseline(self):
        all_pixels = np.concatenate([s.reshape(-1, 3) for s in self._baseline_samples], axis=0)
        self._lip_hsv_mean = np.mean(all_pixels, axis=0).astype(np.float32)
        self._lip_hsv_std = np.std(all_pixels, axis=0).astype(np.float32)

    def _compute_tongue_range(self):
        all_pixels = np.concatenate([s.reshape(-1, 3) for s in self._tongue_samples], axis=0)
        median = np.median(all_pixels, axis=0)
        mad = np.median(np.abs(all_pixels - median), axis=0)
        spread = np.maximum(mad * 2, np.array([12, 40, 40]))
        self._tongue_hsv_lower = np.clip(median - spread, 0, 255).astype(np.uint8)
        self._tongue_hsv_upper = np.clip(median + spread, 0, 255).astype(np.uint8)

    def get_tongue_hsv_range(self) -> dict | None:
        if self._tongue_hsv_lower is None:
            return None
        return {"lower": self._tongue_hsv_lower.tolist(), "upper": self._tongue_hsv_upper.tolist()}

    def get_lip_stats(self) -> dict | None:
        if self._lip_hsv_mean is None:
            return None
        return {"mean": self._lip_hsv_mean.tolist(), "std": self._lip_hsv_std.tolist()}

    def load_tongue_range(self, lower: list[int], upper: list[int]):
        self._tongue_hsv_lower = np.array(lower, dtype=np.uint8)
        self._tongue_hsv_upper = np.array(upper, dtype=np.uint8)
