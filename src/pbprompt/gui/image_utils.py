"""Qt-based image utilities: thumbnails, format detection, full-image dialog."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt5.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def detect_image_format(data: bytes) -> str | None:
    """Return ``'jpeg'``, ``'png'``, or ``None`` based on magic bytes.

    Detection is done on content, not on filename extension.
    """
    if len(data) >= 3 and data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return None


def generate_thumbnail(image_data: bytes, width: int, height: int) -> bytes | None:
    """Scale *image_data* to fit within (*width*, *height*), return PNG bytes.

    Uses Qt's image scaling (smooth transformation, aspect ratio preserved).
    Returns ``None`` if the image data cannot be decoded.
    """
    img = QImage()
    if not img.loadFromData(QByteArray(image_data)):
        logger.warning("generate_thumbnail: failed to load image data.")
        return None
    scaled = img.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    if not scaled.save(buf, "PNG"):
        logger.warning("generate_thumbnail: failed to save scaled image.")
        return None
    buf.close()
    return bytes(ba)


def pixmap_from_bytes(data: bytes) -> QPixmap | None:
    """Load *data* into a QPixmap.  Returns ``None`` on failure."""
    pm = QPixmap()
    if not pm.loadFromData(QByteArray(data)):
        return None
    return pm


def qimage_to_bytes(image: QImage, fmt: str = "PNG") -> bytes | None:
    """Convert a QImage to raw bytes in *fmt* format (``'PNG'`` or ``'JPEG'``)."""
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    if not image.save(buf, fmt):
        return None
    buf.close()
    return bytes(ba)


# ---------------------------------------------------------------------------
# Image file dialog with live preview
# ---------------------------------------------------------------------------


def open_image_file_dialog(
    parent: Any,
    title: str,
    filter_str: str,
    no_preview_text: str = "No preview",
    directory: str = "",
) -> str | None:
    """Open a *non-native* QFileDialog with a live image preview panel.

    The preview label is injected into the dialog's QGridLayout at column 3,
    row 1 (to the right of the file-listing area).  On platforms or Qt builds
    where that layout trick does not work, the dialog opens normally without
    a preview (graceful degradation).

    *directory* sets the initial directory shown by the dialog; ignored if empty.

    Returns the selected file path, or ``None`` if the user cancelled.
    """
    dialog = QFileDialog(parent, title)
    dialog.setNameFilter(filter_str)
    dialog.setFileMode(QFileDialog.ExistingFile)
    if directory:
        dialog.setDirectory(directory)
    # Non-native dialog is required so we can inject a custom widget.
    dialog.setOption(QFileDialog.DontUseNativeDialog)

    # ------------------------------------------------------------------
    # Preview label
    # ------------------------------------------------------------------
    preview = QLabel(no_preview_text)
    preview.setAlignment(Qt.AlignCenter)
    preview.setMinimumSize(180, 180)
    preview.setMaximumWidth(220)
    preview.setFrameShape(QFrame.StyledPanel)
    preview.setWordWrap(True)
    preview.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def _update_preview(path: str) -> None:
        if path:
            pm = QPixmap(path)
            if not pm.isNull():
                preview.setPixmap(
                    pm.scaled(
                        max(preview.width() - 8, 1),
                        max(preview.height() - 8, 1),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
                return
        preview.setPixmap(QPixmap())
        preview.setText(no_preview_text)

    dialog.currentChanged.connect(_update_preview)

    # ------------------------------------------------------------------
    # Inject preview into the dialog's grid layout.
    # Qt5 non-native QFileDialog uses a QGridLayout where:
    #   row 0 — navigation toolbar
    #   row 1 — sidebar (col 0) + file list (cols 1-2)
    #   rows 2-3 — file name / filter fields and OK/Cancel buttons
    # We add the preview at (row=1, col=3) spanning all remaining rows.
    # ------------------------------------------------------------------
    try:
        grid = dialog.layout()
        if isinstance(grid, QGridLayout):
            row_span = max(1, grid.rowCount() - 1)
            grid.addWidget(preview, 1, 3, row_span, 1)
    except Exception:
        logger.debug("Could not inject image preview into file dialog.", exc_info=True)

    if not dialog.exec_():
        return None
    files = dialog.selectedFiles()
    return files[0] if files else None


# ---------------------------------------------------------------------------
# Full-image viewer dialog
# ---------------------------------------------------------------------------


class ImageViewDialog(QDialog):
    """Simple dialog that shows a full-size image with a scroll area."""

    def __init__(self, image_data: bytes, title: str = "Image", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setAttribute(Qt.WA_DeleteOnClose)

        pm = pixmap_from_bytes(image_data)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        label = QLabel()
        if pm and not pm.isNull():
            label.setPixmap(pm)
            # Resize dialog to fit image, capped at 80 % of screen.
            screen = self.screen() if self.screen() else None
            if screen:
                sg = screen.availableGeometry()
                max_w = int(sg.width() * 0.8)
                max_h = int(sg.height() * 0.8)
            else:
                max_w, max_h = 1200, 900
            dialog_w = min(pm.width() + 24, max_w)
            dialog_h = min(pm.height() + 80, max_h)
            self.resize(dialog_w, dialog_h)
        else:
            label.setText("(No image)")
        scroll.setWidget(label)
        layout.addWidget(scroll)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
