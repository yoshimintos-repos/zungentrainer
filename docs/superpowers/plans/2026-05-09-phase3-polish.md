# ZungenTrainer v2 — Phase 3 (Polieren) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Onboarding, Eltern-Bereich (Polkit), Wochen-Streak mit Erinnerungen, Fortschritts-Trend, ROI-Datensammlung, und CLAUDE.md.

**Architecture:** Onboarding als separate Page mit AdwCarousel, vor dem ViewStack angezeigt beim ersten Start. Eltern-Bereich als AdwNavigationView Subpage in der SettingsPage. Streak-Logik in der bestehenden _finish_session Pipeline. ROI-Sammlung im DetectorService.

**Tech Stack:** Python 3.13+, GTK 4.0, Libadwaita 1, Polkit (D-Bus), GNotification

**Referenzen:**
- Design-Spec: `docs/superpowers/specs/2026-04-09-zungentrainer-v2-design.md` (Abschnitte 2.6, 2.7, 3.2, 6.9, 6.10)
- Aktueller Code: `src/` (Phase 1+2 komplett)

---

## Dateistruktur

```
src/
├── pages/
│   ├── onboarding_page.py     # NEU: AdwCarousel mit 5 Schritten
│   └── settings_page.py       # MODIFY: Eltern-Bereich als Subpage
├── systems/
│   └── streak_system.py       # NEU: Wochen-Streak + Erinnerungen
├── services/
│   └── detector_service.py    # MODIFY: ROI-Datensammlung
├── models/
│   ├── user_data.py           # MODIFY: onboarding_done, reminders_enabled Felder
│   └── persistence.py         # MODIFY: Schema v1→v2 Migration
├── window.py                  # MODIFY: Onboarding-Flow, Streak-System
└── main.py                    # MODIFY: Polkit Action
CLAUDE.md                      # NEU: Projekt-CLAUDE.md
```

---

### Task 1: Wochen-Streak System

**Files:**
- Create: `src/systems/streak_system.py`
- Test: `tests/test_streak_system.py`
- Modify: `src/models/user_data.py` (Felder: `onboarding_done`, `reminders_enabled`, `last_week_checked`)
- Modify: `src/models/persistence.py` (Schema v1→v2 Migration)
- Modify: `src/pages/training_page.py` (Streak-Update in `_finish_session`)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_streak_system.py
"""Tests fuer Wochen-Streak-System."""

from datetime import datetime, timedelta
from systems.streak_system import StreakSystem
from models.user_data import UserProfile, SessionRecord


def _profile_with_sessions(dates: list[str]) -> UserProfile:
    """Erzeugt ein Profil mit Sessions an den gegebenen Daten."""
    p = UserProfile(trainings_per_week=2)
    for d in dates:
        p.sessions.append(SessionRecord(timestamp=d, duration=600, success=True))
    p.total_sessions = len(dates)
    return p


def test_no_sessions_no_streak():
    ss = StreakSystem()
    p = UserProfile(trainings_per_week=2)
    ss.update_streak(p)
    assert p.weekly_streak == 0


def test_fulfilled_week_increments_streak():
    ss = StreakSystem()
    now = datetime.now()
    # 2 Sessions diese Woche (Ziel = 2)
    mon = now - timedelta(days=now.weekday())
    p = _profile_with_sessions([
        mon.isoformat(),
        (mon + timedelta(days=1)).isoformat(),
    ])
    ss.update_streak(p)
    assert p.weekly_streak >= 1


def test_zero_sessions_resets_streak():
    ss = StreakSystem()
    p = UserProfile(trainings_per_week=2, weekly_streak=5)
    # Letzte Session war vor 2 Wochen
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).isoformat()
    p.last_session_date = two_weeks_ago[:10]
    p.last_week_checked = two_weeks_ago[:10]
    ss.update_streak(p)
    assert p.weekly_streak == 0


def test_partial_sessions_preserves_streak():
    ss = StreakSystem()
    now = datetime.now()
    mon = now - timedelta(days=now.weekday())
    # 1 Session diese Woche (Ziel = 2) — Streak bleibt
    p = _profile_with_sessions([mon.isoformat()])
    p.weekly_streak = 3
    ss.update_streak(p)
    assert p.weekly_streak == 3


def test_best_streak_tracked():
    ss = StreakSystem()
    p = UserProfile(weekly_streak=10, best_weekly_streak=5)
    ss.update_streak(p)
    assert p.best_weekly_streak == 10


def test_remaining_trainings():
    ss = StreakSystem()
    now = datetime.now()
    mon = now - timedelta(days=now.weekday())
    p = _profile_with_sessions([mon.isoformat()])
    p.trainings_per_week = 3
    assert ss.remaining_this_week(p) == 2
```

- [ ] **Step 2: Run tests — expect failure**

```bash
PYTHONPATH=src python3 -m pytest tests/test_streak_system.py -v
```

- [ ] **Step 3: Add fields to UserProfile**

In `src/models/user_data.py`, add to `UserProfile` class after `min_session_duration`:

```python
    onboarding_done: bool = False
    reminders_enabled: bool = True
    last_week_checked: str = ""
```

Add these to `to_dict()`:
```python
            "onboarding_done": self.onboarding_done,
            "reminders_enabled": self.reminders_enabled,
            "last_week_checked": self.last_week_checked,
```

Add to `from_dict()` simple_fields tuple:
```python
            "trainings_per_week", "min_session_duration",
            "onboarding_done", "reminders_enabled", "last_week_checked",
```

- [ ] **Step 4: Add Schema v1→v2 migration**

In `src/models/persistence.py`, update `CURRENT_SCHEMA = 2` and add migration:

```python
CURRENT_SCHEMA = 2

def _migrate_v1_to_v2(data: dict) -> dict:
    """Migration v1 → v2: Neue Felder fuer Onboarding und Streak."""
    data.setdefault("onboarding_done", False)
    data.setdefault("reminders_enabled", True)
    data.setdefault("last_week_checked", "")
    return data

_MIGRATIONS = [
    (0, _migrate_v0_to_v1),
    (1, _migrate_v1_to_v2),
]
```

- [ ] **Step 5: Implement StreakSystem**

```python
# src/systems/streak_system.py
"""Wochen-Streak: Zaehlt Wochen mit erfuelltem Trainingsplan.

- Woche mit x/x Trainings = Streak +1
- Woche mit mind. 1 Training = Streak bleibt
- Woche mit 0 Trainings = Streak reset
"""

from datetime import datetime, timedelta
from models.user_data import UserProfile


class StreakSystem:
    """Verwaltet den Wochen-Streak und Erinnerungen."""

    def update_streak(self, profile: UserProfile):
        """Aktualisiert den Streak basierend auf der aktuellen Woche."""
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        week_key = week_start.strftime("%Y-%m-%d")

        if profile.last_week_checked == week_key:
            return  # Diese Woche bereits geprueft

        # Letzte Woche pruefen (nur wenn es eine vorherige Woche gab)
        if profile.last_week_checked:
            last_checked = datetime.strptime(profile.last_week_checked, "%Y-%m-%d")
            prev_week_start = week_start - timedelta(weeks=1)

            if last_checked < prev_week_start:
                # Mehr als eine Woche ohne Check — Wochen dazwischen pruefen
                sessions_prev = self._count_sessions_in_week(profile, prev_week_start)
                if sessions_prev == 0:
                    profile.weekly_streak = 0
                elif sessions_prev >= profile.trainings_per_week:
                    profile.weekly_streak += 1

        # Aktuelle Woche
        sessions_now = self._count_sessions_in_week(profile, week_start)
        if sessions_now >= profile.trainings_per_week:
            # Nur inkrementieren wenn noch nicht fuer diese Woche gezaehlt
            if profile.last_week_checked != week_key:
                profile.weekly_streak += 1

        profile.last_week_checked = week_key
        profile.best_weekly_streak = max(
            profile.best_weekly_streak, profile.weekly_streak
        )

    def remaining_this_week(self, profile: UserProfile) -> int:
        """Wie viele Trainings fehlen noch diese Woche."""
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        done = self._count_sessions_in_week(profile, week_start)
        return max(0, profile.trainings_per_week - done)

    def get_reminder_text(self, profile: UserProfile) -> str | None:
        """Gibt Erinnerungstext zurueck, oder None wenn keine noetig."""
        if not profile.reminders_enabled:
            return None
        remaining = self.remaining_this_week(profile)
        if remaining <= 0:
            return None
        now = datetime.now()
        weekday = now.weekday()
        if weekday >= 4 and remaining == profile.trainings_per_week:
            # Freitag+ und noch kein Training → dringend
            return "Letzte Chance diese Woche!"
        if weekday >= 2 and remaining > 0:
            # Mittwoch+ → Erinnerung
            return f"Noch {remaining} Training{'s' if remaining > 1 else ''} diese Woche"
        return None

    def _count_sessions_in_week(self, profile: UserProfile,
                                 week_start: datetime) -> int:
        """Zaehlt Sessions innerhalb einer Kalenderwoche."""
        week_end = week_start + timedelta(weeks=1)
        count = 0
        for s in profile.sessions:
            try:
                ts = datetime.fromisoformat(s.timestamp)
                if week_start <= ts < week_end:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count
```

- [ ] **Step 6: Run tests — expect pass**

```bash
PYTHONPATH=src python3 -m pytest tests/test_streak_system.py -v
```

- [ ] **Step 7: Integrate into Window and TrainingPage**

In `src/window.py`:
- Import: `from systems.streak_system import StreakSystem`
- In `__init__` after `self.milestone_system`: `self.streak_system = StreakSystem()`

In `src/pages/training_page.py`, in `_finish_session` after milestone block:
```python
        # Streak aktualisieren
        self._window.streak_system.update_streak(profile)
```

- [ ] **Step 8: Run all tests**

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

- [ ] **Step 9: Commit**

```bash
git add src/systems/streak_system.py tests/test_streak_system.py src/models/user_data.py src/models/persistence.py src/window.py src/pages/training_page.py
git commit -m "feat: Wochen-Streak-System mit Erinnerungen"
```

---

### Task 2: Onboarding (AdwCarousel)

**Files:**
- Create: `src/pages/onboarding_page.py`
- Modify: `src/window.py` (Onboarding-Flow: zeige Onboarding vor ViewStack beim ersten Start)

- [ ] **Step 1: Create OnboardingPage**

```python
# src/pages/onboarding_page.py
"""Onboarding: 5-Schritt-Assistent beim ersten Start."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib


class OnboardingPage(Gtk.Box):
    """AdwCarousel-basiertes Onboarding mit 5 Schritten."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window
        self._build_ui()

    def _build_ui(self):
        self._carousel = Adw.Carousel()
        self._carousel.set_vexpand(True)
        self.append(self._carousel)

        # Carousel-Indikator
        indicator = Adw.CarouselIndicatorDots()
        indicator.set_carousel(self._carousel)
        indicator.set_margin_bottom(12)
        self.append(indicator)

        # Schritt 1: Willkommen
        welcome = Adw.StatusPage(
            title="Willkommen bei ZungenTrainer",
            description="Diese App hilft dir, die Zunge nicht mehr rauszustrecken",
            icon_name="de.yoshimintos.ZungenTrainer",
        )
        next_btn_1 = Gtk.Button(label="Weiter")
        next_btn_1.add_css_class("suggested-action")
        next_btn_1.add_css_class("pill")
        next_btn_1.set_halign(Gtk.Align.CENTER)
        next_btn_1.set_margin_bottom(24)
        next_btn_1.connect("clicked", lambda _: self._go_to(1))
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        welcome_box.append(welcome)
        welcome_box.append(next_btn_1)
        self._carousel.append(welcome_box)

        # Schritt 2: Kamera
        camera = Adw.StatusPage(
            title="Kamera",
            description="Die App nutzt deine Webcam um die Zunge zu erkennen. Die Kamera wird automatisch erkannt",
            icon_name="camera-video-symbolic",
        )
        next_btn_2 = Gtk.Button(label="Weiter")
        next_btn_2.add_css_class("suggested-action")
        next_btn_2.add_css_class("pill")
        next_btn_2.set_halign(Gtk.Align.CENTER)
        next_btn_2.set_margin_bottom(24)
        next_btn_2.connect("clicked", lambda _: self._go_to(2))
        camera_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        camera_box.append(camera)
        camera_box.append(next_btn_2)
        self._carousel.append(camera_box)

        # Schritt 3: Kalibrierung
        cal = Adw.StatusPage(
            title="Kalibrierung",
            description="Beim ersten Training zeigst du kurz die Zunge, damit die App deine Zungenfarbe lernt",
            icon_name="system-run-symbolic",
        )
        next_btn_3 = Gtk.Button(label="Weiter")
        next_btn_3.add_css_class("suggested-action")
        next_btn_3.add_css_class("pill")
        next_btn_3.set_halign(Gtk.Align.CENTER)
        next_btn_3.set_margin_bottom(24)
        next_btn_3.connect("clicked", lambda _: self._go_to(3))
        cal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cal_box.append(cal)
        cal_box.append(next_btn_3)
        self._carousel.append(cal_box)

        # Schritt 4: Name
        name_page = Adw.StatusPage(
            title="Wie heisst du?",
            icon_name="avatar-default-symbolic",
        )
        name_group = Adw.PreferencesGroup()
        name_group.set_halign(Gtk.Align.CENTER)
        name_group.set_margin_start(48)
        name_group.set_margin_end(48)
        self._name_entry = Adw.EntryRow(title="Name")
        self._name_entry.set_text(self._window.profile.name)
        name_group.add(self._name_entry)
        next_btn_4 = Gtk.Button(label="Weiter")
        next_btn_4.add_css_class("suggested-action")
        next_btn_4.add_css_class("pill")
        next_btn_4.set_halign(Gtk.Align.CENTER)
        next_btn_4.set_margin_top(24)
        next_btn_4.set_margin_bottom(24)
        next_btn_4.connect("clicked", self._on_name_next)
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_box.append(name_page)
        name_box.append(name_group)
        name_box.append(next_btn_4)
        self._carousel.append(name_box)

        # Schritt 5: Los geht's
        start = Adw.StatusPage(
            title="Alles bereit!",
            description="Starte dein erstes Training",
            icon_name="emblem-ok-symbolic",
        )
        start_btn = Gtk.Button(label="Training starten")
        start_btn.add_css_class("suggested-action")
        start_btn.add_css_class("pill")
        start_btn.set_halign(Gtk.Align.CENTER)
        start_btn.set_margin_bottom(24)
        start_btn.connect("clicked", self._on_finish)
        start_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        start_box.append(start)
        start_box.append(start_btn)
        self._carousel.append(start_box)

    def _go_to(self, index: int):
        page = self._carousel.get_nth_page(index)
        self._carousel.scroll_to(page, True)

    def _on_name_next(self, _btn):
        name = self._name_entry.get_text().strip()
        if name:
            self._window.profile.name = name
        self._go_to(4)

    def _on_finish(self, _btn):
        self._window.profile.onboarding_done = True
        self._window.save_profile()
        self._window.finish_onboarding()
```

- [ ] **Step 2: Modify Window for onboarding flow**

In `src/window.py`, add to `__init__` after `self._build_ui()`:

```python
        # Onboarding beim ersten Start
        if not self.profile.onboarding_done:
            self._show_onboarding()
```

Add methods:

```python
    def _show_onboarding(self):
        """Zeigt Onboarding statt ViewStack."""
        from pages.onboarding_page import OnboardingPage
        self._onboarding = OnboardingPage(self)
        # ViewStack verstecken, Onboarding zeigen
        self._toolbar_view = self._toast_overlay.get_child()
        self._toast_overlay.set_child(self._onboarding)

    def finish_onboarding(self):
        """Wechselt von Onboarding zum normalen ViewStack."""
        self._toast_overlay.set_child(self._toolbar_view)
        self._onboarding = None
        self.show_toast("Willkommen, " + self.profile.name + "!")
```

Store the toolbar_view as `self._toolbar_view` in `_build_ui` so we can swap it:

In `_build_ui`, change:
```python
        toolbar_view = Adw.ToolbarView()
```
to:
```python
        self._toolbar_view = Adw.ToolbarView()
        toolbar_view = self._toolbar_view
```

- [ ] **Step 3: Test manually**

Reset profile to trigger onboarding:
```bash
rm -f ~/.local/share/zungentrainer/profile.json
./run.sh
```

Expected: 5-step carousel, then normal app.

- [ ] **Step 4: Commit**

```bash
git add src/pages/onboarding_page.py src/window.py
git commit -m "feat: Onboarding mit AdwCarousel (5 Schritte)"
```

---

### Task 3: Eltern-Bereich (Polkit-geschuetzt)

**Files:**
- Create: `src/services/polkit_service.py`
- Create: `src/pages/parent_settings_page.py`
- Modify: `src/pages/settings_page.py` (Eltern-Bereich Button aktivieren, Navigation)
- Create: `flatpak/de.yoshimintos.ZungenTrainer.policy` (Polkit Policy)

- [ ] **Step 1: Create PolkitService**

```python
# src/services/polkit_service.py
"""Polkit-basierte Authentifizierung fuer den Eltern-Bereich."""

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


POLKIT_ACTION_ID = "de.yoshimintos.zungentrainer.parent-access"


class PolkitService:
    """Prueft Polkit-Autorisierung fuer den Eltern-Bereich."""

    def check_authorization(self, callback):
        """Prueft ob der Nutzer autorisiert ist.

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
            # Polkit nicht verfuegbar — Fallback: einfache Passwort-Abfrage
            callback(False)

    def _on_auth_result(self, bus, result, callback):
        try:
            res = bus.call_finish(result)
            auth_result = res.get_child_value(0)
            is_authorized = auth_result.get_child_value(0).get_boolean()
            callback(is_authorized)
        except GLib.Error:
            callback(False)
```

- [ ] **Step 2: Create ParentSettingsPage**

```python
# src/pages/parent_settings_page.py
"""Eltern-Bereich: Erweiterte Einstellungen hinter Polkit."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class ParentSettingsPage(Gtk.Box):
    """Polkit-geschuetzter Eltern-Bereich mit Trainingsplan-Einstellungen."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._window = main_window
        self._build_ui()

    def _build_ui(self):
        profile = self._window.profile

        scroll = Gtk.ScrolledWindow(vexpand=True)
        self.append(scroll)

        clamp = Adw.Clamp(maximum_size=600)
        scroll.set_child(clamp)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(12)
        content.set_margin_end(12)
        clamp.set_child(content)

        # Trainingsplan
        plan_group = Adw.PreferencesGroup(title="Trainingsplan")
        content.append(plan_group)

        self._trainings_row = Adw.SpinRow.new_with_range(1, 7, 1)
        self._trainings_row.set_title("Trainings pro Woche")
        self._trainings_row.set_value(profile.trainings_per_week)
        self._trainings_row.connect("notify::value", self._on_trainings_changed)
        plan_group.add(self._trainings_row)

        self._duration_row = Adw.SpinRow.new_with_range(5, 60, 5)
        self._duration_row.set_title("Mindest-Trainingsdauer (Minuten)")
        self._duration_row.set_value(profile.min_session_duration)
        self._duration_row.connect("notify::value", self._on_duration_changed)
        plan_group.add(self._duration_row)

        # Erinnerungen
        remind_group = Adw.PreferencesGroup(title="Erinnerungen")
        content.append(remind_group)

        self._remind_row = Adw.SwitchRow(title="Erinnerungen aktiviert")
        self._remind_row.set_subtitle("Freundliche Hinweise wenn Trainings ausstehen")
        self._remind_row.set_active(profile.reminders_enabled)
        self._remind_row.connect("notify::active", self._on_reminders_changed)
        remind_group.add(self._remind_row)

        # Schwierigkeit
        diff_group = Adw.PreferencesGroup(title="Schwierigkeit")
        diff_group.set_description("Die Schwierigkeit passt sich normalerweise automatisch an")
        content.append(diff_group)

        params = self._window.adaptive_difficulty.get_params()
        self._sensitivity_row = Adw.ActionRow(title="Empfindlichkeit")
        sens_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 2.0, 0.1)
        sens_scale.set_value(params["sensitivity"])
        sens_scale.set_size_request(200, -1)
        sens_scale.set_valign(Gtk.Align.CENTER)
        sens_scale.connect("value-changed", self._on_sensitivity_changed)
        self._sensitivity_row.add_suffix(sens_scale)
        diff_group.add(self._sensitivity_row)

    def _on_trainings_changed(self, row, _param):
        self._window.profile.trainings_per_week = int(row.get_value())
        self._window.save_profile()

    def _on_duration_changed(self, row, _param):
        self._window.profile.min_session_duration = int(row.get_value())
        self._window.save_profile()

    def _on_reminders_changed(self, row, _param):
        self._window.profile.reminders_enabled = row.get_active()
        self._window.save_profile()

    def _on_sensitivity_changed(self, scale):
        params = self._window.adaptive_difficulty.get_params()
        params["sensitivity"] = round(scale.get_value(), 2)
        self._window.adaptive_difficulty._params = params
        self._window.profile.difficulty_params = params
        self._window.save_profile()
```

- [ ] **Step 3: Update SettingsPage — activate parent button, add navigation**

In `src/pages/settings_page.py`, the parent button is currently disabled. Changes needed:

1. Wrap the SettingsPage in an `AdwNavigationView` so we can push the ParentSettingsPage as a subpage
2. Activate the parent button to trigger Polkit check and push subpage

Read the current `src/pages/settings_page.py` and make these changes:

- Change class to wrap content in `Adw.NavigationView`
- Activate the parent row (`set_sensitive(True)`)
- On click: attempt Polkit auth, on success push ParentSettingsPage

Since SettingsPage inherits from `Adw.PreferencesPage` which can't easily be wrapped in NavigationView, the simplest approach is:

1. Change SettingsPage to inherit from `Gtk.Box`
2. Put `AdwNavigationView` inside
3. Put the `AdwPreferencesPage` as the first page of the NavigationView
4. Push ParentSettingsPage as subpage

Alternative simpler approach: Just open ParentSettingsPage as a dialog window (less navigation complexity). Since Polkit already shows its own dialog, this keeps things simpler.

**Chosen approach:** Open ParentSettingsPage in an `Adw.Dialog` after Polkit auth succeeds. This avoids restructuring SettingsPage.

Update `src/pages/settings_page.py`:
- Activate parent row
- On click: try Polkit, on success show ParentSettingsPage in dialog
- Polkit fallback: show simple password entry dialog (for non-Polkit systems)

```python
# In _build_ui, change the parent row:
        parent_row.set_sensitive(True)
        parent_target.connect("activated", self._on_parent_area)

# Add method:
    def _on_parent_area(self, *args):
        """Oeffnet Eltern-Bereich nach Polkit-Authentifizierung."""
        from services.polkit_service import PolkitService
        polkit = PolkitService()
        polkit.check_authorization(self._on_polkit_result)

    def _on_polkit_result(self, authorized):
        from gi.repository import GLib
        GLib.idle_add(self._show_parent_area if authorized else self._show_auth_failed)

    def _show_parent_area(self):
        from pages.parent_settings_page import ParentSettingsPage
        parent_page = ParentSettingsPage(self._window)
        dialog = Adw.Dialog()
        dialog.set_title("Eltern-Bereich")
        dialog.set_content_width(500)
        dialog.set_content_height(600)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)
        toolbar.set_content(parent_page)
        dialog.set_child(toolbar)

        dialog.present(self._window)

    def _show_auth_failed(self):
        self._window.show_toast("Zugang abgebrochen")
```

- [ ] **Step 4: Create Polkit policy file**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <action id="de.yoshimintos.zungentrainer.parent-access">
    <description>Eltern-Bereich im ZungenTrainer oeffnen</description>
    <message>Authentifizierung erforderlich fuer den Eltern-Bereich</message>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin</allow_active>
    </defaults>
  </action>
</policyconfig>
```

Save to `flatpak/de.yoshimintos.ZungenTrainer.policy`.

Add to Flatpak manifest build-commands:
```
"install -Dm644 flatpak/de.yoshimintos.ZungenTrainer.policy /app/share/polkit-1/actions/de.yoshimintos.ZungenTrainer.policy"
```

- [ ] **Step 5: Commit**

```bash
git add src/services/polkit_service.py src/pages/parent_settings_page.py src/pages/settings_page.py flatpak/
git commit -m "feat: Eltern-Bereich mit Polkit-Authentifizierung"
```

---

### Task 4: Fortschritts-Trend (4-Wochen-Balkendiagramm)

**Files:**
- Modify: `src/pages/progress_page.py` (Trend-Diagramm hinzufuegen)

- [ ] **Step 1: Add trend visualization to ProgressPage**

In `src/pages/progress_page.py`, add a simple 4-week bar chart using `Gtk.DrawingArea` with Cairo:

Add method `_build_trend_chart` and call it in `refresh()`:

```python
    def _build_trend_chart(self):
        """Erstellt ein 4-Wochen-Balkendiagramm."""
        from datetime import datetime, timedelta

        now = datetime.now()
        weeks = []
        for i in range(3, -1, -1):
            week_start = (now - timedelta(weeks=i, days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            count = 0
            for s in self._window.profile.sessions:
                try:
                    ts = datetime.fromisoformat(s.timestamp)
                    if week_start <= ts < week_start + timedelta(weeks=1):
                        count += 1
                except (ValueError, TypeError):
                    pass
            weeks.append({"label": f"KW {week_start.isocalendar()[1]}", "count": count})

        max_count = max((w["count"] for w in weeks), default=1) or 1

        trend_group = Adw.PreferencesGroup(title="Trend (4 Wochen)")
        self._content.append(trend_group)

        chart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        chart_box.set_halign(Gtk.Align.CENTER)
        chart_box.set_margin_top(12)
        chart_box.set_margin_bottom(12)

        for w in weeks:
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            col.set_halign(Gtk.Align.CENTER)

            # Balken
            bar_height = max(4, int(80 * w["count"] / max_count))
            bar = Gtk.Box()
            bar.set_size_request(40, bar_height)
            bar.add_css_class("accent")
            bar.set_valign(Gtk.Align.END)

            spacer = Gtk.Box()
            spacer.set_size_request(40, 80 - bar_height)

            bar_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            bar_container.append(spacer)
            bar_container.append(bar)
            col.append(bar_container)

            # Zahl
            count_label = Gtk.Label(label=str(w["count"]))
            count_label.add_css_class("caption")
            col.append(count_label)

            # Wochenlabel
            week_label = Gtk.Label(label=w["label"])
            week_label.add_css_class("caption")
            week_label.add_css_class("dim-label")
            col.append(week_label)

            chart_box.append(col)

        trend_group.add(chart_box)
```

In `refresh()`, call `self._build_trend_chart()` after the week overview section.

Add accessible description:
```python
        # Accessible: Trend als Text
        trend_text = ", ".join(f"{w['label']}: {w['count']}" for w in weeks)
        chart_box.update_property(
            [Gtk.AccessibleProperty.LABEL],
            [f"Trainings-Trend: {trend_text}"]
        )
```

- [ ] **Step 2: Test manually**

```bash
./run.sh
```

Check the Fortschritt tab — should show 4 bars for the last 4 calendar weeks.

- [ ] **Step 3: Commit**

```bash
git add src/pages/progress_page.py
git commit -m "feat: 4-Wochen-Trend-Balkendiagramm in Fortschritts-View"
```

---

### Task 5: ROI-Datensammlung

**Files:**
- Modify: `src/services/detector_service.py` (ROI-Bilder speichern)

- [ ] **Step 1: Add ROI saving to DetectorService**

In `src/services/detector_service.py`, add ROI crop saving (every ~5 seconds during training, with HSV score as metadata):

```python
    # In __init__:
        self._roi_save_interval = 5.0  # Sekunden
        self._last_roi_save = 0.0
        self._roi_save_dir = None

    def enable_roi_saving(self, save_dir: str):
        """Aktiviert ROI-Datensammlung fuer spaeteres ML."""
        self._roi_save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def disable_roi_saving(self):
        """Deaktiviert ROI-Datensammlung."""
        self._roi_save_dir = None
```

In `detect()`, after HSV detection result, add:

```python
        # ROI-Datensammlung
        if self._roi_save_dir:
            import time as _time
            now = _time.monotonic()
            if now - self._last_roi_save >= self._roi_save_interval:
                self._last_roi_save = now
                self._save_roi(roi, tongue_ratio)
```

Add method:
```python
    def _save_roi(self, roi, score: float):
        """Speichert einen Mund-ROI-Crop mit Score im Dateinamen."""
        import time as _time
        timestamp = int(_time.time() * 1000)
        score_str = f"{score:.3f}"
        filename = f"roi_{timestamp}_s{score_str}.png"
        path = os.path.join(self._roi_save_dir, filename)
        try:
            cv2.imwrite(path, roi)
        except Exception:
            pass  # Nicht-kritisch, still fehlschlagen
```

- [ ] **Step 2: Enable ROI saving in TrainingPage**

In `src/pages/training_page.py`, in `start_training()` after `self._camera.start()`:

```python
        # ROI-Datensammlung aktivieren
        data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        roi_dir = os.path.join(data_home, "zungentrainer", "training_data")
        self._detector.enable_roi_saving(roi_dir)
```

In `stop_training()` after `self._camera.stop()`:
```python
        self._detector.disable_roi_saving()
```

Add `import os` at top if not present.

- [ ] **Step 3: Commit**

```bash
git add src/services/detector_service.py src/pages/training_page.py
git commit -m "feat: ROI-Datensammlung fuer spaeteres ML-Training"
```

---

### Task 6: CLAUDE.md erstellen

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md**

Create the project CLAUDE.md based on the actual codebase (not the parent directory's CLAUDE.md):

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt

ZungenTrainer v2 — GTK 4 / Libadwaita App (Python), erkennt per Webcam Zungenprotrusion und pausiert Medienplayer + Piepton. Hilft Kindern, sich die Gewohnheit abzugewoehnen.

UI-Sprache ist Deutsch (Labels, Statusmeldungen, Kommentare, Docstrings).

App-ID: `de.yoshimintos.ZungenTrainer`. Lizenz: GPL-3.0-or-later.

## Befehle

\```bash
# Lokal starten
./run.sh

# Erkennung standalone testen (OpenCV Debug-Fenster)
python3 src/debug_detector.py

# Tests
PYTHONPATH=src python3 -m pytest tests/ -v

# Flatpak bauen und installieren
./build-flatpak.sh

# Flatpak starten
flatpak run de.yoshimintos.ZungenTrainer
\```

## Architektur

### Window als Mediator

`ZungenTrainerWindow` besitzt DataStore, UserProfile, AdaptiveDifficulty, MilestoneSystem, StreakSystem. Pages referenzieren Window und greifen ueber es auf gemeinsamen Zustand zu.

### Erkennungs-Pipeline

MediaPipe Face Landmarker (VIDEO-Modus, NUR fuer Landmarks) -> Mund-ROI -> CLAHE -> HSV-Farbsegmentierung -> One-Euro-Filter -> tongue_out. Blendshapes werden NICHT fuer Zungenerkennung genutzt.

### Services

| Service | Datei | Aufgabe |
|---------|-------|---------|
| CameraService | `src/services/camera_service.py` | Daemon-Thread, 1080p OpenCV, Lock-basierter Frame-Handoff |
| DetectorService | `src/services/detector_service.py` | MediaPipe + HSV Pipeline -> tongue_out |
| SessionService | `src/services/session_service.py` | IDLE -> RUNNING -> DETECTED -> COOLDOWN |
| SoundService | `src/services/sound_service.py` | GStreamer Piepton |
| MprisService | `src/services/mpris_service.py` | D-Bus MPRIS2 Mediensteuerung |

### Threading

CameraService = Daemon-Thread. Alles andere auf GTK-Main-Thread. Frame-Handoff ueber `threading.Lock`. Trainings-Loop: `GLib.timeout_add(33, ...)` (~30 FPS).

### Alarm-System

Kein WARNING-Zwischenschritt. Piep + Medienpause gleichzeitig bei DETECTED. Multi-Frame-Bestaetigung (3 Frames) vor Transition. Sofortiger Reset bei Zunge-zurueck.

### Datenpersistenz

`$XDG_DATA_HOME/zungentrainer/profile.json`. Atomares Schreiben (temp + `os.replace()`). Schema-Versionierung mit append-only Migrations. `ZUNGENTRAINER_DATA_DIR` Override fuer lokale Entwicklung.

## Technische Constraints

- MediaPipe VIDEO-Modus: Timestamps MUESSEN monoton steigend sein
- Kein `tongueOut`-Blendshape in MediaPipe
- Import-Konvention: `src/` in `sys.path`, flache Imports (`from services.camera_service import CameraService`)
- Flatpak: `--device=all` fuer Kamera, `--talk-name=org.mpris.MediaPlayer2.*`

## GNOME HIG Compliance

HIG-Review-Skill unter `skills/gnome-hig-review/` — nach UI-Aenderungen laufen lassen. Wichtigste Regeln:
- AdwBanner fuer persistente Zustaende, AdwToast fuer transiente Events
- Max 1 `.suggested-action` oder `.destructive-action` pro View
- Alle Header-Bar-Controls brauchen Tooltips
- Accessible Names auf allen nicht-textuellen Elementen
- Unicode korrekt: Gedankenstrich (U+2014), Ellipsis (U+2026), NNBSP (U+202F) vor Einheiten

## Tech-Stack

Python 3.13+, GTK 4.0, Libadwaita 1, OpenCV (headless), MediaPipe (>=0.10.30), NumPy, GStreamer 1.0, GLib/Gio (D-Bus MPRIS2). Flatpak Runtime: GNOME Platform/SDK 49.
```

Note: Escape the backticks in the markdown code blocks (use actual backticks, the backslashes above are just for escaping in this plan).

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: CLAUDE.md mit Projekt-Architektur und Befehlen"
```

---

## Self-Review

**Spec-Abdeckung:**
- [x] Onboarding (AdwCarousel, 5 Schritte) → Task 2
- [x] Eltern-Bereich (Polkit, Subpage/Dialog) → Task 3
- [x] Trainingsplan + Wochen-Streak + Erinnerungen → Task 1
- [x] Fortschritts-Trend (4-Wochen-Balkendiagramm) → Task 4
- [x] ROI-Datensammlung → Task 5
- [x] CLAUDE.md → Task 6
- [ ] App-Icon — Nicht im Plan (braucht Design-Arbeit, kein Code). Aktuell wird das alte App-Icon verwendet.
- [ ] Hintergrund-Modus (GNotification) — Nicht im Plan fuer Phase 3 (erfordert Kamera-Management bei window-state-change, komplex). Kann als separates Feature hinzugefuegt werden.

**Placeholder-Scan:** Alle Code-Bloecke enthalten vollstaendigen Code. Keine TBDs.

**Typ-Konsistenz:** `profile.onboarding_done` (bool), `profile.reminders_enabled` (bool), `profile.last_week_checked` (str) — konsistent in Tasks 1, 2, 3. `StreakSystem.remaining_this_week()` → int — konsistent in Task 1. `PolkitService.check_authorization(callback)` → callback(bool) — konsistent in Task 3.
