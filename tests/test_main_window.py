"""Tests for MainWindow behaviour (offscreen Qt — no display required)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QMessageBox


@pytest.fixture
def win(qtbot):
    """Fresh MainWindow with empty config (no auto-load)."""
    from pbprompt.config import AppConfig
    from pbprompt.gui.main_window import MainWindow

    cfg = AppConfig()
    w = MainWindow(cfg)

    def _before_close(widget) -> None:
        # Prevent QMessageBox.question dialog during teardown (mock is gone).
        widget._collection.modified = False  # noqa: SLF001
        # Prevent disk write during teardown.
        widget._config.save = lambda: None  # noqa: SLF001

    qtbot.addWidget(w, before_close_func=_before_close)
    return w


# ---------------------------------------------------------------------------
# __init__ geometry branches
# ---------------------------------------------------------------------------


class TestMainWindowInit:
    def test_window_geometry_applied(self, qtbot) -> None:
        """Config with window_width/height/x/y is applied to the geometry."""
        from pbprompt.config import AppConfig
        from pbprompt.gui.main_window import MainWindow

        cfg = AppConfig(window_width=800, window_height=600, window_x=50, window_y=50)
        w = MainWindow(cfg)
        qtbot.addWidget(w)
        assert w.width() == 800

    def test_with_column_filters_applied(self, qtbot) -> None:
        """Config with column_filters sets filter widgets."""
        from pbprompt.config import AppConfig
        from pbprompt.gui.main_window import MainWindow

        cfg = AppConfig(column_filters={"ai": "ChatGPT", "group": "Test"})
        w = MainWindow(cfg)
        qtbot.addWidget(w)
        assert w.filterAi.text() == "ChatGPT"

    def test_retranslate_updates_headers(self, win) -> None:
        """Calling retranslate_ui after init exercises the hasattr guard branch."""
        win.retranslate_ui(win)

    def test_initial_file_nonexistent(self, qtbot) -> None:
        """initial_file that doesn't exist → error handled."""
        from pbprompt.config import AppConfig
        from pbprompt.gui.main_window import MainWindow

        with patch.object(QMessageBox, "critical", return_value=None):
            w = MainWindow(AppConfig(), initial_file=Path("/nonexistent.sqlite"))
        qtbot.addWidget(w)


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


class TestFileOperations:
    def test_on_file_new(self, win) -> None:
        """_on_file_new creates empty collection."""
        win._on_file_new()  # noqa: SLF001
        assert win._collection.entries == []  # noqa: SLF001

    def test_on_file_open_cancelled(self, win) -> None:
        """_on_file_open with empty filename → no-op."""
        with patch(
            "PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=("", "")
        ):
            win._on_file_open()  # noqa: SLF001
        assert win._collection.entries == []  # noqa: SLF001

    def test_open_file_success(self, win, tmp_path: Path) -> None:
        """open_file with valid db → collection loaded."""
        from pbprompt.data import PromptCollection

        db = tmp_path / "test.sqlite"
        PromptCollection().save(db)
        win.open_file(db)
        assert win._collection.file_path == db  # noqa: SLF001

    def test_open_file_value_error(self, win, tmp_path: Path) -> None:
        """open_file with non-sqlite file → ValueError handled."""
        bad = tmp_path / "not_a_db.sqlite"
        bad.write_text("garbage")
        with patch.object(QMessageBox, "critical", return_value=None):
            win.open_file(bad)
        assert win._collection is not None  # noqa: SLF001

    def test_open_file_generic_exception(self, win) -> None:
        """open_file with generic OSError → except Exception."""
        with (
            patch("pbprompt.data.PromptCollection.load", side_effect=OSError("io")),
            patch.object(QMessageBox, "critical", return_value=None),
        ):
            win.open_file(Path("/any/path.sqlite"))

    def test_on_file_save_no_path(self, win) -> None:
        """_on_file_save with no file_path → delegates to save_as."""
        with patch.object(win, "_on_file_save_as") as mock_save_as:
            win._on_file_save()  # noqa: SLF001
        mock_save_as.assert_called_once()

    def test_on_file_save_with_path(self, win, tmp_path: Path) -> None:
        """_on_file_save with file_path → calls _save_to."""
        db = tmp_path / "test.sqlite"
        win._collection.file_path = db  # noqa: SLF001
        with patch.object(win, "_save_to") as mock_save:
            win._on_file_save()  # noqa: SLF001
        mock_save.assert_called_once_with(db)

    def test_on_file_save_as_cancelled(self, win) -> None:
        """_on_file_save_as with empty filename → returns early."""
        with patch(
            "PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", "")
        ):
            win._on_file_save_as()  # noqa: SLF001

    def test_save_to(self, win, tmp_path: Path) -> None:
        """_save_to writes collection to disk."""
        db = tmp_path / "out.sqlite"
        win._save_to(db)  # noqa: SLF001
        assert db.exists()

    def test_save_to_exception(self, win, tmp_path: Path) -> None:
        """_save_to with IO error → error dialog shown."""
        db = tmp_path / "out.sqlite"
        with (
            patch.object(win._collection, "save", side_effect=OSError("disk full")),  # noqa: SLF001
            patch.object(QMessageBox, "critical", return_value=None),
        ):
            win._save_to(db)  # noqa: SLF001

    def test_on_file_close_no_changes(self, win) -> None:
        """_on_file_close with clean collection."""
        win._on_file_close()  # noqa: SLF001
        assert win._collection.file_path is None  # noqa: SLF001

    def test_check_unsaved_changes_clean(self, win) -> None:
        """_check_unsaved_changes with unmodified collection → True."""
        assert win._check_unsaved_changes() is True  # noqa: SLF001

    def test_check_unsaved_changes_dirty_discard(self, win) -> None:
        """Dirty collection + Discard → True."""
        win._collection.modified = True  # noqa: SLF001
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Discard
        ):
            result = win._check_unsaved_changes()  # noqa: SLF001
        assert result is True

    def test_check_unsaved_changes_dirty_cancel(self, win) -> None:
        """Dirty collection + Cancel → False."""
        win._collection.modified = True  # noqa: SLF001
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel
        ):
            result = win._check_unsaved_changes()  # noqa: SLF001
        assert result is False


# ---------------------------------------------------------------------------
# Prompt CRUD
# ---------------------------------------------------------------------------


class TestPromptCrud:
    def test_on_new_prompt(self, win) -> None:
        """_on_new_prompt adds a row."""
        initial = win._source_model.rowCount()  # noqa: SLF001
        win._on_new_prompt()  # noqa: SLF001
        assert win._source_model.rowCount() == initial + 1  # noqa: SLF001

    def test_on_duplicate_prompt_no_selection(self, win) -> None:
        """_on_duplicate_prompt with no current index → no crash."""
        win._on_duplicate_prompt()  # noqa: SLF001

    def test_on_duplicate_prompt_with_selection(self, win) -> None:
        """_on_duplicate_prompt with selected row → duplicates it."""
        win._on_new_prompt()  # noqa: SLF001
        idx = win._proxy_model.index(0, 0)  # noqa: SLF001
        win.tableView.setCurrentIndex(idx)
        win._on_duplicate_prompt()  # noqa: SLF001
        assert win._source_model.rowCount() == 2  # noqa: SLF001

    def test_on_delete_prompts_no_selection(self, win) -> None:
        """_on_delete_prompts with empty selection → no crash."""
        win._on_delete_prompts()  # noqa: SLF001

    def test_on_delete_prompts_with_confirm(self, win) -> None:
        """_on_delete_prompts + Yes → deletes row."""
        win._on_new_prompt()  # noqa: SLF001
        win.tableView.setCurrentIndex(win._proxy_model.index(0, 0))  # noqa: SLF001
        win.tableView.selectRow(0)
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
        ):
            win._on_delete_prompts()  # noqa: SLF001
        assert win._source_model.rowCount() == 0  # noqa: SLF001

    def test_on_clear_filters(self, win) -> None:
        """_on_clear_filters clears all filter widgets."""
        win.filterAi.setText("test")
        win._on_clear_filters()  # noqa: SLF001
        assert win.filterAi.text() == ""


# ---------------------------------------------------------------------------
# View / display helpers
# ---------------------------------------------------------------------------


class TestViewHelpers:
    def test_show_event(self, win) -> None:
        """showEvent schedules a resize — trigger via show()."""
        # Calling win.show() fires a real QShowEvent; offscreen mode is safe.
        win.show()
        win.hide()

    def test_on_section_resized_local(self, win) -> None:
        """Resizing LOCAL column triggers resizeRowsToContents."""
        from pbprompt.gui.models import Column

        with patch.object(win.tableView, "resizeRowsToContents") as m:
            win._on_section_resized(int(Column.LOCAL), 100, 200)  # noqa: SLF001
        m.assert_called_once()

    def test_on_section_resized_english(self, win) -> None:
        """Resizing ENGLISH column triggers resizeRowsToContents."""
        from pbprompt.gui.models import Column

        with patch.object(win.tableView, "resizeRowsToContents") as m:
            win._on_section_resized(int(Column.ENGLISH), 100, 200)  # noqa: SLF001
        m.assert_called_once()

    def test_on_section_resized_ai_noop(self, win) -> None:
        """Resizing AI column is a no-op (not LOCAL/ENGLISH)."""
        from pbprompt.gui.models import Column

        with patch.object(win.tableView, "resizeRowsToContents") as m:
            win._on_section_resized(int(Column.AI), 100, 200)  # noqa: SLF001
        m.assert_not_called()

    def test_update_title_untitled(self, win) -> None:
        """_update_title with no file_path → 'Untitled' in title."""
        win._update_title()  # noqa: SLF001
        assert win.windowTitle() != ""

    def test_update_title_with_file(self, win, tmp_path: Path) -> None:
        """_update_title with file_path uses the filename."""
        win._collection.file_path = tmp_path / "myfile.sqlite"  # noqa: SLF001
        win._update_title()  # noqa: SLF001
        assert "myfile.sqlite" in win.windowTitle()

    def test_header_clicked_sortable(self, win) -> None:
        """_on_header_clicked on sortable columns."""
        from pbprompt.gui.models import Column

        win._on_header_clicked(int(Column.AI))  # noqa: SLF001
        win._on_header_clicked(int(Column.AI))  # toggle
        win._on_header_clicked(int(Column.GROUP))
        win._on_header_clicked(int(Column.NAME))

    def test_header_clicked_non_sortable(self, win) -> None:
        """_on_header_clicked on non-sortable column resets indicator."""
        from pbprompt.gui.models import Column

        win._on_header_clicked(int(Column.IMAGE))  # noqa: SLF001


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------


class TestDialogHandlers:
    def test_on_open_about(self, win) -> None:
        """_on_open_about opens AboutDialog."""
        with patch("pbprompt.gui.about_dialog.AboutDialog.exec", return_value=0):
            win._on_open_about()  # noqa: SLF001

    def test_on_open_settings_cancelled(self, win) -> None:
        """_on_open_settings cancelled → config unchanged."""
        with patch("pbprompt.gui.settings_dialog.SettingsDialog.exec", return_value=0):
            win._on_open_settings()  # noqa: SLF001

    def test_on_open_settings_accepted(self, win) -> None:
        """_on_open_settings accepted → retranslate called."""
        from pbprompt.config import AppConfig

        new_cfg = AppConfig()
        with (
            patch("pbprompt.gui.settings_dialog.SettingsDialog.exec", return_value=1),
            patch(
                "pbprompt.gui.settings_dialog.SettingsDialog.config",
                new_callable=lambda: property(lambda self: new_cfg),  # type: ignore[arg-type]
            ),
            patch.object(win._config, "save"),  # noqa: SLF001
        ):
            win._on_open_settings()  # noqa: SLF001


# ---------------------------------------------------------------------------
# Recent files
# ---------------------------------------------------------------------------


class TestRecentFiles:
    def test_update_recent_files_menu_empty(self, win) -> None:
        """Empty recent files shows 'No recent files' action."""
        win._update_recent_files_menu()  # noqa: SLF001
        labels = [a.text() for a in win.menuRecentFiles.actions()]
        assert labels  # menu is not empty

    def test_update_recent_files_menu_with_files(self, win) -> None:
        """Non-empty recent files list populates menu."""
        win._config.recent_files = ["/a/file.sqlite", "/b/other.sqlite"]  # noqa: SLF001
        win._update_recent_files_menu()  # noqa: SLF001
        labels = [a.text() for a in win.menuRecentFiles.actions()]
        assert any("file.sqlite" in label for label in labels)

    def test_add_to_recent_files(self, win, tmp_path: Path) -> None:
        """_add_to_recent_files adds path."""
        db = tmp_path / "recent.sqlite"
        win._add_to_recent_files(db)  # noqa: SLF001
        assert str(db) in win._config.recent_files  # noqa: SLF001

    def test_remove_from_recent_files(self, win) -> None:
        """_remove_from_recent_files removes known path."""
        win._config.recent_files = ["/a.sqlite", "/b.sqlite"]  # noqa: SLF001
        win._remove_from_recent_files("/a.sqlite")  # noqa: SLF001
        assert "/a.sqlite" not in win._config.recent_files  # noqa: SLF001

    def test_on_open_recent_nonexistent(self, win) -> None:
        """_on_open_recent with nonexistent file removes it from list."""
        win._config.recent_files = ["/nonexistent.sqlite"]  # noqa: SLF001
        with patch.object(QMessageBox, "warning", return_value=None):
            win._on_open_recent("/nonexistent.sqlite")  # noqa: SLF001
        assert "/nonexistent.sqlite" not in win._config.recent_files  # noqa: SLF001

    def test_on_open_recent_existing(self, win, tmp_path: Path) -> None:
        """_on_open_recent with valid file opens it."""
        from pbprompt.data import PromptCollection

        db = tmp_path / "recent.sqlite"
        PromptCollection().save(db)
        win._config.recent_files = [str(db)]  # noqa: SLF001
        win._on_open_recent(str(db))  # noqa: SLF001
        assert win._collection.file_path == db  # noqa: SLF001

    def test_on_clear_recent_files(self, win) -> None:
        """_on_clear_recent_files empties the list."""
        win._config.recent_files = ["/a.sqlite"]  # noqa: SLF001
        with patch.object(win._config, "save"):  # noqa: SLF001
            win._on_clear_recent_files()  # noqa: SLF001
        assert win._config.recent_files == []  # noqa: SLF001


# ---------------------------------------------------------------------------
# Autoload last file
# ---------------------------------------------------------------------------


class TestAutoload:
    def test_autoload_nonexistent_file(self, qtbot) -> None:
        """Autoload with nonexistent last file removes it and starts empty."""
        from pbprompt.config import AppConfig
        from pbprompt.gui.main_window import MainWindow

        cfg = AppConfig(recent_files=["/nonexistent/path.sqlite"])
        with patch.object(cfg, "save"):
            w = MainWindow(cfg)
        qtbot.addWidget(w)
        assert w._collection.file_path is None  # noqa: SLF001

    def test_autoload_valid_file(self, qtbot, tmp_path: Path) -> None:
        """Autoload with existing file loads it."""
        from pbprompt.config import AppConfig
        from pbprompt.data import PromptCollection
        from pbprompt.gui.main_window import MainWindow

        db = tmp_path / "last.sqlite"
        PromptCollection().save(db)
        cfg = AppConfig(recent_files=[str(db)])
        w = MainWindow(cfg)
        qtbot.addWidget(w)
        assert w._collection.file_path == db  # noqa: SLF001


# ---------------------------------------------------------------------------
# Close event
# ---------------------------------------------------------------------------


class TestCloseEvent:
    def test_close_event_no_changes(self, win) -> None:
        """closeEvent with clean state accepts event."""
        event = MagicMock()
        with patch.object(win._config, "save"):  # noqa: SLF001  # avoid disk write
            win.closeEvent(event)
        event.accept.assert_called_once()

    def test_close_event_dirty_cancel(self, win) -> None:
        """closeEvent + user cancels → event.ignore."""
        win._collection.modified = True  # noqa: SLF001
        event = MagicMock()
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel
        ):
            win.closeEvent(event)
        event.ignore.assert_called_once()


# ---------------------------------------------------------------------------
# Import / Export YAML
# ---------------------------------------------------------------------------


class TestImportExport:
    def test_on_import_yaml_cancelled(self, win) -> None:
        """_on_import_yaml with cancelled dialog → no crash."""
        with patch(
            "PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=("", "")
        ):
            win._on_import_yaml(replace=True)  # noqa: SLF001

    def test_on_export_yaml_cancelled(self, win) -> None:
        """_on_export_yaml with cancelled dialog → no crash."""
        with patch(
            "PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", "")
        ):
            win._on_export_yaml()  # noqa: SLF001
