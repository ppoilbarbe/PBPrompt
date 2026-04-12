"""Application configuration: load, validate, and persist settings."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from pbprompt.platform import get_config_dir

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

TRANSLATION_SERVICES = (
    "google",
    "mymemory",
    "deepl",
    "microsoft",
    "yandex",
    "libretranslate",
    "baidu",
    "papago",
    "qcri",
    "pons",
    "linguee",
    "reverso",
)

CONFIG_FILENAME = "config.yaml"


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class AppConfig:
    """All user-configurable settings for PBPrompt."""

    display_language: str = ""
    translation_language: str = ""
    translation_service: str = "google"
    translation_api_key: str = ""
    translation_app_id: str = ""
    translation_app_secret: str = ""
    libretranslate_url: str = "https://libretranslate.com"
    log_level: str = "INFO"
    recent_files: list[str] = field(default_factory=list)
    recent_files_max: int = 10
    thumbnail_width: int = 64
    thumbnail_height: int = 64
    window_x: int | None = None
    window_y: int | None = None
    window_width: int | None = None
    window_height: int | None = None
    last_import_dir: str = ""
    last_export_dir: str = ""
    last_image_dir: str = ""
    _extra: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def config_path(cls) -> Path:
        """Return the platform-appropriate path for the config file."""
        return get_config_dir() / CONFIG_FILENAME

    @classmethod
    def load(cls) -> AppConfig:
        """Load config from disk; unknown / invalid keys fall back to defaults."""
        path = cls.config_path()
        cfg = cls()
        if not path.exists():
            logger.info("No config file found at %s; using defaults.", path)
            return cfg

        yaml = YAML()
        try:
            raw: dict[str, Any] = yaml.load(path) or {}
        except Exception:
            logger.warning(
                "Failed to parse config file %s; using defaults.", path, exc_info=True
            )
            return cfg

        cfg.display_language = cls._str_or(
            raw, "display_language", cfg.display_language
        )
        cfg.translation_language = cls._str_or(
            raw, "translation_language", cfg.translation_language
        )
        cfg.translation_service = cls._choice_or(
            raw, "translation_service", TRANSLATION_SERVICES, cfg.translation_service
        )
        cfg.translation_api_key = cls._str_or(
            raw, "translation_api_key", cfg.translation_api_key
        )
        cfg.translation_app_id = cls._str_or(
            raw, "translation_app_id", cfg.translation_app_id
        )
        cfg.translation_app_secret = cls._str_or(
            raw, "translation_app_secret", cfg.translation_app_secret
        )
        cfg.libretranslate_url = cls._str_or(
            raw, "libretranslate_url", cfg.libretranslate_url
        )
        cfg.log_level = cls._choice_or(
            raw, "log_level", VALID_LOG_LEVELS, cfg.log_level
        )
        cfg.recent_files_max = cls._int_or(raw, "recent_files_max", 10, 1, 50)
        raw_recent = raw.get("recent_files", [])
        if isinstance(raw_recent, list):
            cfg.recent_files = [str(p) for p in raw_recent if isinstance(p, str)][
                : cfg.recent_files_max
            ]
        cfg.thumbnail_width = cls._int_or(raw, "thumbnail_width", 64, 16, 512)
        cfg.thumbnail_height = cls._int_or(raw, "thumbnail_height", 64, 16, 512)
        cfg.window_x = cls._opt_int(raw, "window_x")
        cfg.window_y = cls._opt_int(raw, "window_y")
        cfg.window_width = cls._opt_int(raw, "window_width", min_val=100)
        cfg.window_height = cls._opt_int(raw, "window_height", min_val=100)
        cfg.last_import_dir = cls._str_or(raw, "last_import_dir", "")
        cfg.last_export_dir = cls._str_or(raw, "last_export_dir", "")
        cfg.last_image_dir = cls._str_or(raw, "last_image_dir", "")

        known = {
            "display_language",
            "translation_language",
            "translation_service",
            "translation_api_key",
            "translation_app_id",
            "translation_app_secret",
            "libretranslate_url",
            "log_level",
            "recent_files",
            "recent_files_max",
            "thumbnail_width",
            "thumbnail_height",
            "window_x",
            "window_y",
            "window_width",
            "window_height",
            "last_import_dir",
            "last_export_dir",
            "last_image_dir",
        }
        cfg._extra = {k: v for k, v in raw.items() if k not in known}
        logger.debug("Config loaded from %s: %r", path, cfg)
        return cfg

    def save(self) -> None:
        """Persist the current configuration to disk."""
        path = self.config_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "display_language": self.display_language,
            "translation_language": self.translation_language,
            "translation_service": self.translation_service,
            "translation_api_key": self.translation_api_key,
            "translation_app_id": self.translation_app_id,
            "translation_app_secret": self.translation_app_secret,
            "libretranslate_url": self.libretranslate_url,
            "log_level": self.log_level,
            "recent_files_max": self.recent_files_max,
            "recent_files": self.recent_files,
            "thumbnail_width": self.thumbnail_width,
            "thumbnail_height": self.thumbnail_height,
        }
        for key in ("window_x", "window_y", "window_width", "window_height"):
            val = getattr(self, key)
            if val is not None:
                data[key] = val
        for key in ("last_import_dir", "last_export_dir", "last_image_dir"):
            val = getattr(self, key)
            if val:
                data[key] = val
        data.update(self._extra)

        yaml = YAML()
        yaml.version = (1, 2)  # type: ignore[assignment]
        yaml.default_flow_style = False
        with path.open("w", encoding="utf-8") as fh:
            yaml.dump(data, fh)
        logger.info("Config saved to %s", path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _str_or(d: dict[str, Any], key: str, default: str) -> str:
        val = d.get(key, default)
        return str(val) if isinstance(val, str) else default

    @staticmethod
    def _int_or(
        d: dict[str, Any], key: str, default: int, min_val: int, max_val: int
    ) -> int:
        val = d.get(key, default)
        if isinstance(val, int) and min_val <= val <= max_val:
            return val
        return default

    @staticmethod
    def _choice_or(
        d: dict[str, Any], key: str, choices: tuple[str, ...], default: str
    ) -> str:
        val = d.get(key, default)
        return str(val) if isinstance(val, str) and val in choices else default

    @staticmethod
    def _opt_int(d: dict[str, Any], key: str, min_val: int | None = None) -> int | None:
        val = d.get(key)
        if not isinstance(val, int):
            return None
        if min_val is not None and val < min_val:
            return None
        return val
