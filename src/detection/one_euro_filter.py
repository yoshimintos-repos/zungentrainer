"""One-Euro-Filter: Adaptive Signalglaettung.

Glaettet stark bei Ruhe (weniger Fehlalarme) und reagiert schnell bei
Bewegung (niedrige Latenz). Ideal fuer Echtzeit-Score-Glaettung.

Referenz: Casiez et al., "1 Euro Filter", CHI 2012.
"""
import math


class OneEuroFilter:
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0):
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    def filter(self, x: float, timestamp: float) -> float:
        if self._t_prev is None:
            self._x_prev = x
            self._t_prev = timestamp
            self._dx_prev = 0.0
            return x
        dt = timestamp - self._t_prev
        if dt <= 0:
            return self._x_prev
        dx = (x - self._x_prev) / dt
        alpha_d = self._smoothing_factor(dt, self._d_cutoff)
        dx_hat = alpha_d * dx + (1 - alpha_d) * self._dx_prev
        cutoff = self._min_cutoff + self._beta * abs(dx_hat)
        alpha = self._smoothing_factor(dt, cutoff)
        x_hat = alpha * x + (1 - alpha) * self._x_prev
        self._x_prev = x_hat
        self._dx_prev = dx_hat
        self._t_prev = timestamp
        return x_hat

    def reset(self):
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    @staticmethod
    def _smoothing_factor(dt: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)
