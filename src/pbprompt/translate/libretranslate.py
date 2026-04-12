"""LibreTranslate back-end via ``deep-translator``.

LibreTranslate is a free, open-source machine translation API.
Self-host at https://github.com/LibreTranslate/LibreTranslate or use
a public instance at https://libretranslate.com (API key required).
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class LibreTranslateTranslator(BaseTranslator):
    """LibreTranslate machine translation.

    Args:
        api_key: API key for authenticated instances (empty string for open instances).
        url: Base URL of the LibreTranslate instance.

    Example:
        .. code-block:: python

            translator = LibreTranslateTranslator(
                api_key="",
                url="http://localhost:5000",
            )
            english = translator.to_english("Bonjour", source_language="fr")
    """

    def __init__(
        self,
        api_key: str = "",
        url: str = "https://libretranslate.com",
    ) -> None:
        self._api_key = api_key
        self._url = url.rstrip("/")

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import LibreTranslator as _LT  # noqa: PLC0415, N814

        kwargs: dict[str, str] = {
            "source": source,
            "target": target,
            "base_url": self._url + "/translate",
        }
        if self._api_key:
            kwargs["api_key"] = self._api_key
        return str(_LT(**kwargs).translate(text))
