"""Main application window – behaviour on top of the generated UI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHeaderView,
    QMainWindow,
    QMenu,
    QMessageBox,
)

from pbprompt import __app_name__, __version__
from pbprompt.data import PromptCollection, PromptEntry
from pbprompt.gui.icons import get_icon
from pbprompt.gui.models import (
    Column,
    CurrentCellHighlightDelegate,
    ImageDelegate,
    MultiFilterProxyModel,
    MultiLineDelegate,
    PromptTableModel,
)
from pbprompt.gui.ui_main_window import Ui_MainWindow
from pbprompt.i18n import get_translate, language_label, system_language

if TYPE_CHECKING:
    from pbprompt.config import AppConfig

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main PBPrompt window.

    Parameters
    ----------
    config:
        Application configuration instance.
    parent:
        Optional Qt parent widget.
    """

    def __init__(
        self,
        config: AppConfig,
        initial_file: Path | None = None,
        parent: None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config

        # Set up the UI from the generated Ui_MainWindow
        self.setupUi(self)

        # Override retranslateUi strings with gettext immediately
        self.retranslateUi(self)

        # Data layer
        self._collection = PromptCollection()

        # Qt models
        self._source_model = PromptTableModel(self._collection, parent=self)
        self._proxy_model = MultiFilterProxyModel(parent=self)
        self._proxy_model.setSourceModel(self._source_model)
        self.tableView.setModel(self._proxy_model)

        # Set column headers now that _source_model exists (retranslateUi ran
        # before the model was created, so the local-language header must be
        # applied explicitly here).
        self._source_model.set_header_labels(
            [
                self._("AI"),
                self._("Group"),
                self._("Name"),
                self._("Image"),
                language_label(self._config.translation_language or system_language()),
                self._("English"),
            ]
        )
        _edit_tip = self._(
            "Enter: confirm  ·  Ctrl+Enter or Shift+Enter: insert new line\n"
            "Tab / Shift+Tab: move to adjacent cell  ·  Esc: cancel"
        )
        self._source_model.set_header_tooltips(
            [
                self._("AI model name.\nSort: primary AI → Group → Name"),
                self._("Prompt group / category.\nSort: primary Group → Name → AI"),
                self._("Prompt title.\nSort: primary Name → Group → AI"),
                self._("Double-click to view · Right-click for options"),
                self._("Prompt in local language.\n") + _edit_tip,
                self._("Prompt in English.\n") + _edit_tip,
            ]
        )

        # Column sizing
        hdr = self.tableView.horizontalHeader()
        hdr.setSectionResizeMode(Column.AI, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(Column.GROUP, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(Column.NAME, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(Column.IMAGE, QHeaderView.Fixed)
        self.tableView.setColumnWidth(Column.IMAGE, self._config.thumbnail_width + 12)
        hdr.setSectionResizeMode(Column.LOCAL, QHeaderView.Stretch)
        hdr.setSectionResizeMode(Column.ENGLISH, QHeaderView.Stretch)
        hdr.setSortIndicatorShown(True)

        # Multi-line delegate for the two text columns
        _ml_delegate = MultiLineDelegate(self.tableView, parent=self)
        self.tableView.setItemDelegateForColumn(Column.LOCAL, _ml_delegate)
        self.tableView.setItemDelegateForColumn(Column.ENGLISH, _ml_delegate)
        self.tableView.setWordWrap(True)

        # Image delegate for the IMAGE column
        self._image_delegate = ImageDelegate(
            self.tableView,
            thumb_w=self._config.thumbnail_width,
            thumb_h=self._config.thumbnail_height,
            parent=self,
        )
        self.tableView.setItemDelegateForColumn(Column.IMAGE, self._image_delegate)

        # Current-cell highlight delegate for the three short columns
        _cc_delegate = CurrentCellHighlightDelegate(self.tableView, parent=self)
        self.tableView.setItemDelegateForColumn(Column.AI, _cc_delegate)
        self.tableView.setItemDelegateForColumn(Column.GROUP, _cc_delegate)
        self.tableView.setItemDelegateForColumn(Column.NAME, _cc_delegate)

        # Context menu
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)

        # Sort state – tracked here to avoid relying on QHeaderView internal state,
        # which can be reset by signals emitted during QSortFilterProxyModel.sort().
        self._sort_col: int = Column.AI
        self._sort_order: Qt.SortOrder = Qt.AscendingOrder

        hdr.sectionClicked.connect(self._on_header_clicked)
        self._proxy_model.sort(self._sort_col, self._sort_order)
        hdr.setSortIndicator(self._sort_col, self._sort_order)

        # Icons
        self._apply_icons()

        # Connect signals
        self._connect_signals()

        # Recent files menu (initial population)
        self._update_recent_files_menu()

        self._update_title()
        self.statusBar().showMessage(self._("Ready"))

        # Restore window geometry saved on last exit
        if config.window_width is not None and config.window_height is not None:
            self.resize(config.window_width, config.window_height)
        if config.window_x is not None and config.window_y is not None:
            self.move(config.window_x, config.window_y)

        # File to open at startup: CLI argument takes priority over last-used file
        if initial_file is not None:
            self._open_initial_file(initial_file)
        else:
            self._autoload_last_file()

    # ------------------------------------------------------------------
    # retranslateUi override – uses gettext
    # ------------------------------------------------------------------

    def retranslateUi(self, widget: QMainWindow) -> None:  # type: ignore[override]  # noqa: N802
        """Override the generated retranslate to use gettext strings."""
        _ = get_translate()
        self._ = _  # convenient shorthand

        widget.setWindowTitle(__app_name__)

        self.filterLabel.setText(_("Filter:"))
        self.filterAi.setPlaceholderText(_("AI…"))
        self.filterGroup.setPlaceholderText(_("Group…"))
        self.filterName.setPlaceholderText(_("Name…"))
        self.filterLocal.setPlaceholderText(_("Local language…"))
        self.filterEnglish.setPlaceholderText(_("English…"))
        self.clearFiltersButton.setText(_("Clear"))
        self.clearFiltersButton.setToolTip(_("Clear all filters"))

        self.menuFile.setTitle(_("&File"))
        self.menuTools.setTitle(_("&Tools"))
        self.menuHelp.setTitle(_("&Help"))

        self.actionFileNew.setText(_("&New"))
        self.actionFileNew.setToolTip(_("New file"))
        self.actionFileOpen.setText(_("&Open…"))
        self.actionFileOpen.setToolTip(_("Open a prompt file"))
        self.actionFileSave.setText(_("&Save"))
        self.actionFileSave.setToolTip(_("Save the current file"))
        self.actionFileSaveAs.setText(_("Save &As…"))
        self.actionFileSaveAs.setToolTip(_("Save to a new file"))
        self.actionFileClose.setText(_("&Close"))
        self.actionFileClose.setToolTip(_("Close current file"))
        self.actionFileQuit.setText(_("&Quit"))
        self.actionFileQuit.setToolTip(_("Quit PBPrompt"))
        self.actionToolsOptions.setText(_("&Options…"))
        self.actionToolsOptions.setToolTip(_("Open settings dialog"))
        self.actionHelpAbout.setText(_("&About…"))
        self.actionHelpAbout.setToolTip(_("About PBPrompt"))
        self.actionNewPrompt.setText(_("New Prompt"))
        self.actionNewPrompt.setToolTip(_("Add a new prompt entry"))
        self.actionDuplicatePrompt.setText(_("Duplicate"))
        self.actionDuplicatePrompt.setToolTip(_("Duplicate the current row"))
        self.actionDeletePrompts.setText(_("Delete"))
        self.actionDeletePrompts.setToolTip(_("Delete selected prompts"))
        self.actionTranslateToEnglish.setText(_("→ English"))
        self.actionTranslateToEnglish.setToolTip(
            _("Translate selected rows to English")
        )
        self.actionTranslateFromEnglish.setText(_("← Local"))
        self.actionTranslateFromEnglish.setToolTip(
            _("Translate selected rows from English")
        )
        self.menuImportYaml.setTitle(_("Import &YAML"))
        self.actionImportYamlAdd.setText(_("Add entries…"))
        self.actionImportYamlAdd.setToolTip(_("Import YAML file (append)"))
        self.actionImportYamlReplace.setText(_("Replace all…"))
        self.actionImportYamlReplace.setToolTip(_("Import YAML file (replace all)"))
        self.actionExportYaml.setText(_("Export &YAML…"))
        self.actionExportYaml.setToolTip(_("Export YAML file"))
        self.actionRefreshThumbnails.setText(_("Refresh Thumbnails"))
        self.actionRefreshThumbnails.setToolTip(
            _("Regenerate all thumbnails from stored images")
        )

        self.menuRecentFiles.setTitle(_("Recent &Files"))

        # Keyboard shortcuts — set here because Ui_MainWindow.retranslateUi is
        # shadowed by this override (Python MRO) and therefore never called at
        # runtime.  Shortcuts are language-independent but must be applied on
        # every retranslateUi call so they survive a language change.
        self.actionFileNew.setShortcut(QKeySequence("Ctrl+N"))
        self.actionFileOpen.setShortcut(QKeySequence("Ctrl+O"))
        self.actionFileSave.setShortcut(QKeySequence("Ctrl+S"))
        self.actionFileSaveAs.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.actionFileClose.setShortcut(QKeySequence("Ctrl+W"))
        self.actionFileQuit.setShortcut(QKeySequence("Ctrl+Q"))
        self.actionToolsOptions.setShortcut(QKeySequence("Ctrl+,"))
        self.actionNewPrompt.setShortcut(QKeySequence("Ins"))
        self.actionDuplicatePrompt.setShortcut(QKeySequence("Ctrl+D"))
        self.actionDeletePrompts.setShortcut(QKeySequence("Del"))
        self.actionTranslateToEnglish.setShortcut(QKeySequence("F6"))
        self.actionTranslateFromEnglish.setShortcut(QKeySequence("F7"))
        self.actionImportYamlAdd.setShortcut(QKeySequence("Ctrl+I"))
        self.actionImportYamlReplace.setShortcut(QKeySequence("Ctrl+Shift+I"))
        self.actionExportYaml.setShortcut(QKeySequence("Ctrl+E"))

        # Column headers
        if hasattr(self, "_source_model"):
            self._source_model.set_header_labels(
                [
                    _("AI"),
                    _("Group"),
                    _("Name"),
                    _("Image"),
                    language_label(
                        self._config.translation_language or system_language()
                    ),
                    _("English"),
                ]
            )
            _edit_tip = _(
                "Enter: confirm  ·  Ctrl+Enter or Shift+Enter: insert new line\n"
                "Tab / Shift+Tab: move to adjacent cell  ·  Esc: cancel"
            )
            self._source_model.set_header_tooltips(
                [
                    _("AI model name.\nSort: primary AI → Group → Name"),
                    _("Prompt group / category.\nSort: primary Group → Name → AI"),
                    _("Prompt title.\nSort: primary Name → Group → AI"),
                    _("Double-click to view · Right-click for options"),
                    _("Prompt in local language.\n") + _edit_tip,
                    _("Prompt in English.\n") + _edit_tip,
                ]
            )

        # Status bar tips: rebuild after every retranslate (tooltips may have changed)
        self._update_status_tips()

    # ------------------------------------------------------------------
    # Status bar tips
    # ------------------------------------------------------------------

    def _update_status_tips(self) -> None:
        """Set each action's status tip from its translated tool tip and shortcut.

        Qt automatically shows the ``statusTip`` of the currently hovered
        action in the main window's status bar — for both menu items and
        toolbar buttons.  We build it from the already-translated
        ``toolTip()`` and the action's shortcut key so the status bar
        always displays a useful description with the matching shortcut.
        """
        for action in self.findChildren(QAction):
            tip = action.toolTip()
            if not tip:
                continue
            sc = action.shortcut().toString()
            action.setStatusTip(f"{tip}  ({sc})" if sc else tip)

    # ------------------------------------------------------------------
    # Icon setup
    # ------------------------------------------------------------------

    def _apply_icons(self) -> None:
        """Assign icons to actions and window."""
        self.setWindowIcon(get_icon("app"))
        self.actionFileNew.setIcon(get_icon("new"))
        self.actionFileOpen.setIcon(get_icon("open"))
        self.actionFileSave.setIcon(get_icon("save"))
        self.actionFileSaveAs.setIcon(get_icon("save_as"))
        self.actionFileQuit.setIcon(get_icon("quit"))
        self.actionNewPrompt.setIcon(get_icon("new_prompt"))
        self.actionDuplicatePrompt.setIcon(get_icon("duplicate"))
        self.actionDeletePrompts.setIcon(get_icon("delete"))
        self.actionToolsOptions.setIcon(get_icon("options"))
        self.actionHelpAbout.setIcon(get_icon("about"))
        self.actionTranslateToEnglish.setIcon(get_icon("translate_right"))
        self.actionTranslateFromEnglish.setIcon(get_icon("translate_left"))
        self.actionImportYamlAdd.setIcon(get_icon("import_yaml"))
        self.actionImportYamlReplace.setIcon(get_icon("import_yaml"))
        self.actionExportYaml.setIcon(get_icon("export_yaml"))
        self.actionRefreshThumbnails.setIcon(get_icon("refresh_thumbnails"))

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # File menu
        self.actionFileNew.triggered.connect(self._on_file_new)
        self.actionFileOpen.triggered.connect(self._on_file_open)
        self.actionFileSave.triggered.connect(self._on_file_save)
        self.actionFileSaveAs.triggered.connect(self._on_file_save_as)
        self.actionImportYamlAdd.triggered.connect(
            lambda: self._on_import_yaml(replace=False)
        )
        self.actionImportYamlReplace.triggered.connect(
            lambda: self._on_import_yaml(replace=True)
        )
        self.actionExportYaml.triggered.connect(self._on_export_yaml)
        self.actionFileClose.triggered.connect(self._on_file_close)
        self.actionFileQuit.triggered.connect(self.close)

        # Tools / Help
        self.actionToolsOptions.triggered.connect(self._on_open_settings)
        self.actionHelpAbout.triggered.connect(self._on_open_about)
        self.actionRefreshThumbnails.triggered.connect(self._on_refresh_thumbnails)

        # Prompt actions
        self.actionNewPrompt.triggered.connect(self._on_new_prompt)
        self.actionDuplicatePrompt.triggered.connect(self._on_duplicate_prompt)
        self.actionDeletePrompts.triggered.connect(self._on_delete_prompts)

        # Translation
        self.actionTranslateToEnglish.triggered.connect(
            lambda: self._on_translate(to_english=True)
        )
        self.actionTranslateFromEnglish.triggered.connect(
            lambda: self._on_translate(to_english=False)
        )

        # Filters
        self.filterAi.textChanged.connect(
            lambda t: self._proxy_model.set_filter(Column.AI, t)
        )
        self.filterGroup.textChanged.connect(
            lambda t: self._proxy_model.set_filter(Column.GROUP, t)
        )
        self.filterName.textChanged.connect(
            lambda t: self._proxy_model.set_filter(Column.NAME, t)
        )
        self.filterLocal.textChanged.connect(
            lambda t: self._proxy_model.set_filter(Column.LOCAL, t)
        )
        self.filterEnglish.textChanged.connect(
            lambda t: self._proxy_model.set_filter(Column.ENGLISH, t)
        )
        self.clearFiltersButton.clicked.connect(self._on_clear_filters)

        # Model modified → title update
        self._source_model.collection_modified.connect(self._update_title)

        # Auto-resize row heights when data or column widths change
        self._proxy_model.dataChanged.connect(lambda *_: self._resize_rows())
        self._proxy_model.modelReset.connect(self._resize_rows)
        self._proxy_model.rowsInserted.connect(lambda *_: self._resize_rows())
        self.tableView.horizontalHeader().sectionResized.connect(
            self._on_section_resized
        )

        # Context menu + clipboard notifications
        self.tableView.customContextMenuRequested.connect(self._on_context_menu)
        self.tableView.cell_copied.connect(
            lambda text: self.statusBar().showMessage(
                self._("Copied: %s") % text[:60], 3000
            )
        )
        self.tableView.image_activated.connect(self._on_image_activated)
        self.tableView.image_drop_requested.connect(self._on_image_drop)

    # ------------------------------------------------------------------
    # Header sort
    # ------------------------------------------------------------------

    def _on_header_clicked(self, column: int) -> None:
        """Select sort column (ascending); if already active, toggle direction."""
        if column not in (Column.AI, Column.GROUP, Column.NAME):
            return  # IMAGE, LOCAL, and ENGLISH are not sortable
        if self._sort_col == column:
            self._sort_order = (
                Qt.DescendingOrder
                if self._sort_order == Qt.AscendingOrder
                else Qt.AscendingOrder
            )
        else:
            self._sort_col = column
            self._sort_order = Qt.AscendingOrder
        self._proxy_model.sort(self._sort_col, self._sort_order)
        self.tableView.horizontalHeader().setSortIndicator(
            self._sort_col, self._sort_order
        )

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _on_file_new(self) -> None:
        if not self._check_unsaved_changes():
            return
        self._collection = PromptCollection()
        self._source_model.set_collection(self._collection)
        self._update_title()
        self.statusBar().showMessage(self._("New file created"))

    def _on_file_open(self) -> None:
        if not self._check_unsaved_changes():
            return
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            self._("Open Prompt File"),
            "",
            self._("PBPrompt database (*.sqlite);;All files (*.*)"),
        )
        if not path_str:
            return
        self.open_file(Path(path_str))

    def open_file(self, path: Path) -> None:
        """Load *path* into the current collection (public API for CLI use)."""
        try:
            self._collection = PromptCollection.load(path)
            self._source_model.set_collection(self._collection)
            self._add_to_recent_files(path)
            self._update_title()
            self.statusBar().showMessage(
                self._("Loaded {n} entries from {path}").format(
                    n=len(self._collection.entries), path=str(path)
                )
            )
        except ValueError as exc:
            logger.exception("Not a PBPrompt database: %s", path)
            QMessageBox.critical(
                self,
                self._("Error Opening File"),
                self._("Could not open file:\n{path}\n\n{error}").format(
                    path=str(path), error=str(exc)
                ),
            )
            self._collection = PromptCollection()
            self._source_model.set_collection(self._collection)
            self._update_title()
        except Exception:
            logger.exception("Failed to open %s", path)
            QMessageBox.critical(
                self,
                self._("Error"),
                self._("Could not open file:\n{path}").format(path=str(path)),
            )

    def _on_file_save(self) -> None:
        if self._collection.file_path is None:
            self._on_file_save_as()
        else:
            self._save_to(self._collection.file_path)

    def _on_file_save_as(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            self._("Save Prompt File"),
            str(self._collection.file_path or ""),
            self._("PBPrompt database (*.sqlite);;All files (*.*)"),
        )
        if path_str:
            path = Path(path_str)
            if path.suffix.lower() != ".sqlite":
                path = path.with_suffix(".sqlite")
            self._save_to(path)

    def _save_to(self, path: Path) -> None:
        try:
            self._collection.save(path)
            self._add_to_recent_files(path)
            self._update_title()
            self.statusBar().showMessage(self._("File saved successfully"))
        except Exception:
            logger.exception("Failed to save to %s", path)
            QMessageBox.critical(
                self,
                self._("Error"),
                self._("Could not save file:\n{path}").format(path=path),
            )

    def _on_import_yaml(self, replace: bool) -> None:
        """Import entries from a YAML file (append or replace)."""
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            self._("Import YAML"),
            "",
            self._("YAML files (*.yaml *.yml);;All files (*.*)"),
        )
        if not path_str:
            return
        try:
            from pbprompt.gui.image_utils import generate_thumbnail  # noqa: PLC0415

            def _thumb_factory(data: bytes) -> bytes | None:
                return generate_thumbnail(
                    data,
                    self._config.thumbnail_width,
                    self._config.thumbnail_height,
                )

            imported, skipped = self._collection.import_yaml(
                Path(path_str),
                replace=replace,
                thumbnail_factory=_thumb_factory,
            )
            self._source_model.set_collection(self._collection)
            self._update_title()
            msg = self._("Imported {n} entries from {path}").format(
                n=imported, path=path_str
            )
            if skipped:
                msg += "  " + self._("({k} duplicate(s) skipped)").format(k=skipped)
            self.statusBar().showMessage(msg, 4000)
        except Exception as exc:
            logger.exception("Failed to import YAML from %s", path_str)
            QMessageBox.critical(
                self,
                self._("Error"),
                self._("Import failed:\n{error}").format(error=str(exc)),
            )

    def _on_export_yaml(self) -> None:
        """Export all entries to a YAML file."""
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            self._("Export YAML"),
            "",
            self._("YAML files (*.yaml *.yml);;All files (*.*)"),
        )
        if not path_str:
            return
        try:
            path = Path(path_str)
            if path.suffix.lower() not in (".yaml", ".yml"):
                path = path.with_suffix(".yaml")
            self._collection.export_yaml(path)
            self.statusBar().showMessage(
                self._("Exported {n} entries to {path}").format(
                    n=len(self._collection.entries), path=str(path)
                ),
                4000,
            )
        except Exception as exc:
            logger.exception("Failed to export YAML to %s", path_str)
            QMessageBox.critical(
                self,
                self._("Error"),
                self._("Export failed:\n{error}").format(error=str(exc)),
            )

    def _on_file_close(self) -> None:
        if not self._check_unsaved_changes():
            return
        self._collection = PromptCollection()
        self._source_model.set_collection(self._collection)
        self._update_title()
        self.statusBar().showMessage(self._("File closed"))

    def _check_unsaved_changes(self) -> bool:
        """Return True if safe to proceed (no unsaved changes or user confirmed)."""
        if not self._collection.modified:
            return True
        reply = QMessageBox.question(
            self,
            self._("Unsaved Changes"),
            self._(
                "The document has been modified.\nDo you want to save your changes?"
            ),
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if reply == QMessageBox.Save:
            self._on_file_save()
            return not self._collection.modified  # False if save was cancelled
        return reply == QMessageBox.Discard

    # ------------------------------------------------------------------
    # Prompt CRUD
    # ------------------------------------------------------------------

    def _on_new_prompt(self) -> None:
        source_row = self._source_model.append_row(PromptEntry())
        # Map source row to proxy
        source_index = self._source_model.index(source_row, 0)
        proxy_index = self._proxy_model.mapFromSource(source_index)
        if proxy_index.isValid():
            self.tableView.scrollTo(proxy_index)
            self.tableView.setCurrentIndex(proxy_index)
            # Start editing AI cell immediately
            self.tableView.edit(proxy_index)

    def _on_duplicate_prompt(self) -> None:
        """Duplicate the current row and insert it immediately below."""
        import copy  # noqa: PLC0415

        idx = self.tableView.currentIndex()
        if not idx.isValid():
            return
        source_idx = self._proxy_model.mapToSource(idx)
        row = source_idx.row()
        duplicate = copy.copy(self._collection.entries[row])
        new_row = self._source_model.insert_row(row + 1, duplicate)
        new_source_index = self._source_model.index(new_row, idx.column())
        new_proxy_index = self._proxy_model.mapFromSource(new_source_index)
        if new_proxy_index.isValid():
            self.tableView.scrollTo(new_proxy_index)
            self.tableView.setCurrentIndex(new_proxy_index)
        self.statusBar().showMessage(self._("Row duplicated"), 3000)

    def _on_delete_prompts(self) -> None:
        selected = self.tableView.selectionModel().selectedRows()
        if not selected:
            return
        n = len(selected)
        reply = QMessageBox.question(
            self,
            self._("Confirm Delete"),
            self._("Are you sure you want to delete {n} selected row(s)?").format(n=n),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        # Map proxy rows to source rows
        source_rows = sorted(
            {self._proxy_model.mapToSource(idx).row() for idx in selected},
            reverse=True,
        )
        self._source_model.remove_rows(source_rows)
        self.statusBar().showMessage(
            self._("Deleted {n} row(s)").format(n=len(source_rows))
        )

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    def _on_clear_filters(self) -> None:
        self.filterAi.clear()
        self.filterGroup.clear()
        self.filterName.clear()
        self.filterLocal.clear()
        self.filterEnglish.clear()
        self._proxy_model.clear_filters()

    # ------------------------------------------------------------------
    # Row auto-resize (multi-line content)
    # ------------------------------------------------------------------

    def _resize_rows(self) -> None:
        """Recompute row heights to fit wrapped content.

        Only acts when the window is already visible and columns have their
        final widths.  The initial resize after startup is handled by
        showEvent(), which fires after the first layout pass.
        """
        if self.isVisible():
            self.tableView.resizeRowsToContents()

    def showEvent(self, event: object) -> None:  # noqa: N802
        """Schedule row resize after the window's first layout pass."""
        super().showEvent(event)  # type: ignore[arg-type]
        QTimer.singleShot(0, self.tableView.resizeRowsToContents)

    def _on_section_resized(self, col: int, old_size: int, new_size: int) -> None:
        """Resize rows when a Local or English column width changes."""
        if col in (Column.LOCAL, Column.ENGLISH):
            self.tableView.resizeRowsToContents()

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _on_context_menu(self, pos: object) -> None:
        """Show a context menu at *pos* (viewport coordinates)."""
        _ = self._
        idx = self.tableView.indexAt(pos)
        if idx.isValid():
            source_idx = self._proxy_model.mapToSource(idx)
            if source_idx.column() == int(Column.IMAGE):
                self._show_image_context_menu(pos, source_idx)
                return

        menu = QMenu(self.tableView)
        act_copy = menu.addAction(_("Copy"))
        act_copy.setShortcut(QKeySequence(QKeySequence.Copy))
        act_cut = menu.addAction(_("Cut"))
        act_cut.setShortcut(QKeySequence(QKeySequence.Cut))
        act_paste = menu.addAction(_("Paste"))
        act_paste.setShortcut(QKeySequence(QKeySequence.Paste))

        has_selection = idx.isValid()
        act_copy.setEnabled(has_selection)
        act_cut.setEnabled(has_selection)
        act_paste.setEnabled(has_selection)

        act_copy.triggered.connect(self.tableView._do_copy)
        act_cut.triggered.connect(self.tableView._do_cut)
        act_paste.triggered.connect(self.tableView._do_paste)

        menu.exec_(self.tableView.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Image operations
    # ------------------------------------------------------------------

    def _on_refresh_thumbnails(self) -> None:
        """Regenerate all thumbnails from stored full images."""
        from pbprompt.gui.image_utils import generate_thumbnail  # noqa: PLC0415

        updated = 0
        for row, entry in enumerate(self._collection.entries):
            if not entry.image:
                continue
            thumb = generate_thumbnail(
                entry.image,
                self._config.thumbnail_width,
                self._config.thumbnail_height,
            )
            self._source_model.set_image(row, entry.image, thumb)
            updated += 1
        self.statusBar().showMessage(
            self._("Thumbnails refreshed: {n} image(s) updated").format(n=updated),
            4000,
        )

    def _on_image_activated(self, source_idx: object) -> None:
        """Show the full image in a dialog."""
        from PyQt5.QtCore import QModelIndex  # noqa: PLC0415

        from pbprompt.gui.image_utils import ImageViewDialog  # noqa: PLC0415

        if not isinstance(source_idx, QModelIndex):
            return
        row = source_idx.row()
        if row >= len(self._collection.entries):
            return
        entry = self._collection.entries[row]
        if not entry.image:
            return
        dlg = ImageViewDialog(entry.image, parent=self)
        dlg.exec_()

    def _on_image_drop(self, source_idx: object, mime_data: object) -> None:
        """Handle a dropped image or file URL onto an IMAGE cell."""
        from PyQt5.QtCore import QModelIndex  # noqa: PLC0415
        from PyQt5.QtGui import QImage  # noqa: PLC0415

        from pbprompt.gui.image_utils import (  # noqa: PLC0415
            detect_image_format,
            generate_thumbnail,
            qimage_to_bytes,
        )

        if not isinstance(source_idx, QModelIndex):
            return

        image_bytes: bytes | None = None

        if hasattr(mime_data, "hasImage") and mime_data.hasImage():
            qimg = mime_data.imageData()
            if isinstance(qimg, QImage) and not qimg.isNull():
                image_bytes = qimage_to_bytes(qimg)

        if (
            image_bytes is None
            and hasattr(mime_data, "hasUrls")
            and mime_data.hasUrls()
        ):
            for url in mime_data.urls():
                if url.isLocalFile():
                    try:
                        with open(url.toLocalFile(), "rb") as fh:
                            data = fh.read()
                        if detect_image_format(data):
                            image_bytes = data
                            break
                    except OSError:
                        pass

        if image_bytes is None:
            return
        if not detect_image_format(image_bytes):
            QMessageBox.warning(
                self,
                self._("Unsupported Format"),
                self._("Unsupported image format"),
            )
            return

        thumb = generate_thumbnail(
            image_bytes,
            self._config.thumbnail_width,
            self._config.thumbnail_height,
        )
        self._source_model.set_image(source_idx.row(), image_bytes, thumb)

    def _show_image_context_menu(self, pos: object, source_idx: object) -> None:
        """Show the image-specific context menu."""
        from PyQt5.QtCore import QModelIndex  # noqa: PLC0415

        if not isinstance(source_idx, QModelIndex):
            return
        _ = self._
        menu = QMenu(self.tableView)
        act_load = menu.addAction(_("Load image from file…"))
        act_paste = menu.addAction(_("Paste image"))
        menu.addSeparator()
        act_clear = menu.addAction(_("Clear image"))
        act_load.triggered.connect(lambda: self._on_image_load_from_file(source_idx))
        act_paste.triggered.connect(lambda: self._on_image_paste(source_idx))
        act_clear.triggered.connect(lambda: self._on_image_clear(source_idx))
        menu.exec_(self.tableView.viewport().mapToGlobal(pos))

    def _on_image_load_from_file(self, source_idx: object) -> None:
        """Load an image from disk into the IMAGE cell."""
        from PyQt5.QtCore import QModelIndex  # noqa: PLC0415

        from pbprompt.gui.image_utils import (  # noqa: PLC0415
            detect_image_format,
            generate_thumbnail,
            open_image_file_dialog,
        )

        if not isinstance(source_idx, QModelIndex):
            return
        path_str = open_image_file_dialog(
            self,
            self._("Load Image"),
            self._("Image files (*.jpg *.jpeg *.png);;All files (*.*)"),
            no_preview_text=self._("No preview"),
        )
        if not path_str:
            return
        try:
            with open(path_str, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            QMessageBox.critical(
                self,
                self._("Error"),
                self._("Could not read file:\n{error}").format(error=str(exc)),
            )
            return
        if not detect_image_format(data):
            QMessageBox.warning(
                self,
                self._("Unsupported Format"),
                self._("Unsupported image format"),
            )
            return
        thumb = generate_thumbnail(
            data,
            self._config.thumbnail_width,
            self._config.thumbnail_height,
        )
        self._source_model.set_image(source_idx.row(), data, thumb)

    def _on_image_paste(self, source_idx: object) -> None:
        """Paste an image or file path from the clipboard."""
        from PyQt5.QtCore import QModelIndex  # noqa: PLC0415

        from pbprompt.gui.image_utils import (  # noqa: PLC0415
            detect_image_format,
            generate_thumbnail,
            qimage_to_bytes,
        )

        if not isinstance(source_idx, QModelIndex):
            return

        clipboard = QApplication.clipboard()
        image_bytes: bytes | None = None

        # Try image data first
        qimg = clipboard.image()
        if not qimg.isNull():
            image_bytes = qimage_to_bytes(qimg)

        # Fall back to text (treated as file path)
        if image_bytes is None:
            text = clipboard.text().strip()
            if text:
                try:
                    with open(text, "rb") as fh:
                        data = fh.read()
                    if detect_image_format(data):
                        image_bytes = data
                except OSError:
                    pass

        if image_bytes is None:
            QMessageBox.information(
                self,
                self._("No Image"),
                self._("No image in clipboard"),
            )
            return
        if not detect_image_format(image_bytes):
            QMessageBox.warning(
                self,
                self._("Unsupported Format"),
                self._("Unsupported image format"),
            )
            return
        thumb = generate_thumbnail(
            image_bytes,
            self._config.thumbnail_width,
            self._config.thumbnail_height,
        )
        self._source_model.set_image(source_idx.row(), image_bytes, thumb)

    def _on_image_clear(self, source_idx: object) -> None:
        """Clear the image from the IMAGE cell."""
        from PyQt5.QtCore import QModelIndex  # noqa: PLC0415

        if not isinstance(source_idx, QModelIndex):
            return
        self._source_model.set_image(source_idx.row(), None, None)

    # ------------------------------------------------------------------
    # Translation
    # ------------------------------------------------------------------

    def _on_translate(self, to_english: bool) -> None:
        """Translate selected rows using the configured service."""
        # Commit any active inline editor before reading cell data.
        # NOTE: setFocus on the view itself would not work – Qt's delegate
        # eventFilter skips commitData when focus moves to an ancestor of
        # the editor.  clearFocus() on the editor widget itself triggers an
        # unconditional FocusOut → commitData + closeEditor.
        fw = QApplication.focusWidget()
        if fw is not None and self.tableView.isAncestorOf(fw):
            fw.clearFocus()

        selected = self.tableView.selectionModel().selectedRows()
        if not selected:
            self.statusBar().showMessage(self._("No rows selected"))
            return

        try:
            from pbprompt.translate import get_translator  # noqa: PLC0415

            translator = get_translator(self._config)
        except Exception:
            logger.exception("Failed to create translator")
            QMessageBox.warning(
                self,
                self._("Translation Error"),
                self._(
                    "Could not initialise the translation service.\n"
                    "Check your API key in Options."
                ),
            )
            return

        lang = self._config.translation_language or system_language()
        translated = 0
        for proxy_idx in selected:
            source_idx = self._proxy_model.mapToSource(proxy_idx)
            row = source_idx.row()
            entry = self._collection.entries[row]
            try:
                if to_english:
                    result = translator.to_english(entry.local, source_language=lang)
                    self._source_model.setData(
                        self._source_model.index(row, Column.ENGLISH),
                        result,
                    )
                else:
                    result = translator.from_english(
                        entry.english, target_language=lang
                    )
                    self._source_model.setData(
                        self._source_model.index(row, Column.LOCAL),
                        result,
                    )
                translated += 1
            except Exception as exc:
                logger.warning("Translation failed for row %d", row, exc_info=True)
                QMessageBox.critical(
                    self,
                    self._("Translation Error"),
                    self._("Translation failed:\n{error}").format(error=str(exc)),
                )
                break

        if translated:
            self.statusBar().showMessage(
                self._("Translated {n} row(s)").format(n=translated), 4000
            )

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def _on_open_settings(self) -> None:
        from pbprompt.gui.settings_dialog import SettingsDialog  # noqa: PLC0415

        dlg = SettingsDialog(config=self._config, parent=self)
        if dlg.exec_() == dlg.Accepted:
            # Config was updated and saved inside the dialog
            self._config = dlg.config
            # Reload i18n if language changed
            from pbprompt.i18n import reload_i18n  # noqa: PLC0415

            reload_i18n(self._config.display_language)
            self.retranslateUi(self)
            # Update image delegate size
            self._image_delegate.update_size(
                self._config.thumbnail_width,
                self._config.thumbnail_height,
            )
            self.tableView.setColumnWidth(
                Column.IMAGE, self._config.thumbnail_width + 12
            )
            # Trim recent files list if max was reduced
            if len(self._config.recent_files) > self._config.recent_files_max:
                self._config.recent_files = self._config.recent_files[
                    : self._config.recent_files_max
                ]
                self._config.save()
            self._update_recent_files_menu()

    def _on_open_about(self) -> None:
        from pbprompt.gui.about_dialog import AboutDialog  # noqa: PLC0415

        dlg = AboutDialog(parent=self)
        dlg.exec_()

    # ------------------------------------------------------------------
    # Recent files
    # ------------------------------------------------------------------

    def _update_recent_files_menu(self) -> None:
        """Rebuild the Recent Files submenu from the current configuration."""
        menu = self.menuRecentFiles
        menu.clear()

        files = self._config.recent_files
        if not files:
            no_action = menu.addAction(self._("No recent files"))
            no_action.setEnabled(False)
        else:
            for path_str in files:
                action = menu.addAction(path_str)
                action.setData(path_str)
                # Use default-argument capture to avoid late-binding closure bug
                action.triggered.connect(
                    lambda _checked=False, p=path_str: self._on_open_recent(p)
                )
            menu.addSeparator()

        clear_action = menu.addAction(self._("Clear list"))
        clear_action.triggered.connect(self._on_clear_recent_files)

    def _add_to_recent_files(self, path: Path) -> None:
        """Prepend *path* to the recent-files list, then trim and persist."""
        path_str = str(path)
        recent = list(self._config.recent_files)
        if path_str in recent:
            recent.remove(path_str)
        recent.insert(0, path_str)
        self._config.recent_files = recent[: self._config.recent_files_max]
        self._config.save()
        self._update_recent_files_menu()

    def _remove_from_recent_files(self, path_str: str) -> None:
        """Remove *path_str* from the recent-files list and persist."""
        recent = list(self._config.recent_files)
        if path_str in recent:
            recent.remove(path_str)
        self._config.recent_files = recent
        self._config.save()
        self._update_recent_files_menu()

    def _on_open_recent(self, path_str: str) -> None:
        """Open a file from the Recent Files list."""
        if not self._check_unsaved_changes():
            return
        path = Path(path_str)
        if not path.exists():
            QMessageBox.warning(
                self,
                self._("File Not Found"),
                self._("The file no longer exists:\n{path}").format(path=path_str),
            )
            self._remove_from_recent_files(path_str)
            return
        try:
            self._collection = PromptCollection.load(path)
            self._source_model.set_collection(self._collection)
            self._add_to_recent_files(path)
            self._update_title()
            self.statusBar().showMessage(
                self._("Loaded {n} entries from {path}").format(
                    n=len(self._collection.entries), path=path_str
                )
            )
        except Exception:
            logger.exception("Failed to open recent file %s", path_str)
            QMessageBox.critical(
                self,
                self._("Error"),
                self._("Could not open file:\n{path}").format(path=path_str),
            )

    def _on_clear_recent_files(self) -> None:
        """Clear the entire recent-files list."""
        self._config.recent_files.clear()
        self._config.save()
        self._update_recent_files_menu()

    def _open_initial_file(self, path: Path) -> None:
        """Open *path* supplied on the command line.

        On success the file is added to the recent-files list.
        On failure a dialog shows the reason and an empty collection is loaded.
        """
        try:
            self._collection = PromptCollection.load(path)
            self._source_model.set_collection(self._collection)
            self._add_to_recent_files(path)
            self._update_title()
            self.statusBar().showMessage(
                self._("Loaded {n} entries from {path}").format(
                    n=len(self._collection.entries), path=str(path)
                )
            )
        except Exception as exc:
            logger.exception("Failed to open initial file %s", path)
            QMessageBox.critical(
                self,
                self._("Error Opening File"),
                self._("Could not open file:\n{path}\n\n{error}").format(
                    path=str(path), error=str(exc)
                ),
            )
            self._collection = PromptCollection()
            self._source_model.set_collection(self._collection)
            self._update_title()
            self.statusBar().showMessage(self._("Ready"))

    def _autoload_last_file(self) -> None:
        """Load the most recently used file silently at startup.

        If the file no longer exists it is removed from the list and an
        empty collection is shown instead.
        """
        if not self._config.recent_files:
            return
        last = self._config.recent_files[0]
        path = Path(last)
        if not path.exists():
            logger.info("Last file %s no longer exists; starting empty.", last)
            self._config.recent_files.pop(0)
            self._config.save()
            self._update_recent_files_menu()
            return
        try:
            self._collection = PromptCollection.load(path)
            self._source_model.set_collection(self._collection)
            self._update_title()
            self.statusBar().showMessage(
                self._("Loaded {n} entries from {path}").format(
                    n=len(self._collection.entries), path=last
                )
            )
        except Exception:
            logger.warning("Failed to auto-load %s.", last, exc_info=True)
            self._config.recent_files.pop(0)
            self._config.save()
            self._update_recent_files_menu()

    # ------------------------------------------------------------------
    # Title management
    # ------------------------------------------------------------------

    def _update_title(self) -> None:
        name = (
            self._collection.file_path.name
            if self._collection.file_path
            else self._("Untitled")
        )
        modified_marker = "*" if self._collection.modified else ""
        self.setWindowTitle(f"{modified_marker}{name} – {__app_name__} {__version__}")

    # ------------------------------------------------------------------
    # Close event
    # ------------------------------------------------------------------

    def closeEvent(self, event: object) -> None:  # noqa: N802
        if self._check_unsaved_changes():
            self._config.window_x = self.x()
            self._config.window_y = self.y()
            self._config.window_width = self.width()
            self._config.window_height = self.height()
            self._config.save()
            event.accept()  # type: ignore[attr-defined]
        else:
            event.ignore()  # type: ignore[attr-defined]
