"""Linguee dictionary translator via ``deep-translator``.

Linguee is a bilingual corpus-based dictionary — best suited for words
and short phrases rather than full paragraphs.  No API key required.
"""

from __future__ import annotations

from pbprompt.translate.base import BaseTranslator


class LingueeTranslator(BaseTranslator):
    """Linguee bilingual dictionary via ``deep-translator``.

    Note
    ----
    Linguee uses full language names (e.g. ``"french"``).  ISO-639-1 codes
    are converted automatically.

    Example
    -------
        translator = LingueeTranslator()
        english = translator.to_english("Bonjour", source_language="fr")
    """

    _LANG_MAP: dict[str, str] = {
        "bg": "bulgarian",
        "zh": "chinese",
        "cs": "czech",
        "da": "danish",
        "nl": "dutch",
        "en": "english",
        "et": "estonian",
        "fi": "finnish",
        "fr": "french",
        "de": "german",
        "el": "greek",
        "hu": "hungarian",
        "it": "italian",
        "ja": "japanese",
        "lv": "latvian",
        "lt": "lithuanian",
        "mt": "maltese",
        "pl": "polish",
        "pt": "portuguese",
        "ro": "romanian",
        "ru": "russian",
        "sk": "slovak",
        "sl": "slovenian",
        "es": "spanish",
        "sv": "swedish",
    }

    def _to_linguee_lang(self, code: str) -> str:
        short = code.lower().split("-")[0]
        return self._LANG_MAP.get(short, short)

    def _do_translate(self, text: str, source: str, target: str) -> str:
        from deep_translator import LingueeTranslator as _LT  # noqa: PLC0415, N814

        return str(
            _LT(
                source=self._to_linguee_lang(source),
                target=self._to_linguee_lang(target),
            ).translate(word=text)
        )
