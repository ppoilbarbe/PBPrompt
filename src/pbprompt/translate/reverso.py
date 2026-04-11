"""Reverso translation back-end via unofficial public API.

No API key required.  Uses the public ``api.reverso.net`` endpoint.
This is an unofficial integration; it may break if Reverso changes their API.
"""

from __future__ import annotations

import logging

import requests

from pbprompt.translate.base import BaseTranslator

logger = logging.getLogger(__name__)

_REVERSO_URL = "https://api.reverso.net/translate/v1/translation"
_TIMEOUT = 15  # seconds

# Reverso uses its own language codes (mostly ISO-639-1 but lowercase)
_LANG_MAP = {
    "en": "eng",
    "fr": "fra",
    "de": "ger",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "nl": "dut",
    "pl": "pol",
    "ru": "rus",
    "zh": "chi",
    "ja": "jpn",
    "ar": "ara",
}


def _to_reverso_code(lang: str) -> str:
    """Map an IETF tag to a Reverso language code (best-effort)."""
    short = lang.lower().split("-")[0]
    return _LANG_MAP.get(short, short)


class ReversoTranslator(BaseTranslator):
    """Translation via the Reverso public REST API.

    Example
    -------
        translator = ReversoTranslator()
        english = translator.to_english("Bonjour", source_language="fr")
    """

    def _do_translate(self, text: str, source: str, target: str) -> str:
        payload = {
            "input": text,
            "from": _to_reverso_code(source),
            "to": _to_reverso_code(target),
            "format": "text",
            "options": {
                "sentenceSplitter": False,
                "origin": "translation.web",
                "contextResults": False,
                "languageDetection": True,
            },
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        resp = requests.post(
            _REVERSO_URL, json=payload, headers=headers, timeout=_TIMEOUT
        )
        resp.raise_for_status()
        translations: list[str] = resp.json().get("translation", [])
        if not translations:
            raise ValueError("Empty translation response from Reverso.")
        return translations[0]
