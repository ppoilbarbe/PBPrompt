"""Render resources/icons/app_color.svg → pbprompt.png (128×128)."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).parent.parent
SVG = ROOT / "resources" / "icons" / "app_color.svg"
OUT = ROOT / "pbprompt.png"
SIZE = 128

app = QApplication(sys.argv + ["-platform", "offscreen"])

renderer = QSvgRenderer(str(SVG))
if not renderer.isValid():
    print(f"[png] error: cannot load {SVG}", file=sys.stderr)
    sys.exit(1)

image = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
image.fill(Qt.GlobalColor.transparent)
painter = QPainter(image)
renderer.render(painter)
painter.end()

if not image.save(str(OUT)):
    print(f"[png] error: cannot save {OUT}", file=sys.stderr)
    sys.exit(1)

print(f"[png] {OUT} ({SIZE}×{SIZE})")
