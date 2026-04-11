"""DeepL translation back-end using the ``deep-translator`` library.

Requires a DeepL API key (free tier available at https://www.deepl.com/pro-api).
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class DeepLTranslator(BaseTranslator):
    """DeepL machine translation via ``deep-translator``.

    Parameters
    ----------
    api_key:
        DeepL authentication key.

    Example
    -------
        translator = DeepLTranslator(api_key="your-key-here")
        english = translator.to_english("Bonjour", source_language="fr")
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("DeepLTranslator requires a non-empty API key.")
        self._api_key = api_key

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import DeeplTranslator as _DT  # noqa: PLC0415, N814

        return str(
            _DT(api_key=self._api_key, source=source, target=target).translate(text)
        )
