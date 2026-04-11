"""PONS dictionary translator via ``deep-translator``.

PONS is a bilingual dictionary service — best suited for individual words
and short phrases rather than full sentences.  No API key required.
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class PonsTranslator(BaseTranslator):
    """PONS bilingual dictionary via ``deep-translator``.

    Note
    ----
    PONS uses full language names (e.g. ``"french"``) rather than language
    codes.  This translator converts ISO-639-1 codes automatically.

    Example
    -------
        translator = PonsTranslator()
        english = translator.to_english("Bonjour", source_language="fr")
    """

    # Mapping from ISO-639-1 code to the full name PONS expects
    _LANG_MAP: dict[str, str] = {
        "ar": "arabic",
        "bg": "bulgarian",
        "zh": "chinese",
        "cs": "czech",
        "da": "danish",
        "nl": "dutch",
        "en": "english",
        "fi": "finnish",
        "fr": "french",
        "de": "german",
        "el": "greek",
        "hu": "hungarian",
        "it": "italian",
        "no": "norwegian",
        "pl": "polish",
        "pt": "portuguese",
        "ro": "romanian",
        "ru": "russian",
        "sk": "slovak",
        "sl": "slovenian",
        "es": "spanish",
        "sv": "swedish",
        "tr": "turkish",
    }

    def _to_pons_lang(self, code: str) -> str:
        short = code.lower().split("-")[0]
        return self._LANG_MAP.get(short, short)

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import PonsTranslator as _PT  # noqa: PLC0415, N814

        return str(
            _PT(
                source=self._to_pons_lang(source),
                target=self._to_pons_lang(target),
            ).translate(word=text)
        )
