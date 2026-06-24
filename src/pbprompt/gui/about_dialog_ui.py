# UI definition for the About dialog.
# Source file — do NOT regenerate from about_dialog.ui via pyside6-uic.

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)


class Ui_AboutDialog:  # noqa: N801
    def setupUi(self, AboutDialog: QDialog) -> None:  # noqa: N802
        if not AboutDialog.objectName():
            AboutDialog.setObjectName("AboutDialog")
        AboutDialog.resize(360, 260)
        AboutDialog.setModal(True)

        self.verticalLayout = QVBoxLayout(AboutDialog)
        self.verticalLayout.setObjectName("verticalLayout")

        # Header: app icon on the left, name/version/author on the right
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setObjectName("headerLayout")

        self.iconLabel = QLabel(AboutDialog)
        self.iconLabel.setObjectName("iconLabel")
        self.iconLabel.setMinimumSize(QSize(64, 64))
        self.iconLabel.setMaximumSize(QSize(64, 64))
        self.iconLabel.setAlignment(Qt.AlignCenter)
        self.headerLayout.addWidget(self.iconLabel)

        self.infoLayout = QVBoxLayout()
        self.infoLayout.setObjectName("infoLayout")

        self.appNameLabel = QLabel(AboutDialog)
        self.appNameLabel.setObjectName("appNameLabel")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.appNameLabel.setFont(font)
        self.infoLayout.addWidget(self.appNameLabel)

        self.versionLabel = QLabel(AboutDialog)
        self.versionLabel.setObjectName("versionLabel")
        self.infoLayout.addWidget(self.versionLabel)

        self.authorLabel = QLabel(AboutDialog)
        self.authorLabel.setObjectName("authorLabel")
        self.infoLayout.addWidget(self.authorLabel)

        self.descriptionLabel = QLabel(AboutDialog)
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.descriptionLabel.setWordWrap(True)
        self.infoLayout.addWidget(self.descriptionLabel)

        self.headerLayout.addLayout(self.infoLayout)
        self.verticalLayout.addLayout(self.headerLayout)

        # License link (centered)
        self.licenseLabel = QLabel(AboutDialog)
        self.licenseLabel.setObjectName("licenseLabel")
        self.licenseLabel.setOpenExternalLinks(True)
        self.licenseLabel.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.licenseLabel)

        self.verticalSpacer = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(AboutDialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(AboutDialog)
        self.buttonBox.rejected.connect(AboutDialog.reject)
        QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog: QDialog) -> None:  # noqa: N802
        tr = QCoreApplication.translate
        AboutDialog.setWindowTitle(tr("AboutDialog", "About PBPrompt"))
        self.iconLabel.setText("")
        self.appNameLabel.setText(tr("AboutDialog", "PBPrompt"))
        self.versionLabel.setText(tr("AboutDialog", "Version: 1.0.0"))
        self.authorLabel.setText(
            tr("AboutDialog", "Authors: PBMou, Claude (Anthropic)")
        )
        self.descriptionLabel.setText(
            tr("AboutDialog", "A program to register and categorize IA prompts.")
        )
        self.licenseLabel.setText(
            tr(
                "AboutDialog",
                '<a href="https://opensource.org/licenses/MIT">MIT License</a>',
            )
        )
