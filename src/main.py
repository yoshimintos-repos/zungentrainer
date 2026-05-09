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
            self._setup_shortcuts(win)
        win.present()

    def _setup_shortcuts(self, win):
        # Ctrl+Q: Beenden
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

        # Space: Training starten/stoppen
        toggle_action = Gio.SimpleAction.new("toggle-training", None)
        toggle_action.connect("activate", lambda *_: win.toggle_training())
        win.add_action(toggle_action)
        self.set_accels_for_action("win.toggle-training", ["space"])

        # Escape: Training abbrechen
        stop_action = Gio.SimpleAction.new("stop-training", None)
        stop_action.connect("activate", lambda *_: win.training_page.stop_training())
        win.add_action(stop_action)
        self.set_accels_for_action("win.stop-training", ["Escape"])


def main():
    app = ZungenTrainerApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
