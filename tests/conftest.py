"""Shared pytest fixtures."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Force offscreen rendering before Qt is imported — required when DISPLAY is absent
# (CI headless, SSH without X forwarding, etc.).  Must come before any PySide6 import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from pbprompt.config import AppConfig
from pbprompt.data import PromptCollection, PromptEntry


@pytest.fixture(autouse=True)
def _isolated_config_dir(tmp_path: Path) -> Any:
    """Redirect AppConfig.config_path() to a temp dir for every test.

    Applies to *all* tests automatically, even ones that build AppConfig()
    directly instead of using the `default_config` fixture below — this is
    what prevents a test's AppConfig.save() from overwriting the developer's
    real ~/.config/pbprompt/config.yaml.
    """
    AppConfig.set_config_dir(tmp_path / "pbprompt-test-config")
    yield
    AppConfig.set_config_dir(None)


@pytest.fixture
def sample_entries() -> list[PromptEntry]:
    """Return a small list of PromptEntry objects for tests."""
    return [
        PromptEntry(
            ai="ChatGPT",
            group="Writing",
            name="Summary",
            local="Résume ce texte",
            english="Summarise this text",
        ),
        PromptEntry(
            ai="Claude",
            group="Code",
            name="Review",
            local="Relis ce code",
            english="Review this code",
        ),
        PromptEntry(
            ai="Gemini",
            group="Writing",
            name="Translate",
            local="Traduis ce texte",
            english="Translate this text",
        ),
    ]


@pytest.fixture
def sample_collection(sample_entries: list[PromptEntry]) -> PromptCollection:
    """Return a PromptCollection populated with sample entries."""
    col = PromptCollection(entries=list(sample_entries))
    return col


@pytest.fixture
def tmp_sqlite(sample_collection: PromptCollection, tmp_path: Path) -> Path:
    """Save sample_collection to a temp SQLite file and return the path."""
    path = tmp_path / "prompts.sqlite"
    sample_collection.save(path)
    return path


@pytest.fixture
def default_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    """Return a default AppConfig with config_path redirected to tmp_path."""

    def _config_path() -> Path:
        return tmp_path / "config.yaml"

    monkeypatch.setattr(AppConfig, "config_path", staticmethod(_config_path))
    return AppConfig()
