"""Qt item models and custom view for the prompt table."""

from __future__ import annotations

import logging
import re
from enum import IntEnum
from typing import Any

from PyQt5.QtCore import (
    QAbstractTableModel,
    QEvent,
    QModelIndex,
    QSize,
    QSortFilterProxyModel,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QKeySequence,
    QPainter,
    QPalette,
    QPen,
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate,
    QApplication,
    QFrame,
    QPlainTextEdit,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
)

from pbprompt.data import PromptCollection, PromptEntry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------


class Column(IntEnum):
    """Index constants for the five table columns."""

    AI = 0
    GROUP = 1
    NAME = 2
    LOCAL = 3
    ENGLISH = 4


_COLUMN_FIELDS = {
    Column.AI: "ai",
    Column.GROUP: "group",
    Column.NAME: "name",
    Column.LOCAL: "local",
    Column.ENGLISH: "english",
}

# Multi-column sort order per primary column
_SORT_ORDER = {
    Column.AI: [Column.AI, Column.GROUP, Column.NAME],
    Column.GROUP: [Column.GROUP, Column.NAME, Column.AI],
    Column.NAME: [Column.NAME, Column.GROUP, Column.AI],
}

# Columns that support sort
_SORTABLE_COLUMNS = frozenset({Column.AI, Column.GROUP, Column.NAME})


# ---------------------------------------------------------------------------
# Source model
# ---------------------------------------------------------------------------


class PromptTableModel(QAbstractTableModel):
    """Qt model backed by a :class:`~pbprompt.data.PromptCollection`.

    Signals
    -------
    collection_modified:
        Emitted whenever the underlying collection is changed through the model.
    """

    collection_modified = pyqtSignal()

    # Header labels (translated at runtime via retranslate)
    _headers: list[str] = ["AI", "Group", "Name", "Local language", "English"]

    # Header tooltips (translated at runtime via retranslate)
    _header_tooltips: list[str] = ["", "", "", "", ""]

    def __init__(
        self,
        collection: PromptCollection | None = None,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._collection = collection or PromptCollection()

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if parent.isValid():
            return 0
        return len(self._collection.entries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if parent.isValid():
            return 0
        return len(Column)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._collection.entries):
            return None
        entry = self._collection.entries[row]

        if role in (Qt.DisplayRole, Qt.EditRole):
            field = _COLUMN_FIELDS.get(Column(col), "")
            return getattr(entry, field, "")

        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignVCenter | Qt.AlignLeft)

        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False
        row, col = index.row(), index.column()
        if row >= len(self._collection.entries):
            return False

        field = _COLUMN_FIELDS.get(Column(col), "")
        if not field:
            return False

        self._collection.update_field(row, field, str(value))
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        self.collection_modified.emit()
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> Any:
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                try:
                    return self._headers[section]
                except IndexError:
                    return None
            if role == Qt.ToolTipRole:
                try:
                    tip = self._header_tooltips[section]
                    return tip or None
                except IndexError:
                    return None
            return None
        if role == Qt.DisplayRole:
            return str(section + 1)
        return None

    # ------------------------------------------------------------------
    # Collection access
    # ------------------------------------------------------------------

    @property
    def collection(self) -> PromptCollection:
        """Return the underlying data collection."""
        return self._collection

    def set_collection(self, collection: PromptCollection) -> None:
        """Replace the entire data collection and reset the view."""
        self.beginResetModel()
        self._collection = collection
        self.endResetModel()

    # ------------------------------------------------------------------
    # Mutation helpers (called from MainWindow)
    # ------------------------------------------------------------------

    def append_row(self, entry: PromptEntry | None = None) -> int:
        """Append a new entry; return its row index."""
        pos = len(self._collection.entries)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._collection.append(entry)
        self.endInsertRows()
        self.collection_modified.emit()
        return pos

    def insert_row(self, pos: int, entry: PromptEntry) -> int:
        """Insert *entry* at *pos*; return its row index."""
        pos = min(pos, len(self._collection.entries))
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._collection.entries.insert(pos, entry)
        self._collection.modified = True
        self.endInsertRows()
        self.collection_modified.emit()
        return pos

    def remove_rows(self, source_rows: list[int]) -> None:
        """Remove entries at *source_rows* (indices in the source model)."""
        # Remove in reverse so indices stay valid
        for row in sorted(set(source_rows), reverse=True):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._collection.entries.pop(row)
            self.endRemoveRows()
        self._collection.modified = True
        self.collection_modified.emit()

    def set_header_labels(self, labels: list[str]) -> None:
        """Update column header labels (called from retranslateUi)."""
        self._headers = labels
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(Column) - 1)

    def set_header_tooltips(self, tooltips: list[str]) -> None:
        """Update column header tooltips (called from retranslateUi)."""
        self._header_tooltips = tooltips
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(Column) - 1)


# ---------------------------------------------------------------------------
# Proxy model (multi-column filter + custom sort)
# ---------------------------------------------------------------------------


class MultiFilterProxyModel(QSortFilterProxyModel):
    """Proxy model supporting per-column regex filters and multi-key sort.

    Filtering
    ---------
    Set a pattern for a column with :meth:`set_filter`.  All active
    patterns are ANDed: a row is displayed only if it matches every filter.
    Invalid regexes are silently ignored.

    Sorting
    -------
    Sorting is limited to columns AI, Group and Name.  The sort criteria
    are hierarchical according to the column chosen as primary key:

    * Primary AI   → secondary Group → tertiary Name
    * Primary Group → secondary Name → tertiary AI
    * Primary Name  → secondary Group → tertiary AI
    """

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._filters: dict[int, str] = {}

    def set_filter(self, column: int, pattern: str) -> None:
        """Set the regex *pattern* for *column* (empty string removes the filter)."""
        if pattern:
            self._filters[column] = pattern
        else:
            self._filters.pop(column, None)
        self.invalidateFilter()

    def clear_filters(self) -> None:
        """Remove all column filters."""
        self._filters.clear()
        self.invalidateFilter()

    # ------------------------------------------------------------------
    # QSortFilterProxyModel overrides
    # ------------------------------------------------------------------

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        for col, pattern in self._filters.items():
            if not pattern:
                continue
            idx = model.index(source_row, col, source_parent)
            cell_data: str = model.data(idx, Qt.DisplayRole) or ""
            try:
                if not re.search(pattern, cell_data, re.IGNORECASE):
                    return False
            except re.error:
                pass  # Invalid regex → skip this filter
        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """Multi-column comparison for sort stability.

        Qt calls ``lessThan(right, left)`` (arguments swapped) when the sort
        order is descending, so this function always expresses the ascending
        relation; Qt handles the direction flip automatically.
        """
        primary_col = Column(left.column())
        sort_cols = _SORT_ORDER.get(primary_col, [primary_col])
        model = self.sourceModel()

        for col in sort_cols:
            # Use int() explicitly: some PyQt5 builds reject IntEnum via SIP,
            # which would silently return an invalid index and make data()
            # return None, causing every secondary comparison to be skipped.
            c = int(col)
            left_idx = model.index(left.row(), c, left.parent())
            right_idx = model.index(right.row(), c, right.parent())
            left_val = (model.data(left_idx, Qt.DisplayRole) or "").lower()
            right_val = (model.data(right_idx, Qt.DisplayRole) or "").lower()
            if left_val != right_val:
                return left_val < right_val
        return False

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Restrict sorting to the three sortable columns."""
        if Column(column) not in _SORTABLE_COLUMNS:
            return
        super().sort(column, order)


# ---------------------------------------------------------------------------
# Current-cell highlight delegate (all columns)
# ---------------------------------------------------------------------------


class CurrentCellHighlightDelegate(QStyledItemDelegate):
    """Delegate that draws a distinct border on the current cell within a selected row.

    Apply this to any column where you want the *current* cell to stand out
    from the other cells that share the selection highlight.
    """

    def __init__(self, view: QTableView, parent: Any = None) -> None:
        super().__init__(parent)
        self._view = view

    def _draw_current_highlight(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Overlay a border when *index* is the current cell in a selected row."""
        if self._view.currentIndex() == index and bool(
            option.state & QStyle.State_Selected
        ):
            painter.save()
            color = option.palette.color(QPalette.Highlight).darker(160)
            pen = QPen(color)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(option.rect.adjusted(1, 1, -2, -2))
            painter.restore()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        super().paint(painter, option, index)
        self._draw_current_highlight(painter, option, index)


# ---------------------------------------------------------------------------
# Multi-line delegate (Local / English columns)
# ---------------------------------------------------------------------------

#: Unicode marker rendered at the position of each real newline (U+21B5 ↵).
_NEWLINE_MARKER = "\u21b5"


class MultiLineDelegate(CurrentCellHighlightDelegate):
    """Delegate for the Local and English columns.

    * Displays text with automatic word-wrap; real ``\\n`` characters are
      rendered as ``↵`` (U+21B5) followed by a line break so they remain
      visible while the text continues on the next line.
    * Opens a ``QPlainTextEdit`` for in-place multi-line editing.  Return
      inserts a newline; Tab / Shift+Tab commit and navigate; Escape reverts;
      clicking outside commits.
    * :meth:`sizeHint` computes the exact height required for the wrapped text
      so that ``resizeRowsToContents()`` produces correct row heights.
    * The current cell is drawn with a distinct border via the parent class.
    """

    def __init__(self, view: QTableView, parent: Any = None) -> None:
        super().__init__(view, parent)

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    @staticmethod
    def _display_text(raw: str) -> str:
        """Replace every ``\\n`` with ``↵\\n`` for display purposes."""
        return raw.replace("\n", f"{_NEWLINE_MARKER}\n")

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        col = index.column()
        if col not in (Column.LOCAL, Column.ENGLISH):
            super().paint(painter, option, index)
            return

        # Draw background / selection highlight without any text.
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)

        raw: str = index.data(Qt.DisplayRole) or ""
        display = self._display_text(raw)

        if opt.state & QStyle.State_Selected:
            color = opt.palette.color(QPalette.HighlightedText)
        else:
            color = opt.palette.color(QPalette.Text)

        margin = 4
        text_rect = opt.rect.adjusted(margin, margin, -margin, -margin)

        painter.save()
        painter.setClipRect(opt.rect)
        painter.setFont(opt.font)
        painter.setPen(color)
        painter.drawText(
            text_rect,
            Qt.TextWordWrap | Qt.AlignTop | Qt.AlignLeft,
            display,
        )
        painter.restore()

        self._draw_current_highlight(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        col = index.column()
        if col not in (Column.LOCAL, Column.ENGLISH):
            return super().sizeHint(option, index)

        width = self._view.columnWidth(col)
        if width <= 8:
            width = 100  # fallback before the first layout pass

        raw: str = index.data(Qt.DisplayRole) or ""
        display = self._display_text(raw)

        margin = 4
        # QFontMetrics.boundingRect with TextWordWrap mirrors QPainter.drawText
        fm = option.fontMetrics
        bounding = fm.boundingRect(
            0,
            0,
            max(width - 2 * margin, 1),
            10000,
            Qt.TextWordWrap | Qt.AlignTop | Qt.AlignLeft,
            display,
        )
        h = bounding.height() + 2 * margin + 4  # a bit of extra breathing room
        base = super().sizeHint(option, index)
        return QSize(base.width(), max(h, base.height()))

    # ------------------------------------------------------------------
    # Editor lifecycle
    # ------------------------------------------------------------------

    def createEditor(
        self,
        parent: Any,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> Any:
        col = index.column()
        if col not in (Column.LOCAL, Column.ENGLISH):
            return super().createEditor(parent, option, index)
        editor = QPlainTextEdit(parent)
        editor.setFrameShape(QFrame.NoFrame)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        return editor

    def setEditorData(self, editor: Any, index: QModelIndex) -> None:
        if not isinstance(editor, QPlainTextEdit):
            super().setEditorData(editor, index)
            return
        text: str = index.data(Qt.EditRole) or ""
        editor.setPlainText(text)
        editor.selectAll()

    def setModelData(self, editor: Any, model: Any, index: QModelIndex) -> None:
        if not isinstance(editor, QPlainTextEdit):
            super().setModelData(editor, model, index)
            return
        model.setData(index, editor.toPlainText(), Qt.EditRole)

    def updateEditorGeometry(
        self,
        editor: Any,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        r = option.rect
        # Ensure a usable minimum height even for single-line cells.
        editor.setGeometry(r.x(), r.y(), r.width(), max(r.height(), 80))

    def eventFilter(self, obj: Any, event: Any) -> bool:
        """Handle key events inside the QPlainTextEdit editor.

        * Enter / Return       → commit the edit and close the editor.
        * Ctrl+Enter / Ctrl+Return → insert a real newline character.
        * Tab / Backtab        → commit and move to the adjacent cell.
        * Up / Down            → natural cursor movement (no commit).
        * Escape / FocusOut    → handled by the base class (reverts on Escape).
        """
        if isinstance(obj, QPlainTextEdit):
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key in (Qt.Key_Return, Qt.Key_Enter):
                    if event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier):
                        # Ctrl+Enter or Shift+Enter → insert a real newline.
                        obj.insertPlainText("\n")
                        return True
                    # Plain Enter → validate and close the editor.
                    self.commitData.emit(obj)
                    self.closeEditor.emit(obj, QAbstractItemDelegate.NoHint)
                    return True
                # Up/Down: let QPlainTextEdit move the cursor naturally.
                if key in (Qt.Key_Up, Qt.Key_Down):
                    return False
                # Tab / Backtab: commit and move to adjacent cell.
                if key == Qt.Key_Tab:
                    self.commitData.emit(obj)
                    self.closeEditor.emit(obj, QAbstractItemDelegate.EditNextItem)
                    return True
                if key == Qt.Key_Backtab:
                    self.commitData.emit(obj)
                    self.closeEditor.emit(obj, QAbstractItemDelegate.EditPreviousItem)
                    return True
            # Escape / FocusOut: handled by the base class.
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)


# ---------------------------------------------------------------------------
# Custom table view
# ---------------------------------------------------------------------------


class PromptTableView(QTableView):
    """QTableView with clipboard support and a copy-notification signal.

    Signals
    -------
    cell_copied:
        Emitted with the text that was copied to the clipboard.
    """

    #: Emitted with the copied text when a cell is copied to the clipboard.
    cell_copied = pyqtSignal(str)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: Any) -> None:  # type: ignore[override]
        """Handle Ctrl+C / Ctrl+X / Ctrl+V for clipboard operations."""
        if event.matches(QKeySequence.Copy):
            self._do_copy()
        elif event.matches(QKeySequence.Cut):
            self._do_cut()
        elif event.matches(QKeySequence.Paste):
            self._do_paste()
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Clipboard helpers
    # ------------------------------------------------------------------

    def _current_text(self) -> str:
        """Return the display text of the current index, or empty string."""
        idx = self.currentIndex()
        if not idx.isValid():
            return ""
        return self.model().data(idx, Qt.DisplayRole) or ""

    def _do_copy(self) -> None:
        """Copy the current cell's text to the clipboard."""
        text = self._current_text()
        if text:
            QApplication.clipboard().setText(text)
            self.cell_copied.emit(text)

    def _do_cut(self) -> None:
        """Copy the current cell to the clipboard and clear it."""
        idx = self.currentIndex()
        if not idx.isValid():
            return
        text = self.model().data(idx, Qt.DisplayRole) or ""
        if text:
            QApplication.clipboard().setText(text)
            self.cell_copied.emit(text)
        self.model().setData(idx, "", Qt.EditRole)

    def _do_paste(self) -> None:
        """Paste clipboard text into the current cell."""
        idx = self.currentIndex()
        if not idx.isValid():
            return
        text = QApplication.clipboard().text()
        if text:
            self.model().setData(idx, text, Qt.EditRole)
