# UI definition for the Settings dialog.
# Source-controlled file — edit directly, there is no .ui file to regenerate from.

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
)


class Ui_SettingsDialog:  # noqa: N801
    def setup_ui(self, settings_dialog: QDialog) -> None:
        if not settings_dialog.objectName():
            settings_dialog.setObjectName("SettingsDialog")
        settings_dialog.resize(440, 440)
        settings_dialog.setModal(True)

        self.verticalLayout = QVBoxLayout(settings_dialog)
        self.verticalLayout.setObjectName("verticalLayout")

        # --- Language group ---
        self.groupLanguage = QGroupBox(settings_dialog)
        self.groupLanguage.setObjectName("groupLanguage")
        self.formLayoutLang = QFormLayout(self.groupLanguage)
        self.formLayoutLang.setObjectName("formLayoutLang")

        self.labelDisplayLang = QLabel(self.groupLanguage)
        self.labelDisplayLang.setObjectName("labelDisplayLang")
        self.formLayoutLang.setWidget(
            0, QFormLayout.ItemRole.LabelRole, self.labelDisplayLang
        )

        self.comboDisplayLanguage = QComboBox(self.groupLanguage)
        self.comboDisplayLanguage.setObjectName("comboDisplayLanguage")
        self.formLayoutLang.setWidget(
            0, QFormLayout.ItemRole.FieldRole, self.comboDisplayLanguage
        )

        self.labelTranslationLang = QLabel(self.groupLanguage)
        self.labelTranslationLang.setObjectName("labelTranslationLang")
        self.formLayoutLang.setWidget(
            1, QFormLayout.ItemRole.LabelRole, self.labelTranslationLang
        )

        self.comboTranslationLanguage = QComboBox(self.groupLanguage)
        self.comboTranslationLanguage.setObjectName("comboTranslationLanguage")
        self.formLayoutLang.setWidget(
            1, QFormLayout.ItemRole.FieldRole, self.comboTranslationLanguage
        )

        self.verticalLayout.addWidget(self.groupLanguage)

        # --- Translation service group ---
        self.groupTranslation = QGroupBox(settings_dialog)
        self.groupTranslation.setObjectName("groupTranslation")
        self.formLayoutTranslation = QFormLayout(self.groupTranslation)
        self.formLayoutTranslation.setObjectName("formLayoutTranslation")

        self.labelService = QLabel(self.groupTranslation)
        self.labelService.setObjectName("labelService")
        self.formLayoutTranslation.setWidget(
            0, QFormLayout.ItemRole.LabelRole, self.labelService
        )

        self.comboService = QComboBox(self.groupTranslation)
        self.comboService.setObjectName("comboService")
        self.formLayoutTranslation.setWidget(
            0, QFormLayout.ItemRole.FieldRole, self.comboService
        )

        self.labelApiKey = QLabel(self.groupTranslation)
        self.labelApiKey.setObjectName("labelApiKey")
        self.formLayoutTranslation.setWidget(
            1, QFormLayout.ItemRole.LabelRole, self.labelApiKey
        )

        self.lineEditApiKey = QLineEdit(self.groupTranslation)
        self.lineEditApiKey.setObjectName("lineEditApiKey")
        self.lineEditApiKey.setEchoMode(QLineEdit.Password)
        self.formLayoutTranslation.setWidget(
            1, QFormLayout.ItemRole.FieldRole, self.lineEditApiKey
        )

        self.labelAppId = QLabel(self.groupTranslation)
        self.labelAppId.setObjectName("labelAppId")
        self.formLayoutTranslation.setWidget(
            2, QFormLayout.ItemRole.LabelRole, self.labelAppId
        )

        self.lineEditAppId = QLineEdit(self.groupTranslation)
        self.lineEditAppId.setObjectName("lineEditAppId")
        self.formLayoutTranslation.setWidget(
            2, QFormLayout.ItemRole.FieldRole, self.lineEditAppId
        )

        self.labelAppSecret = QLabel(self.groupTranslation)
        self.labelAppSecret.setObjectName("labelAppSecret")
        self.formLayoutTranslation.setWidget(
            3, QFormLayout.ItemRole.LabelRole, self.labelAppSecret
        )

        self.lineEditAppSecret = QLineEdit(self.groupTranslation)
        self.lineEditAppSecret.setObjectName("lineEditAppSecret")
        self.lineEditAppSecret.setEchoMode(QLineEdit.Password)
        self.formLayoutTranslation.setWidget(
            3, QFormLayout.ItemRole.FieldRole, self.lineEditAppSecret
        )

        self.verticalLayout.addWidget(self.groupTranslation)

        # --- Logging group ---
        self.groupLogging = QGroupBox(settings_dialog)
        self.groupLogging.setObjectName("groupLogging")
        self.formLayoutLog = QFormLayout(self.groupLogging)
        self.formLayoutLog.setObjectName("formLayoutLog")

        self.labelLogLevel = QLabel(self.groupLogging)
        self.labelLogLevel.setObjectName("labelLogLevel")
        self.formLayoutLog.setWidget(
            0, QFormLayout.ItemRole.LabelRole, self.labelLogLevel
        )

        self.comboLogLevel = QComboBox(self.groupLogging)
        self.comboLogLevel.setObjectName("comboLogLevel")
        self.formLayoutLog.setWidget(
            0, QFormLayout.ItemRole.FieldRole, self.comboLogLevel
        )

        self.verticalLayout.addWidget(self.groupLogging)

        # --- Files group ---
        self.groupFiles = QGroupBox(settings_dialog)
        self.groupFiles.setObjectName("groupFiles")
        self.formLayoutFiles = QFormLayout(self.groupFiles)
        self.formLayoutFiles.setObjectName("formLayoutFiles")

        self.labelMaxRecentFiles = QLabel(self.groupFiles)
        self.labelMaxRecentFiles.setObjectName("labelMaxRecentFiles")
        self.formLayoutFiles.setWidget(
            0, QFormLayout.ItemRole.LabelRole, self.labelMaxRecentFiles
        )

        self.spinBoxMaxRecentFiles = QSpinBox(self.groupFiles)
        self.spinBoxMaxRecentFiles.setObjectName("spinBoxMaxRecentFiles")
        self.spinBoxMaxRecentFiles.setMinimum(1)
        self.spinBoxMaxRecentFiles.setMaximum(50)
        self.spinBoxMaxRecentFiles.setValue(10)
        self.formLayoutFiles.setWidget(
            0, QFormLayout.ItemRole.FieldRole, self.spinBoxMaxRecentFiles
        )

        self.verticalLayout.addWidget(self.groupFiles)

        # --- Images group ---
        self.groupImages = QGroupBox(settings_dialog)
        self.groupImages.setObjectName("groupImages")
        self.formLayoutImages = QFormLayout(self.groupImages)
        self.formLayoutImages.setObjectName("formLayoutImages")

        self.labelThumbnailWidth = QLabel(self.groupImages)
        self.labelThumbnailWidth.setObjectName("labelThumbnailWidth")
        self.formLayoutImages.setWidget(
            0, QFormLayout.ItemRole.LabelRole, self.labelThumbnailWidth
        )

        self.spinBoxThumbnailWidth = QSpinBox(self.groupImages)
        self.spinBoxThumbnailWidth.setObjectName("spinBoxThumbnailWidth")
        self.spinBoxThumbnailWidth.setMinimum(16)
        self.spinBoxThumbnailWidth.setMaximum(512)
        self.spinBoxThumbnailWidth.setValue(80)
        self.formLayoutImages.setWidget(
            0, QFormLayout.ItemRole.FieldRole, self.spinBoxThumbnailWidth
        )

        self.labelThumbnailHeight = QLabel(self.groupImages)
        self.labelThumbnailHeight.setObjectName("labelThumbnailHeight")
        self.formLayoutImages.setWidget(
            1, QFormLayout.ItemRole.LabelRole, self.labelThumbnailHeight
        )

        self.spinBoxThumbnailHeight = QSpinBox(self.groupImages)
        self.spinBoxThumbnailHeight.setObjectName("spinBoxThumbnailHeight")
        self.spinBoxThumbnailHeight.setMinimum(16)
        self.spinBoxThumbnailHeight.setMaximum(512)
        self.spinBoxThumbnailHeight.setValue(80)
        self.formLayoutImages.setWidget(
            1, QFormLayout.ItemRole.FieldRole, self.spinBoxThumbnailHeight
        )

        self.labelViewerZoomMax = QLabel(self.groupImages)
        self.labelViewerZoomMax.setObjectName("labelViewerZoomMax")
        self.formLayoutImages.setWidget(
            2, QFormLayout.ItemRole.LabelRole, self.labelViewerZoomMax
        )

        self.spinBoxViewerZoomMax = QSpinBox(self.groupImages)
        self.spinBoxViewerZoomMax.setObjectName("spinBoxViewerZoomMax")
        self.spinBoxViewerZoomMax.setMinimum(1)
        self.spinBoxViewerZoomMax.setMaximum(16)
        self.spinBoxViewerZoomMax.setValue(4)
        self.formLayoutImages.setWidget(
            2, QFormLayout.ItemRole.FieldRole, self.spinBoxViewerZoomMax
        )

        self.labelViewerZoomStep = QLabel(self.groupImages)
        self.labelViewerZoomStep.setObjectName("labelViewerZoomStep")
        self.formLayoutImages.setWidget(
            3, QFormLayout.ItemRole.LabelRole, self.labelViewerZoomStep
        )

        self.spinBoxViewerZoomStep = QSpinBox(self.groupImages)
        self.spinBoxViewerZoomStep.setObjectName("spinBoxViewerZoomStep")
        self.spinBoxViewerZoomStep.setMinimum(1)
        self.spinBoxViewerZoomStep.setMaximum(50)
        self.spinBoxViewerZoomStep.setValue(10)
        self.formLayoutImages.setWidget(
            3, QFormLayout.ItemRole.FieldRole, self.spinBoxViewerZoomStep
        )

        # When checked, image store dimensions below are disabled
        self.checkBoxImageOriginal = QCheckBox(self.groupImages)
        self.checkBoxImageOriginal.setObjectName("checkBoxImageOriginal")
        self.checkBoxImageOriginal.setChecked(True)
        self.formLayoutImages.setWidget(
            4, QFormLayout.ItemRole.SpanningRole, self.checkBoxImageOriginal
        )

        self.labelImageStoreMaxWidth = QLabel(self.groupImages)
        self.labelImageStoreMaxWidth.setObjectName("labelImageStoreMaxWidth")
        self.labelImageStoreMaxWidth.setEnabled(False)
        self.formLayoutImages.setWidget(
            5, QFormLayout.ItemRole.LabelRole, self.labelImageStoreMaxWidth
        )

        self.spinBoxImageStoreMaxWidth = QSpinBox(self.groupImages)
        self.spinBoxImageStoreMaxWidth.setObjectName("spinBoxImageStoreMaxWidth")
        self.spinBoxImageStoreMaxWidth.setEnabled(False)
        self.spinBoxImageStoreMaxWidth.setMinimum(64)
        self.spinBoxImageStoreMaxWidth.setMaximum(32000)
        self.spinBoxImageStoreMaxWidth.setValue(1920)
        self.formLayoutImages.setWidget(
            5, QFormLayout.ItemRole.FieldRole, self.spinBoxImageStoreMaxWidth
        )

        self.labelImageStoreMaxHeight = QLabel(self.groupImages)
        self.labelImageStoreMaxHeight.setObjectName("labelImageStoreMaxHeight")
        self.labelImageStoreMaxHeight.setEnabled(False)
        self.formLayoutImages.setWidget(
            6, QFormLayout.ItemRole.LabelRole, self.labelImageStoreMaxHeight
        )

        self.spinBoxImageStoreMaxHeight = QSpinBox(self.groupImages)
        self.spinBoxImageStoreMaxHeight.setObjectName("spinBoxImageStoreMaxHeight")
        self.spinBoxImageStoreMaxHeight.setEnabled(False)
        self.spinBoxImageStoreMaxHeight.setMinimum(64)
        self.spinBoxImageStoreMaxHeight.setMaximum(32000)
        self.spinBoxImageStoreMaxHeight.setValue(1080)
        self.formLayoutImages.setWidget(
            6, QFormLayout.ItemRole.FieldRole, self.spinBoxImageStoreMaxHeight
        )

        self.verticalLayout.addWidget(self.groupImages)

        self.verticalSpacer = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(settings_dialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Save
        )
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslate_ui(settings_dialog)
        self.buttonBox.accepted.connect(settings_dialog.accept)
        self.buttonBox.rejected.connect(settings_dialog.reject)
        QMetaObject.connectSlotsByName(settings_dialog)

    def retranslate_ui(self, settings_dialog: QDialog) -> None:
        tr = QCoreApplication.translate
        settings_dialog.setWindowTitle(tr("SettingsDialog", "Settings"))
        self.groupLanguage.setTitle(tr("SettingsDialog", "Language"))
        self.labelDisplayLang.setText(tr("SettingsDialog", "Display language:"))
        self.labelTranslationLang.setText(tr("SettingsDialog", "Translation language:"))
        self.groupTranslation.setTitle(tr("SettingsDialog", "Translation service"))
        self.labelService.setText(tr("SettingsDialog", "Service:"))
        self.labelApiKey.setText(tr("SettingsDialog", "API key:"))
        self.lineEditApiKey.setPlaceholderText(
            tr("SettingsDialog", "DeepL, Microsoft, Yandex, QCRI, LibreTranslate")
        )
        self.labelAppId.setText(tr("SettingsDialog", "App ID:"))
        self.lineEditAppId.setPlaceholderText(
            tr("SettingsDialog", "Baidu (appid) · Papago (client_id)")
        )
        self.labelAppSecret.setText(tr("SettingsDialog", "App secret:"))
        self.lineEditAppSecret.setPlaceholderText(
            tr("SettingsDialog", "Baidu (appkey) · Papago (secret_key)")
        )
        self.groupLogging.setTitle(tr("SettingsDialog", "Logging"))
        self.labelLogLevel.setText(tr("SettingsDialog", "Log level:"))
        self.groupFiles.setTitle(tr("SettingsDialog", "Files"))
        self.labelMaxRecentFiles.setText(tr("SettingsDialog", "Maximum recent files:"))
        self.groupImages.setTitle(tr("SettingsDialog", "Images"))
        self.labelThumbnailWidth.setText(tr("SettingsDialog", "Thumbnail width (px):"))
        self.labelThumbnailHeight.setText(
            tr("SettingsDialog", "Thumbnail height (px):")
        )
        self.labelViewerZoomMax.setText(
            tr("SettingsDialog", "Image viewer max zoom (×):")
        )
        self.labelViewerZoomStep.setText(tr("SettingsDialog", "Zoom step (%):"))
        self.checkBoxImageOriginal.setText(
            tr("SettingsDialog", "Keep original dimensions")
        )
        self.labelImageStoreMaxWidth.setText(tr("SettingsDialog", "Max width (px):"))
        self.labelImageStoreMaxHeight.setText(tr("SettingsDialog", "Max height (px):"))
