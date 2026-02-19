"""Sammlungs-Seite mit Abzeichen und Zungenfreunden."""

import math

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from gamification.badge_system import BadgeSystem
from gamification.creature_system import CreatureSystem, CREATURE_DEFS


class CollectionPage(Gtk.Box):
    """Zeigt freigeschaltete Abzeichen und Zungenfreunde-Galerie."""

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._window = main_window
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroll)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        scroll.set_child(clamp)

        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self._content.set_margin_top(24)
        self._content.set_margin_bottom(24)
        self._content.set_margin_start(16)
        self._content.set_margin_end(16)
        clamp.set_child(self._content)

        # Fortschrittsanzeige
        self._progress_label = Gtk.Label()
        self._progress_label.add_css_class("caption")
        self._progress_label.add_css_class("dim-label")
        self._progress_label.set_halign(Gtk.Align.CENTER)
        self._content.append(self._progress_label)

        # Zungenfreunde-Galerie
        creatures_group = Adw.PreferencesGroup()
        creatures_group.set_title("Zungenfreunde")
        self._content.append(creatures_group)

        self._creatures_grid = Gtk.FlowBox()
        self._creatures_grid.set_homogeneous(True)
        self._creatures_grid.set_min_children_per_line(3)
        self._creatures_grid.set_max_children_per_line(4)
        self._creatures_grid.set_column_spacing(12)
        self._creatures_grid.set_row_spacing(12)
        self._creatures_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        creatures_group.add(self._creatures_grid)

        # Abzeichen-Galerie
        badges_group = Adw.PreferencesGroup()
        badges_group.set_title("Abzeichen")
        self._content.append(badges_group)

        self._badges_list = Gtk.ListBox()
        self._badges_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._badges_list.add_css_class("boxed-list")
        badges_group.add(self._badges_list)

    def refresh(self):
        """Aktualisiert die Sammlungs-Anzeige."""
        profile = self._window.profile

        # Fortschritt
        unlocked_creatures = sum(1 for c in profile.creatures if c.unlocked)
        total_creatures = len(CREATURE_DEFS)
        unlocked_badges = sum(1 for b in profile.badges if b.unlocked)
        total_badges = len(BadgeSystem.all_badges())

        self._progress_label.set_label(
            f"Zungenfreunde: {unlocked_creatures}/{total_creatures}  \u00b7  "
            f"Abzeichen: {unlocked_badges}/{total_badges}"
        )

        # Kreaturen-Grid neu aufbauen
        while child := self._creatures_grid.get_first_child():
            self._creatures_grid.remove(child)

        unlocked_ids = {c.creature_id: c for c in profile.creatures if c.unlocked}

        for cid, name, desc, _, _ in CREATURE_DEFS:
            card = self._create_creature_card(cid, name, desc, unlocked_ids.get(cid))
            self._creatures_grid.append(card)

        # Abzeichen-Liste neu aufbauen
        while child := self._badges_list.get_first_child():
            self._badges_list.remove(child)

        unlocked_badge_ids = {b.badge_id for b in profile.badges if b.unlocked}

        for bid, name, desc in BadgeSystem.all_badges():
            row = Adw.ActionRow()
            row.set_title(name)
            row.set_subtitle(desc)

            if bid in unlocked_badge_ids:
                icon = Gtk.Image.new_from_icon_name("object-select-symbolic")
                icon.add_css_class("accent")
                row.add_prefix(icon)
            else:
                icon = Gtk.Image.new_from_icon_name("channel-secure-symbolic")
                icon.set_opacity(0.3)
                row.add_prefix(icon)
                row.set_sensitive(False)

            self._badges_list.append(row)

    def _create_creature_card(self, creature_id, name, desc, creature):
        """Erstellt eine Karte für eine Kreatur."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_halign(Gtk.Align.CENTER)
        box.set_size_request(100, 120)

        unlocked = creature is not None
        golden = creature.golden if creature else False

        # Cairo-Zeichenfläche
        drawing = Gtk.DrawingArea()
        drawing.set_size_request(80, 80)
        drawing.set_halign(Gtk.Align.CENTER)

        if unlocked:
            drawing.set_draw_func(
                self._draw_creature_func, (creature_id, golden)
            )
        else:
            drawing.set_draw_func(self._draw_locked_func, None)

        box.append(drawing)

        # Name
        label = Gtk.Label(label=name if unlocked else "???")
        label.add_css_class("caption")
        if not unlocked:
            label.set_opacity(0.4)
        box.append(label)

        return box

    @staticmethod
    def _draw_creature_func(area, cr, width, height, data):
        """Zeichnet eine freigeschaltete Kreatur."""
        creature_id, golden = data
        size = min(width, height) * 0.35
        CreatureSystem.draw_creature(
            cr, creature_id, width / 2, height / 2, size, golden
        )

    @staticmethod
    def _draw_locked_func(area, cr, width, height, _data):
        """Zeichnet einen gesperrten Platzhalter."""
        cx, cy = width / 2, height / 2
        size = min(width, height) * 0.3

        cr.set_source_rgba(0.5, 0.5, 0.5, 0.3)
        cr.arc(cx, cy, size, 0, 2 * math.pi)
        cr.fill()

        # Fragezeichen
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)
        cr.set_font_size(size * 0.8)
        cr.move_to(cx - size * 0.2, cy + size * 0.25)
        cr.show_text("?")
