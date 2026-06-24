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

# Mapping from logical name to FreeDesktop theme name.
# Honoured on Linux/KDE/GNOME; ignored silently on other platforms.
_THEME_ICON_MAP: dict[str, str] = {
    "new": "document-new",
    "open": "document-open",
    "save": "document-save",
    "save_as": "document-save-as",
    "close": "window-close",
    "quit": "application-exit",
    "delete": "edit-delete",
    "options": "preferences-system",
    "about": "help-about",
    "translate_right": "go-next",
    "translate_left": "go-previous",
    "new_prompt": "list-add",
    "duplicate": "edit-copy",
    "import_yaml": "document-import",
    "export_yaml": "document-export",
    "refresh_thumbnails": "view-refresh",
    "zoom_fit": "zoom-fit-best",
    "zoom_original": "zoom-original",
    "zoom_width": "zoom-fit-width",
    "zoom_height": "zoom-fit-height",
    "zoom_in": "zoom-in",
    "zoom_out": "zoom-out",
    "app": "pbprompt",
}

# Qt built-in fallback icons (last resort, no external files needed).
_STANDARD_ICON_MAP: dict[str, QStyle.StandardPixmap] = {
    "app": QStyle.SP_ComputerIcon,
    "new": QStyle.SP_FileIcon,
    "open": QStyle.SP_DialogOpenButton,
    "save": QStyle.SP_DialogSaveButton,
    "save_as": QStyle.SP_DialogSaveButton,
    "close": QStyle.SP_DialogCloseButton,
    "quit": QStyle.SP_TitleBarCloseButton,
    "delete": QStyle.SP_TrashIcon,
    "options": QStyle.SP_FileDialogDetailedView,
    "about": QStyle.SP_MessageBoxInformation,
    "translate_right": QStyle.SP_ArrowRight,
    "translate_left": QStyle.SP_ArrowLeft,
    "new_prompt": QStyle.SP_FileIcon,
    "duplicate": QStyle.SP_FileDialogContentsView,
    "import_yaml": QStyle.SP_DialogOpenButton,
    "export_yaml": QStyle.SP_DialogSaveButton,
    "refresh_thumbnails": QStyle.SP_BrowserReload,
    "zoom_fit": QStyle.SP_TitleBarMaxButton,
    "zoom_original": QStyle.SP_FileDialogDetailedView,
    "zoom_width": QStyle.SP_ArrowRight,
    "zoom_height": QStyle.SP_ArrowDown,
    "zoom_in": QStyle.SP_ArrowUp,
    "zoom_out": QStyle.SP_ArrowDown,
}


def get_icon(name: str) -> QIcon:
    """Return a QIcon for *name*, trying theme → file → Qt standard.

    Parameters
    ----------
    name:
        Logical icon name (e.g. ``"new"``, ``"save"``, ``"app"``).

    Returns
    -------
    QIcon
        Loaded icon, or an empty QIcon if nothing found.
    """
    # 1. Desktop icon theme (FreeDesktop; Linux/KDE/GNOME)
    theme_name = _THEME_ICON_MAP.get(name)
    if theme_name:
        theme_icon = QIcon.fromTheme(theme_name)
        if not theme_icon.isNull():
            return theme_icon

    # 2. Package icon files — try exact name first, then colour/light variants
    for suffix in (".svg", ".png"):
        for variant in (name, f"{name}_color", f"{name}_light", f"{name}_dark"):
            path = _ICON_DIR / f"{variant}{suffix}"
            if path.exists():
                icon = QIcon(str(path))
                if not icon.isNull():
                    return icon

    # 3. Qt built-in fallback (always available, no external files)
    if name in _STANDARD_ICON_MAP:
        app = QApplication.instance()
        if app:
            return app.style().standardIcon(_STANDARD_ICON_MAP[name])

    logger.debug("No icon found for %r; returning empty QIcon.", name)
    return QIcon()
