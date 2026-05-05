#!/usr/bin/env bash
# Compile Qt Designer .ui files and the .qrc resource file.
# Requires pyside6-uic and pyside6-rcc (provided by the pyside6 package).
# Usage: ./scripts/build_qm.sh

set -euo pipefail

SRC_GUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/src/pbprompt/gui"
RESOURCES="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/resources"

echo "Compiling .ui files..."
for ui_file in "$SRC_GUI"/*.ui; do
    base="$(basename "$ui_file" .ui)"
    out="$SRC_GUI/ui_${base}.py"
    echo "  pyside6-uic $ui_file -> $out"
    pyside6-uic "$ui_file" -o "$out"
done

echo "Compiling resources.qrc..."
pyside6-rcc "$RESOURCES/resources.qrc" -o "$SRC_GUI/resources_rc.py"
echo "  -> $SRC_GUI/resources_rc.py"

echo "Done."
