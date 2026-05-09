#!/bin/bash
# ZungenTrainer Installation auf einem neuen Gerät
#
# Voraussetzungen:
#   - Flatpak installiert
#   - Internetzugang (für Runtime-Download, falls nötig)
#
# Verwendung:
#   ./install-remote.sh ZungenTrainer.flatpak
#
set -e

BUNDLE="${1:-ZungenTrainer.flatpak}"

if [ ! -f "$BUNDLE" ]; then
    echo "Fehler: $BUNDLE nicht gefunden"
    echo "Verwendung: $0 <pfad-zur-flatpak-datei>"
    exit 1
fi

echo "=== ZungenTrainer Installation ==="

# Runtime installieren falls nötig
if ! flatpak info org.gnome.Platform//49 &>/dev/null; then
    echo "Installiere GNOME Platform Runtime..."
    flatpak install --user -y flathub org.gnome.Platform//49
fi

echo "Installiere ZungenTrainer..."
flatpak install --user -y "$BUNDLE"

echo ""
echo "Installation abgeschlossen!"
echo "Starten mit: flatpak run de.yoshimintos.ZungenTrainer"
echo "Oder über die GNOME App-Übersicht suchen."
