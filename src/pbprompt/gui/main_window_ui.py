# UI definition for the main application window.
# Source-controlled file — edit directly, there is no .ui file to regenerate from.

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pbprompt.gui.models import PromptTableView


class Ui_MainWindow:  # noqa: N801
    def setup_ui(self, main_window: QMainWindow) -> None:
        if not main_window.objectName():
            main_window.setObjectName("MainWindow")
        main_window.resize(1100, 700)

        # --- Actions ---
        self.actionFileNew = QAction(main_window)
        self.actionFileNew.setObjectName("actionFileNew")
        self.actionFileOpen = QAction(main_window)
        self.actionFileOpen.setObjectName("actionFileOpen")
        self.actionFileSave = QAction(main_window)
        self.actionFileSave.setObjectName("actionFileSave")
        self.actionFileSaveAs = QAction(main_window)
        self.actionFileSaveAs.setObjectName("actionFileSaveAs")
        self.actionFileClose = QAction(main_window)
        self.actionFileClose.setObjectName("actionFileClose")
        self.actionFileQuit = QAction(main_window)
        self.actionFileQuit.setObjectName("actionFileQuit")
        self.actionToolsOptions = QAction(main_window)
        self.actionToolsOptions.setObjectName("actionToolsOptions")
        self.actionHelpAbout = QAction(main_window)
        self.actionHelpAbout.setObjectName("actionHelpAbout")
        self.actionNewPrompt = QAction(main_window)
        self.actionNewPrompt.setObjectName("actionNewPrompt")
        self.actionDuplicatePrompt = QAction(main_window)
        self.actionDuplicatePrompt.setObjectName("actionDuplicatePrompt")
        self.actionDeletePrompts = QAction(main_window)
        self.actionDeletePrompts.setObjectName("actionDeletePrompts")
        self.actionTranslateToEnglish = QAction(main_window)
        self.actionTranslateToEnglish.setObjectName("actionTranslateToEnglish")
        self.actionTranslateFromEnglish = QAction(main_window)
        self.actionTranslateFromEnglish.setObjectName("actionTranslateFromEnglish")
        self.actionImportYamlAdd = QAction(main_window)
        self.actionImportYamlAdd.setObjectName("actionImportYamlAdd")
        self.actionImportYamlReplace = QAction(main_window)
        self.actionImportYamlReplace.setObjectName("actionImportYamlReplace")
        self.actionExportYaml = QAction(main_window)
        self.actionExportYaml.setObjectName("actionExportYaml")
        self.actionRefreshThumbnails = QAction(main_window)
        self.actionRefreshThumbnails.setObjectName("actionRefreshThumbnails")

        # --- Central widget ---
        self.centralwidget = QWidget(main_window)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 4)

        # Filter bar: one QLineEdit per searchable column
        self.filterLayout = QHBoxLayout()
        self.filterLayout.setSpacing(4)
        self.filterLayout.setObjectName("filterLayout")

        self.filterLabel = QLabel(self.centralwidget)
        self.filterLabel.setObjectName("filterLabel")
        self.filterLabel.setMinimumWidth(40)
        self.filterLayout.addWidget(self.filterLabel)

        self.filterAi = QLineEdit(self.centralwidget)
        self.filterAi.setObjectName("filterAi")
        self.filterAi.setClearButtonEnabled(True)
        self.filterLayout.addWidget(self.filterAi)

        self.filterGroup = QLineEdit(self.centralwidget)
        self.filterGroup.setObjectName("filterGroup")
        self.filterGroup.setClearButtonEnabled(True)
        self.filterLayout.addWidget(self.filterGroup)

        self.filterName = QLineEdit(self.centralwidget)
        self.filterName.setObjectName("filterName")
        self.filterName.setClearButtonEnabled(True)
        self.filterLayout.addWidget(self.filterName)

        self.filterLocal = QLineEdit(self.centralwidget)
        self.filterLocal.setObjectName("filterLocal")
        self.filterLocal.setClearButtonEnabled(True)
        self.filterLayout.addWidget(self.filterLocal)

        self.filterEnglish = QLineEdit(self.centralwidget)
        self.filterEnglish.setObjectName("filterEnglish")
        self.filterEnglish.setClearButtonEnabled(True)
        self.filterLayout.addWidget(self.filterEnglish)

        self.clearFiltersButton = QPushButton(self.centralwidget)
        self.clearFiltersButton.setObjectName("clearFiltersButton")
        self.clearFiltersButton.setMaximumWidth(60)
        self.filterLayout.addWidget(self.clearFiltersButton)

        self.verticalLayout.addLayout(self.filterLayout)

        # Prompt table
        self.tableView = PromptTableView(self.centralwidget)
        self.tableView.setObjectName("tableView")
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSortingEnabled(False)
        self.tableView.setWordWrap(False)
        self.verticalLayout.addWidget(self.tableView)

        main_window.setCentralWidget(self.centralwidget)

        # --- Menu bar ---
        self.menubar = QMenuBar(main_window)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1100, 24))

        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuRecentFiles = QMenu(self.menuFile)
        self.menuRecentFiles.setObjectName("menuRecentFiles")
        self.menuImportYaml = QMenu(self.menuFile)
        self.menuImportYaml.setObjectName("menuImportYaml")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        main_window.setMenuBar(self.menubar)

        # File menu structure
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionFileNew)
        self.menuFile.addAction(self.actionFileOpen)
        self.menuFile.addAction(self.menuRecentFiles.menuAction())
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionFileSave)
        self.menuFile.addAction(self.actionFileSaveAs)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.menuImportYaml.menuAction())
        self.menuFile.addAction(self.actionExportYaml)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionFileClose)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionFileQuit)
        self.menuImportYaml.addAction(self.actionImportYamlAdd)
        self.menuImportYaml.addAction(self.actionImportYamlReplace)
        self.menuTools.addAction(self.actionToolsOptions)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionRefreshThumbnails)
        self.menuHelp.addAction(self.actionHelpAbout)

        # --- Toolbar ---
        self.mainToolBar = QToolBar(main_window)
        self.mainToolBar.setObjectName("mainToolBar")
        main_window.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.mainToolBar)
        self.mainToolBar.addAction(self.actionFileNew)
        self.mainToolBar.addAction(self.actionFileOpen)
        self.mainToolBar.addAction(self.actionFileSave)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.actionNewPrompt)
        self.mainToolBar.addAction(self.actionDuplicatePrompt)
        self.mainToolBar.addAction(self.actionDeletePrompts)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.actionTranslateToEnglish)
        self.mainToolBar.addAction(self.actionTranslateFromEnglish)

        # --- Status bar ---
        self.statusbar = QStatusBar(main_window)
        self.statusbar.setObjectName("statusbar")
        main_window.setStatusBar(self.statusbar)

        self.retranslate_ui(main_window)
        QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, main_window: QMainWindow) -> None:
        # Shortcuts omitted: MainWindow.retranslate_ui() in main_window.py overrides
        # this method via Python MRO and sets all shortcuts there.
        tr = QCoreApplication.translate
        main_window.setWindowTitle(tr("MainWindow", "PBPrompt"))
        self.actionFileNew.setText(tr("MainWindow", "&New"))
        self.actionFileNew.setToolTip(tr("MainWindow", "New file"))
        self.actionFileOpen.setText(tr("MainWindow", "&Open…"))
        self.actionFileOpen.setToolTip(tr("MainWindow", "Open a prompt file"))
        self.actionFileSave.setText(tr("MainWindow", "&Save"))
        self.actionFileSave.setToolTip(tr("MainWindow", "Save the current file"))
        self.actionFileSaveAs.setText(tr("MainWindow", "Save &As…"))
        self.actionFileSaveAs.setToolTip(tr("MainWindow", "Save to a new file"))
        self.actionFileClose.setText(tr("MainWindow", "&Close"))
        self.actionFileClose.setToolTip(tr("MainWindow", "Close current file"))
        self.actionFileQuit.setText(tr("MainWindow", "&Quit"))
        self.actionFileQuit.setToolTip(tr("MainWindow", "Quit PBPrompt"))
        self.actionToolsOptions.setText(tr("MainWindow", "&Options…"))
        self.actionToolsOptions.setToolTip(tr("MainWindow", "Open settings dialog"))
        self.actionHelpAbout.setText(tr("MainWindow", "&About…"))
        self.actionHelpAbout.setToolTip(tr("MainWindow", "About PBPrompt"))
        self.actionNewPrompt.setText(tr("MainWindow", "New Prompt"))
        self.actionNewPrompt.setToolTip(tr("MainWindow", "Add a new prompt entry"))
        self.actionDuplicatePrompt.setText(tr("MainWindow", "Duplicate"))
        self.actionDuplicatePrompt.setToolTip(
            tr("MainWindow", "Duplicate the current row")
        )
        self.actionDeletePrompts.setText(tr("MainWindow", "Delete"))
        self.actionDeletePrompts.setToolTip(tr("MainWindow", "Delete selected prompts"))
        self.actionTranslateToEnglish.setText(tr("MainWindow", "→ English"))
        self.actionTranslateToEnglish.setToolTip(
            tr("MainWindow", "Translate selected rows to English")
        )
        self.actionTranslateFromEnglish.setText(tr("MainWindow", "← Local"))
        self.actionTranslateFromEnglish.setToolTip(
            tr("MainWindow", "Translate selected rows from English")
        )
        self.actionImportYamlAdd.setText(tr("MainWindow", "Add entries…"))
        self.actionImportYamlAdd.setToolTip(
            tr("MainWindow", "Import YAML file (append)")
        )
        self.actionImportYamlReplace.setText(tr("MainWindow", "Replace all…"))
        self.actionImportYamlReplace.setToolTip(
            tr("MainWindow", "Import YAML file (replace all)")
        )
        self.actionExportYaml.setText(tr("MainWindow", "Export &YAML…"))
        self.actionExportYaml.setToolTip(tr("MainWindow", "Export YAML file"))
        self.actionRefreshThumbnails.setText(tr("MainWindow", "Refresh Thumbnails"))
        self.actionRefreshThumbnails.setToolTip(
            tr("MainWindow", "Regenerate all thumbnails from stored images")
        )
        self.filterLabel.setText(tr("MainWindow", "Filter:"))
        self.filterAi.setPlaceholderText(tr("MainWindow", "AI…"))
        self.filterGroup.setPlaceholderText(tr("MainWindow", "Group…"))
        self.filterName.setPlaceholderText(tr("MainWindow", "Name…"))
        self.filterLocal.setPlaceholderText(tr("MainWindow", "Local language…"))
        self.filterEnglish.setPlaceholderText(tr("MainWindow", "English…"))
        self.clearFiltersButton.setText(tr("MainWindow", "Clear"))
        self.clearFiltersButton.setToolTip(tr("MainWindow", "Clear all filters"))
        self.menuFile.setTitle(tr("MainWindow", "&File"))
        self.menuRecentFiles.setTitle(tr("MainWindow", "Recent &Files"))
        self.menuImportYaml.setTitle(tr("MainWindow", "Import &YAML"))
        self.menuTools.setTitle(tr("MainWindow", "&Tools"))
        self.menuHelp.setTitle(tr("MainWindow", "&Help"))
