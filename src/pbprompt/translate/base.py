"""Abstract base class for translation services."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseTranslator(ABC):
    """Contract that every translation back-end must fulfil.

    Sub-classes implement ``_do_translate`` and the two public helpers
    are provided for free.

    Example
    -------
        class MyTranslator(BaseTranslator):
            def _do_translate(self, text, source, target):
                ...  # call your API

        t = MyTranslator()
        english = t.to_english("Bonjour", source_language="fr")
        french  = t.from_english("Hello",  target_language="fr")
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def to_english(self, text: str, source_language: str) -> str:
        """Translate *text* from *source_language* to English.

        Parameters
        ----------
        text:
            Source text to translate.
        source_language:
            IETF language tag of the source text (e.g. ``"fr"``).

        Returns
        -------
        str
            Translated text in English.

        Raises
        ------
        Exception
            Any exception raised by the underlying service is propagated
            so that callers can display a meaningful error to the user.
        """
        if not text.strip():
            return text
        result = self._do_translate(text, source=source_language, target="en")
        logger.debug("Translated %r → %r", text[:40], result[:40])
        return result

    def from_english(self, text: str, target_language: str) -> str:
        """Translate *text* from English to *target_language*.

        Parameters
        ----------
        text:
            English source text.
        target_language:
            IETF language tag of the target language (e.g. ``"fr"``).

        Returns
        -------
        str
            Translated text.

        Raises
        ------
        Exception
            Any exception raised by the underlying service is propagated
            so that callers can display a meaningful error to the user.
        """
        if not text.strip():
            return text
        result = self._do_translate(text, source="en", target=target_language)
        logger.debug("Translated %r → %r", text[:40], result[:40])
        return result

    # ------------------------------------------------------------------
    # Sub-class contract
    # ------------------------------------------------------------------

    @abstractmethod
    def _do_translate(self, text: str, source: str, target: str) -> str:
        """Perform the actual translation and return the translated string.

        Parameters
        ----------
        text:
            Text to translate.
        source:
            Source language code (e.g. ``"fr"``).
        target:
            Target language code (e.g. ``"en"``).
        """
