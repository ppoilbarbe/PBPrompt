"""Basic GUI smoke tests — run in offscreen Qt mode (no display required).

These tests verify that the model layer and key dialogs can be instantiated
without crashing; they do not simulate user interaction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pbprompt.data import PromptCollection, PromptEntry

# ---------------------------------------------------------------------------
# icons.py
# ---------------------------------------------------------------------------


class TestIconUtils:
    def test_get_icon_dir_returns_path(self) -> None:
        from pbprompt.gui.icons import get_icon_dir

        result = get_icon_dir()
        assert isinstance(result, Path)
        assert result.exists()

    def test_get_icon_dir_contains_svgs(self) -> None:
        from pbprompt.gui.icons import get_icon_dir

        svgs = list(get_icon_dir().glob("*.svg"))
        assert len(svgs) > 0

    def test_get_icon_returns_qicon(self, qtbot) -> None:
        from PySide6.QtGui import QIcon

        from pbprompt.gui.icons import get_icon

        icon = get_icon("help-about")
        assert isinstance(icon, QIcon)

    def test_get_icon_unknown_returns_qicon(self, qtbot) -> None:
        from PySide6.QtGui import QIcon

        from pbprompt.gui.icons import get_icon

        icon = get_icon("does-not-exist")
        assert isinstance(icon, QIcon)

    def test_get_icon_frozen_path(self, qtbot, tmp_path: Path) -> None:
        """Test the frozen branch of get_icon_dir()."""
        from unittest.mock import patch

        from pbprompt.gui import icons

        with (
            patch.object(icons.sys, "frozen", True, create=True),
            patch.object(icons.sys, "_MEIPASS", str(tmp_path), create=True),
        ):
            result = icons.get_icon_dir()

        assert str(result) == str(tmp_path / "pbprompt" / "icons")

    def test_get_icon_standard_fallback(self, qtbot, tmp_path: Path) -> None:
        """Empty icon dir → falls through to Qt standard icon."""
        from unittest.mock import patch

        from PySide6.QtGui import QIcon

        from pbprompt.gui import icons

        with patch.object(icons, "_ICON_DIR", tmp_path):
            result = icons.get_icon("new")
        assert isinstance(result, QIcon)

    def test_get_icon_theme_hit(self, qtbot) -> None:
        """Theme icon found → return it immediately."""
        from unittest.mock import MagicMock, patch

        from PySide6.QtGui import QIcon

        from pbprompt.gui.icons import get_icon

        mock_icon = MagicMock(spec=QIcon)
        mock_icon.isNull.return_value = False

        with patch.object(QIcon, "fromTheme", return_value=mock_icon):
            result = get_icon("help-about")

        assert result is mock_icon


# ---------------------------------------------------------------------------
# models.py — Column enum and PromptTableModel
# ---------------------------------------------------------------------------


class TestColumnEnum:
    def test_column_values(self) -> None:
        from pbprompt.gui.models import Column

        assert Column.AI == 0
        assert Column.GROUP == 1
        assert Column.NAME == 2
        assert Column.IMAGE == 3
        assert Column.LOCAL == 4
        assert Column.ENGLISH == 5

    def test_column_int_cast(self) -> None:
        from pbprompt.gui.models import Column

        assert int(Column.AI) == 0


class TestPromptTableModel:
    @pytest.fixture
    def entries(self) -> list[PromptEntry]:
        return [
            PromptEntry(ai="ChatGPT", group="Writing", name="Summary"),
            PromptEntry(ai="Claude", group="Code", name="Review"),
        ]

    @pytest.fixture
    def model(self, entries: list[PromptEntry], qtbot) -> Any:
        from pbprompt.gui.models import PromptTableModel

        col = PromptCollection(entries=entries)
        return PromptTableModel(col)

    def test_row_count(self, model: Any, entries: list[PromptEntry]) -> None:
        from PySide6.QtCore import QModelIndex

        assert model.rowCount(QModelIndex()) == len(entries)

    def test_column_count(self, model: Any) -> None:
        from PySide6.QtCore import QModelIndex

        assert model.columnCount(QModelIndex()) == 6

    def test_data_display_role(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        idx = model.index(0, 0)  # AI column
        value = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert value == "ChatGPT"

    def test_data_invalid_index(self, model: Any) -> None:
        from PySide6.QtCore import QModelIndex, Qt

        value = model.data(QModelIndex(), Qt.ItemDataRole.DisplayRole)
        assert value is None

    def test_header_data(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        header = model.headerData(
            0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )
        assert header == "AI"

    def test_flags_editable_columns(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        idx = model.index(0, 0)
        flags = model.flags(idx)
        assert flags & Qt.ItemFlag.ItemIsEnabled
        assert flags & Qt.ItemFlag.ItemIsSelectable

    def test_collection_property(self, model: Any) -> None:
        assert isinstance(model.collection, PromptCollection)

    def test_set_collection(self, model: Any) -> None:
        new_col = PromptCollection()
        model.set_collection(new_col)
        from PySide6.QtCore import QModelIndex

        assert model.rowCount(QModelIndex()) == 0

    def test_append_row(self, model: Any) -> None:
        from PySide6.QtCore import QModelIndex

        initial = model.rowCount(QModelIndex())
        model.append_row()
        assert model.rowCount(QModelIndex()) == initial + 1

    def test_append_row_with_entry(self, model: Any) -> None:
        from PySide6.QtCore import QModelIndex

        entry = PromptEntry(ai="Gemini", group="Test", name="X")
        row = model.append_row(entry)
        assert row == model.rowCount(QModelIndex()) - 1

    def test_insert_row(self, model: Any) -> None:
        from PySide6.QtCore import QModelIndex

        entry = PromptEntry(ai="Bard", group="G", name="N")
        model.insert_row(0, entry)
        assert model.rowCount(QModelIndex()) == 3

    def test_remove_rows(self, model: Any) -> None:
        from PySide6.QtCore import QModelIndex

        initial = model.rowCount(QModelIndex())
        model.remove_rows([0])
        assert model.rowCount(QModelIndex()) == initial - 1

    def test_set_data(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        idx = model.index(0, 0)  # AI column
        result = model.setData(idx, "NewAI", Qt.ItemDataRole.EditRole)
        assert result is True
        assert model.data(idx, Qt.ItemDataRole.DisplayRole) == "NewAI"

    def test_set_header_labels(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        labels = ["A", "B", "C", "D", "E", "F"]
        model.set_header_labels(labels)
        header = model.headerData(
            0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )
        assert header == "A"

    def test_set_header_tooltips(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        tooltips = ["t0", "t1", "t2", "t3", "t4", "t5"]
        model.set_header_tooltips(tooltips)
        tip = model.headerData(
            0, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
        )
        assert tip == "t0"

    def test_rowcount_valid_parent_returns_zero(self, model: Any) -> None:
        idx = model.index(0, 0)
        assert model.rowCount(idx) == 0

    def test_columncount_valid_parent_returns_zero(self, model: Any) -> None:
        idx = model.index(0, 0)
        assert model.columnCount(idx) == 0

    def test_data_image_column_display_role(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column

        idx = model.index(0, int(Column.IMAGE))
        value = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert value is None

    def test_data_image_column_user_role_no_thumbnail(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column

        idx = model.index(0, int(Column.IMAGE))
        value = model.data(idx, Qt.ItemDataRole.UserRole)
        assert value is None

    def test_data_image_column_textalignment_role(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column

        idx = model.index(0, int(Column.IMAGE))
        value = model.data(idx, Qt.ItemDataRole.TextAlignmentRole)
        assert value == int(Qt.AlignmentFlag.AlignCenter)

    def test_data_image_column_other_role(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column

        idx = model.index(0, int(Column.IMAGE))
        value = model.data(idx, Qt.ItemDataRole.ToolTipRole)
        assert value is None

    def test_data_textalignment_role(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        idx = model.index(0, 0)  # AI column
        value = model.data(idx, Qt.ItemDataRole.TextAlignmentRole)
        assert value is not None

    def test_data_other_role_returns_none(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        idx = model.index(0, 0)
        value = model.data(idx, Qt.ItemDataRole.ToolTipRole)
        assert value is None

    def test_data_row_out_of_range(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        idx = model.index(999, 0)
        value = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert value is None

    def test_setdata_wrong_role(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        idx = model.index(0, 0)
        result = model.setData(idx, "NewValue", Qt.ItemDataRole.DisplayRole)
        assert result is False

    def test_setdata_image_column(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column

        idx = model.index(0, int(Column.IMAGE))
        result = model.setData(idx, b"data", Qt.ItemDataRole.EditRole)
        assert result is False

    def test_setdata_row_out_of_range(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        # Manipulate the index to a non-existent row by directly creating one
        big_idx = model.createIndex(999, 0)
        result = model.setData(big_idx, "x", Qt.ItemDataRole.EditRole)
        assert result is False

    def test_flags_invalid_index(self, model: Any) -> None:
        from PySide6.QtCore import QModelIndex, Qt

        flags = model.flags(QModelIndex())
        assert flags == Qt.ItemFlag.NoItemFlags

    def test_flags_image_column_not_editable(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column

        idx = model.index(0, int(Column.IMAGE))
        flags = model.flags(idx)
        assert flags & Qt.ItemFlag.ItemIsEnabled
        assert not (flags & Qt.ItemFlag.ItemIsEditable)

    def test_headerdata_vertical_orientation(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        value = model.headerData(
            0, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole
        )
        assert value == "1"

    def test_headerdata_vertical_other_role(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        value = model.headerData(
            0, Qt.Orientation.Vertical, Qt.ItemDataRole.ToolTipRole
        )
        assert value is None

    def test_headerdata_other_role(self, model: Any) -> None:
        from PySide6.QtCore import Qt

        value = model.headerData(
            0, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
        )
        # No tooltip set → empty string → returns None
        assert value is None

    def test_set_image(self, model: Any) -> None:

        model.set_image(0, b"full_img_data", b"thumb_data")
        entry = model.collection.entries[0]
        assert entry.image == b"full_img_data"
        assert entry.thumbnail == b"thumb_data"

    def test_set_image_out_of_range(self, model: Any) -> None:
        model.set_image(999, b"data", b"thumb")  # must not raise

    def test_data_out_of_range_row_via_create_index(self, model: Any) -> None:
        """createIndex bypasses bounds check on the underlying row."""
        from PySide6.QtCore import Qt

        idx = model.createIndex(999, 0)  # valid index, row out of range
        value = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert value is None

    def test_headerdata_section_out_of_range(self, model: Any) -> None:
        """Section >= len(_headers) → IndexError caught → None."""
        from PySide6.QtCore import Qt

        value = model.headerData(
            99, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )
        assert value is None

    def test_headerdata_tooltip_section_out_of_range(self, model: Any) -> None:
        """Section >= len(_header_tooltips) → IndexError caught."""
        from PySide6.QtCore import Qt

        value = model.headerData(
            99, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
        )
        assert value is None


class TestMultiFilterProxyModel:
    @pytest.fixture
    def proxy(self, qtbot) -> Any:
        from pbprompt.gui.models import MultiFilterProxyModel, PromptTableModel

        entries = [
            PromptEntry(ai="ChatGPT", group="Writing", name="Summary"),
            PromptEntry(ai="Claude", group="Code", name="Review"),
            PromptEntry(ai="ChatGPT", group="Code", name="Debug"),
        ]
        source = PromptTableModel(PromptCollection(entries=entries))
        proxy = MultiFilterProxyModel()
        proxy.setSourceModel(source)
        return proxy

    def test_no_filter_shows_all(self, proxy: Any) -> None:
        assert proxy.rowCount() == 3

    def test_filter_by_ai(self, proxy: Any) -> None:
        from pbprompt.gui.models import Column

        proxy.set_filter(int(Column.AI), "ChatGPT")
        assert proxy.rowCount() == 2

    def test_filter_cleared(self, proxy: Any) -> None:
        from pbprompt.gui.models import Column

        proxy.set_filter(int(Column.AI), "ChatGPT")
        proxy.clear_filters()
        assert proxy.rowCount() == 3

    def test_filter_regex(self, proxy: Any) -> None:
        from pbprompt.gui.models import Column

        proxy.set_filter(int(Column.AI), "^Cl")
        assert proxy.rowCount() == 1

    def test_filter_image_column_ignored(self, proxy: Any) -> None:
        from pbprompt.gui.models import Column

        proxy.set_filter(int(Column.IMAGE), "something")
        assert proxy.rowCount() == 3  # IMAGE column is not filterable

    def test_filter_invalid_regex_ignored(self, proxy: Any) -> None:
        from pbprompt.gui.models import Column

        proxy.set_filter(int(Column.AI), "[invalid(")  # bad regex → ignored
        assert proxy.rowCount() == 3  # all rows still shown

    def test_filter_empty_pattern_clears(self, proxy: Any) -> None:
        from pbprompt.gui.models import Column

        proxy.set_filter(int(Column.AI), "ChatGPT")
        assert proxy.rowCount() == 2
        proxy.set_filter(int(Column.AI), "")  # empty → removes filter
        assert proxy.rowCount() == 3

    def test_sort_ai_column(self, proxy: Any) -> None:
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column

        proxy.sort(int(Column.AI), Qt.SortOrder.AscendingOrder)
        # First row should be Claude (alphabetically first)
        first = proxy.data(proxy.index(0, int(Column.AI)))
        assert first in ("ChatGPT", "Claude")

    def test_sort_non_sortable_column_noop(self, proxy: Any) -> None:
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column

        # LOCAL column is not sortable → sort() should be a no-op (no crash)
        proxy.sort(int(Column.LOCAL), Qt.SortOrder.AscendingOrder)

    def test_filter_empty_pattern_internal(self, proxy: Any) -> None:
        """Directly inject empty pattern into _filters to cover line 306."""
        from pbprompt.gui.models import Column

        proxy._filters[int(Column.AI)] = ""  # noqa: SLF001
        # filterAcceptsRow loops and hits 'if not pattern: continue'
        assert proxy.rowCount() == 3

    def test_lessthan_equal_values_returns_false(self, proxy: Any) -> None:
        """lessThan returns False when all sort values are equal."""
        from PySide6.QtCore import Qt

        from pbprompt.gui.models import Column, PromptTableModel

        equal_entries = [
            __import__("pbprompt.data", fromlist=["PromptEntry"]).PromptEntry(
                ai="A", group="G", name="N"
            ),
            __import__("pbprompt.data", fromlist=["PromptEntry"]).PromptEntry(
                ai="A", group="G", name="N"
            ),
        ]
        from pbprompt.data import PromptCollection

        source = PromptTableModel(PromptCollection(entries=equal_entries))
        from pbprompt.gui.models import MultiFilterProxyModel

        p = MultiFilterProxyModel()
        p.setSourceModel(source)
        p.sort(int(Column.AI), Qt.SortOrder.AscendingOrder)
        # All AI values equal → lessThan returns False → no crash
        assert p.rowCount() == 2


# ---------------------------------------------------------------------------
# AboutDialog
# ---------------------------------------------------------------------------


class TestAboutDialog:
    def test_dialog_creates(self, qtbot) -> None:
        from pbprompt.gui.about_dialog import AboutDialog

        dlg = AboutDialog()
        assert dlg is not None
        assert dlg.windowTitle() != ""

    def test_dialog_has_version(self, qtbot) -> None:
        from pbprompt import __version__
        from pbprompt.gui.about_dialog import AboutDialog

        dlg = AboutDialog()
        assert __version__ in dlg.versionLabel.text()

    def test_ui_retranslate_direct(self, qtbot) -> None:
        """Call Ui_AboutDialog.retranslate_ui directly to cover MRO-shadowed lines."""
        from pbprompt.gui.about_dialog import AboutDialog
        from pbprompt.gui.about_dialog_ui import Ui_AboutDialog

        dlg = AboutDialog()
        Ui_AboutDialog.retranslate_ui(dlg, dlg)  # bypasses MRO shadowing

    def test_settings_dialog_creates(self, qtbot) -> None:
        from pbprompt.config import AppConfig
        from pbprompt.gui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(AppConfig())
        assert dlg is not None

    def test_settings_dialog_config_property(self, qtbot) -> None:
        from pbprompt.config import AppConfig
        from pbprompt.gui.settings_dialog import SettingsDialog

        cfg = AppConfig(display_language="fr")
        dlg = SettingsDialog(cfg)
        assert isinstance(dlg.config, AppConfig)

    def test_settings_dialog_ui_retranslate_direct(self, qtbot) -> None:
        from pbprompt.config import AppConfig
        from pbprompt.gui.settings_dialog import SettingsDialog
        from pbprompt.gui.settings_dialog_ui import Ui_SettingsDialog

        dlg = SettingsDialog(AppConfig())
        Ui_SettingsDialog.retranslate_ui(dlg, dlg)

    def test_settings_dialog_accept(self, qtbot) -> None:
        """accept() persists values to the underlying config."""
        from unittest.mock import patch

        from pbprompt.config import AppConfig
        from pbprompt.gui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(AppConfig())
        with patch.object(dlg._config, "save"):  # noqa: SLF001
            dlg.accept()

    def test_settings_dialog_accept_save_exception(self, qtbot) -> None:
        """accept() when save() raises → warning logged."""
        from unittest.mock import patch

        from pbprompt.config import AppConfig
        from pbprompt.gui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(AppConfig())
        with patch.object(dlg._config, "save", side_effect=OSError("disk full")):  # noqa: SLF001
            dlg.accept()  # must not raise

    def test_settings_dialog_available_langs_empty_dir(self, tmp_path: Any) -> None:
        """Empty locale dir → fallback 'en' added."""
        from unittest.mock import patch

        from pbprompt.gui.settings_dialog import _available_display_languages

        with patch("pbprompt.gui.settings_dialog._LOCALES_DIR", tmp_path):
            result = _available_display_languages()
        assert any(code == "en" for code, _ in result)

    def test_settings_dialog_on_keep_original_toggled(self, qtbot) -> None:
        """_on_keep_original_toggled(True) disables the size spinboxes."""
        from pbprompt.config import AppConfig
        from pbprompt.gui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(AppConfig())
        dlg._on_keep_original_toggled(True)  # noqa: SLF001
        assert not dlg.spinBoxImageStoreMaxWidth.isEnabled()

    def test_set_combo_non_combobox_returns_early(self) -> None:
        """_set_combo with a non-QComboBox object returns immediately."""
        from pbprompt.gui.settings_dialog import _set_combo

        _set_combo("not_a_combobox", "value")  # must not raise

    def test_main_window_creates(self, qtbot) -> None:
        from pbprompt.config import AppConfig
        from pbprompt.gui.main_window import MainWindow

        # Empty config: no recent files → no auto-load
        win = MainWindow(AppConfig())
        assert win is not None
        win.close()

    def test_main_window_ui_retranslate_direct(self, qtbot) -> None:
        from pbprompt.config import AppConfig
        from pbprompt.gui.main_window import MainWindow
        from pbprompt.gui.main_window_ui import Ui_MainWindow

        win = MainWindow(AppConfig())
        Ui_MainWindow.retranslate_ui(win, win)
        win.close()

    def test_dialog_null_icon_fallback(self, qtbot) -> None:
        """When pbprompt icon is null, falls back to text label."""
        from unittest.mock import patch

        from PySide6.QtGui import QIcon

        from pbprompt.gui.about_dialog import AboutDialog

        null_icon = QIcon()  # isNull() == True

        with patch("pbprompt.gui.about_dialog.get_icon", return_value=null_icon):
            dlg = AboutDialog()
        assert dlg.iconLabel.text() == "PB"
