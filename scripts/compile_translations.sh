#!/usr/bin/env bash
# Compile all .po files to .mo (gettext binary format).
# Usage: ./scripts/compile_translations.sh

set -euo pipefail

LOCALES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/locales"

echo "Compiling translations from: $LOCALES_DIR"

for po_file in "$LOCALES_DIR"/*/*/messages.po; do
    mo_file="${po_file%.po}.mo"
    echo "  msgfmt $po_file -> $mo_file"
    msgfmt "$po_file" -o "$mo_file"
done

echo "Done."
