"""Tests for pbprompt.gui.image_utils (offscreen Qt — no display required)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QByteArray, QIODeviceBase
from PySide6.QtGui import QImage

from pbprompt.gui.image_utils import (
    ImageViewDialog,
    _ZoomMode,
    detect_image_format,
    generate_thumbnail,
    open_image_file_dialog,
    pixmap_from_bytes,
    qimage_to_bytes,
    resize_for_storage,
)


def _make_image_bytes(fmt: str, width: int = 20, height: int = 10) -> bytes:
    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(0xFF112233)
    ba = QByteArray()
    from PySide6.QtCore import QBuffer

    buf = QBuffer(ba)
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    img.save(buf, fmt)
    buf.close()
    return bytes(ba)


PNG_BYTES = _make_image_bytes("PNG")
JPEG_BYTES = _make_image_bytes("JPEG")


# ---------------------------------------------------------------------------
# detect_image_format
# ---------------------------------------------------------------------------


class TestDetectImageFormat:
    def test_jpeg_magic(self) -> None:
        assert detect_image_format(JPEG_BYTES) == "jpeg"

    def test_png_magic(self) -> None:
        assert detect_image_format(PNG_BYTES) == "png"

    def test_unknown_returns_none(self) -> None:
        assert detect_image_format(b"not an image") is None

    def test_too_short_returns_none(self) -> None:
        assert detect_image_format(b"\xff") is None


# ---------------------------------------------------------------------------
# generate_thumbnail
# ---------------------------------------------------------------------------


class TestGenerateThumbnail:
    def test_success(self, qtbot) -> None:
        result = generate_thumbnail(PNG_BYTES, 8, 8)
        assert result is not None
        assert detect_image_format(result) == "png"

    def test_invalid_data_returns_none(self, qtbot) -> None:
        assert generate_thumbnail(b"garbage", 8, 8) is None

    def test_format_conversion_failure(self, qtbot) -> None:
        bad_img = MagicMock()
        bad_img.loadFromData.return_value = True
        bad_img.convertToFormat.return_value = bad_img
        bad_img.isNull.return_value = True
        with patch("pbprompt.gui.image_utils.QImage", return_value=bad_img):
            assert generate_thumbnail(PNG_BYTES, 8, 8) is None

    def test_scaled_null(self, qtbot) -> None:
        converted = MagicMock()
        converted.isNull.return_value = False
        scaled = MagicMock()
        scaled.isNull.return_value = True
        converted.scaled.return_value = scaled
        img = MagicMock()
        img.loadFromData.return_value = True
        img.convertToFormat.return_value = converted
        with patch("pbprompt.gui.image_utils.QImage", return_value=img):
            assert generate_thumbnail(PNG_BYTES, 8, 8) is None

    def test_save_failure(self, qtbot) -> None:
        scaled = MagicMock()
        scaled.isNull.return_value = False
        scaled.save.return_value = False
        converted = MagicMock()
        converted.isNull.return_value = False
        converted.scaled.return_value = scaled
        img = MagicMock()
        img.loadFromData.return_value = True
        img.convertToFormat.return_value = converted
        with patch("pbprompt.gui.image_utils.QImage", return_value=img):
            assert generate_thumbnail(PNG_BYTES, 8, 8) is None


# ---------------------------------------------------------------------------
# resize_for_storage
# ---------------------------------------------------------------------------


class TestResizeForStorage:
    def test_already_within_bounds_unchanged(self, qtbot) -> None:
        result = resize_for_storage(PNG_BYTES, 1000, 1000)
        assert result == PNG_BYTES

    def test_invalid_data_unchanged(self, qtbot) -> None:
        assert resize_for_storage(b"garbage", 4, 4) == b"garbage"

    def test_resizes_png(self, qtbot) -> None:
        result = resize_for_storage(PNG_BYTES, 4, 4)
        assert result != PNG_BYTES
        assert detect_image_format(result) == "png"

    def test_resizes_jpeg(self, qtbot) -> None:
        result = resize_for_storage(JPEG_BYTES, 4, 4)
        assert detect_image_format(result) == "jpeg"

    def test_format_conversion_failure_returns_original(self, qtbot) -> None:
        img = MagicMock()
        img.loadFromData.return_value = True
        img.width.return_value = 100
        img.height.return_value = 100
        converted = MagicMock()
        converted.isNull.return_value = True
        img.convertToFormat.return_value = converted
        with patch("pbprompt.gui.image_utils.QImage", return_value=img):
            assert resize_for_storage(PNG_BYTES, 4, 4) == PNG_BYTES

    def test_scaled_null_returns_original(self, qtbot) -> None:
        scaled = MagicMock()
        scaled.isNull.return_value = True
        converted = MagicMock()
        converted.isNull.return_value = False
        converted.scaled.return_value = scaled
        img = MagicMock()
        img.loadFromData.return_value = True
        img.width.return_value = 100
        img.height.return_value = 100
        img.convertToFormat.return_value = converted
        with patch("pbprompt.gui.image_utils.QImage", return_value=img):
            assert resize_for_storage(PNG_BYTES, 4, 4) == PNG_BYTES

    def test_save_failure_returns_original(self, qtbot) -> None:
        scaled = MagicMock()
        scaled.isNull.return_value = False
        scaled.save.return_value = False
        converted = MagicMock()
        converted.isNull.return_value = False
        converted.scaled.return_value = scaled
        img = MagicMock()
        img.loadFromData.return_value = True
        img.width.return_value = 100
        img.height.return_value = 100
        img.convertToFormat.return_value = converted
        with patch("pbprompt.gui.image_utils.QImage", return_value=img):
            assert resize_for_storage(PNG_BYTES, 4, 4) == PNG_BYTES


# ---------------------------------------------------------------------------
# pixmap_from_bytes / qimage_to_bytes
# ---------------------------------------------------------------------------


class TestPixmapFromBytes:
    def test_success(self, qtbot) -> None:
        pm = pixmap_from_bytes(PNG_BYTES)
        assert pm is not None
        assert not pm.isNull()

    def test_failure_returns_none(self, qtbot) -> None:
        assert pixmap_from_bytes(b"garbage") is None


class TestQimageToBytes:
    def test_success_png(self, qtbot) -> None:
        img = QImage(4, 4, QImage.Format.Format_ARGB32)
        img.fill(0xFFFFFFFF)
        result = qimage_to_bytes(img, "PNG")
        assert result is not None
        assert detect_image_format(result) == "png"

    def test_save_failure_returns_none(self, qtbot) -> None:
        img = MagicMock()
        img.save.return_value = False
        assert qimage_to_bytes(img) is None


# ---------------------------------------------------------------------------
# open_image_file_dialog
# ---------------------------------------------------------------------------


class TestOpenImageFileDialog:
    def test_cancelled_returns_none(self, qtbot) -> None:
        with patch("pbprompt.gui.image_utils.QFileDialog") as mock_cls:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = False
            mock_dialog.layout.return_value = None
            mock_cls.return_value = mock_dialog
            result = open_image_file_dialog(None, "Title", "*.png")
        assert result is None

    def test_accepted_returns_path(self, qtbot) -> None:
        with patch("pbprompt.gui.image_utils.QFileDialog") as mock_cls:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = True
            mock_dialog.selectedFiles.return_value = ["/tmp/foo.png"]
            mock_dialog.layout.return_value = None
            mock_cls.return_value = mock_dialog
            result = open_image_file_dialog(None, "Title", "*.png", directory="/tmp")
        assert result == "/tmp/foo.png"

    def test_accepted_no_files_returns_none(self, qtbot) -> None:
        with patch("pbprompt.gui.image_utils.QFileDialog") as mock_cls:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = True
            mock_dialog.selectedFiles.return_value = []
            mock_dialog.layout.return_value = None
            mock_cls.return_value = mock_dialog
            result = open_image_file_dialog(None, "Title", "*.png")
        assert result is None

    def test_grid_layout_injection(self, qtbot) -> None:
        from PySide6.QtWidgets import QGridLayout

        with patch("pbprompt.gui.image_utils.QFileDialog") as mock_cls:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = False
            grid = QGridLayout()
            mock_dialog.layout.return_value = grid
            mock_cls.return_value = mock_dialog
            result = open_image_file_dialog(None, "Title", "*.png")
        assert result is None

    def test_layout_injection_exception_ignored(self, qtbot) -> None:
        with patch("pbprompt.gui.image_utils.QFileDialog") as mock_cls:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = False
            mock_dialog.layout.side_effect = RuntimeError("boom")
            mock_cls.return_value = mock_dialog
            result = open_image_file_dialog(None, "Title", "*.png")
        assert result is None

    def test_update_preview_valid_image(self, qtbot, tmp_path: Any) -> None:
        img_path = tmp_path / "img.png"
        img_path.write_bytes(PNG_BYTES)
        captured: dict[str, Any] = {}

        with patch("pbprompt.gui.image_utils.QFileDialog") as mock_cls:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = False
            mock_dialog.layout.return_value = None

            def _connect(fn: Any) -> None:
                captured["fn"] = fn

            mock_dialog.currentChanged.connect.side_effect = _connect
            mock_cls.return_value = mock_dialog
            open_image_file_dialog(None, "Title", "*.png")

        captured["fn"](str(img_path))  # must not raise

    def test_update_preview_invalid_path(self, qtbot) -> None:
        captured: dict[str, Any] = {}

        with patch("pbprompt.gui.image_utils.QFileDialog") as mock_cls:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = False
            mock_dialog.layout.return_value = None

            def _connect(fn: Any) -> None:
                captured["fn"] = fn

            mock_dialog.currentChanged.connect.side_effect = _connect
            mock_cls.return_value = mock_dialog
            open_image_file_dialog(None, "Title", "*.png")

        captured["fn"]("")  # empty path → no preview branch
        captured["fn"]("/does/not/exist.png")  # unloadable → no preview branch


# ---------------------------------------------------------------------------
# ImageViewDialog
# ---------------------------------------------------------------------------


class TestImageViewDialog:
    def test_creates_with_valid_image(self, qtbot) -> None:
        dlg = ImageViewDialog(PNG_BYTES, title="Test")
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Test"

    def test_creates_with_invalid_image(self, qtbot) -> None:
        dlg = ImageViewDialog(b"garbage")
        qtbot.addWidget(dlg)
        assert dlg._pixmap is None  # noqa: SLF001

    def test_creates_with_config_geometry(self, qtbot) -> None:
        from pbprompt.config import AppConfig

        cfg = AppConfig(
            image_viewer_x=10,
            image_viewer_y=20,
            image_viewer_width=500,
            image_viewer_height=450,
        )
        dlg = ImageViewDialog(PNG_BYTES, config=cfg)
        qtbot.addWidget(dlg)
        assert dlg.width() == 500
        assert dlg.height() == 450

    def test_close_event_persists_config(self, qtbot) -> None:
        from pbprompt.config import AppConfig

        cfg = AppConfig()
        with patch.object(AppConfig, "save"):
            dlg = ImageViewDialog(PNG_BYTES, config=cfg)
            qtbot.addWidget(dlg)
            dlg.close()
        assert cfg.image_viewer_width is not None
        assert cfg.image_viewer_height is not None

    def test_show_event_applies_mode_once(self, qtbot) -> None:
        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg.show()
        assert dlg._initial_shown is True  # noqa: SLF001
        dlg.close()

    @pytest.mark.parametrize(
        ("method", "mode"),
        [
            ("_on_fit", _ZoomMode.FIT),
            ("_on_one", _ZoomMode.ONE),
            ("_on_width", _ZoomMode.WIDTH),
            ("_on_height", _ZoomMode.HEIGHT),
        ],
    )
    def test_zoom_mode_actions(self, qtbot, method: str, mode: _ZoomMode) -> None:
        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg.resize(300, 300)
        getattr(dlg, method)()
        assert dlg._mode == mode  # noqa: SLF001
        dlg.close()

    def test_zoom_in_out(self, qtbot) -> None:
        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg.resize(300, 300)
        dlg._on_fit()  # noqa: SLF001
        initial_scale = dlg._scale  # noqa: SLF001
        dlg._on_zoom_in()  # noqa: SLF001
        assert dlg._mode == _ZoomMode.MANUAL  # noqa: SLF001
        assert dlg._scale >= initial_scale  # noqa: SLF001
        dlg._on_zoom_out()  # noqa: SLF001
        dlg.close()

    def test_zoom_in_caps_at_max(self, qtbot) -> None:
        dlg = ImageViewDialog(PNG_BYTES, max_zoom=1)
        qtbot.addWidget(dlg)
        dlg._scale = 1.0  # noqa: SLF001
        dlg._mode = _ZoomMode.MANUAL  # noqa: SLF001
        dlg._on_zoom_in()  # noqa: SLF001
        assert dlg._scale <= 1.0  # noqa: SLF001
        dlg.close()

    def test_zoom_out_floors_at_min_scale(self, qtbot) -> None:
        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg._scale = dlg._MIN_SCALE  # noqa: SLF001
        dlg._mode = _ZoomMode.MANUAL  # noqa: SLF001
        dlg._on_zoom_out()  # noqa: SLF001
        assert dlg._scale == dlg._MIN_SCALE  # noqa: SLF001
        dlg.close()

    def test_apply_mode_noop_without_pixmap(self, qtbot) -> None:
        dlg = ImageViewDialog(b"garbage")
        qtbot.addWidget(dlg)
        dlg._apply_mode()  # must not raise  # noqa: SLF001
        dlg.close()

    def test_apply_scale_noop_without_pixmap(self, qtbot) -> None:
        dlg = ImageViewDialog(b"garbage")
        qtbot.addWidget(dlg)
        dlg._apply_scale(1.0)  # must not raise  # noqa: SLF001
        dlg.close()

    def test_resize_event_triggers_apply_mode_when_ready(self, qtbot) -> None:
        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg.show()
        dlg.resize(500, 500)  # must not raise
        dlg.close()

    def test_zoom_to_point_zero_size_label(self, qtbot) -> None:
        from PySide6.QtCore import QPoint

        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg._img_label.resize(0, 0)  # noqa: SLF001
        dlg._zoom_to_point(QPoint(0, 0))  # noqa: SLF001
        dlg.close()

    def test_zoom_to_point_valid_label(self, qtbot) -> None:
        from PySide6.QtCore import QPoint

        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg.resize(300, 300)
        dlg._on_fit()  # noqa: SLF001
        dlg._zoom_to_point(QPoint(5, 5))  # noqa: SLF001
        assert dlg._mode == _ZoomMode.MANUAL  # noqa: SLF001
        dlg.close()

    def test_event_filter_double_click_zooms(self, qtbot) -> None:
        from PySide6.QtCore import QEvent, QPointF
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtGui import Qt as QtGui

        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg.resize(300, 300)
        dlg._on_fit()  # noqa: SLF001

        event = QMouseEvent(
            QEvent.Type.MouseButtonDblClick,
            QPointF(5, 5),
            QPointF(5, 5),
            QtGui.MouseButton.LeftButton,
            QtGui.MouseButton.LeftButton,
            QtGui.KeyboardModifier.NoModifier,
        )
        result = dlg.eventFilter(dlg._img_label, event)  # noqa: SLF001
        assert result is True
        dlg.close()

    def test_event_filter_other_object_delegates(self, qtbot) -> None:
        from PySide6.QtCore import QEvent, QObject

        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        other = QObject(dlg)
        event = QEvent(QEvent.Type.Paint)
        result = dlg.eventFilter(other, event)
        assert result is False
        dlg.close()

    def test_event_filter_wheel_zooms(self, qtbot) -> None:
        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg.resize(300, 300)
        dlg._on_fit()  # noqa: SLF001

        from PySide6.QtCore import QEvent, QPointF

        event = MagicMock()
        event.type.return_value = QEvent.Type.Wheel
        event.position.return_value = QPointF(5, 5)
        angle = MagicMock()
        angle.y.return_value = 10
        event.angleDelta.return_value = angle

        result = dlg.eventFilter(dlg._scroll.viewport(), event)  # noqa: SLF001
        assert result is True
        dlg.close()

    def test_event_filter_wheel_scrolls_down(self, qtbot) -> None:
        dlg = ImageViewDialog(PNG_BYTES)
        qtbot.addWidget(dlg)
        dlg.resize(300, 300)
        dlg._on_fit()  # noqa: SLF001

        from PySide6.QtCore import QEvent, QPointF

        event = MagicMock()
        event.type.return_value = QEvent.Type.Wheel
        event.position.return_value = QPointF(5, 5)
        angle = MagicMock()
        angle.y.return_value = -10
        event.angleDelta.return_value = angle

        result = dlg.eventFilter(dlg._scroll.viewport(), event)  # noqa: SLF001
        assert result is True
        dlg.close()
