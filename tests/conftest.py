"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from pbprompt.config import AppConfig
from pbprompt.data import PromptCollection, PromptEntry


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
def tmp_yaml(sample_collection: PromptCollection, tmp_path: Path) -> Path:
    """Save sample_collection to a temp YAML file and return the path."""
    path = tmp_path / "prompts.yaml"
    sample_collection.save(path)
    return path


@pytest.fixture
def default_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    """Return a default AppConfig with config_path redirected to tmp_path."""

    def _config_path() -> Path:
        return tmp_path / "config.yaml"

    monkeypatch.setattr(AppConfig, "config_path", staticmethod(_config_path))
    return AppConfig()
