"""About dialog behaviour."""

from __future__ import annotations

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog

from pbprompt import __app_name__, __author__, __description__, __version__
from pbprompt.gui.icons import get_icon
from pbprompt.gui.ui_about_dialog import Ui_AboutDialog
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
        self.setupUi(self)
        self.retranslateUi(self)

        # Application icon
        icon = get_icon("app")
        if not icon.isNull():
            pixmap: QPixmap = icon.pixmap(64, 64)
            self.iconLabel.setPixmap(pixmap)
        else:
            self.iconLabel.setText("PB")

        # Version and author labels
        _ = get_translate()
        self.versionLabel.setText(f"{_('Version:')} {__version__}")
        self.authorLabel.setText(f"{_('Author:')} {__author__}")

    def retranslateUi(self, widget: QDialog) -> None:  # type: ignore[override]  # noqa: N802
        _ = get_translate()
        widget.setWindowTitle(_("About {app}").format(app=__app_name__))
        self.appNameLabel.setText(__app_name__)
        self.descriptionLabel.setText(_(__description__))
        self.licenseLabel.setText(
            '<a href="https://opensource.org/licenses/MIT">' + _("MIT License") + "</a>"
        )
