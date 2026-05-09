"""MPRIS2 D-Bus Mediensteuerung - pausiert und setzt laufende Player fort."""

import gi

gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib


class MprisService:
    """Steuert Medienplayer über MPRIS2 D-Bus-Schnittstelle."""

    MPRIS_PREFIX = "org.mpris.MediaPlayer2."
    MPRIS_PATH = "/org/mpris/MediaPlayer2"
    PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
    PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"

    def __init__(self):
        self._paused_players: list[str] = []
        self._bus = None
        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error as e:
            print(f"MprisService: D-Bus nicht verfügbar: {e.message}")

    def _get_player_names(self) -> list[str]:
        """Findet alle aktiven MPRIS2-Player auf dem Bus."""
        if not self._bus:
            return []
        try:
            result = self._bus.call_sync(
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus",
                "ListNames",
                None,
                GLib.VariantType.new("(as)"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
            names = result.get_child_value(0).unpack()
            return [n for n in names if n.startswith(self.MPRIS_PREFIX)]
        except GLib.Error:
            return []

    def _get_playback_status(self, bus_name: str) -> str:
        """Gibt den Playback-Status eines Players zurück."""
        try:
            result = self._bus.call_sync(
                bus_name,
                self.MPRIS_PATH,
                self.PROPERTIES_IFACE,
                "Get",
                GLib.Variant("(ss)", (self.PLAYER_IFACE, "PlaybackStatus")),
                GLib.VariantType.new("(v)"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
            return result.get_child_value(0).get_variant().get_string()
        except GLib.Error:
            return "Unknown"

    def _call_player_method(self, bus_name: str, method: str):
        """Ruft eine Methode auf dem Player-Interface auf."""
        try:
            self._bus.call_sync(
                bus_name,
                self.MPRIS_PATH,
                self.PLAYER_IFACE,
                method,
                None,
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except GLib.Error as e:
            print(f"MprisService: {method} fehlgeschlagen für {bus_name}: {e.message}")

    def pause_all(self):
        """Pausiert alle spielenden Medienplayer und merkt sie sich."""
        self._paused_players.clear()
        for name in self._get_player_names():
            status = self._get_playback_status(name)
            if status == "Playing":
                self._call_player_method(name, "Pause")
                self._paused_players.append(name)

    def resume_paused(self):
        """Setzt alle von uns pausierten Player fort."""
        for name in self._paused_players:
            status = self._get_playback_status(name)
            if status == "Paused":
                self._call_player_method(name, "Play")
        self._paused_players.clear()
