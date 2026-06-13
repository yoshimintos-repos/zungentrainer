"""Piepton-Wiedergabe über GStreamer.

Bietet zwei Tonarten: beep() für Zungenalarm (konfigurierbare Frequenz/Lautstärke)
und beep_soft() als dezenter Hinweiston bei fehlendem Gesicht (400 Hz, halbe Lautstärke).
"""

import gi

gi.require_version("Gst", "1.0")

from gi.repository import Gst


class SoundService:
    """Spielt einen Piepton über GStreamer ab."""

    def __init__(self, frequency: int = 800, duration_ms: int = 500):
        self._frequency = frequency
        self._duration_ms = duration_ms
        self._volume = 0.5
        self._beep_pipeline = None
        self._loop_pipeline = None
        self._beep_timeout_id = None

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
        """Spielt einen kurzen Piepton ab (Zungenalarm)."""
        self._play_tone(self._frequency, self._duration_ms, self._volume)

    def beep_soft(self):
        """Spielt einen dezenten Hinweiston (kein Gesicht erkannt)."""
        self._play_tone(frequency=400, duration_ms=200,
                        volume=self._volume * 0.5)

    def start_alarm_loop(self):
        """Startet eine stoerende Audioschleife fuer den No-Media-Fall."""
        if self._loop_pipeline:
            return

        pipeline_str = (
            "audiotestsrc wave=2 freq=520 is-live=true "
            "! audioconvert ! audioresample "
            f"! volume volume={self._volume * 0.6} "
            "! autoaudiosink"
        )
        self._loop_pipeline = Gst.parse_launch(pipeline_str)
        bus = self._loop_pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_loop_error)
        self._loop_pipeline.set_state(Gst.State.PLAYING)

    def stop_alarm_loop(self):
        """Stoppt die stoerende Audioschleife."""
        if self._loop_pipeline:
            bus = self._loop_pipeline.get_bus()
            bus.remove_signal_watch()
            self._loop_pipeline.set_state(Gst.State.NULL)
            self._loop_pipeline = None

    @property
    def alarm_loop_playing(self) -> bool:
        return self._loop_pipeline is not None

    def _play_tone(self, frequency: int, duration_ms: int, volume: float):
        """Spielt einen Ton mit gegebenen Parametern."""
        from gi.repository import GLib

        # Alten Beep sauber beenden (inkl. Timeout und Bus-Watch)
        if self._beep_timeout_id is not None:
            GLib.source_remove(self._beep_timeout_id)
            self._beep_timeout_id = None
        if self._beep_pipeline:
            bus = self._beep_pipeline.get_bus()
            bus.remove_signal_watch()
            self._beep_pipeline.set_state(Gst.State.NULL)
            self._beep_pipeline = None

        pipeline_str = (
            f"audiotestsrc freq={frequency} wave=0 "
            f"! audioconvert ! audioresample "
            f"! volume volume={volume} "
            f"! autoaudiosink"
        )
        self._beep_pipeline = Gst.parse_launch(pipeline_str)

        bus = self._beep_pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)

        self._beep_pipeline.set_state(Gst.State.PLAYING)

        self._beep_timeout_id = GLib.timeout_add(duration_ms, self._stop_beep)

    def _stop_beep(self):
        self._beep_timeout_id = None
        if self._beep_pipeline:
            bus = self._beep_pipeline.get_bus()
            bus.remove_signal_watch()
            self._beep_pipeline.set_state(Gst.State.NULL)
            self._beep_pipeline = None
        return False

    def _on_error(self, bus, msg):
        err, debug = msg.parse_error()
        print(f"SoundService Fehler: {err.message}")
        self._stop_beep()

    def _on_loop_error(self, bus, msg):
        err, debug = msg.parse_error()
        print(f"SoundService Alarm-Schleife Fehler: {err.message}")
        self.stop_alarm_loop()

    def cleanup(self):
        from gi.repository import GLib

        if self._beep_timeout_id is not None:
            GLib.source_remove(self._beep_timeout_id)
            self._beep_timeout_id = None
        if self._beep_pipeline:
            bus = self._beep_pipeline.get_bus()
            bus.remove_signal_watch()
            self._beep_pipeline.set_state(Gst.State.NULL)
            self._beep_pipeline = None
        self.stop_alarm_loop()
