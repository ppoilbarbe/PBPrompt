"""Tests for pbprompt.__main__ (argument parsing, non-frozen font loading)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestParseArgs:
    def test_no_args(self) -> None:
        from pbprompt.__main__ import _parse_args

        with patch.object(sys, "argv", ["pbprompt"]):
            args = _parse_args()
        assert args.file is None
        assert args.log_level is None

    def test_with_file(self) -> None:
        from pbprompt.__main__ import _parse_args

        with patch.object(sys, "argv", ["pbprompt", "prompts.sqlite"]):
            args = _parse_args()
        assert args.file == "prompts.sqlite"

    def test_log_level_debug(self) -> None:
        from pbprompt.__main__ import _parse_args

        with patch.object(sys, "argv", ["pbprompt", "--log-level", "DEBUG"]):
            args = _parse_args()
        assert args.log_level == "DEBUG"

    def test_log_level_choices(self) -> None:
        import pytest  # noqa: PLC0415

        from pbprompt.__main__ import _parse_args

        for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            with patch.object(sys, "argv", ["pbprompt", "--log-level", level]):
                args = _parse_args()
            assert args.log_level == level

        with (
            patch.object(sys, "argv", ["pbprompt", "--log-level", "VERBOSE"]),
            pytest.raises(SystemExit),
        ):
            _parse_args()


class TestLoadBundledFonts:
    def test_nonfrozen_returns_early(self) -> None:
        from pbprompt.__main__ import _load_bundled_fonts

        # Without sys.frozen = True the function is a no-op
        _load_bundled_fonts(None)  # must not raise

    def test_frozen_no_fonts_dir(self, tmp_path: Path) -> None:
        from pbprompt.__main__ import _load_bundled_fonts

        # sys.frozen = True but tmp_path/fonts doesn't exist → returns after the check
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", str(tmp_path), create=True),
        ):
            _load_bundled_fonts(None)  # must not raise

    def test_frozen_with_ubuntu_font(self, tmp_path: Path) -> None:
        from pbprompt.__main__ import _load_bundled_fonts

        fonts_dir = tmp_path / "fonts"
        fonts_dir.mkdir()
        (fonts_dir / "Ubuntu-R.ttf").write_bytes(b"fake font")

        mock_fdb = MagicMock()
        mock_fdb.addApplicationFont.return_value = 0
        mock_fdb.applicationFontFamilies.return_value = ["Ubuntu"]

        mock_qtgui = MagicMock()
        mock_qtgui.QFontDatabase = mock_fdb
        mock_qtgui.QFont = MagicMock(return_value=MagicMock())

        mock_app = MagicMock()
        mock_app.font.return_value.pointSize.return_value = 11

        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", str(tmp_path), create=True),
            patch.dict("sys.modules", {"PySide6.QtGui": mock_qtgui}),
        ):
            _load_bundled_fonts(mock_app)

        mock_app.setFont.assert_called_once()

    def test_frozen_font_not_added(self, tmp_path: Path) -> None:
        """addApplicationFont returns -1 → no families added, setFont not called."""
        from pbprompt.__main__ import _load_bundled_fonts

        fonts_dir = tmp_path / "fonts"
        fonts_dir.mkdir()
        (fonts_dir / "bad.ttf").write_bytes(b"not a font")

        mock_fdb = MagicMock()
        mock_fdb.addApplicationFont.return_value = -1  # failure

        mock_qtgui = MagicMock()
        mock_qtgui.QFontDatabase = mock_fdb
        mock_qtgui.QFont = MagicMock()

        mock_app = MagicMock()

        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", str(tmp_path), create=True),
            patch.dict("sys.modules", {"PySide6.QtGui": mock_qtgui}),
        ):
            _load_bundled_fonts(mock_app)

        mock_app.setFont.assert_not_called()
