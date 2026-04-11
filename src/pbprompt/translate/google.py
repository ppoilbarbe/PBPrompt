"""Google Translate back-end using the ``deep-translator`` library."""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class GoogleTranslator(BaseTranslator):
    """Free, unofficial Google Translate API via ``deep-translator``.

    No API key required.  Suitable for moderate volumes; for high-volume
    production use consider the official Google Cloud Translation API.

    Example
    -------
        translator = GoogleTranslator()
        english = translator.to_english("Bonjour", source_language="fr")
    """

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import GoogleTranslator as _GT  # noqa: PLC0415, N814

        return str(_GT(source=source, target=target).translate(text))
