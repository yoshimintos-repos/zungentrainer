"""JSON-basierte Datenspeicherung in XDG_DATA_HOME."""

import json
import os
import tempfile
from models.user_data import UserProfile


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
        """Lädt das Profil oder erstellt ein neues."""
        if not os.path.exists(self._path):
            return UserProfile()
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return UserProfile.from_dict(data)
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
