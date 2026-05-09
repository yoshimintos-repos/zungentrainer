"""Polkit-basierte Authentifizierung fuer den Eltern-Bereich."""

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


POLKIT_ACTION_ID = "de.yoshimintos.zungentrainer.parent-access"


class PolkitService:
    """Prueft Polkit-Autorisierung fuer den Eltern-Bereich."""

    def check_authorization(self, callback):
        """Prueft ob der Nutzer autorisiert ist.

        Versucht Polkit-Authentifizierung ueber D-Bus. Bei Fehler
        (z.B. lokale Entwicklung ohne Polkit) wird der Callback mit
        True aufgerufen (Fallback: kein Passwortschutz im Dev-Modus).

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
                    ("unix-process", {
                        "pid": GLib.Variant("u", GLib.get_real_time()),
                        "start-time": GLib.Variant("t", 0),
                    }),
                    POLKIT_ACTION_ID,
                    {},
                    1,  # AllowUserInteraction
                    "",
                )),
                GLib.VariantType.new("((bba{ss}))"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                self._on_auth_result,
                callback,
            )
        except GLib.Error:
            # Polkit nicht verfuegbar — Fallback fuer lokale Entwicklung
            callback(True)

    def _on_auth_result(self, bus, result, callback):
        try:
            res = bus.call_finish(result)
            auth_result = res.get_child_value(0)
            is_authorized = auth_result.get_child_value(0).get_boolean()
            callback(is_authorized)
        except GLib.Error:
            # Bei Fehler: Fallback fuer lokale Entwicklung ohne Policy-Datei
            callback(True)
