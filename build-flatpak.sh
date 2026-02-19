#!/bin/bash
# ZungenTrainer Flatpak Build-Skript
#
# Voraussetzungen:
#   flatpak install flathub org.gnome.Platform//49
#   flatpak install flathub org.gnome.Sdk//48
#   flatpak install flathub org.flatpak.Builder
#
# Verwendung:
#   ./build-flatpak.sh          # Baut und installiert lokal
#   ./build-flatpak.sh bundle   # Erstellt eine .flatpak Datei zum Weitergeben

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

BUILD_DIR="$SCRIPT_DIR/.flatpak-build"
REPO_DIR="$SCRIPT_DIR/.flatpak-repo"
APP_ID="de.yoshimintos.ZungenTrainer"

echo "=== ZungenTrainer Flatpak Build ==="

# Prüfe ob pip-cache existiert
if [ ! -d "flatpak/pip-cache" ] || [ -z "$(ls flatpak/pip-cache/*.whl 2>/dev/null)" ]; then
    echo ""
    echo "Lade Python-Abhängigkeiten herunter..."
    mkdir -p flatpak/pip-cache
    pip3 download \
        --dest flatpak/pip-cache \
        --only-binary=:all: \
        --python-version 313 \
        --platform manylinux_2_28_x86_64 \
        --platform manylinux_2_17_x86_64 \
        --platform manylinux2014_x86_64 \
        --platform linux_x86_64 \
        --platform any \
        "mediapipe>=0.10.30" numpy opencv-python-headless
    echo "Abhängigkeiten heruntergeladen."
fi

# OSTree-Repo initialisieren (mit min-free-space=0 für kleine Festplatten)
if [ ! -d "$REPO_DIR" ]; then
    flatpak run --command=ostree org.flatpak.Builder \
        init --repo="$REPO_DIR" --mode=archive-z2
    flatpak run --command=ostree org.flatpak.Builder \
        config set --repo="$REPO_DIR" core.min-free-space-percent 0
fi

echo ""
echo "Baue Flatpak..."
flatpak run org.flatpak.Builder \
    --force-clean \
    --disable-cache \
    --user \
    --install \
    --repo="$REPO_DIR" \
    "$BUILD_DIR" \
    flatpak/de.yoshimintos.ZungenTrainer.json

echo ""
echo "Flatpak installiert! Starten mit:"
echo "  flatpak run $APP_ID"

# Build-Artefakte aufräumen
rm -rf "$BUILD_DIR" .flatpak-builder

# Bundle erstellen wenn gewünscht
if [ "${1:-}" = "bundle" ]; then
    echo ""
    echo "Erstelle Bundle..."
    flatpak build-bundle "$REPO_DIR" \
        "ZungenTrainer.flatpak" \
        "$APP_ID"
    rm -rf "$REPO_DIR"
    SIZE=$(du -h ZungenTrainer.flatpak | cut -f1)
    echo ""
    echo "Bundle erstellt: ZungenTrainer.flatpak ($SIZE)"
    echo ""
    echo "Auf einem anderen Computer installieren mit:"
    echo "  flatpak install flathub org.gnome.Platform//49"
    echo "  flatpak install ZungenTrainer.flatpak"
fi
