"""Tests for the translation layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pbprompt.translate.base import BaseTranslator


class _EchoTranslator(BaseTranslator):
    """A no-op translator that echoes the input with a prefix."""

    def _do_translate(self, text: str, source: str, target: str) -> str:
        return f"[{source}→{target}] {text}"


class TestBaseTranslator:
    def test_to_english(self) -> None:
        t = _EchoTranslator()
        result = t.to_english("hello", source_language="fr")
        assert "fr→en" in result

    def test_from_english(self) -> None:
        t = _EchoTranslator()
        result = t.from_english("hello", target_language="fr")
        assert "en→fr" in result

    def test_empty_text_returns_unchanged(self) -> None:
        t = _EchoTranslator()
        assert t.to_english("", source_language="fr") == ""
        assert t.from_english("  ", target_language="fr") == "  "

    def test_error_propagates(self) -> None:
        import pytest  # noqa: PLC0415

        class _BrokenTranslator(BaseTranslator):
            def _do_translate(self, text: str, source: str, target: str) -> str:
                raise RuntimeError("API down")

        t = _BrokenTranslator()
        with pytest.raises(RuntimeError, match="API down"):
            t.to_english("bonjour", source_language="fr")


class TestGoogleTranslator:
    def test_uses_deep_translator(self) -> None:
        from pbprompt.translate.google import GoogleTranslator  # noqa: PLC0415

        mock_instance = MagicMock()
        mock_instance.translate.return_value = "Hello"

        with patch(
            "pbprompt.translate.google.GoogleTranslator._do_translate",
            return_value="Hello",
        ):
            t = GoogleTranslator()
            result = t.to_english("Bonjour", source_language="fr")
            assert result == "Hello"


class TestGetTranslator:
    def test_returns_google_by_default(self) -> None:
        from pbprompt.config import AppConfig  # noqa: PLC0415
        from pbprompt.translate import get_translator  # noqa: PLC0415
        from pbprompt.translate.google import GoogleTranslator  # noqa: PLC0415

        cfg = AppConfig(translation_service="google")
        translator = get_translator(cfg)
        assert isinstance(translator, GoogleTranslator)

    def test_returns_mymemory(self) -> None:
        from pbprompt.config import AppConfig  # noqa: PLC0415
        from pbprompt.translate import get_translator  # noqa: PLC0415
        from pbprompt.translate.mymemory import MyMemoryTranslator  # noqa: PLC0415

        cfg = AppConfig(translation_service="mymemory")
        assert isinstance(get_translator(cfg), MyMemoryTranslator)

    def test_returns_reverso(self) -> None:
        from pbprompt.config import AppConfig  # noqa: PLC0415
        from pbprompt.translate import get_translator  # noqa: PLC0415
        from pbprompt.translate.reverso import ReversoTranslator  # noqa: PLC0415

        cfg = AppConfig(translation_service="reverso")
        assert isinstance(get_translator(cfg), ReversoTranslator)

    def test_unknown_service_falls_back_to_google(self) -> None:
        from pbprompt.config import AppConfig  # noqa: PLC0415
        from pbprompt.translate import get_translator  # noqa: PLC0415
        from pbprompt.translate.google import GoogleTranslator  # noqa: PLC0415

        cfg = AppConfig()
        cfg.translation_service = "nonexistent_service"  # bypass validation
        assert isinstance(get_translator(cfg), GoogleTranslator)
