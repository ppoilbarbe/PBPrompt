"""Settings dialog behaviour."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QDialog

from pbprompt.config import TRANSLATION_SERVICES, VALID_LOG_LEVELS, AppConfig
from pbprompt.gui.ui_settings_dialog import Ui_SettingsDialog
from pbprompt.i18n import get_locale_dir, get_translate, language_label

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Resolved at import time; handles both normal execution and PyInstaller bundles.
_LOCALES_DIR = get_locale_dir()


def _available_display_languages() -> list[tuple[str, str]]:
    """Return (code, label) pairs for every compiled UI translation.

    Scans *locales/* for sub-directories that contain a compiled
    ``LC_MESSAGES/messages.mo`` file.  The list is sorted alphabetically by
    code so the combo box order is deterministic.  English is always included
    even if no ``.mo`` file is found (gettext falls back to the source strings).
    """
    found: list[tuple[str, str]] = []
    if _LOCALES_DIR.exists():
        for lang_dir in sorted(_LOCALES_DIR.iterdir()):
            if (
                lang_dir.is_dir()
                and (lang_dir / "LC_MESSAGES" / "messages.mo").exists()
            ):
                code = lang_dir.name
                found.append((code, language_label(code)))
    if not found:
        found.append(("en", language_label("en")))
    return found


# Language codes for the translation (content) column.
# This list covers common translation-service target languages and is
# intentionally broader than the UI translations list.
_TRANSLATION_LANGUAGES: list[tuple[str, str]] = [
    (code, language_label(code))
    for code in (
        "ar",
        "cs",
        "da",
        "de",
        "el",
        "es",
        "fi",
        "fr",
        "he",
        "hu",
        "it",
        "ja",
        "ko",
        "nl",
        "nb",
        "pl",
        "pt",
        "ro",
        "ru",
        "sk",
        "sv",
        "tr",
        "uk",
        "vi",
        "zh_CN",
        "zh_TW",
    )
]

# Service display names (order matches TRANSLATION_SERVICES in config.py)
_SERVICE_LABELS: dict[str, str] = {
    "google": "Google Translate",
    "mymemory": "MyMemory",
    "deepl": "DeepL",
    "microsoft": "Microsoft Translator (Bing)",
    "yandex": "Yandex Translate",
    "libretranslate": "LibreTranslate",
    "baidu": "Baidu Translate",
    "papago": "Papago (Naver)",
    "qcri": "QCRI",
    "pons": "PONS",
    "linguee": "Linguee",
    "reverso": "Reverso",
}


class SettingsDialog(QDialog, Ui_SettingsDialog):
    """Settings dialog allowing the user to configure application options.

    Parameters
    ----------
    config:
        Current application configuration (will be copied, not mutated until
        the user clicks Save).
    parent:
        Optional Qt parent widget.
    """

    def __init__(self, config: AppConfig, parent: None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.retranslateUi(self)

        # Work on a copy so we can discard changes on Cancel
        self._config = AppConfig(
            display_language=config.display_language,
            translation_language=config.translation_language,
            translation_service=config.translation_service,
            translation_api_key=config.translation_api_key,
            translation_app_id=config.translation_app_id,
            translation_app_secret=config.translation_app_secret,
            libretranslate_url=config.libretranslate_url,
            log_level=config.log_level,
            recent_files=list(config.recent_files),
            recent_files_max=config.recent_files_max,
            thumbnail_width=config.thumbnail_width,
            thumbnail_height=config.thumbnail_height,
        )

        self._populate_combos()
        self._load_values()

    # ------------------------------------------------------------------
    # Populated config accessor (valid after exec_() == Accepted)
    # ------------------------------------------------------------------

    @property
    def config(self) -> AppConfig:
        """Return the (possibly modified) config after the dialog closes."""
        return self._config

    # ------------------------------------------------------------------
    # retranslateUi override
    # ------------------------------------------------------------------

    def retranslateUi(self, widget: QDialog) -> None:  # type: ignore[override]  # noqa: N802
        _ = get_translate()
        widget.setWindowTitle(_("Settings"))

        # --- Language group ---
        self.groupLanguage.setTitle(_("Language"))
        self.labelDisplayLang.setText(_("Display language:"))
        self.comboDisplayLanguage.setToolTip(
            _(
                "Language used for the user interface.\n"
                "'System default' uses the operating system locale."
            )
        )
        self.labelTranslationLang.setText(_("Translation language:"))
        self.comboTranslationLanguage.setToolTip(
            _(
                "Language of the 'Local language' column.\n"
                "Used as the source or target when translating prompts.\n"
                "'System default' uses the operating system locale."
            )
        )

        # --- Translation service group ---
        self.groupTranslation.setTitle(_("Translation service"))
        self.labelService.setText(_("Service:"))
        self.comboService.setToolTip(
            _(
                "Translation service used to fill the 'Local language' column\n"
                "automatically when clicking the Translate button."
            )
        )
        self.labelApiKey.setText(_("API key:"))
        self.lineEditApiKey.setToolTip(
            _(
                "API key required by DeepL, Microsoft Translator, Yandex,\n"
                "QCRI and LibreTranslate.\n"
                "Leave blank for services that do not require one\n"
                "(Google, MyMemory, PONS, Linguee, Reverso…)."
            )
        )
        self.lineEditApiKey.setPlaceholderText(
            _("DeepL, Microsoft, Yandex, QCRI, LibreTranslate")
        )
        self.labelAppId.setText(_("App ID:"))
        self.lineEditAppId.setToolTip(
            _(
                "Application identifier required by some services:\n"
                "• Baidu: appid\n"
                "• Papago: client_id"
            )
        )
        self.lineEditAppId.setPlaceholderText(_("Baidu (appid) · Papago (client_id)"))
        self.labelAppSecret.setText(_("App secret:"))
        self.lineEditAppSecret.setToolTip(
            _(
                "Application secret required by some services:\n"
                "• Baidu: appkey\n"
                "• Papago: secret_key"
            )
        )
        self.lineEditAppSecret.setPlaceholderText(
            _("Baidu (appkey) · Papago (secret_key)")
        )

        # --- Logging group ---
        self.groupLogging.setTitle(_("Logging"))
        self.labelLogLevel.setText(_("Log level:"))
        self.comboLogLevel.setToolTip(
            _(
                "Verbosity of the application log.\n"
                "DEBUG shows all messages; ERROR shows only critical failures.\n"
                "Effective after restarting the application."
            )
        )

        # --- Files group ---
        self.groupFiles.setTitle(_("Files"))
        self.labelMaxRecentFiles.setText(_("Maximum recent files:"))
        self.spinBoxMaxRecentFiles.setToolTip(
            _("Maximum number of recently opened files shown in the File menu.")
        )

        # --- Images group ---
        self.groupImages.setTitle(_("Images"))
        self.labelThumbnailWidth.setText(_("Thumbnail width (px):"))
        self.spinBoxThumbnailWidth.setToolTip(
            _(
                "Maximum width (in pixels) of the thumbnail stored in the database.\n"
                "Larger values improve quality but increase database size."
            )
        )
        self.labelThumbnailHeight.setText(_("Thumbnail height (px):"))
        self.spinBoxThumbnailHeight.setToolTip(
            _(
                "Maximum height (in pixels) of the thumbnail stored in the database.\n"
                "Larger values improve quality but increase database size."
            )
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _populate_combos(self) -> None:
        """Fill all combo boxes with available choices."""
        _ = get_translate()
        self.comboDisplayLanguage.clear()
        # Empty string = use the OS locale (always first, always the default)
        self.comboDisplayLanguage.addItem(_("System default"), userData="")
        for code, label in _available_display_languages():
            self.comboDisplayLanguage.addItem(label, userData=code)

        self.comboTranslationLanguage.clear()
        # Empty string = use the OS locale (always first, always the default)
        self.comboTranslationLanguage.addItem(_("System default"), userData="")
        for code, label in _TRANSLATION_LANGUAGES:
            self.comboTranslationLanguage.addItem(label, userData=code)

        self.comboService.clear()
        for svc in TRANSLATION_SERVICES:
            self.comboService.addItem(_SERVICE_LABELS.get(svc, svc), userData=svc)

        self.comboLogLevel.clear()
        for level in VALID_LOG_LEVELS:
            self.comboLogLevel.addItem(level, userData=level)

    def _load_values(self) -> None:
        """Set combo boxes and fields to current config values."""
        _set_combo(self.comboDisplayLanguage, self._config.display_language)
        _set_combo(self.comboTranslationLanguage, self._config.translation_language)
        _set_combo(self.comboService, self._config.translation_service)
        _set_combo(self.comboLogLevel, self._config.log_level)
        self.lineEditApiKey.setText(self._config.translation_api_key)
        self.lineEditAppId.setText(self._config.translation_app_id)
        self.lineEditAppSecret.setText(self._config.translation_app_secret)
        self.spinBoxMaxRecentFiles.setValue(self._config.recent_files_max)
        self.spinBoxThumbnailWidth.setValue(self._config.thumbnail_width)
        self.spinBoxThumbnailHeight.setValue(self._config.thumbnail_height)

    # ------------------------------------------------------------------
    # QDialog override
    # ------------------------------------------------------------------

    def accept(self) -> None:
        """Persist the user's choices before closing."""
        self._config.display_language = self.comboDisplayLanguage.currentData() or ""
        self._config.translation_language = (
            self.comboTranslationLanguage.currentData() or ""
        )
        self._config.translation_service = self.comboService.currentData() or "google"
        self._config.translation_api_key = self.lineEditApiKey.text().strip()
        self._config.translation_app_id = self.lineEditAppId.text().strip()
        self._config.translation_app_secret = self.lineEditAppSecret.text().strip()
        self._config.log_level = self.comboLogLevel.currentData() or "INFO"
        self._config.recent_files_max = self.spinBoxMaxRecentFiles.value()
        self._config.thumbnail_width = self.spinBoxThumbnailWidth.value()
        self._config.thumbnail_height = self.spinBoxThumbnailHeight.value()

        try:
            self._config.save()
        except Exception:
            logger.warning("Failed to save configuration.", exc_info=True)

        super().accept()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_combo(combo: object, value: str) -> None:
    """Select the item whose userData matches *value* in *combo*."""
    from PyQt5.QtWidgets import QComboBox  # noqa: PLC0415

    if not isinstance(combo, QComboBox):
        return
    for i in range(combo.count()):
        if combo.itemData(i) == value:
            combo.setCurrentIndex(i)
            return
