"""MyMemory translation back-end (free, no API key required).

Limits: 10 000 characters per day per IP without a key.
With a registered email key the daily limit is 50 000 characters.
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class MyMemoryTranslator(BaseTranslator):
    """MyMemory free translation service via ``deep-translator``.

    Parameters
    ----------
    email:
        Optional registered e-mail for higher daily limits.

    Example
    -------
        translator = MyMemoryTranslator()
        english = translator.to_english("Bonjour", source_language="fr")
    """

    def __init__(self, email: str = "") -> None:
        self._email = email

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import MyMemoryTranslator as _MMT  # noqa: PLC0415, N814

        kwargs: dict[str, str] = {"source": source, "target": target}
        if self._email:
            kwargs["email"] = self._email
        return str(_MMT(**kwargs).translate(text))
