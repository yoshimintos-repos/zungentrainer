"""Hauptfenster fuer die unauffaellige Ueberwachung."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

from pages.training_page import TrainingPage
from models.persistence import DataStore
from systems.adaptive_difficulty import AdaptiveDifficulty
from systems.milestone_system import MilestoneSystem
from systems.streak_system import StreakSystem


class ZungenTrainerWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("ZungenTrainer")
        self.set_default_size(480, 700)
        self.set_size_request(360, 500)

        self.data_store = DataStore()
        self.profile = self.data_store.load()
        self.adaptive_difficulty = AdaptiveDifficulty.from_dict(
            self.profile.difficulty_params
        )
        self.milestone_system = MilestoneSystem()
        self.streak_system = StreakSystem()

        self._build_ui()
        self.connect("close-request", self._on_close)

        # Hintergrund-Modus: Fenster-Sichtbarkeit tracken
        self.connect("notify::is-active", self._on_active_changed)
        self._window_visible = True

        # Onboarding beim ersten Start
        if not self.profile.onboarding_done:
            self._show_onboarding()

    def show_toast(self, title: str, timeout: int = 3):
        """Zeigt einen Toast auf Window-Ebene (sichtbar auf jeder Page)."""
        toast = Adw.Toast(title=title)
        toast.set_timeout(timeout)
        self._toast_overlay.add_toast(toast)

    def _build_ui(self):
        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        self._toolbar_view = Adw.ToolbarView()
        self._toast_overlay.set_child(self._toolbar_view)

        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="ZungenTrainer"))

        # Hamburger-Menue
        menu_model = Gio.Menu()
        menu_model.append("Einstellungen", "win.settings")
        menu_model.append("Ueber ZungenTrainer", "app.about")
        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_menu_model(menu_model)
        menu_button.set_tooltip_text("Hauptmenue")
        header.pack_end(menu_button)

        self._toolbar_view.add_top_bar(header)

        self.training_page = TrainingPage(self)
        self._toolbar_view.set_content(self.training_page)

        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", lambda *_: self._show_settings_dialog())
        self.add_action(settings_action)

    def _show_onboarding(self):
        """Zeigt Onboarding statt ViewStack."""
        from pages.onboarding_page import OnboardingPage
        self._onboarding = OnboardingPage(self)
        # ViewStack verstecken, Onboarding zeigen
        self._toast_overlay.set_child(self._onboarding)

    def finish_onboarding(self):
        """Wechselt von Onboarding zum normalen ViewStack."""
        self._toast_overlay.set_child(self._toolbar_view)
        self._onboarding = None
        self.show_toast("Willkommen, " + self.profile.name + "!")

    def _show_settings_dialog(self):
        """Oeffnet die reduzierten Einstellungen aus dem Hauptmenue."""
        from pages.settings_page import SettingsPage

        settings_page = SettingsPage(self)
        dialog = Adw.Dialog()
        dialog.set_title("Einstellungen")
        dialog.set_content_width(500)
        dialog.set_content_height(600)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)
        toolbar.set_content(settings_page)
        dialog.set_child(toolbar)
        dialog.present(self)

    def toggle_training(self):
        """Space-Taste: Ueberwachung starten oder stoppen."""
        from services.session_service import SessionState
        if self.training_page._session.state == SessionState.IDLE:
            self.training_page.start_training()
        else:
            self.training_page.stop_training()

    def save_profile(self):
        try:
            self.data_store.save(self.profile)
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")

    def refresh_pages(self):
        pass

    def _on_active_changed(self, window, _param):
        """Fenster wurde aktiviert/deaktiviert (Minimize, Workspace-Wechsel)."""
        active = self.is_active()
        if active and not self._window_visible:
            # Fenster wieder sichtbar
            self._window_visible = True
            self.training_page.set_background_mode(False)
        elif not active and self._window_visible:
            # Fenster nicht mehr sichtbar
            self._window_visible = False
            self.training_page.set_background_mode(True)

    def _on_close(self, *args):
        self.training_page.cleanup()
        self.save_profile()
        return False
