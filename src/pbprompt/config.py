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

# Valid keys for the column_filters config entry (matches PROMPTS_COLUMNS order,
# excluding the image column which is not filterable).
_FILTER_COLUMNS: frozenset[str] = frozenset({"ai", "group", "name", "local", "english"})


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
    image_viewer_zoom_max: int = 4
    image_viewer_zoom_step: int = 10
    image_store_keep_original: bool = True
    image_store_max_width: int = 1920
    image_store_max_height: int = 1080
    column_filters: dict[str, str] = field(default_factory=dict)
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
        cfg.image_viewer_zoom_max = cls._int_or(raw, "image_viewer_zoom_max", 4, 1, 16)
        cfg.image_viewer_zoom_step = cls._int_or(
            raw, "image_viewer_zoom_step", 10, 1, 50
        )
        cfg.image_store_keep_original = cls._bool_or(
            raw, "image_store_keep_original", True
        )
        cfg.image_store_max_width = cls._int_or(
            raw, "image_store_max_width", 1920, 64, 32000
        )
        cfg.image_store_max_height = cls._int_or(
            raw, "image_store_max_height", 1080, 64, 32000
        )
        cfg.window_x = cls._opt_int(raw, "window_x")
        cfg.window_y = cls._opt_int(raw, "window_y")
        cfg.window_width = cls._opt_int(raw, "window_width", min_val=100)
        cfg.window_height = cls._opt_int(raw, "window_height", min_val=100)
        cfg.last_import_dir = cls._str_or(raw, "last_import_dir", "")
        cfg.last_export_dir = cls._str_or(raw, "last_export_dir", "")
        cfg.last_image_dir = cls._str_or(raw, "last_image_dir", "")
        raw_filters = raw.get("column_filters", {})
        if isinstance(raw_filters, dict):
            cfg.column_filters = {
                k: str(v)
                for k, v in raw_filters.items()
                if isinstance(k, str) and k in _FILTER_COLUMNS and isinstance(v, str)
            }

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
            "image_viewer_zoom_max",
            "image_viewer_zoom_step",
            "image_store_keep_original",
            "image_store_max_width",
            "image_store_max_height",
            "window_x",
            "window_y",
            "window_width",
            "window_height",
            "last_import_dir",
            "last_export_dir",
            "last_image_dir",
            "column_filters",
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
            "image_viewer_zoom_max": self.image_viewer_zoom_max,
            "image_viewer_zoom_step": self.image_viewer_zoom_step,
            "image_store_keep_original": self.image_store_keep_original,
            "image_store_max_width": self.image_store_max_width,
            "image_store_max_height": self.image_store_max_height,
        }
        for key in ("window_x", "window_y", "window_width", "window_height"):
            val = getattr(self, key)
            if val is not None:
                data[key] = val
        for key in ("last_import_dir", "last_export_dir", "last_image_dir"):
            val = getattr(self, key)
            if val:
                data[key] = val
        active_filters = {k: v for k, v in self.column_filters.items() if v}
        if active_filters:
            data["column_filters"] = active_filters
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
    def _bool_or(d: dict[str, Any], key: str, default: bool) -> bool:
        val = d.get(key, default)
        return bool(val) if isinstance(val, bool) else default

    @staticmethod
    def _opt_int(d: dict[str, Any], key: str, min_val: int | None = None) -> int | None:
        val = d.get(key)
        if not isinstance(val, int):
            return None
        if min_val is not None and val < min_val:
            return None
        return val
