"""Hauptfenster mit ViewStack-Navigation (3 Views)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

from pages.training_page import TrainingPage
from pages.progress_page import ProgressPage
from pages.settings_page import SettingsPage
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
        toolbar_view = self._toolbar_view
        self._toast_overlay.set_child(toolbar_view)

        header = Adw.HeaderBar()

        # Hamburger-Menue
        menu_model = Gio.Menu()
        menu_model.append("Ueber ZungenTrainer", "app.about")
        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_menu_model(menu_model)
        menu_button.set_tooltip_text("Hauptmenue")
        header.pack_end(menu_button)

        toolbar_view.add_top_bar(header)

        self.view_stack = Adw.ViewStack()
        self.view_stack.set_vexpand(True)
        toolbar_view.set_content(self.view_stack)

        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self.view_stack)
        toolbar_view.add_bottom_bar(switcher_bar)

        switcher_title = Adw.ViewSwitcherTitle()
        switcher_title.set_stack(self.view_stack)
        switcher_title.set_title("ZungenTrainer")
        header.set_title_widget(switcher_title)

        switcher_title.connect(
            "notify::title-visible",
            lambda st, _: switcher_bar.set_reveal(st.get_title_visible()),
        )

        self.training_page = TrainingPage(self)
        self.progress_page = ProgressPage(self)
        self.settings_page = SettingsPage(self)

        self.view_stack.add_titled_with_icon(
            self.training_page, "training", "Training", "camera-video-symbolic"
        )
        self.view_stack.add_titled_with_icon(
            self.progress_page, "progress", "Fortschritt", "starred-symbolic"
        )
        self.view_stack.add_titled_with_icon(
            self.settings_page, "settings", "Einstellungen", "preferences-system-symbolic"
        )

        # View-Wechsel: Training pausieren/fortsetzen
        self.view_stack.connect(
            "notify::visible-child",
            self._on_visible_child_changed,
        )

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

    def _on_visible_child_changed(self, stack, _param):
        visible = stack.get_visible_child()
        if visible == self.training_page:
            self.training_page.resume_training()
        else:
            self.training_page.pause_training()

    def toggle_training(self):
        """Space-Taste: Training starten oder stoppen."""
        from services.session_service import SessionState
        if self.training_page._session.state == SessionState.IDLE:
            self.view_stack.set_visible_child(self.training_page)
            self.training_page.start_training()
        else:
            self.training_page.stop_training()

    def save_profile(self):
        try:
            self.data_store.save(self.profile)
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")

    def refresh_pages(self):
        self.progress_page.refresh()
        self.settings_page.refresh()

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
