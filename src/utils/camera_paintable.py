"""Gdk.Paintable-Implementierung für OpenCV-Frames in GTK4."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Graphene", "1.0")

from gi.repository import Gdk, GLib, GObject, Graphene
import cv2
import numpy as np


class CameraPaintable(GObject.Object, Gdk.Paintable):
    """Zeigt OpenCV-Frames (numpy BGR arrays) als Gdk.Paintable an."""

    __gtype_name__ = "CameraPaintable"

    def __init__(self):
        super().__init__()
        self._texture = None
        self._width = 0
        self._height = 0

    def clear(self):
        """Löscht den aktuellen Frame (z.B. wenn Kamera gestoppt wird)."""
        self._texture = None
        self._width = 0
        self._height = 0
        self.invalidate_contents()
        self.invalidate_size()

    def set_frame(self, frame: np.ndarray):
        """Setzt einen neuen Frame (BGR numpy array) und löst Neuzeichnung aus."""
        if frame is None:
            return

        # BGR → RGB konvertieren
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, _ = rgb.shape
        size_changed = (w != self._width or h != self._height)
        self._width = w
        self._height = h

        # Daten als zusammenhängenden Buffer
        data = rgb.tobytes()
        gbytes = GLib.Bytes.new(data)

        self._texture = Gdk.MemoryTexture.new(
            w, h, Gdk.MemoryFormat.R8G8B8, gbytes, w * 3
        )

        self.invalidate_contents()
        if size_changed:
            self.invalidate_size()

    def do_snapshot(self, snapshot, width, height):
        if self._texture is None:
            return
        self._texture.snapshot(snapshot, width, height)

    def do_get_intrinsic_width(self):
        return self._width

    def do_get_intrinsic_height(self):
        return self._height

    def do_get_intrinsic_aspect_ratio(self):
        if self._height > 0:
            return self._width / self._height
        return 0.0
