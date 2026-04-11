"""Yandex Translate back-end via ``deep-translator``.

Requires a Yandex API key from https://yandex.com/dev/translate/.
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class YandexTranslator(BaseTranslator):
    """Yandex machine translation.

    Parameters
    ----------
    api_key:
        Yandex Translate API key.

    Example
    -------
        translator = YandexTranslator(api_key="your-key-here")
        english = translator.to_english("Bonjour", source_language="fr")
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("YandexTranslator requires a non-empty API key.")
        self._api_key = api_key

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import YandexTranslator as _YT  # noqa: PLC0415, N814

        return str(
            _YT(api_key=self._api_key, source=source, target=target).translate(text)
        )
