"""Unit tests for pbprompt.config module."""

from __future__ import annotations

from pathlib import Path

import pytest

from pbprompt.config import CONFIG_FILENAME, AppConfig


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


class TestConfigPath:
    def test_config_path_ends_with_config_filename(self) -> None:
        """The real config_path() implementation returns a valid Path."""
        path = AppConfig.config_path()
        assert isinstance(path, Path)
        assert path.name == CONFIG_FILENAME


class TestSaveWindowGeometry:
    def test_save_and_reload_window_geometry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig(window_x=10, window_y=20, window_width=800, window_height=600)
        cfg.save()
        loaded = AppConfig.load()
        assert loaded.window_x == 10
        assert loaded.window_y == 20
        assert loaded.window_width == 800
        assert loaded.window_height == 600

    def test_save_none_window_geometry_omitted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        AppConfig().save()
        loaded = AppConfig.load()
        assert loaded.window_x is None
        assert loaded.window_width is None

    def test_save_preserves_extra_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig()
        cfg._extra = {"future_option": "value"}
        cfg.save()
        loaded = AppConfig.load()
        assert loaded._extra == {"future_option": "value"}


class TestLoadEdgeCases:
    def test_recent_files_loaded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        path.write_text(
            "recent_files:\n  - /a/b.sqlite\n  - /c/d.sqlite\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg.recent_files == ["/a/b.sqlite", "/c/d.sqlite"]

    def test_recent_files_truncated_to_max(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        files = "\n".join(f"  - /file{i}.sqlite" for i in range(20))
        path = tmp_path / "cfg.yaml"
        path.write_text(
            f"recent_files_max: 5\nrecent_files:\n{files}\n", encoding="utf-8"
        )
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert len(cfg.recent_files) == 5

    def test_load_extra_keys_stored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        path.write_text("unknown_key: some_value\n", encoding="utf-8")
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg._extra == {"unknown_key": "some_value"}

    def test_window_min_val_constraint(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """window_width/height below 100 are rejected → None."""
        path = tmp_path / "cfg.yaml"
        path.write_text("window_width: 50\nwindow_height: 50\n", encoding="utf-8")
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg.window_width is None
        assert cfg.window_height is None

    def test_window_valid_values_accepted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        path.write_text("window_width: 1024\nwindow_height: 768\n", encoding="utf-8")
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg.window_width == 1024
        assert cfg.window_height == 768


class TestLastDirs:
    def test_defaults_are_empty(self) -> None:
        cfg = AppConfig()
        assert cfg.last_import_dir == ""
        assert cfg.last_export_dir == ""
        assert cfg.last_image_dir == ""

    def test_save_and_reload_last_dirs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig()
        cfg.last_import_dir = "/home/user/imports"
        cfg.last_export_dir = "/home/user/exports"
        cfg.last_image_dir = "/home/user/images"
        cfg.save()
        loaded = AppConfig.load()
        assert loaded.last_import_dir == "/home/user/imports"
        assert loaded.last_export_dir == "/home/user/exports"
        assert loaded.last_image_dir == "/home/user/images"

    def test_empty_last_dirs_omitted_from_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        AppConfig().save()
        content = path.read_text(encoding="utf-8")
        assert "last_import_dir" not in content
        assert "last_export_dir" not in content
        assert "last_image_dir" not in content

    def test_invalid_last_dir_type_falls_back_to_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "cfg.yaml"
        path.write_text("last_import_dir: 42\n", encoding="utf-8")
        monkeypatch.setattr(AppConfig, "config_path", staticmethod(lambda: path))
        cfg = AppConfig.load()
        assert cfg.last_import_dir == ""


class TestHelpers:
    def test_str_or_returns_default_for_non_string(self) -> None:
        assert AppConfig._str_or({"k": 42}, "k", "default") == "default"

    def test_str_or_returns_value_for_string(self) -> None:
        assert AppConfig._str_or({"k": "hello"}, "k", "default") == "hello"

    def test_str_or_returns_default_for_missing_key(self) -> None:
        assert AppConfig._str_or({}, "k", "default") == "default"

    def test_int_or_out_of_range_returns_default(self) -> None:
        assert AppConfig._int_or({"k": 9999}, "k", 64, 16, 512) == 64

    def test_int_or_in_range_returns_value(self) -> None:
        assert AppConfig._int_or({"k": 128}, "k", 64, 16, 512) == 128

    def test_int_or_non_int_returns_default(self) -> None:
        assert AppConfig._int_or({"k": "big"}, "k", 64, 16, 512) == 64

    def test_opt_int_below_min_returns_none(self) -> None:
        assert AppConfig._opt_int({"k": 50}, "k", min_val=100) is None

    def test_opt_int_at_min_returns_value(self) -> None:
        assert AppConfig._opt_int({"k": 100}, "k", min_val=100) == 100

    def test_opt_int_above_min_returns_value(self) -> None:
        assert AppConfig._opt_int({"k": 150}, "k", min_val=100) == 150

    def test_opt_int_no_min_returns_value(self) -> None:
        assert AppConfig._opt_int({"k": 42}, "k") == 42

    def test_opt_int_non_int_returns_none(self) -> None:
        assert AppConfig._opt_int({"k": "nope"}, "k") is None

    def test_opt_int_missing_key_returns_none(self) -> None:
        assert AppConfig._opt_int({}, "k") is None
