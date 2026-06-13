"""Polkit-basierte Authentifizierung fuer den Eltern-Bereich."""

import os
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


POLKIT_ACTION_ID = "de.yoshimintos.zungentrainer.parent-access"


def _dev_fallback_enabled() -> bool:
    return os.environ.get("ZUNGENTRAINER_POLKIT_DEV_FALLBACK") == "1"


def _process_start_time_ticks(pid: int) -> int:
    """Liest den Linux-Prozess-Startzeitpunkt fuer Polkit aus /proc."""
    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8") as f:
            stat = f.read()
        # Feld 2 (comm) steht in Klammern und kann Leerzeichen enthalten.
        after_comm = stat.rsplit(") ", 1)[1]
        fields_from_state = after_comm.split()
        return int(fields_from_state[19])  # procfs-Feld 22: starttime
    except (OSError, IndexError, ValueError):
        return 0


def _unix_process_subject() -> tuple:
    pid = os.getpid()
    return (
        "unix-process",
        {
            "pid": GLib.Variant("u", pid),
            "start-time": GLib.Variant("t", _process_start_time_ticks(pid)),
        },
    )


class PolkitService:
    """Prueft Polkit-Autorisierung fuer den Eltern-Bereich."""

    def check_authorization(self, callback):
        """Prueft ob der Nutzer autorisiert ist.

        Versucht Polkit-Authentifizierung ueber D-Bus. Fehler sind standardmaessig
        fail-closed. Fuer lokale Entwicklung kann
        ZUNGENTRAINER_POLKIT_DEV_FALLBACK=1 gesetzt werden.

        Args:
            callback: Wird mit (success: bool) aufgerufen.
        """
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            bus.call(
                "org.freedesktop.PolicyKit1",
                "/org/freedesktop/PolicyKit1/Authority",
                "org.freedesktop.PolicyKit1.Authority",
                "CheckAuthorization",
                GLib.Variant("((sa{sv})sa{ss}us)", (
                    _unix_process_subject(),
                    POLKIT_ACTION_ID,
                    {},
                    1,  # AllowUserInteraction
                    "",
                )),
                GLib.VariantType.new("(bba{ss})"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                self._on_auth_result,
                callback,
            )
        except GLib.Error:
            callback(_dev_fallback_enabled())

    def _on_auth_result(self, bus, result, callback):
        try:
            res = bus.call_finish(result)
            is_authorized = res.get_child_value(0).get_boolean()
            callback(is_authorized)
        except GLib.Error:
            callback(_dev_fallback_enabled())
