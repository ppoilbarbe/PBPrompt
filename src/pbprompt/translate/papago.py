"""Papago (Naver) translation back-end via ``deep-translator``.

Requires a Naver Cloud Platform account.
Free tier: 10 000 characters/day.
Sign up at https://www.ncloud.com/product/aiService/papagoTranslation
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class PapagoTranslator(BaseTranslator):
    """Papago (Naver) machine translation via ``deep-translator``.

    Parameters
    ----------
    client_id:
        Naver Cloud client ID.
    secret_key:
        Naver Cloud client secret.

    Example
    -------
        translator = PapagoTranslator(client_id="your-id", secret_key="your-secret")
        english = translator.to_english("Bonjour", source_language="fr")
    """

    def __init__(self, client_id: str, secret_key: str) -> None:
        if not client_id or not secret_key:
            raise ValueError("PapagoTranslator requires both client_id and secret_key.")
        self._client_id = client_id
        self._secret_key = secret_key

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import PapagoTranslator as _PT  # noqa: PLC0415, N814

        return str(
            _PT(
                client_id=self._client_id,
                secret_key=self._secret_key,
                source=source,
                target=target,
            ).translate(text)
        )
