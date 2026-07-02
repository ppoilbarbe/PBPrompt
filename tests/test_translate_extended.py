"""Extended tests for translation back-ends and the get_translator factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pbprompt.config import AppConfig

# ---------------------------------------------------------------------------
# get_translator factory — all service branches
# ---------------------------------------------------------------------------


class TestGetTranslatorAllServices:
    def _cfg(self, service: str, **kw: str) -> AppConfig:
        cfg = AppConfig(translation_service=service)
        for k, v in kw.items():
            setattr(cfg, k, v)
        return cfg

    def test_pons(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.pons import PonsTranslator

        assert isinstance(get_translator(self._cfg("pons")), PonsTranslator)

    def test_linguee(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.linguee import LingueeTranslator

        assert isinstance(get_translator(self._cfg("linguee")), LingueeTranslator)

    def test_deepl(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.deepl import DeepLTranslator

        t = get_translator(self._cfg("deepl", translation_api_key="key123"))
        assert isinstance(t, DeepLTranslator)

    def test_yandex(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.yandex import YandexTranslator

        t = get_translator(self._cfg("yandex", translation_api_key="key123"))
        assert isinstance(t, YandexTranslator)

    def test_microsoft(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.microsoft import MicrosoftTranslator

        t = get_translator(self._cfg("microsoft", translation_api_key="key123"))
        assert isinstance(t, MicrosoftTranslator)

    def test_qcri(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.qcri import QcriTranslator

        t = get_translator(self._cfg("qcri", translation_api_key="key123"))
        assert isinstance(t, QcriTranslator)

    def test_libretranslate(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.libretranslate import LibreTranslateTranslator

        cfg = self._cfg(
            "libretranslate",
            translation_api_key="key",
            libretranslate_url="http://localhost:5000",
        )
        assert isinstance(get_translator(cfg), LibreTranslateTranslator)

    def test_baidu(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.baidu import BaiduTranslator

        cfg = self._cfg("baidu", translation_app_id="id", translation_app_secret="sec")
        assert isinstance(get_translator(cfg), BaiduTranslator)

    def test_papago(self) -> None:
        from pbprompt.translate import get_translator
        from pbprompt.translate.papago import PapagoTranslator

        cfg = self._cfg("papago", translation_app_id="id", translation_app_secret="sec")
        assert isinstance(get_translator(cfg), PapagoTranslator)


# ---------------------------------------------------------------------------
# Translator constructors — validation
# ---------------------------------------------------------------------------


class TestTranslatorConstructors:
    def test_deepl_requires_key(self) -> None:
        from pbprompt.translate.deepl import DeepLTranslator

        with pytest.raises(ValueError, match="API key"):
            DeepLTranslator(api_key="")

    def test_deepl_accepts_key(self) -> None:
        from pbprompt.translate.deepl import DeepLTranslator

        t = DeepLTranslator(api_key="abc")
        assert t._api_key == "abc"

    def test_yandex_requires_key(self) -> None:
        from pbprompt.translate.yandex import YandexTranslator

        with pytest.raises(ValueError):
            YandexTranslator(api_key="")

    def test_microsoft_requires_key(self) -> None:
        from pbprompt.translate.microsoft import MicrosoftTranslator

        with pytest.raises(ValueError):
            MicrosoftTranslator(api_key="")

    def test_microsoft_accepts_region(self) -> None:
        from pbprompt.translate.microsoft import MicrosoftTranslator

        t = MicrosoftTranslator(api_key="k", region="westeurope")
        assert t._region == "westeurope"

    def test_qcri_requires_key(self) -> None:
        from pbprompt.translate.qcri import QcriTranslator

        with pytest.raises(ValueError):
            QcriTranslator(api_key="")

    def test_baidu_requires_both_credentials(self) -> None:
        from pbprompt.translate.baidu import BaiduTranslator

        with pytest.raises(ValueError):
            BaiduTranslator(appid="", appkey="sec")
        with pytest.raises(ValueError):
            BaiduTranslator(appid="id", appkey="")

    def test_papago_requires_both_credentials(self) -> None:
        from pbprompt.translate.papago import PapagoTranslator

        with pytest.raises(ValueError):
            PapagoTranslator(client_id="", secret_key="s")
        with pytest.raises(ValueError):
            PapagoTranslator(client_id="id", secret_key="")

    def test_mymemory_default_no_email(self) -> None:
        from pbprompt.translate.mymemory import MyMemoryTranslator

        t = MyMemoryTranslator()
        assert t._email == ""

    def test_mymemory_with_email(self) -> None:
        from pbprompt.translate.mymemory import MyMemoryTranslator

        t = MyMemoryTranslator(email="user@example.com")
        assert t._email == "user@example.com"

    def test_libretranslate_accepts_url(self) -> None:
        from pbprompt.translate.libretranslate import LibreTranslateTranslator

        t = LibreTranslateTranslator(api_key="k", url="http://host:5000")
        assert t is not None


# ---------------------------------------------------------------------------
# _do_translate — monkeypatched calls to deep_translator
# ---------------------------------------------------------------------------


class TestDoTranslate:
    def test_google_do_translate(self) -> None:
        from pbprompt.translate.google import GoogleTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.GoogleTranslator", mock_cls):
            t = GoogleTranslator()
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"
        mock_cls.assert_called_once_with(source="fr", target="en")

    def test_mymemory_do_translate_no_email(self) -> None:
        from pbprompt.translate.mymemory import MyMemoryTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.MyMemoryTranslator", mock_cls):
            t = MyMemoryTranslator()
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"
        call_kwargs = mock_cls.call_args[1]
        assert "email" not in call_kwargs

    def test_mymemory_do_translate_with_email(self) -> None:
        from pbprompt.translate.mymemory import MyMemoryTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hi"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.MyMemoryTranslator", mock_cls):
            t = MyMemoryTranslator(email="a@b.com")
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hi"
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("email") == "a@b.com"


# ---------------------------------------------------------------------------
# _do_translate for API-key and credential translators
# ---------------------------------------------------------------------------


class TestDoTranslateCredentialBackends:
    """Test _do_translate for translators that require credentials."""

    def _mock_dt(self, dt_class_name: str, return_value: str = "Hello"):
        """Patch deep_translator.<dt_class_name> and return (mock_cls, mock_inst)."""
        mock_inst = MagicMock()
        mock_inst.translate.return_value = return_value
        mock_cls = MagicMock(return_value=mock_inst)
        return patch(f"deep_translator.{dt_class_name}", mock_cls), mock_cls

    def test_deepl_do_translate(self) -> None:
        from pbprompt.translate.deepl import DeepLTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.DeeplTranslator", mock_cls):
            t = DeepLTranslator(api_key="key")
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"

    def test_yandex_do_translate(self) -> None:
        from pbprompt.translate.yandex import YandexTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.YandexTranslator", mock_cls):
            t = YandexTranslator(api_key="key")
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"

    def test_microsoft_do_translate_no_region(self) -> None:
        from pbprompt.translate.microsoft import MicrosoftTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.MicrosoftTranslator", mock_cls):
            t = MicrosoftTranslator(api_key="key")
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"
        call_kwargs = mock_cls.call_args[1]
        assert "region" not in call_kwargs

    def test_microsoft_do_translate_with_region(self) -> None:
        from pbprompt.translate.microsoft import MicrosoftTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.MicrosoftTranslator", mock_cls):
            t = MicrosoftTranslator(api_key="key", region="westeurope")
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"
        assert mock_cls.call_args[1].get("region") == "westeurope"

    def test_qcri_do_translate(self) -> None:
        from pbprompt.translate.qcri import QcriTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.QcriTranslator", mock_cls):
            t = QcriTranslator(api_key="key")
            result = t._do_translate("مرحبا", "ar", "en")

        assert result == "Hello"

    def test_libretranslate_do_translate_no_key(self) -> None:
        from pbprompt.translate.libretranslate import LibreTranslateTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.LibreTranslator", mock_cls):
            t = LibreTranslateTranslator()
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"
        call_kwargs = mock_cls.call_args[1]
        assert "api_key" not in call_kwargs

    def test_libretranslate_do_translate_with_key(self) -> None:
        from pbprompt.translate.libretranslate import LibreTranslateTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.LibreTranslator", mock_cls):
            t = LibreTranslateTranslator(api_key="k", url="http://host")
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"
        assert mock_cls.call_args[1].get("api_key") == "k"

    def test_baidu_do_translate(self) -> None:
        from pbprompt.translate.baidu import BaiduTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.BaiduTranslator", mock_cls):
            t = BaiduTranslator(appid="id", appkey="sec")
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"

    def test_papago_do_translate(self) -> None:
        from pbprompt.translate.papago import PapagoTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.PapagoTranslator", mock_cls):
            t = PapagoTranslator(client_id="id", secret_key="sec")
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"

    def test_pons_do_translate(self) -> None:
        from pbprompt.translate.pons import PonsTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.PonsTranslator", mock_cls):
            t = PonsTranslator()
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"
        # PONS receives full language names
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("source") == "french"
        assert call_kwargs.get("target") == "english"

    def test_linguee_do_translate(self) -> None:
        from pbprompt.translate.linguee import LingueeTranslator

        mock_inst = MagicMock()
        mock_inst.translate.return_value = "Hello"
        mock_cls = MagicMock(return_value=mock_inst)

        with patch("deep_translator.LingueeTranslator", mock_cls):
            t = LingueeTranslator()
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("source") == "french"
        assert call_kwargs.get("target") == "english"


# ---------------------------------------------------------------------------
# Reverso
# ---------------------------------------------------------------------------


class TestReversoTranslator:
    def test_to_reverso_code_known(self) -> None:
        from pbprompt.translate.reverso import _to_reverso_code

        assert _to_reverso_code("fr") == "fra"
        assert _to_reverso_code("en") == "eng"
        assert _to_reverso_code("de") == "ger"

    def test_to_reverso_code_unknown_passthrough(self) -> None:
        from pbprompt.translate.reverso import _to_reverso_code

        assert _to_reverso_code("xx") == "xx"

    def test_to_reverso_code_normalises_case(self) -> None:
        from pbprompt.translate.reverso import _to_reverso_code

        assert _to_reverso_code("FR") == "fra"
        assert _to_reverso_code("FR-BE") == "fra"

    def test_do_translate_success(self) -> None:
        from pbprompt.translate.reverso import ReversoTranslator

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"translation": ["Hello"]}
        mock_resp.raise_for_status.return_value = None

        with patch("pbprompt.translate.reverso.requests.post", return_value=mock_resp):
            t = ReversoTranslator()
            result = t._do_translate("Bonjour", "fr", "en")

        assert result == "Hello"

    def test_do_translate_empty_response_raises(self) -> None:
        from pbprompt.translate.reverso import ReversoTranslator

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"translation": []}
        mock_resp.raise_for_status.return_value = None

        with patch("pbprompt.translate.reverso.requests.post", return_value=mock_resp):
            t = ReversoTranslator()
            with pytest.raises(ValueError, match="Empty translation"):
                t._do_translate("Bonjour", "fr", "en")

    def test_do_translate_http_error_propagates(self) -> None:
        import requests  # noqa: PLC0415

        from pbprompt.translate.reverso import ReversoTranslator

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("403")

        with patch("pbprompt.translate.reverso.requests.post", return_value=mock_resp):
            t = ReversoTranslator()
            with pytest.raises(requests.HTTPError):
                t._do_translate("Bonjour", "fr", "en")
