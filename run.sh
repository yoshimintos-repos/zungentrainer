#!/bin/bash
# ZungenTrainer - Lokaler Schnellstart (ohne Flatpak)
#
# Voraussetzungen:
#   pip install numpy opencv-python mediapipe
#
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export ZUNGENTRAINER_DATA_DIR="$SCRIPT_DIR/data"
exec python3 "$SCRIPT_DIR/src/main.py" "$@"
