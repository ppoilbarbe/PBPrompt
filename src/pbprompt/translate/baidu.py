"""Baidu Translate back-end via ``deep-translator``.

Requires a Baidu developer account.
Free tier: 2 million characters/month.
Sign up at https://fanyi-api.baidu.com/
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class BaiduTranslator(BaseTranslator):
    """Baidu machine translation via ``deep-translator``.

    Parameters
    ----------
    appid:
        Baidu API application ID.
    appkey:
        Baidu API application key (secret).

    Example
    -------
        translator = BaiduTranslator(appid="your-appid", appkey="your-appkey")
        english = translator.to_english("Bonjour", source_language="fr")
    """

    def __init__(self, appid: str, appkey: str) -> None:
        if not appid or not appkey:
            raise ValueError("BaiduTranslator requires both appid and appkey.")
        self._appid = appid
        self._appkey = appkey

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import BaiduTranslator as _BT  # noqa: PLC0415, N814

        return str(
            _BT(
                appid=self._appid,
                appkey=self._appkey,
                source=source,
                target=target,
            ).translate(text)
        )
