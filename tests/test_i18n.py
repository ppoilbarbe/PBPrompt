"""Tests for pbprompt.i18n."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


class TestGetLocaleDir:
    def test_returns_path(self) -> None:
        from pbprompt.i18n import get_locale_dir

        result = get_locale_dir()
        assert isinstance(result, Path)

    def test_contains_locales(self) -> None:
        from pbprompt.i18n import get_locale_dir

        assert "locales" in str(get_locale_dir())

    def test_frozen_path(self, tmp_path: Path) -> None:
        from pbprompt import i18n

        meipass = str(tmp_path / "meipass")
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", meipass, create=True),
        ):
            result = i18n.get_locale_dir()
        assert str(result) == str(Path(meipass) / "locales")


class TestSetupI18n:
    def test_setup_known_language(self) -> None:
        from pbprompt import i18n

        # French .mo exists — should succeed without error
        i18n.setup_i18n("fr")
        translate = i18n.get_translate()
        assert callable(translate)

    def test_setup_unknown_language_falls_back(self) -> None:
        from pbprompt import i18n

        # No .mo for "zzz" — should fall back silently
        i18n.setup_i18n("zzz")
        translate = i18n.get_translate()
        # Falls back to identity
        assert translate("hello") == "hello"

    def test_setup_none_uses_system_language(self) -> None:
        from pbprompt import i18n

        i18n.setup_i18n(None)
        assert callable(i18n.get_translate())

    def test_setup_resets_to_english(self) -> None:
        from pbprompt import i18n

        i18n.setup_i18n("fr")
        i18n.setup_i18n("zzz")  # no catalog → NullTranslations
        # NullTranslations returns the msgid unchanged
        assert i18n.get_translate()("Save") == "Save"

    def test_reload_i18n(self) -> None:
        from pbprompt import i18n

        i18n.reload_i18n("fr")
        assert callable(i18n.get_translate())

    def test_setup_no_catalog_falls_back_to_null_translate(
        self, tmp_path: Path
    ) -> None:
        """When no .mo exists, _null_translate is used."""
        from pbprompt import i18n

        with patch.object(i18n, "_LOCALE_DIR", tmp_path):
            i18n.setup_i18n("fr")

        translate = i18n.get_translate()
        # _null_translate: returns the input unchanged
        assert translate("Save") == "Save"
        assert translate("hello") == "hello"


class TestGetTranslate:
    def test_returns_callable(self) -> None:
        from pbprompt.i18n import get_translate

        t = get_translate()
        assert callable(t)
        assert isinstance(t("hello"), str)


class TestLanguageLabel:
    def test_known_code(self) -> None:
        from pbprompt.i18n import language_label

        assert language_label("fr") == "Français (fr)"

    def test_zh_cn(self) -> None:
        from pbprompt.i18n import language_label

        assert language_label("zh_CN") == "中文(简体) (zh_CN)"

    def test_base_code_fallback(self) -> None:
        from pbprompt.i18n import language_label

        # "zh_TW" has its own entry; "de_AT" falls back to "de" → "Deutsch"
        assert language_label("de_AT") == "Deutsch (de_AT)"

    def test_unknown_code_returns_code(self) -> None:
        from pbprompt.i18n import language_label

        assert language_label("xx") == "xx"

    def test_all_catalogue_codes(self) -> None:
        from pbprompt.i18n import language_label

        for code in ("en", "de", "es", "it", "ru", "vi", "zh_CN"):
            label = language_label(code)
            assert f"({code})" in label


class TestSystemLanguage:
    def test_returns_string(self) -> None:
        from pbprompt.i18n import system_language

        result = system_language()
        assert isinstance(result, str)
        assert len(result) >= 2

    def test_fallback_on_exception(self) -> None:
        from pbprompt import i18n

        with patch("pbprompt.i18n.locale.getlocale", side_effect=ValueError):
            result = i18n.system_language()
        assert result == "en"

    def test_fallback_when_lang_is_none(self) -> None:
        from pbprompt import i18n

        with patch("pbprompt.i18n.locale.getlocale", return_value=(None, None)):
            result = i18n.system_language()
        assert result == "en"


class TestLanguageCandidates:
    def test_short_code(self) -> None:
        from pbprompt.i18n import _language_candidates

        result = _language_candidates("fr")
        assert "fr" in result
        assert "en" in result

    def test_long_code_with_underscore(self) -> None:
        from pbprompt.i18n import _language_candidates

        result = _language_candidates("fr_FR")
        assert "fr_FR" in result
        assert "fr" in result
        assert "en" in result

    def test_en_not_duplicated(self) -> None:
        from pbprompt.i18n import _language_candidates

        result = _language_candidates("en")
        assert result.count("en") == 1
