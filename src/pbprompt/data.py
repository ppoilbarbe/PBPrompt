"""Domain objects: SQLite persistence and YAML import/export for prompt entries."""

from __future__ import annotations

import base64
import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from pbprompt import __version__

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

#: Canonical text column order for YAML serialisation and display.
PROMPTS_COLUMNS: tuple[str, ...] = ("ai", "group", "name", "local", "english")

#: Binary (BLOB) columns — handled separately from text columns.
PROMPTS_BLOB_COLUMNS: tuple[str, ...] = ("image", "thumbnail")

_SQL_CREATE_PBPROMPT = """
CREATE TABLE IF NOT EXISTS pbprompt (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
)
"""

# "group" is a SQL keyword and must be quoted throughout.
_SQL_CREATE_PROMPTS = """
CREATE TABLE IF NOT EXISTS prompts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ai        TEXT NOT NULL DEFAULT '',
    "group"   TEXT NOT NULL DEFAULT '',
    name      TEXT NOT NULL DEFAULT '',
    image     BLOB,
    thumbnail BLOB,
    local     TEXT NOT NULL DEFAULT '',
    english   TEXT NOT NULL DEFAULT ''
)
"""

# Pre-built SELECT clause — text and BLOB columns in declaration order.
_SQL_SELECT_PROMPTS = (
    'SELECT ai, "group", name, image, thumbnail, local, english'
    " FROM prompts ORDER BY id"
)


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------


@dataclass
class PromptEntry:
    """A single AI-prompt record."""

    ai: str = ""
    group: str = ""
    name: str = ""
    image: bytes | None = None  # Full JPEG or PNG image
    thumbnail: bytes | None = None  # Pre-scaled thumbnail (PNG)
    local: str = ""
    english: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for YAML export.

        All text columns are always present, even when empty.
        The full *image* is base64-encoded when present.
        The thumbnail is never exported (always regenerated on import).
        """
        d: dict[str, Any] = {col: getattr(self, col) for col in PROMPTS_COLUMNS}
        if self.image:
            d["image"] = base64.b64encode(self.image).decode("ascii")
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PromptEntry:
        """Build a :class:`PromptEntry` from a raw dict (e.g. from YAML).

        Unknown keys are silently ignored.  Missing text keys default to ``""``.
        The ``image`` key, if present, is expected to be a base64-encoded string.
        """
        entry = cls(**{col: str(d.get(col, "")) for col in PROMPTS_COLUMNS})
        raw_img = d.get("image")
        if raw_img and isinstance(raw_img, str):
            try:
                entry.image = base64.b64decode(raw_img)
            except Exception:
                logger.warning("Failed to decode base64 image data from YAML entry.")
        return entry


# ---------------------------------------------------------------------------
# Private SQLite helpers
# ---------------------------------------------------------------------------


def _connect(path: Path) -> sqlite3.Connection:
    """Open (or create) a SQLite database with WAL mode and Row factory."""
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _has_pbprompt_table(conn: sqlite3.Connection) -> bool:
    """Return ``True`` if the ``pbprompt`` signature table exists."""
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pbprompt'"
    )
    return cur.fetchone() is not None


def _create_schema(conn: sqlite3.Connection) -> None:
    """Initialise both tables and stamp the current application version."""
    conn.execute(_SQL_CREATE_PBPROMPT)
    conn.execute(_SQL_CREATE_PROMPTS)
    conn.execute(
        "INSERT OR IGNORE INTO pbprompt (key, value) VALUES ('version', ?)",
        (__version__,),
    )
    conn.commit()


def _migrate_prompts_table(conn: sqlite3.Connection) -> list[str]:
    """Add any column missing from the ``prompts`` table.

    The ``prompts`` table is created from scratch if it does not yet exist.
    Returns the list of column names that were added (empty when up-to-date).
    """
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='prompts'"
    )
    if cur.fetchone() is None:
        conn.execute(_SQL_CREATE_PROMPTS)
        conn.commit()
        return []

    cur = conn.execute("PRAGMA table_info(prompts)")
    existing: set[str] = {row[1] for row in cur.fetchall()}

    added: list[str] = []

    # TEXT columns: NOT NULL DEFAULT ''
    for col in PROMPTS_COLUMNS:
        if col not in existing:
            conn.execute(
                f'ALTER TABLE prompts ADD COLUMN "{col}" TEXT NOT NULL DEFAULT ""'
            )
            added.append(col)

    # BLOB columns: nullable, no DEFAULT
    for col in PROMPTS_BLOB_COLUMNS:
        if col not in existing:
            conn.execute(f'ALTER TABLE prompts ADD COLUMN "{col}" BLOB')
            added.append(col)

    if added:
        conn.commit()
        logger.info("Schema migrated: added column(s) %s", added)
    return added


def _read_entries(conn: sqlite3.Connection) -> list[PromptEntry]:
    """Return all rows from ``prompts``, preserving insertion order."""
    cur = conn.execute(_SQL_SELECT_PROMPTS)
    entries: list[PromptEntry] = []
    for row in cur.fetchall():
        entries.append(
            PromptEntry(
                ai=str(row["ai"] or ""),
                group=str(row["group"] or ""),
                name=str(row["name"] or ""),
                image=row["image"],  # bytes | None (BLOB)
                thumbnail=row["thumbnail"],  # bytes | None (BLOB)
                local=str(row["local"] or ""),
                english=str(row["english"] or ""),
            )
        )
    return entries


def _write_entries(conn: sqlite3.Connection, entries: list[PromptEntry]) -> None:
    """Replace all ``prompts`` rows and update the version stamp."""
    conn.execute("DELETE FROM prompts")
    conn.executemany(
        'INSERT INTO prompts (ai, "group", name, image, thumbnail, local, english) '
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (e.ai, e.group, e.name, e.image, e.thumbnail, e.local, e.english)
            for e in entries
        ],
    )
    conn.execute(
        "INSERT OR REPLACE INTO pbprompt (key, value) VALUES ('version', ?)",
        (__version__,),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Collection (in-memory list + dirty flag + file path)
# ---------------------------------------------------------------------------


class PromptCollection:
    """Manages a list of :class:`PromptEntry` objects with SQLite persistence.

    The primary storage format is a SQLite ``.sqlite`` file.  YAML files are
    supported exclusively as an import/export interchange format.
    """

    def __init__(self) -> None:
        self.entries: list[PromptEntry] = []
        self.file_path: Path | None = None
        self.modified: bool = False

    # ------------------------------------------------------------------
    # SQLite persistence
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path) -> PromptCollection:
        """Open a PBPrompt SQLite database and return a populated collection.

        Schema migration is performed automatically when the ``pbprompt``
        signature table is present but the ``prompts`` table lacks columns.

        Raises:
            sqlite3.DatabaseError: *path* is not a valid SQLite file.
            ValueError: the file is a valid SQLite database but does **not**
                contain the ``pbprompt`` signature table, meaning it was not
                created by PBPrompt.
        """
        conn = _connect(path)
        try:
            if not _has_pbprompt_table(conn):
                raise ValueError(f"Not a PBPrompt database: {path}")
            migrated = _migrate_prompts_table(conn)
            if migrated:
                conn.execute(
                    "INSERT OR REPLACE INTO pbprompt (key, value) "
                    "VALUES ('version', ?)",
                    (__version__,),
                )
                conn.commit()
            entries = _read_entries(conn)
        finally:
            conn.close()

        logger.info("Loaded %d entries from %s", len(entries), path)
        col = cls()
        col.entries = entries
        col.file_path = path
        col.modified = False
        return col

    def save(self, path: Path | None = None) -> None:
        """Persist all entries to a SQLite database."""
        target = path or self.file_path
        if target is None:
            raise ValueError("No file path specified for saving.")

        target.parent.mkdir(parents=True, exist_ok=True)
        conn = _connect(target)
        try:
            _create_schema(conn)
            _write_entries(conn, self.entries)
        finally:
            conn.close()

        self.file_path = target
        self.modified = False
        logger.info("Saved %d entries to %s", len(self.entries), target)

    # ------------------------------------------------------------------
    # YAML import / export
    # ------------------------------------------------------------------

    def import_yaml(
        self,
        path: Path,
        replace: bool = False,
        thumbnail_factory: Callable[[bytes], bytes | None] | None = None,
    ) -> tuple[int, int]:
        """Import entries from a YAML file.

        Args:
            path: Path to a YAML file containing a list of dicts.
            replace: When ``True`` the current :attr:`entries` list is
                discarded before importing (full replacement, no dedup).
                When ``False`` imported entries are appended with
                deduplication against existing entries.
            thumbnail_factory: Optional callable that receives full image
                bytes and returns thumbnail bytes (or ``None`` on failure).
                Called for every imported entry that has an image.

        Returns:
            ``(imported_count, skipped_count)`` where *skipped_count* is the
            number of entries skipped due to deduplication (append mode only).
        """
        yaml = YAML()
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.load(fh) or []

        if not isinstance(raw, list):
            logger.warning("Expected a YAML list in %s; got %s", path, type(raw))
            raw = []

        # Build deduplication key set from current entries (append mode only).
        existing_keys: set[tuple[str, str, str, str, str]] = set()
        if not replace:
            existing_keys = {
                (e.ai, e.group, e.name, e.local, e.english) for e in self.entries
            }

        imported: list[PromptEntry] = []
        skipped = 0

        for item in raw:
            if not isinstance(item, dict):
                continue
            entry = PromptEntry.from_dict(item)
            key = (entry.ai, entry.group, entry.name, entry.local, entry.english)
            if not replace and key in existing_keys:
                skipped += 1
                continue
            if entry.image and thumbnail_factory is not None:
                entry.thumbnail = thumbnail_factory(entry.image)
            imported.append(entry)
            if not replace:
                # Prevent within-file duplicates in append mode too.
                existing_keys.add(key)

        if replace:
            self.entries = imported
        else:
            self.entries.extend(imported)

        if imported:
            self.modified = True

        logger.info(
            "Imported %d entries (%d skipped) from %s (replace=%s)",
            len(imported),
            skipped,
            path,
            replace,
        )
        return len(imported), skipped

    def export_yaml(self, path: Path) -> None:
        """Export all entries to a YAML file.

        Every text column in :data:`PROMPTS_COLUMNS` is always written.
        Images are base64-encoded when present.  Thumbnails are never exported.
        """
        data = [e.to_dict() for e in self.entries]
        yaml = YAML()
        yaml.version = (1, 2)  # type: ignore[assignment]
        yaml.default_flow_style = False
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            yaml.dump(data, fh)
        logger.info("Exported %d entries to %s", len(self.entries), path)

    # ------------------------------------------------------------------
    # Mutation helpers (called from the Qt model layer)
    # ------------------------------------------------------------------

    def append(self, entry: PromptEntry | None = None) -> PromptEntry:
        """Append *entry* (or a blank one) and mark the collection dirty."""
        if entry is None:
            entry = PromptEntry()
        self.entries.append(entry)
        self.modified = True
        return entry

    def remove_at(self, index: int) -> PromptEntry:
        """Remove and return the entry at *index*; mark dirty."""
        entry = self.entries.pop(index)
        self.modified = True
        return entry

    def remove_indices(self, indices: list[int]) -> None:
        """Remove multiple entries by index (order-independent); mark dirty."""
        for idx in sorted(set(indices), reverse=True):
            self.entries.pop(idx)
        self.modified = True

    def update_field(self, index: int, field_name: str, value: str) -> None:
        """Set *field_name* on the entry at *index*; mark dirty."""
        setattr(self.entries[index], field_name, value)
        self.modified = True
