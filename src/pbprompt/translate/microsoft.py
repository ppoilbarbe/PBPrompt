"""Microsoft Translator (Bing) back-end via ``deep-translator``.

Requires a Microsoft Azure Cognitive Services API key.
Free tier: 2 million characters/month.
Sign up at https://azure.microsoft.com/en-us/services/cognitive-services/translator/
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class MicrosoftTranslator(BaseTranslator):
    """Microsoft Translator via ``deep-translator``.

    Parameters
    ----------
    api_key:
        Azure Cognitive Services subscription key.
    region:
        Optional Azure region (e.g. ``"westeurope"``).  Required if your
        resource was created in a specific region.

    Example
    -------
        translator = MicrosoftTranslator(api_key="your-key", region="westeurope")
        english = translator.to_english("Bonjour", source_language="fr")
    """

    def __init__(self, api_key: str, region: str = "") -> None:
        if not api_key:
            raise ValueError("MicrosoftTranslator requires a non-empty API key.")
        self._api_key = api_key
        self._region = region

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import MicrosoftTranslator as _MT  # noqa: PLC0415, N814

        kwargs: dict[str, str] = {
            "api_key": self._api_key,
            "source": source,
            "target": target,
        }
        if self._region:
            kwargs["region"] = self._region
        return str(_MT(**kwargs).translate(text))
