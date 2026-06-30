"""Icon loading: theme → package file → Qt standard fallback chain."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

logger = logging.getLogger(__name__)


def get_icon_dir() -> Path:
    """Return the icons directory, handling PyInstaller one-file bundles.

    In a frozen bundle ``sys._MEIPASS`` is the extraction root; icons are
    unpacked there under ``pbprompt/icons/`` (matching the package layout).
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "pbprompt" / "icons"
    return Path(__file__).parent.parent / "icons"


# Resolved once at import time.
_ICON_DIR = get_icon_dir()

# Mapping: SVG filename (without extension) → FreeDesktop theme name.
# Honoured on Linux/KDE/GNOME; ignored silently on other platforms.
_THEME_MAP: dict[str, str] = {
    "new": "document-new",
    "open": "document-open",
    "save": "document-save",
    "save-as": "document-save-as",
    "quit": "application-exit",
    "delete": "edit-delete",
    "preferences-system": "preferences-system",
    "help-about": "help-about",
    "translate-right": "go-next",
    "translate-left": "go-previous",
    "new-prompt": "list-add",
    "duplicate": "edit-copy",
    "import-yaml": "document-import",
    "import-yaml-merged": "document-import",
    "export-yaml": "document-export",
    "refresh-icons": "view-refresh",
    "zoom-fit": "zoom-fit-best",
    "zoom-original": "zoom-original",
    "zoom-width": "zoom-fit-width",
    "zoom-height": "zoom-fit-height",
    "zoom-in": "zoom-in",
    "zoom-out": "zoom-out",
    "pbprompt": "pbprompt",
}

# Qt built-in fallback icons (last resort, no external files needed).
_STANDARD_ICON_MAP: dict[str, QStyle.StandardPixmap] = {
    "pbprompt": QStyle.SP_ComputerIcon,
    "new": QStyle.SP_FileIcon,
    "open": QStyle.SP_DialogOpenButton,
    "save": QStyle.SP_DialogSaveButton,
    "save-as": QStyle.SP_DialogSaveButton,
    "quit": QStyle.SP_TitleBarCloseButton,
    "delete": QStyle.SP_TrashIcon,
    "preferences-system": QStyle.SP_FileDialogDetailedView,
    "help-about": QStyle.SP_MessageBoxInformation,
    "translate-right": QStyle.SP_ArrowRight,
    "translate-left": QStyle.SP_ArrowLeft,
    "new-prompt": QStyle.SP_FileIcon,
    "duplicate": QStyle.SP_FileDialogContentsView,
    "import-yaml": QStyle.SP_DialogOpenButton,
    "import-yaml-merged": QStyle.SP_DialogOpenButton,
    "export-yaml": QStyle.SP_DialogSaveButton,
    "refresh-icons": QStyle.SP_BrowserReload,
    "zoom-fit": QStyle.SP_TitleBarMaxButton,
    "zoom-original": QStyle.SP_FileDialogDetailedView,
    "zoom-width": QStyle.SP_ArrowRight,
    "zoom-height": QStyle.SP_ArrowDown,
    "zoom-in": QStyle.SP_ArrowUp,
    "zoom-out": QStyle.SP_ArrowDown,
}


def get_icon(svg_name: str) -> QIcon:
    """Return a QIcon for *svg_name*, trying theme → file → Qt standard.

    Parameters
    ----------
    svg_name:
        SVG filename without extension (e.g. ``"new"``, ``"save-as"``,
        ``"pbprompt"``). Must match an existing file in the icons package
        directory.

    Returns
    -------
    QIcon
        Loaded icon, or an empty QIcon if nothing found.
    """
    # 1. Desktop icon theme (FreeDesktop; Linux/KDE/GNOME)
    theme_name = _THEME_MAP.get(svg_name, "")
    if theme_name:
        icon = QIcon.fromTheme(theme_name)
        if not icon.isNull():
            return icon

    # 2. Package SVG file
    path = _ICON_DIR / f"{svg_name}.svg"
    if path.exists():
        icon = QIcon(str(path))
        if not icon.isNull():
            return icon

    # 3. Qt built-in fallback (always available, no external files)
    if svg_name in _STANDARD_ICON_MAP:
        app = QApplication.instance()
        if app:
            return app.style().standardIcon(_STANDARD_ICON_MAP[svg_name])

    logger.debug("No icon found for %r; returning empty QIcon.", svg_name)
    return QIcon()
