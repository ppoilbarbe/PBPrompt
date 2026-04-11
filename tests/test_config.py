"""Unit tests for pbprompt.config module."""

from __future__ import annotations

from pathlib import Path

import pytest

from pbprompt.config import AppConfig


class TestAppConfig:
    def test_defaults(self) -> None:
        cfg = AppConfig()
        assert cfg.display_language == ""
        assert cfg.translation_language == ""
        assert cfg.translation_service == "google"
        assert cfg.log_level == "INFO"

    def test_save_creates_file(self, default_config: AppConfig, tmp_path: Path) -> None:
        default_config.save()
        path = default_config.config_path()
        assert path.exists()

    def test_save_and_reload(self, default_config: AppConfig) -> None:
        default_config.display_language = "fr"
        default_config.translation_service = "deepl"
        default_config.log_level = "DEBUG"
        default_config.save()

        loaded = AppConfig.load()
        assert loaded.display_language == "fr"
        assert loaded.translation_service == "deepl"
        assert loaded.log_level == "DEBUG"

    def test_invalid_service_falls_back(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("translation_service: notaservice\n", encoding="utf-8")
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg.translation_service == "google"  # default

    def test_invalid_log_level_falls_back(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("log_level: VERBOSE\n", encoding="utf-8")
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg.log_level == "INFO"

    def test_missing_file_returns_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "nonexistent.yaml"
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg.display_language == ""

    def test_corrupt_file_returns_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "bad.yaml"
        path.write_text("}{invalid yaml", encoding="utf-8")
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg.display_language == ""
