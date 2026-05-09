"""JSON-basierte Datenspeicherung in XDG_DATA_HOME mit Schema-Versionierung."""

import json
import os
import shutil
import tempfile
from models.user_data import UserProfile


# Aktuelle Schema-Version. Bei jeder strukturellen Änderung am Profil-Format
# hochzählen und eine passende Migrationsfunktion hinzufügen.
CURRENT_SCHEMA = 1


def _migrate_v0_to_v1(data: dict) -> dict:
    """Migration v0 → v1: Veraltetes settings.sensitivity entfernen."""
    settings = data.get("settings", {})
    settings.pop("sensitivity", None)
    return data


# Migrationskette: (Quell-Version, Funktion)
_MIGRATIONS = [
    (0, _migrate_v0_to_v1),
]


def _migrate(data: dict) -> tuple[dict, bool]:
    """Wendet alle nötigen Migrationen sequenziell an.

    Returns:
        (migrierte Daten, ob eine Migration stattfand)
    """
    version = data.get("schema_version", 0)
    migrated = False
    for from_version, migrate_fn in _MIGRATIONS:
        if version <= from_version:
            data = migrate_fn(data)
            migrated = True
    data["schema_version"] = CURRENT_SCHEMA
    return data, migrated


def _backup(path: str, old_version: int):
    """Erstellt ein Backup der Profil-Datei vor der Migration."""
    if not os.path.exists(path):
        return
    backup_path = path.replace(".json", f".v{old_version}.json.bak")
    try:
        shutil.copy2(path, backup_path)
        print(f"Profil-Backup erstellt: {backup_path}")
    except OSError as e:
        print(f"Warnung: Backup konnte nicht erstellt werden: {e}")


class DataStore:
    """Speichert und lädt das Benutzerprofil als JSON."""

    def __init__(self):
        data_home = os.environ.get(
            "XDG_DATA_HOME",
            os.path.expanduser("~/.local/share"),
        )
        self._dir = os.path.join(data_home, "zungentrainer")
        self._path = os.path.join(self._dir, "profile.json")

    def load(self) -> UserProfile:
        """Lädt das Profil, führt ggf. Migrationen durch."""
        if not os.path.exists(self._path):
            return UserProfile()
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            old_version = data.get("schema_version", 0)
            data, migrated = _migrate(data)
            profile = UserProfile.from_dict(data)
            if migrated:
                _backup(self._path, old_version)
                self.save(profile)
                print(f"Profil von Schema v{old_version} auf v{CURRENT_SCHEMA} migriert.")
            return profile
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Fehler beim Laden des Profils: {e}")
            return UserProfile()

    def save(self, profile: UserProfile):
        """Speichert das Profil als JSON (atomar via temp-Datei + rename)."""
        os.makedirs(self._dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self._dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self._path)
        except Exception:
            # Temp-Datei aufräumen bei Fehler
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
