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
    QPixmap,
)
from PyQt5.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
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
    """Index constants for the six table columns."""

    AI = 0
    GROUP = 1
    NAME = 2
    IMAGE = 3  # thumbnail display / full-image operations
    LOCAL = 4
    ENGLISH = 5


_COLUMN_FIELDS: dict[Column, str] = {
    Column.AI: "ai",
    Column.GROUP: "group",
    Column.NAME: "name",
    Column.LOCAL: "local",
    Column.ENGLISH: "english",
}
# IMAGE is intentionally absent — it is handled separately.

# Multi-column sort order per primary column
_SORT_ORDER: dict[Column, list[Column]] = {
    Column.AI: [Column.AI, Column.GROUP, Column.NAME],
    Column.GROUP: [Column.GROUP, Column.NAME, Column.AI],
    Column.NAME: [Column.NAME, Column.GROUP, Column.AI],
}

# Columns that support sort (IMAGE / LOCAL / ENGLISH are excluded)
_SORTABLE_COLUMNS: frozenset[Column] = frozenset({Column.AI, Column.GROUP, Column.NAME})


# ---------------------------------------------------------------------------
# Source model
# ---------------------------------------------------------------------------


class PromptTableModel(QAbstractTableModel):
    """Qt model backed by a :class:`~pbprompt.data.PromptCollection`."""

    collection_modified = pyqtSignal()

    _headers: list[str] = ["AI", "Group", "Name", "Image", "Local language", "English"]
    _header_tooltips: list[str] = ["", "", "", "", "", ""]

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
        column = Column(col)

        if column == Column.IMAGE:
            if role == Qt.DecorationRole:
                thumb = entry.thumbnail
                if thumb:
                    from pbprompt.gui.image_utils import (
                        pixmap_from_bytes,  # noqa: PLC0415
                    )

                    pm = pixmap_from_bytes(thumb)
                    return pm if pm and not pm.isNull() else None
                return None
            if role == Qt.DisplayRole or role == Qt.EditRole:
                return None
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignCenter)
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            field = _COLUMN_FIELDS.get(column, "")
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
        column = Column(col)
        if column == Column.IMAGE:
            return False  # images are set via set_image()
        field = _COLUMN_FIELDS.get(column, "")
        if not field:
            return False
        self._collection.update_field(row, field, str(value))
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        self.collection_modified.emit()
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        if Column(index.column()) == Column.IMAGE:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable  # not Qt.ItemIsEditable
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
        return self._collection

    def set_collection(self, collection: PromptCollection) -> None:
        self.beginResetModel()
        self._collection = collection
        self.endResetModel()

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def append_row(self, entry: PromptEntry | None = None) -> int:
        pos = len(self._collection.entries)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._collection.append(entry)
        self.endInsertRows()
        self.collection_modified.emit()
        return pos

    def insert_row(self, pos: int, entry: PromptEntry) -> int:
        pos = min(pos, len(self._collection.entries))
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._collection.entries.insert(pos, entry)
        self._collection.modified = True
        self.endInsertRows()
        self.collection_modified.emit()
        return pos

    def remove_rows(self, source_rows: list[int]) -> None:
        for row in sorted(set(source_rows), reverse=True):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._collection.entries.pop(row)
            self.endRemoveRows()
        self._collection.modified = True
        self.collection_modified.emit()

    def set_image(
        self,
        source_row: int,
        full_image: bytes | None,
        thumbnail: bytes | None,
    ) -> None:
        """Set the full image and thumbnail for *source_row*."""
        if source_row >= len(self._collection.entries):
            return
        entry = self._collection.entries[source_row]
        entry.image = full_image
        entry.thumbnail = thumbnail
        self._collection.modified = True
        idx = self.index(source_row, int(Column.IMAGE))
        self.dataChanged.emit(idx, idx, [Qt.DecorationRole])
        self.collection_modified.emit()

    def set_header_labels(self, labels: list[str]) -> None:
        self._headers = labels
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(Column) - 1)

    def set_header_tooltips(self, tooltips: list[str]) -> None:
        self._header_tooltips = tooltips
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(Column) - 1)


# ---------------------------------------------------------------------------
# Proxy model (multi-column filter + custom sort)
# ---------------------------------------------------------------------------


class MultiFilterProxyModel(QSortFilterProxyModel):
    """Proxy model supporting per-column regex filters and multi-key sort."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._filters: dict[int, str] = {}

    def set_filter(self, column: int, pattern: str) -> None:
        if pattern:
            self._filters[column] = pattern
        else:
            self._filters.pop(column, None)
        self.invalidateFilter()

    def clear_filters(self) -> None:
        self._filters.clear()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        for col, pattern in self._filters.items():
            if not pattern:
                continue
            if col == int(Column.IMAGE):
                continue  # IMAGE column is not filterable
            idx = model.index(source_row, col, source_parent)
            cell_data: str = model.data(idx, Qt.DisplayRole) or ""
            try:
                if not re.search(pattern, cell_data, re.IGNORECASE):
                    return False
            except re.error:
                pass
        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        primary_col = Column(left.column())
        sort_cols = _SORT_ORDER.get(primary_col, [primary_col])
        model = self.sourceModel()
        for col in sort_cols:
            c = int(col)
            left_idx = model.index(left.row(), c, left.parent())
            right_idx = model.index(right.row(), c, right.parent())
            left_val = (model.data(left_idx, Qt.DisplayRole) or "").lower()
            right_val = (model.data(right_idx, Qt.DisplayRole) or "").lower()
            if left_val != right_val:
                return left_val < right_val
        return False

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        if Column(column) not in _SORTABLE_COLUMNS:
            return
        super().sort(column, order)


# ---------------------------------------------------------------------------
# Current-cell highlight delegate (base for all columns)
# ---------------------------------------------------------------------------


class CurrentCellHighlightDelegate(QStyledItemDelegate):
    """Draws a distinct border on the current cell within a selected row."""

    def __init__(self, view: QTableView, parent: Any = None) -> None:
        super().__init__(parent)
        self._view = view

    def _draw_current_highlight(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
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
# Image delegate (IMAGE column)
# ---------------------------------------------------------------------------


class ImageDelegate(CurrentCellHighlightDelegate):
    """Delegate for the IMAGE column.

    Paints the thumbnail centred in the cell, or a placeholder icon when there
    is no image.  Double-click is consumed (the view handles it via
    ``mouseDoubleClickEvent``).
    """

    def __init__(
        self,
        view: QTableView,
        thumb_w: int = 64,
        thumb_h: int = 64,
        parent: Any = None,
    ) -> None:
        super().__init__(view, parent)
        self._thumb_w = thumb_w
        self._thumb_h = thumb_h

    def update_size(self, w: int, h: int) -> None:
        """Update the expected thumbnail size (after settings change)."""
        self._thumb_w = w
        self._thumb_h = h

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        # Draw standard background / selection highlight.
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)

        pixmap: QPixmap | None = index.data(Qt.DecorationRole)
        if pixmap and not pixmap.isNull():
            x = opt.rect.x() + max(0, (opt.rect.width() - pixmap.width()) // 2)
            y = opt.rect.y() + max(0, (opt.rect.height() - pixmap.height()) // 2)
            painter.drawPixmap(x, y, pixmap)
        else:
            # Draw a subtle "no image" placeholder frame.
            painter.save()
            color = opt.palette.color(QPalette.Mid)
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            inner = opt.rect.adjusted(4, 4, -4, -4)
            if inner.isValid():
                painter.drawRect(inner)
            painter.restore()

        self._draw_current_highlight(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        pixmap: QPixmap | None = index.data(Qt.DecorationRole)
        if pixmap and not pixmap.isNull():
            return QSize(self._thumb_w + 8, self._thumb_h + 8)
        # No image: let the row height be determined by other columns
        return QSize(self._thumb_w + 8, 1)

    def createEditor(self, parent: Any, option: Any, index: QModelIndex) -> None:
        return None  # IMAGE column is not inline-editable

    def editorEvent(
        self,
        event: QEvent,
        model: Any,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        # Consume double-click so Qt does not try to open an editor.
        # The view's mouseDoubleClickEvent emits image_activated instead.
        if event.type() == QEvent.MouseButtonDblClick:
            return True
        return super().editorEvent(event, model, option, index)


# ---------------------------------------------------------------------------
# Multi-line delegate (Local / English columns)
# ---------------------------------------------------------------------------

_NEWLINE_MARKER = "\u21b5"


class MultiLineDelegate(CurrentCellHighlightDelegate):
    """Delegate for the Local and English columns (multi-line text)."""

    def __init__(self, view: QTableView, parent: Any = None) -> None:
        super().__init__(view, parent)

    @staticmethod
    def _display_text(raw: str) -> str:
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
            width = 100

        raw: str = index.data(Qt.DisplayRole) or ""
        display = self._display_text(raw)

        margin = 4
        fm = option.fontMetrics
        bounding = fm.boundingRect(
            0,
            0,
            max(width - 2 * margin, 1),
            10000,
            Qt.TextWordWrap | Qt.AlignTop | Qt.AlignLeft,
            display,
        )
        h = bounding.height() + 2 * margin + 4
        base = super().sizeHint(option, index)
        return QSize(base.width(), max(h, base.height()))

    def createEditor(
        self, parent: Any, option: QStyleOptionViewItem, index: QModelIndex
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
        self, editor: Any, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        r = option.rect
        editor.setGeometry(r.x(), r.y(), r.width(), max(r.height(), 80))

    def eventFilter(self, obj: Any, event: Any) -> bool:
        if isinstance(obj, QPlainTextEdit):
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key in (Qt.Key_Return, Qt.Key_Enter):
                    if event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier):
                        obj.insertPlainText("\n")
                        return True
                    self.commitData.emit(obj)
                    self.closeEditor.emit(obj, QAbstractItemDelegate.NoHint)
                    return True
                if key in (Qt.Key_Up, Qt.Key_Down):
                    return False
                if key == Qt.Key_Tab:
                    self.commitData.emit(obj)
                    self.closeEditor.emit(obj, QAbstractItemDelegate.EditNextItem)
                    return True
                if key == Qt.Key_Backtab:
                    self.commitData.emit(obj)
                    self.closeEditor.emit(obj, QAbstractItemDelegate.EditPreviousItem)
                    return True
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)


# ---------------------------------------------------------------------------
# Custom table view
# ---------------------------------------------------------------------------


class PromptTableView(QTableView):
    """QTableView with clipboard support, image activation, and drag-and-drop."""

    cell_copied = pyqtSignal(str)
    #: Emitted (source model index) when the IMAGE column cell is double-clicked.
    image_activated = pyqtSignal(QModelIndex)
    #: Emitted (source model index, QMimeData) when an image is dropped on IMAGE column.
    image_drop_requested = pyqtSignal(object, object)

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: Any) -> None:  # type: ignore[override]
        if event.matches(QKeySequence.Copy):
            self._do_copy()
        elif event.matches(QKeySequence.Cut):
            self._do_cut()
        elif event.matches(QKeySequence.Paste):
            self._do_paste()
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Double-click — show full image for IMAGE column
    # ------------------------------------------------------------------

    def mouseDoubleClickEvent(self, event: Any) -> None:  # type: ignore[override]
        idx = self.indexAt(event.pos())
        if idx.isValid():
            source_idx = self.model().mapToSource(idx)
            if source_idx.column() == int(Column.IMAGE):
                self.image_activated.emit(source_idx)
                return
        super().mouseDoubleClickEvent(event)

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: Any) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if mime.hasImage():
            event.acceptProposedAction()
            return
        if mime.hasUrls() and any(url.isLocalFile() for url in mime.urls()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event: Any) -> None:  # type: ignore[override]
        idx = self.indexAt(event.pos())
        if idx.isValid():
            source_idx = self.model().mapToSource(idx)
            if source_idx.column() == int(Column.IMAGE):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: Any) -> None:  # type: ignore[override]
        idx = self.indexAt(event.pos())
        if idx.isValid():
            source_idx = self.model().mapToSource(idx)
            if source_idx.column() == int(Column.IMAGE):
                self.image_drop_requested.emit(source_idx, event.mimeData())
                event.acceptProposedAction()
                return
        event.ignore()

    # ------------------------------------------------------------------
    # Clipboard helpers
    # ------------------------------------------------------------------

    def _current_text(self) -> str:
        idx = self.currentIndex()
        if not idx.isValid():
            return ""
        return self.model().data(idx, Qt.DisplayRole) or ""

    def _do_copy(self) -> None:
        text = self._current_text()
        if text:
            QApplication.clipboard().setText(text)
            self.cell_copied.emit(text)

    def _do_cut(self) -> None:
        idx = self.currentIndex()
        if not idx.isValid():
            return
        text = self.model().data(idx, Qt.DisplayRole) or ""
        if text:
            QApplication.clipboard().setText(text)
            self.cell_copied.emit(text)
        self.model().setData(idx, "", Qt.EditRole)

    def _do_paste(self) -> None:
        idx = self.currentIndex()
        if not idx.isValid():
            return
        text = QApplication.clipboard().text()
        if text:
            self.model().setData(idx, text, Qt.EditRole)
