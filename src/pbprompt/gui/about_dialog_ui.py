# UI definition for the About dialog.
# Source-controlled file — edit directly, there is no .ui file to regenerate from.

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
    def setup_ui(self, about_dialog: QDialog) -> None:
        if not about_dialog.objectName():
            about_dialog.setObjectName("AboutDialog")
        about_dialog.resize(360, 260)
        about_dialog.setModal(True)

        self.verticalLayout = QVBoxLayout(about_dialog)
        self.verticalLayout.setObjectName("verticalLayout")

        # Header: app icon on the left, name/version/author on the right
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setObjectName("headerLayout")

        self.iconLabel = QLabel(about_dialog)
        self.iconLabel.setObjectName("iconLabel")
        self.iconLabel.setMinimumSize(QSize(64, 64))
        self.iconLabel.setMaximumSize(QSize(64, 64))
        self.iconLabel.setAlignment(Qt.AlignCenter)
        self.headerLayout.addWidget(self.iconLabel)

        self.infoLayout = QVBoxLayout()
        self.infoLayout.setObjectName("infoLayout")

        self.appNameLabel = QLabel(about_dialog)
        self.appNameLabel.setObjectName("appNameLabel")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.appNameLabel.setFont(font)
        self.infoLayout.addWidget(self.appNameLabel)

        self.versionLabel = QLabel(about_dialog)
        self.versionLabel.setObjectName("versionLabel")
        self.infoLayout.addWidget(self.versionLabel)

        self.authorLabel = QLabel(about_dialog)
        self.authorLabel.setObjectName("authorLabel")
        self.infoLayout.addWidget(self.authorLabel)

        self.descriptionLabel = QLabel(about_dialog)
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.descriptionLabel.setWordWrap(True)
        self.infoLayout.addWidget(self.descriptionLabel)

        self.headerLayout.addLayout(self.infoLayout)
        self.verticalLayout.addLayout(self.headerLayout)

        # License link (centered)
        self.licenseLabel = QLabel(about_dialog)
        self.licenseLabel.setObjectName("licenseLabel")
        self.licenseLabel.setOpenExternalLinks(True)
        self.licenseLabel.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.licenseLabel)

        self.verticalSpacer = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(about_dialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslate_ui(about_dialog)
        self.buttonBox.rejected.connect(about_dialog.reject)
        QMetaObject.connectSlotsByName(about_dialog)

    def retranslate_ui(self, about_dialog: QDialog) -> None:
        tr = QCoreApplication.translate
        about_dialog.setWindowTitle(tr("AboutDialog", "About PBPrompt"))
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
