"""Trainings-Seite mit Kamera-Feed und Steuerung."""

import time
from datetime import datetime, date

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from services.camera_service import CameraService
from services.detector_service import DetectorService
from services.sound_service import SoundService
from services.mpris_service import MprisService
from services.session_service import SessionService, SessionState
from utils.camera_paintable import CameraPaintable
from models.user_data import SessionRecord


class TrainingPage(Gtk.Box):
    """Hauptseite für das Training mit Kamera-Feed."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._window = main_window
        self._polling_id = None

        # Services
        self._camera = CameraService(
            main_window.profile.settings.get("camera_index", 0)
        )
        self._detector = DetectorService()
        self._sound = SoundService(
            frequency=main_window.profile.settings.get("beep_frequency", 800)
        )
        self._sound.volume = main_window.profile.settings.get("volume", 0.5)
        self._mpris = MprisService()
        self._session = SessionService()
        self._paintable = CameraPaintable()

        # Session-Callbacks
        self._session.on_warning = self._on_warning
        self._session.on_alarm = self._on_alarm
        self._session.on_alarm_end = self._on_alarm_end
        self._session.on_state_change = self._on_state_change

        # Schwierigkeitsparameter setzen
        self._apply_difficulty()

        self._build_ui()

    def _apply_difficulty(self):
        profile = self._window.profile
        diff = self._window.level_system.get_difficulty(profile.level)
        self._session.beep_delay = diff["beep_delay"]
        self._session.pause_delay = diff["pause_delay"]
        self._session.resume_delay = diff["resume_delay"]
        self._session.cooldown_time = diff["cooldown_time"]
        self._session.max_incidents = diff["max_incidents"]
        self._session.required_session_time = diff["required_session_time"]
        self._detector.sensitivity_multiplier = diff["sensitivity"]

    def _build_ui(self):
        # Status-Banner (nur sichtbar bei Warnungen)
        self._status_banner = Adw.Banner()
        self._status_banner.set_revealed(False)
        self.append(self._status_banner)

        # Kamera-Bild
        self._picture = Gtk.Picture()
        self._picture.set_paintable(self._paintable)
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self._picture.set_vexpand(True)
        self._picture.set_margin_top(12)
        self._picture.set_margin_start(12)
        self._picture.set_margin_end(12)
        self.append(self._picture)

        # Info-Zeile
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        info_box.set_halign(Gtk.Align.CENTER)
        info_box.set_margin_top(12)
        info_box.set_margin_bottom(4)

        self._time_label = Gtk.Label(label="00:00")
        self._time_label.add_css_class("title-2")
        self._time_label.add_css_class("numeric")
        info_box.append(self._time_label)

        self._incident_label = Gtk.Label(label="Vorfälle: 0")
        self._incident_label.add_css_class("dim-label")
        info_box.append(self._incident_label)

        self._score_label = Gtk.Label(label="")
        self._score_label.add_css_class("dim-label")
        info_box.append(self._score_label)

        self.append(info_box)

        # Status-Text unter der Info-Zeile
        self._status_label = Gtk.Label(label="Bereit zum Training")
        self._status_label.add_css_class("dim-label")
        self._status_label.set_margin_bottom(8)
        self.append(self._status_label)

        # Start/Stop-Button
        self._start_button = Gtk.Button(label="Training starten")
        self._start_button.add_css_class("suggested-action")
        self._start_button.add_css_class("pill")
        self._start_button.set_halign(Gtk.Align.CENTER)
        self._start_button.set_margin_bottom(16)
        self._start_button.connect("clicked", self._on_toggle_training)
        self.append(self._start_button)

    def _on_toggle_training(self, button):
        if self._session.state == SessionState.IDLE:
            self.start_training()
        else:
            self.stop_training()

    def start_training(self):
        self._apply_difficulty()
        # Test-Modus: Auslöse-Dauer überschreiben
        if self._window.pause_delay_override is not None:
            self._session.pause_delay = self._window.pause_delay_override
        self._detector.reset_calibration()
        self._camera.start()
        self._session.start()
        self._start_button.set_label("Training stoppen")
        self._start_button.remove_css_class("suggested-action")
        self._start_button.add_css_class("destructive-action")
        self._status_label.set_label("Kalibrierung \u2013 Mund bitte geschlossen halten")
        self._status_banner.set_revealed(False)

        # Polling starten (30 FPS)
        self._polling_id = GLib.timeout_add(33, self._poll_frame)

    def stop_training(self):
        if self._polling_id:
            GLib.source_remove(self._polling_id)
            self._polling_id = None

        result = self._session.stop()
        self._camera.stop()
        self._mpris.resume_paused()

        # Test-Modus nach Sitzung zurücksetzen
        if self._window.pause_delay_override is not None:
            self._window.pause_delay_override = None
            self._window.settings_page.reset_pause_override()

        self._start_button.set_label("Training starten")
        self._start_button.remove_css_class("destructive-action")
        self._start_button.add_css_class("suggested-action")
        self._status_banner.set_revealed(False)
        self._status_label.set_label("Bereit zum Training")

        # Sitzung auswerten
        if result["duration"] > 10:  # Mindestens 10 Sekunden
            self._finish_session(result)

    def _poll_frame(self) -> bool:
        """Wird alle 33ms auf dem GTK-Main-Thread aufgerufen."""
        frame = self._camera.get_frame()
        if frame is None:
            return True

        # Frame anzeigen
        self._paintable.set_frame(frame)

        # Erkennung
        detection = self._detector.detect(frame)

        if detection["face_detected"]:
            score = detection["smoothed_score"]
            self._score_label.set_label(f"Score: {score:.2f}")
            self._session.update(detection["tongue_out"])

            # Status je nach Zustand aktualisieren
            if not detection["calibrated"]:
                self._status_label.set_label(
                    "Kalibrierung \u2013 Mund bitte geschlossen halten"
                )
            elif self._session.state == SessionState.RUNNING:
                if detection["tongue_out"]:
                    self._status_label.set_label("Zunge erkannt!")
                else:
                    self._status_label.set_label("Training läuft")
            elif self._session.state == SessionState.WARNING:
                self._status_label.set_label("Zunge rein!")
            elif self._session.state == SessionState.DETECTED:
                remaining = self._session.remaining_resume
                self._status_label.set_label(
                    f"Medien pausiert... noch {int(remaining)}s"
                )
            elif self._session.state == SessionState.COOLDOWN:
                remaining = self._session.remaining_cooldown
                self._status_label.set_label(
                    f"Abklingzeit... noch {int(remaining)}s"
                )
        else:
            self._score_label.set_label("")
            # Auch ohne Gesicht die Session updaten, damit
            # Übergänge stattfinden
            self._session.update(False)
            # "Kein Gesicht" nur im RUNNING-State anzeigen,
            # damit wichtige Meldungen nicht überschrieben werden
            if self._session.state == SessionState.RUNNING:
                self._status_label.set_label("Kein Gesicht erkannt")
            elif self._session.state == SessionState.DETECTED:
                remaining = self._session.remaining_resume
                self._status_label.set_label(
                    f"Medien pausiert... noch {int(remaining)}s"
                )
            elif self._session.state == SessionState.COOLDOWN:
                remaining = self._session.remaining_cooldown
                self._status_label.set_label(
                    f"Abklingzeit... noch {int(remaining)}s"
                )

        # Timer aktualisieren
        duration = self._session.session_duration
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        self._time_label.set_label(f"{minutes:02d}:{seconds:02d}")

        # Vorfälle
        self._incident_label.set_label(f"Vorfälle: {self._session.incident_count}")

        # Prüfe ob Sitzung fehlgeschlagen
        if self._session.session_failed:
            self._status_banner.set_title("Zu viele Vorfälle \u2013 Sitzung beendet")
            self._status_banner.set_revealed(True)
            # Polling-ID löschen bevor wir False zurückgeben,
            # damit stop_training() nicht versucht eine bereits entfernte Source zu entfernen
            self._polling_id = None
            GLib.timeout_add(100, lambda: self.stop_training() or False)
            return False

        return True  # Weiter pollen

    def _on_warning(self):
        """Wird aufgerufen wenn die Zunge den beep_delay überschritten hat."""
        self._sound.beep()
        self._status_banner.set_title("Zunge rein!")
        self._status_banner.set_revealed(True)

    def _on_alarm(self):
        """Wird aufgerufen wenn die Medienpause ausgelöst wird."""
        self._mpris.pause_all()
        self._status_banner.set_title("Vorfall \u2013 Medien pausiert")
        self._status_banner.set_revealed(True)

    def _on_alarm_end(self):
        """Wird aufgerufen wenn die Medien wieder laufen."""
        self._mpris.resume_paused()
        self._status_banner.set_revealed(False)

    def _on_state_change(self, new_state: SessionState):
        if new_state == SessionState.WARNING:
            self._status_banner.set_title("Zunge rein!")
            self._status_banner.set_revealed(True)
            self._status_label.set_label("Zunge rein!")
        elif new_state == SessionState.DETECTED:
            self._status_banner.set_title("Vorfall \u2013 Medien pausiert")
            self._status_banner.set_revealed(True)
            self._status_label.set_label("Vorfall erkannt!")
        elif new_state == SessionState.COOLDOWN:
            self._status_banner.set_revealed(False)
            self._status_label.set_label("Abklingzeit...")
        elif new_state == SessionState.RUNNING:
            self._status_banner.set_revealed(False)
            self._status_label.set_label("Training läuft")
        elif new_state == SessionState.IDLE:
            self._status_banner.set_revealed(False)
            self._status_label.set_label("Bereit zum Training")

    def _finish_session(self, result: dict):
        """Wertet eine abgeschlossene Sitzung aus."""
        profile = self._window.profile
        level_sys = self._window.level_system
        badge_sys = self._window.badge_system
        creature_sys = self._window.creature_system

        # XP berechnen
        xp = level_sys.award_session_xp(
            profile.level, result["duration"],
            result["incidents"], result["success"],
        )

        # Sitzung aufzeichnen
        record = SessionRecord(
            timestamp=datetime.now().isoformat(),
            duration=result["duration"],
            incidents=result["incidents"],
            success=result["success"],
            xp_earned=xp,
            level_at_time=profile.level,
        )
        profile.sessions.append(record)

        # Profil aktualisieren
        profile.xp += xp
        profile.total_xp += xp
        profile.total_sessions += 1
        profile.total_training_time += result["duration"]
        profile.total_incidents += result["incidents"]
        if result["success"]:
            profile.successful_sessions += 1

        # Streak aktualisieren
        today = date.today().isoformat()
        if profile.last_session_date:
            last = date.fromisoformat(profile.last_session_date)
            diff = (date.today() - last).days
            if diff == 1:
                profile.current_streak += 1
            elif diff > 1:
                profile.current_streak = 1
        else:
            profile.current_streak = 1
        profile.best_streak = max(profile.best_streak, profile.current_streak)
        profile.last_session_date = today

        # Level-Aufstieg prüfen
        new_levels = level_sys.check_level_up(profile)

        # Abzeichen prüfen
        new_badges = badge_sys.check_badges(profile)

        # Kreaturen prüfen
        new_creatures = creature_sys.check_creatures(profile)

        # XP für nächsten Level verbrauchen
        xp_needed = level_sys.xp_for_next_level(profile.level)
        if xp_needed > 0:
            profile.xp = level_sys.xp_in_current_level(profile.level, profile.total_xp)

        # Speichern
        self._window.save_profile()
        self._window.refresh_pages()

        # Ergebnis-Dialog zeigen
        self._show_result_dialog(xp, new_levels, new_badges, new_creatures, result)

    def _show_result_dialog(self, xp, new_levels, new_badges, new_creatures, result):
        """Zeigt einen Dialog mit dem Sitzungs-Ergebnis."""
        minutes = int(result["duration"]) // 60
        seconds = int(result["duration"]) % 60

        lines = [
            f"Dauer: {minutes}:{seconds:02d}",
            f"Vorfälle: {result['incidents']}",
            f"XP verdient: +{xp}",
        ]

        if new_levels:
            for lvl in new_levels:
                lines.append(f"\nLevel {lvl} erreicht!")

        if new_badges:
            for badge in new_badges:
                lines.append(f"\nNeues Abzeichen: {badge.name}")

        if new_creatures:
            for creature in new_creatures:
                lines.append(f"\nNeuer Zungenfreund: {creature.name}")

        heading = "Sitzung erfolgreich!" if result["success"] else "Sitzung beendet"

        dialog = Adw.AlertDialog()
        dialog.set_heading(heading)
        dialog.set_body("\n".join(lines))
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.choose(self._window, None, None)

    def cleanup(self):
        """Gibt alle Ressourcen frei (beim App-Schließen)."""
        self.stop_training()
        self._sound.cleanup()
        self._detector.cleanup()

    def update_settings(self):
        """Wird von SettingsPage aufgerufen wenn sich Einstellungen ändern."""
        profile = self._window.profile
        self._camera.camera_index = profile.settings.get("camera_index", 0)
        self._sound.volume = profile.settings.get("volume", 0.5)
        self._sound.frequency = profile.settings.get("beep_frequency", 800)
