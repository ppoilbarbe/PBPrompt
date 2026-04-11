"""Translation services for PBPrompt.

This package provides a uniform interface to multiple online translation
services.  Import the factory function to obtain a translator instance
based on the user's settings.

Example
-------
    from pbprompt.translate import get_translator
    from pbprompt.config import AppConfig

    cfg = AppConfig.load()
    translator = get_translator(cfg)
    english_text = translator.to_english("Bonjour", source_language="fr")
    french_text  = translator.from_english("Hello",  target_language="fr")
"""

from __future__ import annotations

import logging

from pbprompt.translate.base import BaseTranslator

logger = logging.getLogger(__name__)

# Public re-exports
__all__ = [
    "BaseTranslator",
    "get_translator",
]


def get_translator(config: pbprompt.config.AppConfig) -> BaseTranslator:  # noqa: F821
    """Instantiate the appropriate translator from *config*.

    Parameters
    ----------
    config:
        Application configuration providing ``translation_service`` and
        credential fields (``translation_api_key``, ``translation_app_id``,
        ``translation_app_secret``).

    Returns
    -------
    BaseTranslator
        Concrete translator instance ready to use.
    """
    service = config.translation_service
    key = config.translation_api_key
    app_id = config.translation_app_id
    app_secret = config.translation_app_secret

    logger.debug("Creating translator for service=%r", service)

    # ---- No-credential services ----------------------------------------
    if service == "google":
        from pbprompt.translate.google import GoogleTranslator  # noqa: PLC0415

        return GoogleTranslator()

    if service == "mymemory":
        from pbprompt.translate.mymemory import MyMemoryTranslator  # noqa: PLC0415

        return MyMemoryTranslator()

    if service == "pons":
        from pbprompt.translate.pons import PonsTranslator  # noqa: PLC0415

        return PonsTranslator()

    if service == "linguee":
        from pbprompt.translate.linguee import LingueeTranslator  # noqa: PLC0415

        return LingueeTranslator()

    if service == "reverso":
        from pbprompt.translate.reverso import ReversoTranslator  # noqa: PLC0415

        return ReversoTranslator()

    # ---- API-key services ----------------------------------------------
    if service == "deepl":
        from pbprompt.translate.deepl import DeepLTranslator  # noqa: PLC0415

        return DeepLTranslator(api_key=key)

    if service == "yandex":
        from pbprompt.translate.yandex import YandexTranslator  # noqa: PLC0415

        return YandexTranslator(api_key=key)

    if service == "microsoft":
        from pbprompt.translate.microsoft import MicrosoftTranslator  # noqa: PLC0415

        return MicrosoftTranslator(api_key=key)

    if service == "qcri":
        from pbprompt.translate.qcri import QcriTranslator  # noqa: PLC0415

        return QcriTranslator(api_key=key)

    if service == "libretranslate":
        from pbprompt.translate.libretranslate import (
            LibreTranslateTranslator,  # noqa: PLC0415
        )

        return LibreTranslateTranslator(api_key=key, url=config.libretranslate_url)

    # ---- App-ID + App-secret services ----------------------------------
    if service == "baidu":
        from pbprompt.translate.baidu import BaiduTranslator  # noqa: PLC0415

        return BaiduTranslator(appid=app_id, appkey=app_secret)

    if service == "papago":
        from pbprompt.translate.papago import PapagoTranslator  # noqa: PLC0415

        return PapagoTranslator(client_id=app_id, secret_key=app_secret)

    logger.warning("Unknown translation service %r; falling back to Google.", service)
    from pbprompt.translate.google import GoogleTranslator  # noqa: PLC0415

    return GoogleTranslator()
