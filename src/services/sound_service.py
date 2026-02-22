"""Piepton-Wiedergabe über GStreamer."""

import gi

gi.require_version("Gst", "1.0")

from gi.repository import Gst


class SoundService:
    """Spielt einen Piepton über GStreamer ab."""

    def __init__(self, frequency: int = 800, duration_ms: int = 500):
        self._frequency = frequency
        self._duration_ms = duration_ms
        self._volume = 0.5
        self._pipeline = None
        self._timeout_id = None

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(1.0, value))

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, value: int):
        self._frequency = value

    def beep(self):
        """Spielt einen kurzen Piepton ab."""
        from gi.repository import GLib

        # Alten Beep sauber beenden (inkl. Timeout und Bus-Watch)
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
        if self._pipeline:
            bus = self._pipeline.get_bus()
            bus.remove_signal_watch()
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None

        pipeline_str = (
            f"audiotestsrc freq={self._frequency} wave=0 "
            f"! audioconvert ! audioresample "
            f"! volume volume={self._volume} "
            f"! autoaudiosink"
        )
        self._pipeline = Gst.parse_launch(pipeline_str)

        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)

        self._pipeline.set_state(Gst.State.PLAYING)

        self._timeout_id = GLib.timeout_add(self._duration_ms, self._stop_beep)

    def _stop_beep(self):
        self._timeout_id = None
        if self._pipeline:
            bus = self._pipeline.get_bus()
            bus.remove_signal_watch()
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
        return False

    def _on_error(self, bus, msg):
        err, debug = msg.parse_error()
        print(f"SoundService Fehler: {err.message}")
        self._stop_beep()

    def cleanup(self):
        from gi.repository import GLib

        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
        if self._pipeline:
            bus = self._pipeline.get_bus()
            bus.remove_signal_watch()
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
