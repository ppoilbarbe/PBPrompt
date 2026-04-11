#!/usr/bin/env python3
"""Extract release notes for a given version from CHANGELOG.md.

Usage
-----
    python scripts/extract_changelog.py v1.0.1
    python scripts/extract_changelog.py 1.0.1   # leading 'v' is optional
    python scripts/extract_changelog.py v1.0.1 > RELEASE_NOTES.md

GitHub Actions
--------------
When the ``GITHUB_OUTPUT`` environment variable is set the script appends
a multiline ``notes`` output variable so the calling step can reference it
as ``${{ steps.<id>.outputs.notes }}``.

Exit codes
----------
0  – success
1  – version not found in CHANGELOG.md or wrong usage
"""

from __future__ import annotations

import os
import re
import sys
import uuid
from pathlib import Path


def extract_notes(version: str) -> str:
    """Return the changelog body for *version* (leading 'v' stripped)."""
    version = version.lstrip("v")

    changelog = Path(__file__).parent.parent / "CHANGELOG.md"
    if not changelog.exists():
        print(f"error: CHANGELOG.md not found at {changelog}", file=sys.stderr)
        sys.exit(1)

    text = changelog.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Locate the header line: ## [X.Y.Z] …
    header_re = re.compile(rf"^##\s+\[{re.escape(version)}\]")
    start: int | None = None
    for i, line in enumerate(lines):
        if header_re.match(line):
            start = i + 1
            break

    if start is None:
        print(f"error: version '{version}' not found in CHANGELOG.md", file=sys.stderr)
        sys.exit(1)

    # Collect lines until the next ## section (or end of file).
    end = len(lines)
    for i in range(start, len(lines)):
        if re.match(r"^##\s+\[", lines[i]):
            end = i
            break

    return "\n".join(lines[start:end]).strip()


def main() -> None:
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <version>", file=sys.stderr)
        sys.exit(1)

    notes = extract_notes(sys.argv[1])

    # GitHub Actions: write multiline output variable.
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        delimiter = f"changelog_{uuid.uuid4().hex}"
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"notes<<{delimiter}\n")
            fh.write(notes)
            fh.write(f"\n{delimiter}\n")
    else:
        print(notes)


if __name__ == "__main__":
    main()
