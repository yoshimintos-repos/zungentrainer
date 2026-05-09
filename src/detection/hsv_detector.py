"""HSV-Farbsegmentierung zur Zungenerkennung im Mund-ROI.

Pipeline: BGR -> CLAHE -> HSV -> Maske -> Morphologie -> Kontur -> Score.
"""
import cv2
import numpy as np


class HsvDetector:
    def __init__(self):
        self._tongue_lower: np.ndarray | None = None
        self._tongue_upper: np.ndarray | None = None
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        self._kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    def set_tongue_range(self, lower: list[int], upper: list[int]):
        self._tongue_lower = np.array(lower, dtype=np.uint8)
        self._tongue_upper = np.array(upper, dtype=np.uint8)

    def detect(self, bgr_roi: np.ndarray, mouth_area: float) -> dict:
        if self._tongue_lower is None or mouth_area <= 0:
            return {"tongue_ratio": 0.0, "tongue_tip_y": 0.0, "mask": None}

        # CLAHE on L-channel
        lab = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = self._clahe.apply(lab[:, :, 0])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)

        # Handle red hue wrap-around
        if self._tongue_lower[0] > self._tongue_upper[0]:
            mask1 = cv2.inRange(
                hsv,
                np.array([self._tongue_lower[0], self._tongue_lower[1], self._tongue_lower[2]]),
                np.array([179, self._tongue_upper[1], self._tongue_upper[2]]),
            )
            mask2 = cv2.inRange(
                hsv,
                np.array([0, self._tongue_lower[1], self._tongue_lower[2]]),
                self._tongue_upper,
            )
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv, self._tongue_lower, self._tongue_upper)

        mask = cv2.erode(mask, self._kernel, iterations=1)
        mask = cv2.dilate(mask, self._kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return {"tongue_ratio": 0.0, "tongue_tip_y": 0.0, "mask": mask}

        largest = max(contours, key=cv2.contourArea)
        tongue_area = cv2.contourArea(largest)
        tongue_ratio = min(1.0, tongue_area / mouth_area)

        h = bgr_roi.shape[0]
        bottommost = max(largest, key=lambda p: p[0][1])
        tongue_tip_y = bottommost[0][1] / h if h > 0 else 0.0

        return {"tongue_ratio": float(tongue_ratio), "tongue_tip_y": float(tongue_tip_y), "mask": mask}
