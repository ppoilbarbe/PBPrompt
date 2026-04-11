"""QCRI (Qatar Computing Research Institute) translation back-end.

Provides MT between Arabic and several other languages.
Requires a free API key from https://mt.qcri.org/api/
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class QcriTranslator(BaseTranslator):
    """QCRI machine translation via ``deep-translator``.

    Parameters
    ----------
    api_key:
        QCRI API key.
    domain:
        Translation domain: ``"general"``, ``"news"``, or ``"discourse"``.
        Defaults to ``"general"``.

    Example
    -------
        translator = QcriTranslator(api_key="your-key")
        english = translator.to_english("مرحبا", source_language="ar")
    """

    def __init__(self, api_key: str, domain: str = "general") -> None:
        if not api_key:
            raise ValueError("QcriTranslator requires a non-empty API key.")
        self._api_key = api_key
        self._domain = domain

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import QcriTranslator as _QT  # noqa: PLC0415, N814

        return str(
            _QT(
                api_key=self._api_key,
                source=source,
                target=target,
                domain=self._domain,
            ).translate(text)
        )
