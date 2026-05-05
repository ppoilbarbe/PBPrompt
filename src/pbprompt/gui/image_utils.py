"""Qt-based image utilities: thumbnails, format detection, full-image dialog."""

from __future__ import annotations

import logging
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QBuffer, QByteArray, QEvent, QIODeviceBase, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
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
    # Convert to a known 32-bit format before scaling: avoids an internal QPainter
    # fallback that Qt uses for indexed/paletted images, which fails on some platforms.
    img = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    if img.isNull():
        logger.warning("generate_thumbnail: format conversion failed.")
        return None
    scaled = img.scaled(
        width,
        height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    if scaled.isNull():
        logger.warning("generate_thumbnail: scaled image is null.")
        return None
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    if not scaled.save(buf, "PNG"):
        logger.warning("generate_thumbnail: failed to save scaled image.")
        return None
    buf.close()
    return bytes(ba)


def resize_for_storage(data: bytes, max_width: int, max_height: int) -> bytes:
    """Resize *data* proportionally so it fits within (*max_width*, *max_height*).

    Format is preserved: JPEG in → JPEG out, PNG in → PNG out.
    Returns *data* unchanged if already within bounds or if decoding fails.
    """
    img = QImage()
    if not img.loadFromData(QByteArray(data)):
        logger.warning("resize_for_storage: failed to load image data.")
        return data
    if img.width() <= max_width and img.height() <= max_height:
        return data
    img = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    if img.isNull():
        logger.warning("resize_for_storage: format conversion failed.")
        return data
    scaled = img.scaled(
        max_width,
        max_height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    if scaled.isNull():
        logger.warning("resize_for_storage: scaled image is null.")
        return data
    fmt = detect_image_format(data)
    qt_fmt = "JPEG" if fmt == "jpeg" else "PNG"
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    if not scaled.save(buf, qt_fmt):
        logger.warning("resize_for_storage: failed to save resized image.")
        return data
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
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
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
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    if directory:
        dialog.setDirectory(directory)
    # Non-native dialog is required so we can inject a custom widget.
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog)

    # ------------------------------------------------------------------
    # Preview label
    # ------------------------------------------------------------------
    preview = QLabel(no_preview_text)
    preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
    preview.setMinimumSize(180, 180)
    preview.setMaximumWidth(220)
    preview.setFrameShape(QFrame.Shape.StyledPanel)
    preview.setWordWrap(True)
    preview.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def _update_preview(path: str) -> None:
        if path:
            pm = QPixmap(path)
            if not pm.isNull():
                # Scale via QImage to avoid QPainter engine errors (see _apply_scale).
                scaled_img = pm.toImage().scaled(
                    max(preview.width() - 8, 1),
                    max(preview.height() - 8, 1),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                if not scaled_img.isNull():
                    preview.setPixmap(QPixmap.fromImage(scaled_img))
                    return
        preview.setText(no_preview_text)

    dialog.currentChanged.connect(_update_preview)

    # ------------------------------------------------------------------
    # Inject preview into the dialog's grid layout.
    # Qt non-native QFileDialog uses a QGridLayout where:
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

    if not dialog.exec():
        return None
    files = dialog.selectedFiles()
    return files[0] if files else None


# ---------------------------------------------------------------------------
# Full-image viewer dialog
# ---------------------------------------------------------------------------


class _ZoomMode(IntEnum):
    FIT = 0  # image fits viewport, capped at max_zoom
    ONE = 1  # 1 pixel = 1 displayed pixel
    WIDTH = 2  # fill viewport width
    HEIGHT = 3  # fill viewport height
    MANUAL = 4  # free zoom via +50% / -50% buttons


class ImageViewDialog(QDialog):
    """Image viewer with zoom toolbar (Fit / 1:1 / Width / Height / ±step%)."""

    _MIN_SIZE = 400
    _MIN_SCALE = 0.1
    # _MAX_SCALE is self._max_zoom (float)

    # Persisted across dialog instances
    _last_mode: _ZoomMode = _ZoomMode.FIT
    _last_scale: float = 1.0

    def __init__(
        self,
        image_data: bytes,
        max_zoom: int = 4,
        zoom_step: int = 10,
        title: str = "Image",
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMinimumSize(self._MIN_SIZE, self._MIN_SIZE)

        self._max_zoom: int = max_zoom
        self._zoom_step: float = max(1, zoom_step) / 100.0
        self._mode: _ZoomMode = ImageViewDialog._last_mode
        self._scale: float = ImageViewDialog._last_scale
        self._ready: bool = False
        self._initial_shown: bool = False

        pm = pixmap_from_bytes(image_data)
        self._pixmap: QPixmap | None = pm if (pm and not pm.isNull()) else None

        self._setup_ui()
        self._setup_initial_size()
        self._ready = True

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        from pbprompt.gui.icons import get_icon  # noqa: PLC0415
        from pbprompt.i18n import get_translate  # noqa: PLC0415

        _ = get_translate()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # ---- toolbar ----
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(22, 22))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        layout.addWidget(toolbar)

        # Width shortcut key: translatable ("l" in French, "w" in English, …)
        # Keyboard shortcuts — set here because Ui_MainWindow.retranslateUi is
        # shadowed by this override (Python MRO) and therefore never called at runtime.
        width_key = _("l")

        act_fit = QAction(get_icon("zoom_fit"), _("Fit"), self)
        act_fit.setCheckable(True)
        act_fit.setToolTip(_("Fit image to window (max ×%d)") % self._max_zoom)
        act_fit.triggered.connect(self._on_fit)
        toolbar.addAction(act_fit)

        act_one = QAction(get_icon("zoom_original"), _("×1"), self)
        act_one.setCheckable(True)
        act_one.setShortcut(QKeySequence("1"))
        act_one.setToolTip(_("Actual size — 1 pixel = 1 displayed pixel  [1]"))
        act_one.triggered.connect(self._on_one)
        toolbar.addAction(act_one)

        act_width = QAction(get_icon("zoom_width"), _("Width"), self)
        act_width.setCheckable(True)
        act_width.setShortcut(QKeySequence(width_key))
        act_width.setToolTip(_("Fit image width to window  [%s]") % width_key.upper())
        act_width.triggered.connect(self._on_width)
        toolbar.addAction(act_width)

        act_height = QAction(get_icon("zoom_height"), _("Height"), self)
        act_height.setCheckable(True)
        act_height.setShortcut(QKeySequence("h"))
        act_height.setToolTip(_("Fit image height to window  [H]"))
        act_height.triggered.connect(self._on_height)
        toolbar.addAction(act_height)

        self._act_fit = act_fit
        self._act_one = act_one
        self._act_width = act_width
        self._act_height = act_height
        self._update_mode_buttons()

        toolbar.addSeparator()

        step_pct = round(self._zoom_step * 100)
        act_in = QAction(get_icon("zoom_in"), _("+%d%%") % step_pct, self)
        act_in.setShortcuts(
            [
                QKeySequence(Qt.Key.Key_Plus),
                QKeySequence(
                    Qt.KeyboardModifier.KeypadModifier.value | Qt.Key.Key_Plus.value
                ),
            ]
        )
        act_in.setToolTip(_("Zoom in +%d%%  [+]") % step_pct)
        act_in.triggered.connect(self._on_zoom_in)
        toolbar.addAction(act_in)

        act_out = QAction(get_icon("zoom_out"), _("-%d%%") % step_pct, self)
        act_out.setShortcuts(
            [
                QKeySequence(Qt.Key.Key_Minus),
                QKeySequence(
                    Qt.KeyboardModifier.KeypadModifier.value | Qt.Key.Key_Minus.value
                ),
            ]
        )
        act_out.setToolTip(_("Zoom out -%d%%  [−]") % step_pct)
        act_out.triggered.connect(self._on_zoom_out)
        toolbar.addAction(act_out)

        # Resolution + scale label pushed to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self._scale_label = QLabel()
        self._scale_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        toolbar.addWidget(self._scale_label)

        # ---- scroll area ----
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.viewport().installEventFilter(self)

        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not self._pixmap:
            from pbprompt.i18n import get_translate as _gt  # noqa: PLC0415

            self._img_label.setText(_gt()("(No image)"))
        self._scroll.setWidget(self._img_label)
        layout.addWidget(self._scroll, 1)

        # ---- close button ----
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _setup_initial_size(self) -> None:
        if self._pixmap:
            screen = self.screen() if hasattr(self, "screen") else None
            if screen:
                sg = screen.availableGeometry()
                max_w = int(sg.width() * 0.8)
                max_h = int(sg.height() * 0.8)
            else:
                max_w, max_h = 1200, 900
            # Extra ~80 px for toolbar + button box
            dialog_w = max(self._MIN_SIZE, min(self._pixmap.width() + 24, max_w))
            dialog_h = max(self._MIN_SIZE, min(self._pixmap.height() + 80, max_h))
            self.resize(dialog_w, dialog_h)
        else:
            self.resize(self._MIN_SIZE, self._MIN_SIZE)

    # ------------------------------------------------------------------
    # Qt event overrides
    # ------------------------------------------------------------------

    def eventFilter(self, obj: Any, event: Any) -> bool:  # type: ignore[override]  # noqa: N802
        if obj is self._scroll.viewport() and event.type() == QEvent.Type.Wheel:
            # Fraction of the image under the cursor before zoom (anchor point).
            # QScrollArea::setWidget reparents the label onto the viewport, so
            # mapFrom gives coordinates in the label's own space.
            cursor_vp = event.pos()
            lbl_w = max(self._img_label.width(), 1)
            lbl_h = max(self._img_label.height(), 1)
            cursor_lbl = self._img_label.mapFrom(self._scroll.viewport(), cursor_vp)
            fx = cursor_lbl.x() / lbl_w
            fy = cursor_lbl.y() / lbl_h

            if event.angleDelta().y() > 0:
                self._on_zoom_in()
            else:
                self._on_zoom_out()

            # Reposition scrollbars so the anchor pixel stays under the cursor.
            # setValue clamps automatically to [min, max], giving the best
            # approximation when the geometry does not allow exact centering.
            new_w = self._img_label.width()
            new_h = self._img_label.height()
            self._scroll.horizontalScrollBar().setValue(
                round(fx * new_w) - cursor_vp.x()
            )
            self._scroll.verticalScrollBar().setValue(round(fy * new_h) - cursor_vp.y())
            return True
        return super().eventFilter(obj, event)

    def showEvent(self, event: Any) -> None:  # type: ignore[override]  # noqa: N802
        super().showEvent(event)
        if not self._initial_shown:
            self._initial_shown = True
            QTimer.singleShot(0, self._apply_mode)

    def resizeEvent(self, event: Any) -> None:  # type: ignore[override]  # noqa: N802
        super().resizeEvent(event)
        if self._ready and self._initial_shown and self._mode != _ZoomMode.MANUAL:
            # Defer so viewport geometry is updated before we measure it.
            QTimer.singleShot(0, self._apply_mode)

    # ------------------------------------------------------------------
    # Mode button visual state
    # ------------------------------------------------------------------

    def _update_mode_buttons(self) -> None:
        self._act_fit.setChecked(self._mode == _ZoomMode.FIT)
        self._act_one.setChecked(self._mode == _ZoomMode.ONE)
        self._act_width.setChecked(self._mode == _ZoomMode.WIDTH)
        self._act_height.setChecked(self._mode == _ZoomMode.HEIGHT)
        # MANUAL: no button checked

    # ------------------------------------------------------------------
    # Zoom application
    # ------------------------------------------------------------------

    def _apply_mode(self) -> None:
        if not self._pixmap:
            return

        vp = self._scroll.viewport()
        vw, vh = max(vp.width(), 1), max(vp.height(), 1)
        pw, ph = self._pixmap.width(), self._pixmap.height()
        mode = self._mode

        if mode == _ZoomMode.FIT:
            self._scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self._scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            scale = min(vw / pw, vh / ph, float(self._max_zoom))
            self._apply_scale(scale)

        elif mode == _ZoomMode.ONE:
            self._scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._apply_scale(1.0)

        elif mode == _ZoomMode.WIDTH:
            self._scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self._scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._apply_scale(vw / pw)

        elif mode == _ZoomMode.HEIGHT:
            self._scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self._apply_scale(vh / ph)

        elif mode == _ZoomMode.MANUAL:
            self._scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._apply_scale(self._scale)

    def _apply_scale(self, scale: float) -> None:
        self._scale = max(self._MIN_SCALE, scale)
        if not self._pixmap:
            return
        w = max(1, round(self._pixmap.width() * self._scale))
        h = max(1, round(self._pixmap.height() * self._scale))
        # Scale via QImage to avoid QPainter engine errors: QPixmap.scaled with
        # SmoothTransformation uses QPainter internally, which fails on some platforms.
        # QImage.scaled with SmoothTransformation uses a pure algorithm (no QPainter).
        scaled_img = self._pixmap.toImage().scaled(
            w,
            h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if scaled_img.isNull():
            return
        scaled_pm = QPixmap.fromImage(scaled_img)
        if scaled_pm.isNull():
            return
        self._img_label.setPixmap(scaled_pm)
        self._img_label.resize(scaled_pm.size())
        pw, ph = self._pixmap.width(), self._pixmap.height()
        self._scale_label.setText(f"  {pw} × {ph}  —  {round(self._scale * 100)} %  ")

    # ------------------------------------------------------------------
    # Zoom actions
    # ------------------------------------------------------------------

    def _on_fit(self) -> None:
        self._mode = ImageViewDialog._last_mode = _ZoomMode.FIT
        self._update_mode_buttons()
        self._apply_mode()

    def _on_one(self) -> None:
        self._mode = ImageViewDialog._last_mode = _ZoomMode.ONE
        self._update_mode_buttons()
        self._apply_mode()

    def _on_width(self) -> None:
        self._mode = ImageViewDialog._last_mode = _ZoomMode.WIDTH
        self._update_mode_buttons()
        self._apply_mode()

    def _on_height(self) -> None:
        self._mode = ImageViewDialog._last_mode = _ZoomMode.HEIGHT
        self._update_mode_buttons()
        self._apply_mode()

    def _on_zoom_in(self) -> None:
        new_scale = min(self._scale + self._zoom_step, float(self._max_zoom))
        if new_scale != self._scale or self._mode != _ZoomMode.MANUAL:
            self._scale = new_scale
            self._mode = _ZoomMode.MANUAL
            ImageViewDialog._last_mode = _ZoomMode.MANUAL
            ImageViewDialog._last_scale = new_scale
            self._update_mode_buttons()
            self._apply_mode()

    def _on_zoom_out(self) -> None:
        new_scale = max(self._scale - self._zoom_step, self._MIN_SCALE)
        if new_scale != self._scale or self._mode != _ZoomMode.MANUAL:
            self._scale = new_scale
            self._mode = _ZoomMode.MANUAL
            ImageViewDialog._last_mode = _ZoomMode.MANUAL
            ImageViewDialog._last_scale = new_scale
            self._update_mode_buttons()
            self._apply_mode()
