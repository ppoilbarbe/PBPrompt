#!/usr/bin/env bash
# Build a standalone Linux executable with PyInstaller.
# Prerequisites: pip install pyinstaller
# Usage: ./scripts/build_linux.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="pbprompt"
DIST="$ROOT/dist"

echo "Building $APP_NAME for Linux..."

cd "$ROOT"

# Ensure translations and UI are compiled
make all

pyinstaller \
    --onefile \
    --windowed \
    --name "$APP_NAME" \
    --icon "$ROOT/resources/icons/app_color.svg" \
    --add-data "$ROOT/locales:locales" \
    --add-data "$ROOT/resources:resources" \
    --paths "$ROOT/src" \
    "$ROOT/src/pbprompt/__main__.py"

echo "Executable: $DIST/$APP_NAME"
echo "Done."
