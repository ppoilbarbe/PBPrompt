#!/usr/bin/env bash
# Build a macOS .app bundle with PyInstaller.
# Prerequisites: pip install pyinstaller
# Usage: ./scripts/build_macos.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="pbprompt"
DIST="$ROOT/dist"

echo "Building $APP_NAME for macOS..."
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
    --osx-bundle-identifier "com.pbsoft.pbprompt" \
    "$ROOT/src/pbprompt/__main__.py"

echo "Bundle: $DIST/$APP_NAME.app"
echo ""
echo "Note: To distribute on macOS, code-sign the bundle:"
echo "  codesign --deep --force --sign 'Developer ID Application: Your Name' $DIST/$APP_NAME.app"
echo "Done."
