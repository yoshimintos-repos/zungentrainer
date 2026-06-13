#!/usr/bin/env bash
# ZungenTrainer Flatpak Build-Skript
#
# Verwendung:
#   ./build-flatpak.sh build         # Abhaengigkeiten pruefen, bauen, lokal installieren
#   ./build-flatpak.sh bundle        # Bauen, installieren und ZungenTrainer.flatpak erstellen
#   ./build-flatpak.sh deps          # Fehlende Python-Wheels herunterladen
#   ./build-flatpak.sh deps-refresh  # Wheel-Cache neu erstellen
#   ./build-flatpak.sh clean         # Lokale Build-Artefakte entfernen
#
# Ohne Argument wird "build" ausgefuehrt.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_ID="de.yoshimintos.ZungenTrainer"
RUNTIME="org.gnome.Platform//49"
SDK="org.gnome.Sdk//49"
BUILDER_APP="org.flatpak.Builder"
MANIFEST="flatpak/de.yoshimintos.ZungenTrainer.json"
REQUIREMENTS="flatpak/requirements.txt"
PIP_CACHE="flatpak/pip-cache"
BUILD_DIR="$SCRIPT_DIR/.flatpak-build"
REPO_DIR="$SCRIPT_DIR/.flatpak-repo"
BUNDLE_FILE="ZungenTrainer.flatpak"

usage() {
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
}

die() {
    echo "Fehler: $*" >&2
    exit 1
}

need_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "'$1' ist nicht installiert"
}

check_flatpak_ref() {
    local ref="$1"
    flatpak info "$ref" >/dev/null 2>&1 || die "Flatpak-Ref fehlt: $ref"
}

preflight() {
    need_cmd flatpak
    need_cmd python3
    [ -f "$MANIFEST" ] || die "Manifest fehlt: $MANIFEST"
    [ -f "$REQUIREMENTS" ] || die "Requirements fehlen: $REQUIREMENTS"
    [ -f "data/face_landmarker.task" ] || die "MediaPipe-Modell fehlt: data/face_landmarker.task"

    python3 -m json.tool "$MANIFEST" >/dev/null
    check_flatpak_ref "$RUNTIME"
    check_flatpak_ref "$SDK"
    check_flatpak_ref "$BUILDER_APP"
}

download_deps() {
    local refresh="${1:-0}"
    need_cmd python3
    [ -f "$REQUIREMENTS" ] || die "Requirements fehlen: $REQUIREMENTS"

    if [ "$refresh" = "1" ]; then
        echo "Entferne alten Wheel-Cache..."
        rm -rf "$PIP_CACHE"
    fi

    mkdir -p "$PIP_CACHE"

    echo "Lade Python-Wheels nach $PIP_CACHE..."
    PIP_CACHE_DIR="$SCRIPT_DIR/.pip-cache" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    python3 -m pip download \
        --requirement "$REQUIREMENTS" \
        --dest "$PIP_CACHE" \
        --only-binary=:all: \
        --python-version 313 \
        --implementation cp \
        --abi cp313 \
        --platform manylinux_2_28_x86_64 \
        --platform manylinux_2_17_x86_64 \
        --platform manylinux2014_x86_64 \
        --platform any

    echo "Wheel-Cache bereit."
}

ensure_deps() {
    if [ ! -d "$PIP_CACHE" ] || [ -z "$(find "$PIP_CACHE" -maxdepth 1 -name '*.whl' -print -quit)" ]; then
        download_deps 0
        return
    fi

    PIP_CACHE_DIR="$SCRIPT_DIR/.pip-cache" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    python3 -m pip download \
        --requirement "$REQUIREMENTS" \
        --dest "$PIP_CACHE" \
        --only-binary=:all: \
        --python-version 313 \
        --implementation cp \
        --abi cp313 \
        --platform manylinux_2_28_x86_64 \
        --platform manylinux_2_17_x86_64 \
        --platform manylinux2014_x86_64 \
        --platform any \
        --no-index \
        --find-links "$PIP_CACHE" >/dev/null
}

init_repo() {
    if [ -d "$REPO_DIR" ]; then
        return
    fi

    flatpak run --command=ostree "$BUILDER_APP" \
        init --repo="$REPO_DIR" --mode=archive-z2
    flatpak run --command=ostree "$BUILDER_APP" \
        config set --repo="$REPO_DIR" core.min-free-space-percent 0
}

build_flatpak() {
    preflight
    ensure_deps
    init_repo

    echo "Baue Flatpak..."
    flatpak run "$BUILDER_APP" \
        --force-clean \
        --disable-cache \
        --user \
        --install \
        --repo="$REPO_DIR" \
        "$BUILD_DIR" \
        "$MANIFEST"

    rm -rf "$BUILD_DIR" .flatpak-builder

    echo
    echo "Flatpak installiert. Starten mit:"
    echo "  flatpak run $APP_ID"
}

build_bundle() {
    build_flatpak

    echo
    echo "Erstelle Bundle..."
    flatpak build-bundle "$REPO_DIR" "$BUNDLE_FILE" "$APP_ID"

    local size
    size="$(du -h "$BUNDLE_FILE" | cut -f1)"
    echo
    echo "Bundle erstellt: $BUNDLE_FILE ($size)"
}

clean() {
    rm -rf "$BUILD_DIR" .flatpak-builder .pip-cache
    echo "Build-Artefakte entfernt."
}

case "${1:-build}" in
    build)
        build_flatpak
        ;;
    bundle)
        build_bundle
        ;;
    deps)
        ensure_deps
        ;;
    deps-refresh)
        download_deps 1
        ;;
    clean)
        clean
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        usage >&2
        die "Unbekannter Modus: $1"
        ;;
esac
