"""Unit tests for pbprompt.data module."""

from __future__ import annotations

from pathlib import Path

import pytest

from pbprompt.data import PromptCollection, PromptEntry


class TestPromptEntry:
    def test_to_dict_roundtrip(self) -> None:
        entry = PromptEntry(ai="A", group="G", name="N", local="L", english="E")
        d = entry.to_dict()
        assert d == {"ai": "A", "group": "G", "name": "N", "local": "L", "english": "E"}

    def test_from_dict_missing_keys(self) -> None:
        entry = PromptEntry.from_dict({"ai": "GPT"})
        assert entry.ai == "GPT"
        assert entry.group == ""
        assert entry.english == ""

    def test_from_dict_extra_keys_ignored(self) -> None:
        entry = PromptEntry.from_dict({"ai": "X", "unknown": "ignored"})
        assert entry.ai == "X"


class TestPromptCollection:
    def test_append_marks_modified(self) -> None:
        col = PromptCollection()
        assert not col.modified
        col.append()
        assert col.modified
        assert len(col.entries) == 1

    def test_remove_at(self) -> None:
        col = PromptCollection(
            entries=[PromptEntry(ai="A"), PromptEntry(ai="B"), PromptEntry(ai="C")]
        )
        col.modified = False
        removed = col.remove_at(1)
        assert removed.ai == "B"
        assert [e.ai for e in col.entries] == ["A", "C"]
        assert col.modified

    def test_remove_indices(self) -> None:
        col = PromptCollection(entries=[PromptEntry(ai=str(i)) for i in range(5)])
        col.remove_indices([1, 3])
        assert [e.ai for e in col.entries] == ["0", "2", "4"]

    def test_update_field(self) -> None:
        col = PromptCollection(entries=[PromptEntry(ai="old")])
        col.modified = False
        col.update_field(0, "ai", "new")
        assert col.entries[0].ai == "new"
        assert col.modified

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "test.yaml"
        col = PromptCollection(
            entries=[PromptEntry(ai="GPT", group="G", name="N", local="L", english="E")]
        )
        col.save(path)
        assert path.exists()

        loaded = PromptCollection.load(path)
        assert len(loaded.entries) == 1
        assert loaded.entries[0].ai == "GPT"
        assert loaded.entries[0].english == "E"
        assert not loaded.modified

    def test_load_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        col = PromptCollection.load(path)
        assert col.entries == []

    def test_save_no_path_raises(self) -> None:
        col = PromptCollection()
        with pytest.raises(ValueError):
            col.save()
