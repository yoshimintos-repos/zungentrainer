"""Zungenfreunde - Sammelbare Kreaturen mit Cairo-Zeichnungen."""

import math
from datetime import datetime
from models.user_data import Creature


# Kreatur-Definitionen: (id, name, beschreibung, freischalt-bedingung, farben)
CREATURE_DEFS = [
    (
        "schnecki",
        "Schnecki",
        "Eine fröhliche Schnecke die ihre Zunge immer drin behält",
        lambda p: p.level >= 1 and p.total_sessions >= 1,
        {"body": (0.45, 0.75, 0.35), "accent": (0.6, 0.85, 0.5)},
    ),
    (
        "froschli",
        "Fröschli",
        "Ein kleiner Frosch - Experte im Zunge-Kontrollieren",
        lambda p: p.level >= 2,
        {"body": (0.2, 0.7, 0.3), "accent": (0.3, 0.85, 0.4)},
    ),
    (
        "chameli",
        "Chameli",
        "Ein Chamäleon das seine Zunge perfekt beherrscht",
        lambda p: p.level >= 3,
        {"body": (0.3, 0.8, 0.6), "accent": (0.4, 0.9, 0.7)},
    ),
    (
        "eulchen",
        "Eulchen",
        "Eine weise Eule die über dein Training wacht",
        lambda p: p.level >= 4,
        {"body": (0.55, 0.4, 0.25), "accent": (0.75, 0.6, 0.35)},
    ),
    (
        "drachi",
        "Drachi",
        "Ein kleiner Drache - Feuer nur mit geschlossenem Mund!",
        lambda p: p.level >= 5,
        {"body": (0.85, 0.3, 0.2), "accent": (1.0, 0.5, 0.2)},
    ),
    (
        "pingui",
        "Pingui",
        "Ein eleganter Pinguin mit perfekter Haltung",
        lambda p: p.level >= 6,
        {"body": (0.2, 0.2, 0.3), "accent": (0.9, 0.9, 0.95)},
    ),
    (
        "koali",
        "Koali",
        "Ein entspannter Koala der geduldig trainiert",
        lambda p: p.level >= 7,
        {"body": (0.5, 0.5, 0.5), "accent": (0.7, 0.7, 0.7)},
    ),
    (
        "foxie",
        "Foxie",
        "Ein schlauer Fuchs mit scharfem Blick",
        lambda p: p.level >= 8,
        {"body": (0.9, 0.5, 0.1), "accent": (1.0, 0.7, 0.3)},
    ),
    (
        "phoenix",
        "Phoenix",
        "Ein mythischer Vogel - Symbol der Transformation",
        lambda p: p.level >= 9,
        {"body": (0.95, 0.3, 0.1), "accent": (1.0, 0.8, 0.0)},
    ),
    (
        "einhorn",
        "Einhorn",
        "Das legendäre Einhorn - nur die Besten schaffen es!",
        lambda p: p.level >= 10,
        {"body": (0.85, 0.75, 0.95), "accent": (0.95, 0.85, 1.0)},
    ),
    (
        "sternchen",
        "Sternchen",
        "Leuchtet bei 3 Tagen Streak auf",
        lambda p: p.best_streak >= 3,
        {"body": (1.0, 0.85, 0.0), "accent": (1.0, 0.95, 0.5)},
    ),
    (
        "regenbogi",
        "Regenbogi",
        "Erscheint nach 10 perfekten Sitzungen",
        lambda p: sum(1 for s in p.sessions if s.success and s.incidents == 0) >= 10,
        {"body": (0.8, 0.2, 0.4), "accent": (0.3, 0.6, 0.9)},
    ),
]


class CreatureSystem:
    """Verwaltet Zungenfreunde-Freischaltung und -Zeichnung."""

    def check_creatures(self, profile) -> list[Creature]:
        """Prüft und schaltet neue Kreaturen frei."""
        unlocked_ids = {c.creature_id for c in profile.creatures}
        newly_unlocked = []

        for cid, name, desc, condition_fn, colors in CREATURE_DEFS:
            if cid in unlocked_ids:
                continue
            if condition_fn(profile):
                creature = Creature(
                    creature_id=cid,
                    name=name,
                    description=desc,
                    unlocked=True,
                    unlocked_date=datetime.now().isoformat(),
                    golden=False,
                )
                profile.creatures.append(creature)
                newly_unlocked.append(creature)

        # Goldene Varianten für Streak-Erfolge
        self._check_golden(profile)

        return newly_unlocked

    def _check_golden(self, profile):
        """Schaltet goldene Varianten bei Streak-Meilensteinen frei.

        Pro 7 Tage Streak wird eine weitere Kreatur golden:
        7 Tage → 1 goldene, 14 Tage → 2 goldene, usw.
        """
        if profile.best_streak < 7:
            return
        allowed_golden = profile.best_streak // 7
        current_golden = sum(1 for c in profile.creatures if c.golden)
        for creature in profile.creatures:
            if current_golden >= allowed_golden:
                break
            if not creature.golden and creature.unlocked:
                creature.golden = True
                current_golden += 1

    @staticmethod
    def get_colors(creature_id: str) -> dict:
        """Gibt die Farbpalette einer Kreatur zurück."""
        for cid, _, _, _, colors in CREATURE_DEFS:
            if cid == creature_id:
                return colors
        return {"body": (0.5, 0.5, 0.5), "accent": (0.7, 0.7, 0.7)}

    @staticmethod
    def all_creatures() -> list[tuple[str, str, str]]:
        """Gibt alle möglichen Kreaturen zurück (id, name, beschreibung)."""
        return [(cid, name, desc) for cid, name, desc, _, _ in CREATURE_DEFS]

    @staticmethod
    def draw_creature(cr, creature_id: str, x: float, y: float,
                      size: float, golden: bool = False):
        """Zeichnet eine Kreatur mit Cairo.

        Args:
            cr: Cairo-Kontext
            creature_id: ID der Kreatur
            x, y: Mittelpunkt
            size: Größe (Radius)
            golden: Ob goldene Variante
        """
        colors = CreatureSystem.get_colors(creature_id)
        body_r, body_g, body_b = colors["body"]
        acc_r, acc_g, acc_b = colors["accent"]

        if golden:
            # Goldener Schimmer
            body_r = min(1.0, body_r + 0.3)
            body_g = min(1.0, body_g + 0.2)
            body_b = max(0.0, body_b - 0.1)

        # Goldener Hintergrund-Ring bei goldenen Varianten
        if golden:
            cr.set_source_rgba(1.0, 0.85, 0.0, 0.4)
            cr.arc(x, y, size * 1.2, 0, 2 * math.pi)
            cr.fill()

        # Körper (Kreis)
        cr.set_source_rgb(body_r, body_g, body_b)
        cr.arc(x, y, size, 0, 2 * math.pi)
        cr.fill()

        # Umriss
        cr.set_source_rgb(body_r * 0.6, body_g * 0.6, body_b * 0.6)
        cr.set_line_width(2)
        cr.arc(x, y, size, 0, 2 * math.pi)
        cr.stroke()

        # Augen
        eye_y = y - size * 0.2
        eye_dist = size * 0.3
        eye_r = size * 0.12

        cr.set_source_rgb(1, 1, 1)
        cr.arc(x - eye_dist, eye_y, eye_r, 0, 2 * math.pi)
        cr.fill()
        cr.arc(x + eye_dist, eye_y, eye_r, 0, 2 * math.pi)
        cr.fill()

        # Pupillen
        cr.set_source_rgb(0.1, 0.1, 0.1)
        pupil_r = eye_r * 0.6
        cr.arc(x - eye_dist, eye_y, pupil_r, 0, 2 * math.pi)
        cr.fill()
        cr.arc(x + eye_dist, eye_y, pupil_r, 0, 2 * math.pi)
        cr.fill()

        # Lächeln
        cr.set_source_rgb(body_r * 0.5, body_g * 0.5, body_b * 0.5)
        cr.set_line_width(1.5)
        smile_w = size * 0.35
        smile_y = y + size * 0.15
        cr.arc(x, smile_y, smile_w, 0.1 * math.pi, 0.9 * math.pi)
        cr.stroke()

        # Kreatur-spezifische Details
        _draw_creature_details(cr, creature_id, x, y, size, acc_r, acc_g, acc_b)


def _draw_creature_details(cr, creature_id, x, y, size, ar, ag, ab):
    """Zeichnet kreaturspezifische Details."""
    if creature_id == "schnecki":
        # Schneckenhaus (Spirale auf dem Kopf)
        cr.set_source_rgb(ar, ag, ab)
        cr.set_line_width(2)
        for i in range(20):
            angle = i * 0.5
            r = size * 0.1 + i * size * 0.02
            cx = x + math.cos(angle) * r
            cy = y - size * 0.6 + math.sin(angle) * r * 0.5
            if i == 0:
                cr.move_to(cx, cy)
            else:
                cr.line_to(cx, cy)
        cr.stroke()
        # Fühler
        cr.set_line_width(1.5)
        cr.move_to(x - size * 0.2, y - size * 0.8)
        cr.line_to(x - size * 0.3, y - size * 1.2)
        cr.stroke()
        cr.move_to(x + size * 0.2, y - size * 0.8)
        cr.line_to(x + size * 0.3, y - size * 1.2)
        cr.stroke()

    elif creature_id == "froschli":
        # Große Augen obendrauf
        cr.set_source_rgb(ar, ag, ab)
        for dx in (-0.3, 0.3):
            cr.arc(x + dx * size, y - size * 0.85, size * 0.2, 0, 2 * math.pi)
            cr.fill()

    elif creature_id == "chameli":
        # Spiralschwanz
        cr.set_source_rgb(ar, ag, ab)
        cr.set_line_width(3)
        for i in range(15):
            angle = i * 0.6
            r = size * 0.3 + i * size * 0.02
            cx = x + size * 0.8 + math.cos(angle) * r * 0.3
            cy = y + size * 0.3 + math.sin(angle) * r * 0.3
            if i == 0:
                cr.move_to(cx, cy)
            else:
                cr.line_to(cx, cy)
        cr.stroke()

    elif creature_id == "eulchen":
        # Federohren
        cr.set_source_rgb(ar, ag, ab)
        for dx in (-0.4, 0.4):
            cr.move_to(x + dx * size, y - size * 0.7)
            cr.line_to(x + dx * size * 0.8, y - size * 1.3)
            cr.line_to(x + dx * size * 1.2, y - size * 0.7)
            cr.fill()

    elif creature_id == "drachi":
        # Hörner
        cr.set_source_rgb(ar, ag, ab)
        for dx in (-0.35, 0.35):
            cr.move_to(x + dx * size, y - size * 0.8)
            cr.line_to(x + dx * size * 0.5, y - size * 1.4)
            cr.line_to(x + dx * size * 1.5, y - size * 0.9)
            cr.fill()
        # Flamme
        cr.set_source_rgba(1.0, 0.5, 0.0, 0.7)
        cr.arc(x, y + size * 0.7, size * 0.15, 0, 2 * math.pi)
        cr.fill()

    elif creature_id == "pingui":
        # Bauchfleck
        cr.set_source_rgb(ar, ag, ab)
        cr.save()
        cr.translate(x, y + size * 0.1)
        cr.scale(1.0, 1.3)
        cr.arc(0, 0, size * 0.55, 0, 2 * math.pi)
        cr.restore()
        cr.fill()

    elif creature_id == "koali":
        # Große runde Ohren
        cr.set_source_rgb(ar, ag, ab)
        for dx in (-0.7, 0.7):
            cr.arc(x + dx * size, y - size * 0.8, size * 0.3, 0, 2 * math.pi)
            cr.fill()
        # Kleine dunkle Ohrinnenkreise
        cr.set_source_rgb(ar * 0.5, ag * 0.5, ab * 0.5)
        for dx in (-0.7, 0.7):
            cr.arc(x + dx * size, y - size * 0.8, size * 0.15, 0, 2 * math.pi)
            cr.fill()
        # Große Nase
        cr.set_source_rgb(ar * 0.4, ag * 0.4, ab * 0.4)
        cr.save()
        cr.translate(x, y + size * 0.05)
        cr.scale(1.4, 1.0)
        cr.arc(0, 0, size * 0.22, 0, 2 * math.pi)
        cr.restore()
        cr.fill()

    elif creature_id == "foxie":
        # Spitze Ohren
        cr.set_source_rgb(ar, ag, ab)
        for dx in (-0.4, 0.4):
            cr.move_to(x + dx * size * 0.6, y - size * 0.7)
            cr.line_to(x + dx * size * 0.15, y - size * 1.45)
            cr.line_to(x + dx * size * 1.1, y - size * 0.8)
            cr.fill()
        # Innere Ohrfarbe (dunkler)
        cr.set_source_rgb(ar * 0.7, ag * 0.4, ab * 0.4)
        for dx in (-0.4, 0.4):
            cr.move_to(x + dx * size * 0.55, y - size * 0.75)
            cr.line_to(x + dx * size * 0.2, y - size * 1.3)
            cr.line_to(x + dx * size * 0.95, y - size * 0.85)
            cr.fill()
        # Buschiger Schwanz (rechts unten)
        cr.set_source_rgb(ar, ag, ab)
        cr.set_line_width(3)
        for i in range(10):
            angle = -0.3 + i * 0.15
            r = size * 0.5 + i * size * 0.04
            cx = x + size * 0.9 + math.cos(angle) * r * 0.5
            cy = y + size * 0.5 + math.sin(angle) * r * 0.8
            if i == 0:
                cr.move_to(cx, cy)
            else:
                cr.line_to(cx, cy)
        cr.stroke()

    elif creature_id == "einhorn":
        # Horn
        cr.set_source_rgb(1.0, 0.85, 0.0)
        cr.move_to(x, y - size * 1.5)
        cr.line_to(x - size * 0.15, y - size * 0.8)
        cr.line_to(x + size * 0.15, y - size * 0.8)
        cr.fill()

    elif creature_id == "sternchen":
        # Stern-Strahlen
        cr.set_source_rgba(ar, ag, ab, 0.6)
        cr.set_line_width(2)
        for i in range(8):
            angle = i * math.pi / 4
            inner = size * 1.1
            outer = size * 1.4
            cr.move_to(x + math.cos(angle) * inner, y + math.sin(angle) * inner)
            cr.line_to(x + math.cos(angle) * outer, y + math.sin(angle) * outer)
        cr.stroke()

    elif creature_id == "regenbogi":
        # Regenbogen-Bogen über dem Kopf
        cr.set_line_width(2)
        rainbow = [(1, 0, 0), (1, 0.5, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (0.5, 0, 0.8)]
        for i, (r, g, b) in enumerate(rainbow):
            cr.set_source_rgb(r, g, b)
            radius = size * 0.8 + i * 2
            cr.arc(x, y - size * 0.5, radius, math.pi, 2 * math.pi)
            cr.stroke()

    elif creature_id == "phoenix":
        # Flammen-Flügel
        cr.set_source_rgba(ar, ag, ab, 0.6)
        for dx in (-1, 1):
            cr.move_to(x + dx * size * 0.5, y)
            cr.line_to(x + dx * size * 1.5, y - size * 0.5)
            cr.line_to(x + dx * size * 1.2, y + size * 0.3)
            cr.fill()
