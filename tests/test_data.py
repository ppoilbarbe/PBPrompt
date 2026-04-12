"""Unit tests for pbprompt.data module."""

from __future__ import annotations

import base64
import sqlite3
from pathlib import Path

import pytest

from pbprompt.data import (
    _SQL_CREATE_PBPROMPT,
    PROMPTS_BLOB_COLUMNS,
    PROMPTS_COLUMNS,
    PromptCollection,
    PromptEntry,
    _connect,
    _migrate_prompts_table,
)


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


class TestPromptEntryImage:
    def test_to_dict_includes_base64_image(self) -> None:
        raw = b"fake PNG bytes"
        entry = PromptEntry(ai="X", image=raw)
        d = entry.to_dict()
        assert "image" in d
        assert base64.b64decode(d["image"]) == raw

    def test_to_dict_no_image_omits_key(self) -> None:
        entry = PromptEntry(ai="X")
        d = entry.to_dict()
        assert "image" not in d

    def test_from_dict_valid_base64_image(self) -> None:
        raw = b"fake PNG bytes"
        encoded = base64.b64encode(raw).decode("ascii")
        entry = PromptEntry.from_dict({"ai": "X", "image": encoded})
        assert entry.image == raw

    def test_from_dict_invalid_base64_image(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When base64.b64decode raises, image is silently set to None."""
        import pbprompt.data as data_mod

        def _raise(s: str) -> bytes:
            raise ValueError("bad base64")

        monkeypatch.setattr(data_mod.base64, "b64decode", _raise)
        entry = PromptEntry.from_dict({"ai": "X", "image": "Zm9v"})
        assert entry.image is None

    def test_from_dict_image_non_string_ignored(self) -> None:
        """Non-string image value is ignored (no decode attempt)."""
        entry = PromptEntry.from_dict({"ai": "X", "image": 42})
        assert entry.image is None


class TestPromptCollection:
    def test_append_marks_modified(self) -> None:
        col = PromptCollection()
        assert not col.modified
        col.append()
        assert col.modified
        assert len(col.entries) == 1

    def test_append_with_entry(self) -> None:
        col = PromptCollection()
        e = PromptEntry(ai="GPT")
        returned = col.append(e)
        assert returned is e
        assert col.entries[0].ai == "GPT"

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

    def test_remove_indices_marks_modified(self) -> None:
        col = PromptCollection(entries=[PromptEntry(ai="A"), PromptEntry(ai="B")])
        col.modified = False
        col.remove_indices([0])
        assert col.modified

    def test_update_field(self) -> None:
        col = PromptCollection(entries=[PromptEntry(ai="old")])
        col.modified = False
        col.update_field(0, "ai", "new")
        assert col.entries[0].ai == "new"
        assert col.modified

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "test.sqlite"
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

    def test_save_and_load_preserves_blobs(self, tmp_path: Path) -> None:
        raw_image = b"fake PNG bytes"
        raw_thumb = b"fake thumb bytes"
        entry = PromptEntry(ai="X", image=raw_image, thumbnail=raw_thumb)
        path = tmp_path / "blobs.sqlite"
        PromptCollection(entries=[entry]).save(path)
        loaded = PromptCollection.load(path)
        assert loaded.entries[0].image == raw_image
        assert loaded.entries[0].thumbnail == raw_thumb

    def test_load_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.sqlite"
        PromptCollection().save(path)
        col = PromptCollection.load(path)
        assert col.entries == []

    def test_save_no_path_raises(self) -> None:
        col = PromptCollection()
        with pytest.raises(ValueError):
            col.save()

    def test_save_updates_file_path(self, tmp_path: Path) -> None:
        path = tmp_path / "out.sqlite"
        col = PromptCollection()
        assert col.file_path is None
        col.save(path)
        assert col.file_path == path
        assert not col.modified

    def test_save_to_default_path(self, tmp_path: Path) -> None:
        path = tmp_path / "default.sqlite"
        col = PromptCollection()
        col.file_path = path
        col.save()  # no explicit path — uses self.file_path
        assert path.exists()


class TestSchemaHelpers:
    """Tests for internal SQLite schema helpers and migration paths."""

    def _make_pbprompt_only_db(self, path: Path) -> None:
        """Create a db with the pbprompt signature table but NO prompts table."""
        conn = sqlite3.connect(str(path))
        conn.execute(_SQL_CREATE_PBPROMPT)
        conn.execute(
            "INSERT OR IGNORE INTO pbprompt (key, value) VALUES ('version', '0.0.1')"
        )
        conn.commit()
        conn.close()

    def _make_stripped_prompts_db(self, path: Path) -> None:
        """Create a db with pbprompt + a prompts table missing most columns."""
        conn = sqlite3.connect(str(path))
        conn.execute(_SQL_CREATE_PBPROMPT)
        conn.execute(
            "INSERT OR IGNORE INTO pbprompt (key, value) VALUES ('version', '0.0.1')"
        )
        # Only 'id' and 'ai' — all other columns are missing
        conn.execute(
            "CREATE TABLE prompts "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, ai TEXT NOT NULL DEFAULT '')"
        )
        conn.commit()
        conn.close()

    def test_load_raises_for_non_pbprompt_db(self, tmp_path: Path) -> None:
        path = tmp_path / "plain.sqlite"
        conn = sqlite3.connect(str(path))
        conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        with pytest.raises(ValueError, match="Not a PBPrompt database"):
            PromptCollection.load(path)

    def test_migrate_creates_prompts_table_when_missing(self, tmp_path: Path) -> None:
        """_migrate_prompts_table creates the table when it doesn't exist."""
        path = tmp_path / "no_prompts.sqlite"
        self._make_pbprompt_only_db(path)
        conn = _connect(path)
        added = _migrate_prompts_table(conn)
        conn.close()
        # Table created from scratch — no ALTER TABLE calls, so added is empty
        assert added == []

    def test_migrate_adds_missing_columns(self, tmp_path: Path) -> None:
        """_migrate_prompts_table adds all columns absent from an old schema."""
        path = tmp_path / "stripped.sqlite"
        self._make_stripped_prompts_db(path)
        conn = _connect(path)
        added = _migrate_prompts_table(conn)
        conn.close()
        expected = set(PROMPTS_COLUMNS[1:]) | set(PROMPTS_BLOB_COLUMNS)
        assert set(added) == expected

    def test_load_triggers_migration_and_updates_version(self, tmp_path: Path) -> None:
        """load() runs migration and stamps the new version in pbprompt table."""
        from pbprompt import __version__

        path = tmp_path / "old_schema.sqlite"
        self._make_stripped_prompts_db(path)
        col = PromptCollection.load(path)
        assert col.entries == []

        conn = sqlite3.connect(str(path))
        cur = conn.execute("SELECT value FROM pbprompt WHERE key='version'")
        assert cur.fetchone()[0] == __version__
        conn.close()

    def test_migrate_no_op_when_schema_current(self, tmp_path: Path) -> None:
        """_migrate_prompts_table returns [] when all columns already exist."""
        path = tmp_path / "current.sqlite"
        PromptCollection().save(path)  # creates a fully up-to-date schema
        conn = _connect(path)
        added = _migrate_prompts_table(conn)
        conn.close()
        assert added == []


class TestImportYaml:
    """Tests for PromptCollection.import_yaml()."""

    def _yaml_path(self, tmp_path: Path, entries: list[PromptEntry]) -> Path:
        """Export entries to a temp YAML file and return its path."""
        path = tmp_path / "data.yaml"
        PromptCollection(entries=entries).export_yaml(path)
        return path

    def test_import_replace_discards_existing(self, tmp_path: Path) -> None:
        path = self._yaml_path(tmp_path, [PromptEntry(ai="New", name="N")])
        col = PromptCollection(entries=[PromptEntry(ai="Old")])
        imported, skipped = col.import_yaml(path, replace=True)
        assert imported == 1
        assert skipped == 0
        assert len(col.entries) == 1
        assert col.entries[0].ai == "New"
        assert col.modified

    def test_import_append_keeps_existing(self, tmp_path: Path) -> None:
        path = self._yaml_path(tmp_path, [PromptEntry(ai="B", name="2")])
        col = PromptCollection(entries=[PromptEntry(ai="A", name="1")])
        imported, skipped = col.import_yaml(path, replace=False)
        assert imported == 1
        assert skipped == 0
        assert len(col.entries) == 2

    def test_import_deduplication_skips_existing(self, tmp_path: Path) -> None:
        entry = PromptEntry(ai="X", group="G", name="N", local="L", english="E")
        path = self._yaml_path(tmp_path, [entry])
        col = PromptCollection(entries=[entry])
        imported, skipped = col.import_yaml(path, replace=False)
        assert imported == 0
        assert skipped == 1
        assert not col.modified  # nothing new → not modified

    def test_import_deduplication_within_file(self, tmp_path: Path) -> None:
        """Duplicate entries inside the same YAML file are only imported once."""
        entry = PromptEntry(ai="X", name="N")
        path = self._yaml_path(tmp_path, [entry, entry])
        col = PromptCollection()
        imported, skipped = col.import_yaml(path, replace=False)
        assert imported == 1
        assert skipped == 1

    def test_import_non_dict_items_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "mixed.yaml"
        path.write_text("- just a string\n- ai: X\n  name: Y\n", encoding="utf-8")
        col = PromptCollection()
        imported, _ = col.import_yaml(path, replace=False)
        assert imported == 1  # only the dict item is imported

    def test_import_non_list_yaml_treated_as_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "notlist.yaml"
        path.write_text("key: value\n", encoding="utf-8")
        col = PromptCollection()
        imported, _ = col.import_yaml(path, replace=False)
        assert imported == 0

    def test_import_with_thumbnail_factory(self, tmp_path: Path) -> None:
        raw_image = b"fake image bytes"
        path = self._yaml_path(tmp_path, [PromptEntry(ai="X", image=raw_image)])
        received: list[bytes] = []

        def factory(data: bytes) -> bytes:
            received.append(data)
            return b"thumbnail"

        col = PromptCollection()
        col.import_yaml(path, thumbnail_factory=factory)
        assert len(received) == 1
        assert col.entries[0].thumbnail == b"thumbnail"

    def test_import_no_entries_not_modified(self, tmp_path: Path) -> None:
        path = self._yaml_path(tmp_path, [])
        col = PromptCollection()
        col.import_yaml(path, replace=False)
        assert not col.modified

    def test_import_replace_with_empty_clears_entries(self, tmp_path: Path) -> None:
        path = self._yaml_path(tmp_path, [])
        col = PromptCollection(entries=[PromptEntry(ai="Old")])
        col.import_yaml(path, replace=True)
        assert col.entries == []

    def test_import_replace_does_not_deduplicate(self, tmp_path: Path) -> None:
        """In replace mode the deduplication key set is not built."""
        entry = PromptEntry(ai="X", name="N")
        # Two identical entries in the file — replace mode keeps both
        path = self._yaml_path(tmp_path, [entry, entry])
        col = PromptCollection()
        imported, skipped = col.import_yaml(path, replace=True)
        assert imported == 2
        assert skipped == 0


class TestExportYaml:
    """Tests for PromptCollection.export_yaml()."""

    def test_export_creates_file(self, tmp_path: Path) -> None:
        col = PromptCollection(entries=[PromptEntry(ai="X", name="N")])
        path = tmp_path / "out.yaml"
        col.export_yaml(path)
        assert path.exists()

    def test_export_creates_parent_directories(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "out.yaml"
        PromptCollection(entries=[PromptEntry(ai="X")]).export_yaml(nested)
        assert nested.exists()

    def test_export_roundtrip(self, tmp_path: Path) -> None:
        entries = [
            PromptEntry(ai="A", group="G1", name="N1", local="L1", english="E1"),
            PromptEntry(ai="B", group="G2", name="N2", local="L2", english="E2"),
        ]
        path = tmp_path / "out.yaml"
        PromptCollection(entries=entries).export_yaml(path)
        col = PromptCollection()
        col.import_yaml(path, replace=True)
        assert len(col.entries) == 2
        assert col.entries[0].ai == "A"
        assert col.entries[1].english == "E2"

    def test_export_with_image_roundtrip(self, tmp_path: Path) -> None:
        raw = b"fake PNG bytes"
        entry = PromptEntry(ai="X", image=raw)
        path = tmp_path / "out.yaml"
        PromptCollection(entries=[entry]).export_yaml(path)
        col = PromptCollection()
        col.import_yaml(path, replace=True)
        assert col.entries[0].image == raw

    def test_export_thumbnail_not_included(self, tmp_path: Path) -> None:
        entry = PromptEntry(ai="X", thumbnail=b"thumb bytes")
        path = tmp_path / "out.yaml"
        PromptCollection(entries=[entry]).export_yaml(path)
        assert "thumbnail" not in path.read_text(encoding="utf-8")

    def test_export_empty_collection(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.yaml"
        PromptCollection().export_yaml(path)
        assert path.exists()
        col = PromptCollection()
        col.import_yaml(path, replace=True)
        assert col.entries == []
