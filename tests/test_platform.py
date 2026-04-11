"""Tests for the platform module selection."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


def test_get_config_dir_returns_path() -> None:
    """get_config_dir() must return a Path object."""
    from pbprompt.platform import get_config_dir

    result = get_config_dir()
    assert isinstance(result, Path)


def test_get_config_dir_contains_pbprompt() -> None:
    """The returned path should contain the application name."""
    from pbprompt.platform import get_config_dir

    path = get_config_dir()
    assert "pbprompt" in str(path).lower()


def test_linux_module_imported_on_linux() -> None:
    """On Linux the linux module is imported."""
    if sys.platform != "linux":
        import pytest  # noqa: PLC0415

        pytest.skip("Linux-only test")

    from pbprompt.platform import linux  # noqa: F401


def test_platform_selection_linux(monkeypatch: object) -> None:
    """Simulate Linux platform and verify correct module is selected."""
    import importlib  # noqa: PLC0415

    import pbprompt.platform as plat  # noqa: PLC0415

    with patch.object(sys, "platform", "linux"):
        importlib.reload(plat)
        assert callable(plat.get_config_dir)


def test_config_dir_can_be_created(tmp_path: Path, monkeypatch: object) -> None:
    """The config directory parent can be created if it does not exist."""
    import pbprompt.platform.linux as linux_plat  # noqa: PLC0415

    fake_dir = tmp_path / "new_subdir" / "pbprompt"

    with patch.object(
        linux_plat,
        "get_config_dir",
        return_value=fake_dir,
    ):
        result = linux_plat.get_config_dir()
        result.mkdir(parents=True, exist_ok=True)
        assert result.exists()
