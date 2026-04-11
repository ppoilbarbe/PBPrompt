"""Internationalisation helpers (gettext-based).

Usage
-----
    from pbprompt.i18n import _, setup_i18n

    setup_i18n("fr")
    print(_("Save"))  # → "Enregistrer"
"""

from __future__ import annotations

import gettext
import locale
import logging
import sys
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)


def get_locale_dir() -> Path:
    """Return the locales directory, handling PyInstaller one-file bundles.

    When running from a PyInstaller bundle ``sys.frozen`` is ``True`` and
    ``sys._MEIPASS`` points to the temporary extraction directory where
    ``datas`` entries (including ``locales/``) are unpacked.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "locales"
    return Path(__file__).parent.parent.parent / "locales"


# Locale directory: resolved at import time.
_LOCALE_DIR = get_locale_dir()
_DOMAIN = "messages"

# Active translator – updated by setup_i18n()
_translator: gettext.GNUTranslations | gettext.NullTranslations = (
    gettext.NullTranslations()
)


def _null_translate(message: str) -> str:
    """Identity translation (fallback)."""
    return message


# Public translation callable – reassigned by setup_i18n()
_: Callable[[str], str] = _null_translate


def setup_i18n(language: str | None = None) -> None:
    """Load translations for *language* and bind the module-level ``_``.

    If *language* is ``None`` or the corresponding catalogue is missing, the
    function falls back to the system locale then to English (no-op).

    Parameters
    ----------
    language:
        POSIX locale code such as ``"fr"``, ``"en"``, or ``"fr_FR"``.
        Pass ``None`` to auto-detect from the environment.
    """
    global _, _translator  # noqa: PLW0603

    lang = language or _system_language()
    langs_to_try = _language_candidates(lang)

    try:
        translation = gettext.translation(
            _DOMAIN,
            localedir=str(_LOCALE_DIR),
            languages=langs_to_try,
        )
        translation.install()
        _translator = translation
        _ = translation.gettext
        logger.info("Loaded translations for %s", langs_to_try)
    except FileNotFoundError:
        logger.info(
            "No compiled translation found for %s; falling back to English.",
            langs_to_try,
        )
        _translator = gettext.NullTranslations()
        _ = _null_translate


def reload_i18n(language: str) -> None:
    """Switch to *language* at runtime; call ``retranslateUi()`` on windows yourself."""
    setup_i18n(language)


def get_translate() -> Callable[[str], str]:
    """Return the active translation callable."""
    return _


# ---------------------------------------------------------------------------
# Language display names (native name in the language itself)
# ---------------------------------------------------------------------------

_LANGUAGE_NAMES: dict[str, str] = {
    "ar": "العربية",
    "cs": "Čeština",
    "da": "Dansk",
    "de": "Deutsch",
    "el": "Ελληνικά",
    "en": "English",
    "es": "Español",
    "fi": "Suomi",
    "fr": "Français",
    "he": "עברית",
    "hu": "Magyar",
    "it": "Italiano",
    "ja": "日本語",
    "ko": "한국어",
    "nl": "Nederlands",
    "nb": "Norsk",
    "pl": "Polski",
    "pt": "Português",
    "ro": "Română",
    "ru": "Русский",
    "sk": "Slovenčina",
    "sv": "Svenska",
    "tr": "Türkçe",
    "uk": "Українська",
    "vi": "Tiếng Việt",
    "zh": "中文",
    "zh_CN": "中文(简体)",
    "zh_TW": "中文(繁體)",
}


def language_label(code: str) -> str:
    """Return ``'Native Name (code)'`` for a language code.

    Falls back to the base code (``'zh'`` for ``'zh_CN'``) then to the raw
    code if no name is known.

    Examples
    --------
    >>> language_label('fr')
    'Français (fr)'
    >>> language_label('zh_CN')
    '中文(简体) (zh_CN)'
    >>> language_label('xx')
    'xx'
    """
    name = _LANGUAGE_NAMES.get(code)
    if name is None:
        base = code.split("_")[0]
        name = _LANGUAGE_NAMES.get(base)
    if name:
        return f"{name} ({code})"
    return code


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def system_language() -> str:
    """Detect the system UI language (best-effort).

    Returns a short POSIX language code such as ``"fr"`` or ``"en"``.
    """
    try:
        lang, _ = locale.getlocale()
        if lang:
            return lang.split("_")[0]
    except Exception:  # noqa: BLE001
        pass
    return "en"


# Keep the private alias for internal use
_system_language = system_language


def _language_candidates(lang: str) -> list[str]:
    """Build a fallback list: ['fr_FR', 'fr', 'en']."""
    candidates: list[str] = []
    if "_" not in lang and len(lang) == 2:
        candidates.append(lang)
    else:
        short = lang.split("_")[0]
        candidates.extend([lang, short])
    if "en" not in candidates:
        candidates.append("en")
    return candidates
