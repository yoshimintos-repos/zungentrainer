"""Trainings-Seite mit Kamera-Feed, OSD-Overlays und Session-Steuerung."""

import os
from datetime import datetime
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
from detection.calibration import CalibrationState


class TrainingPage(Gtk.Box):
    """Hauptseite: Kamera-Feed mit OSD-Overlays fuer Training."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._window = main_window
        self._polling_id = None
        self._paused_by_view_switch = False

        profile = main_window.profile
        self._camera = CameraService(profile.settings.get("camera_index", 0))
        self._detector = DetectorService()
        self._sound = SoundService(
            frequency=profile.settings.get("beep_frequency", 800)
        )
        self._sound.volume = profile.settings.get("volume", 0.5)
        self._mpris = MprisService()
        self._session = SessionService()
        self._paintable = CameraPaintable()

        if profile.calibration:
            self._detector.load_calibration(profile.calibration)

        self._session.on_alarm = self._on_alarm
        self._session.on_alarm_end = self._on_alarm_end
        self._session.on_state_change = self._on_state_change

        self._apply_difficulty()
        self._build_ui()

    def _apply_difficulty(self):
        params = self._window.adaptive_difficulty.get_params()
        self._session.resume_delay = params["resume_delay"]
        self._session.cooldown_time = params["cooldown"]
        self._session.required_session_time = self._window.profile.min_session_duration * 60.0
        self._detector.sensitivity = params["sensitivity"]

    def _build_ui(self):
        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_vexpand(True)
        self.append(self._toast_overlay)

        overlay = Gtk.Overlay()
        self._toast_overlay.set_child(overlay)

        self._picture = Gtk.Picture()
        self._picture.set_paintable(self._paintable)
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self._picture.set_vexpand(True)
        self._picture.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Kamera-Vorschau"]
        )
        overlay.set_child(self._picture)

        self._banner = Adw.Banner()
        self._banner.set_revealed(False)
        overlay.add_overlay(self._banner)

        self._timer_label = Gtk.Label(label="00:00")
        self._timer_label.add_css_class("title-2")
        self._timer_label.add_css_class("numeric")
        self._timer_label.set_halign(Gtk.Align.END)
        self._timer_label.set_valign(Gtk.Align.START)
        self._timer_label.set_margin_top(12)
        self._timer_label.set_margin_end(12)
        self._timer_label.set_visible(False)
        self._timer_label.set_tooltip_text("Trainingszeit")
        self._timer_label.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Trainingszeit"]
        )
        overlay.add_overlay(self._timer_label)

        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_box.set_halign(Gtk.Align.CENTER)
        bottom_box.set_valign(Gtk.Align.END)
        bottom_box.set_margin_bottom(12)

        self._incident_label = Gtk.Label(label="0 Vorfaelle")
        self._incident_label.add_css_class("dim-label")
        self._incident_label.set_visible(False)
        self._incident_label.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Anzahl Vorfaelle"]
        )
        bottom_box.append(self._incident_label)

        self._stop_button = Gtk.Button(icon_name="media-playback-stop-symbolic")
        self._stop_button.set_tooltip_text("Training beenden")
        self._stop_button.add_css_class("circular")
        self._stop_button.set_visible(False)
        self._stop_button.connect("clicked", lambda _: self.stop_training())
        bottom_box.append(self._stop_button)

        overlay.add_overlay(bottom_box)

        self._start_button = Gtk.Button(label="Training starten")
        self._start_button.add_css_class("suggested-action")
        self._start_button.add_css_class("pill")
        self._start_button.set_halign(Gtk.Align.CENTER)
        self._start_button.set_valign(Gtk.Align.CENTER)
        self._start_button.set_tooltip_text("Training starten")
        self._start_button.connect("clicked", lambda _: self.start_training())
        overlay.add_overlay(self._start_button)

        self._status_label = Gtk.Label(label="Bereit zum Training")
        self._status_label.add_css_class("dim-label")
        self._status_label.set_margin_top(8)
        self._status_label.set_margin_bottom(8)
        status_clamp = Adw.Clamp(maximum_size=600)
        status_clamp.set_child(self._status_label)
        self.append(status_clamp)

    def start_training(self):
        if self._detector.init_error:
            self._banner.set_title("Kamera konnte nicht gestartet werden")
            self._banner.set_revealed(True)
            return

        self._apply_difficulty()

        if self._detector._calibration.state == CalibrationState.DONE:
            self._detector.start_silent_calibration()
        else:
            self._detector.start_calibration()

        self._detector.reset()
        self._camera.start()

        # ROI-Datensammlung aktivieren
        data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        roi_dir = os.path.join(data_home, "zungentrainer", "training_data")
        self._detector.enable_roi_saving(roi_dir)

        self._session.start()
        self._paused_by_view_switch = False

        self._start_button.set_visible(False)
        self._timer_label.set_visible(True)
        self._incident_label.set_visible(True)
        self._stop_button.set_visible(True)
        self._banner.set_revealed(False)
        self._status_label.set_label("Kalibrierung \u2013 Mund bitte geschlossen halten")

        self._polling_id = GLib.timeout_add(33, self._poll_frame)

    def stop_training(self):
        if self._session.state == SessionState.IDLE:
            return

        if self._polling_id:
            GLib.source_remove(self._polling_id)
            self._polling_id = None

        result = self._session.stop()
        self._camera.stop()
        self._detector.disable_roi_saving()
        self._mpris.resume_paused()

        self._start_button.set_visible(True)
        self._timer_label.set_visible(False)
        self._incident_label.set_visible(False)
        self._stop_button.set_visible(False)
        self._banner.set_revealed(False)
        self._status_label.set_label("Bereit zum Training")

        if result["duration"] > 10:
            self._finish_session(result)

    def pause_training(self):
        if self._session.state == SessionState.IDLE:
            return
        if self._polling_id:
            GLib.source_remove(self._polling_id)
            self._polling_id = None
        self._camera.stop()
        self._mpris.resume_paused()
        self._paused_by_view_switch = True
        self._status_label.set_label("Training pausiert")

    def resume_training(self):
        if not self._paused_by_view_switch:
            return
        self._paused_by_view_switch = False
        self._camera.start()
        self._status_label.set_label("Training laeuft")
        self._polling_id = GLib.timeout_add(33, self._poll_frame)

    def _poll_frame(self) -> bool:
        frame = self._camera.get_frame()
        if frame is None:
            return True

        self._paintable.set_frame(frame)

        try:
            detection = self._detector.detect(frame)
        except Exception as e:
            print(f"Detektor-Fehler: {e}")
            return True

        if detection["face_detected"]:
            self._session.update(detection["tongue_out"])

            cal_state = detection["calibration_state"]
            if cal_state == CalibrationState.BASELINE:
                self._status_label.set_label("Kalibrierung \u2013 Mund bitte geschlossen halten")
            elif cal_state == CalibrationState.TONGUE_PROMPT:
                self._status_label.set_label("Zeig mal kurz die Zunge!")
            elif cal_state == CalibrationState.DONE and not detection["calibrated"]:
                ranges = self._detector._calibration.get_tongue_hsv_range()
                if ranges:
                    self._window.profile.calibration = ranges
                    self._window.save_profile()
            elif self._session.state == SessionState.RUNNING:
                self._status_label.set_label("Training laeuft")
            elif self._session.state == SessionState.DETECTED:
                remaining = self._session.remaining_resume
                if remaining > 0:
                    self._status_label.set_label(f"Film pausiert\u2026 noch {int(remaining)}\u202fs")
                else:
                    self._status_label.set_label("Zunge rein!")
            elif self._session.state == SessionState.COOLDOWN:
                remaining = self._session.remaining_cooldown
                self._status_label.set_label(f"Abklingzeit\u2026 {int(remaining)}\u202fs")
        else:
            self._session.update(False)
            if self._session.state == SessionState.RUNNING:
                self._status_label.set_label("Kein Gesicht erkannt")

        d = self._session.session_duration
        self._timer_label.set_label(f"{int(d) // 60:02d}:{int(d) % 60:02d}")
        self._incident_label.set_label(f"{self._session.incident_count} Vorfaelle")

        if self._session.session_failed:
            self._polling_id = None
            GLib.timeout_add(100, lambda: self.stop_training() or False)
            return False

        return True

    def _on_alarm(self):
        self._sound.beep()
        self._mpris.pause_all()
        self._banner.set_title("Zunge erkannt \u2014 Film pausiert")
        self._banner.set_revealed(True)

    def _on_alarm_end(self):
        self._mpris.resume_paused()
        self._banner.set_revealed(False)

    def _on_state_change(self, new_state):
        if new_state == SessionState.DETECTED:
            self._banner.set_title("Zunge erkannt \u2014 Film pausiert")
            self._banner.set_revealed(True)
        elif new_state in (SessionState.COOLDOWN, SessionState.RUNNING):
            self._banner.set_revealed(False)
        elif new_state == SessionState.IDLE:
            self._banner.set_revealed(False)

    def _finish_session(self, result: dict):
        profile = self._window.profile
        record = SessionRecord(
            timestamp=datetime.now().isoformat(),
            duration=result["duration"],
            incidents=result["incidents"],
            success=result["success"],
        )
        profile.sessions.append(record)
        profile.total_sessions += 1
        profile.total_training_time += result["duration"]
        profile.total_incidents += result["incidents"]
        if result["success"]:
            profile.successful_sessions += 1

        self._window.adaptive_difficulty.adjust_after_session(
            incidents=result["incidents"],
            duration_minutes=result["duration"] / 60.0,
        )
        profile.difficulty_params = self._window.adaptive_difficulty.to_dict()

        self._window.save_profile()
        self._window.refresh_pages()

        # Meilensteine pruefen
        new_milestones = self._window.milestone_system.check_milestones(profile)
        for ms in new_milestones:
            profile.milestones.append(ms)
            toast = Adw.Toast(title=f"Meilenstein: {ms.name}")
            toast.set_timeout(5)
            self._toast_overlay.add_toast(toast)
        if new_milestones:
            self._window.save_profile()

        # Streak aktualisieren
        self._window.streak_system.update_streak(profile)

        toast = Adw.Toast(title=f"Training beendet \u2014 {result['incidents']} Vorfaelle")
        toast.set_timeout(3)
        self._toast_overlay.add_toast(toast)

    def cleanup(self):
        self.stop_training()
        self._sound.cleanup()
        self._detector.cleanup()

    def update_settings(self):
        profile = self._window.profile
        self._camera.camera_index = profile.settings.get("camera_index", 0)
        self._sound.volume = profile.settings.get("volume", 0.5)
        self._sound.frequency = profile.settings.get("beep_frequency", 800)
