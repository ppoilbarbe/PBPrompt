"""About dialog behaviour."""

from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog

from pbprompt import __app_name__, __version__
from pbprompt.gui.about_dialog_ui import Ui_AboutDialog
from pbprompt.gui.icons import get_icon
from pbprompt.i18n import get_translate


class AboutDialog(QDialog, Ui_AboutDialog):
    """Displays application information: icon, name, version, author, license.

    Parameters
    ----------
    parent:
        Optional Qt parent widget.
    """

    def __init__(self, parent: None = None) -> None:
        super().__init__(parent)
        self.setup_ui(self)
        self.retranslate_ui(self)

        # Application icon
        icon = get_icon("pbprompt")
        if not icon.isNull():
            pixmap: QPixmap = icon.pixmap(64, 64)
            self.iconLabel.setPixmap(pixmap)
        else:
            self.iconLabel.setText("PB")

        # Version and author labels
        _ = get_translate()
        self.versionLabel.setText(f"{_('Version:')} {__version__}")
        self.authorLabel.setText(f"{_('Authors:')} PBMou, Claude (Anthropic)")

    def retranslate_ui(self, widget: QDialog) -> None:  # type: ignore[override]
        _ = get_translate()
        widget.setWindowTitle(_("About {app}").format(app=__app_name__))
        self.appNameLabel.setText(__app_name__)
        self.descriptionLabel.setText(
            _("A program to register and categorize AI prompts to keep tries.")
        )
        self.licenseLabel.setText(
            '<a href="https://opensource.org/licenses/MIT">' + _("MIT License") + "</a>"
        )
