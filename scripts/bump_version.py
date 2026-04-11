#!/usr/bin/env python3
"""Bump the semantic version of PBPrompt.

Usage:
    python scripts/bump_version.py {major|minor|patch}

Updates version strings in:
    - src/pbprompt/__init__.py  (__version__ = "...")
    - pyproject.toml             (version = "...")
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_INIT_PATH = ROOT / "src" / "pbprompt" / "__init__.py"
_TOML_PATH = ROOT / "pyproject.toml"


def _read_version() -> tuple[int, int, int]:
    text = _INIT_PATH.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text)
    if not m:
        raise ValueError(f"Could not find __version__ in {_INIT_PATH}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _bump(major: int, minor: int, patch: int, part: str) -> tuple[int, int, int]:
    if part == "major":
        return major + 1, 0, 0
    if part == "minor":
        return major, minor + 1, 0
    if part == "patch":
        return major, minor, patch + 1
    raise ValueError(f"Unknown part {part!r}; expected major, minor or patch.")


def _replace_version(path: Path, pattern: str, new_ver: str, flags: int = 0) -> None:
    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, rf'\g<prefix>"{new_ver}"', text, flags=flags)
    if count == 0:
        raise ValueError(f"Version pattern not found in {path}")
    path.write_text(new_text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("major", "minor", "patch"):
        print(f"Usage: {sys.argv[0]} {{major|minor|patch}}", file=sys.stderr)
        sys.exit(1)

    part = sys.argv[1]
    current = _read_version()
    new = _bump(*current, part)
    old_ver = ".".join(str(x) for x in current)
    new_ver = ".".join(str(x) for x in new)

    # __init__.py:  __version__ = "1.0.0"
    _replace_version(
        _INIT_PATH,
        r'(?P<prefix>__version__\s*=\s*)"[^"]+"',
        new_ver,
    )

    # pyproject.toml:  version = "1.0.0"  (in [project] section)
    _replace_version(
        _TOML_PATH,
        r'(?P<prefix>^version\s*=\s*)"[^"]+"',
        new_ver,
        flags=re.MULTILINE,
    )

    print(f"Version bumped ({part}): {old_ver} → {new_ver}")


if __name__ == "__main__":
    main()
