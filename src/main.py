#!/usr/bin/env python3
"""ZungenTrainer v2 — Zungen-Haltungstrainer mit Webcam-Erkennung."""

import sys
import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Adw, Gio, Gst

Gst.init(None)

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class ZungenTrainerApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="de.yoshimintos.ZungenTrainer",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        from window import ZungenTrainerWindow

        win = self.props.active_window
        if not win:
            win = ZungenTrainerWindow(application=self)
        win.present()


def main():
    app = ZungenTrainerApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
