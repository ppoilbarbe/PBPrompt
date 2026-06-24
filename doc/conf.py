"""Sphinx configuration for PBPrompt documentation."""

import re
import sys
from pathlib import Path

# Make the package importable for autodoc
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# -- Project information -------------------------------------------------------
project = "PBPrompt"
copyright = "2026, PBMou"
author = "PBMou"

# Read version from the package so it stays in sync with __init__.py
try:
    from pbprompt import __version__ as release
except ImportError:
    release = "1.0.1"

# -- General configuration -----------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output ---------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_depth": 3,
    "titles_only": False,
}

# -- Autodoc settings ----------------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Todo extension ------------------------------------------------------------
todo_include_todos = False

# ---------------------------------------------------------------------------
# Changelog — generated from CHANGELOG.md at build time
# ---------------------------------------------------------------------------

_H2 = re.compile(r"^## \[([^\]]+)\]\s+[–-]\s+(\d{4}-\d{2}-\d{2})\s*$")
_H3 = re.compile(r"^### (.+)$")
_LINK = re.compile(r"^\[[^\]]+\]:\s*https?://")

_UNDERLINES = {1: "=", 2: "-", 3: "^"}


def _md_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"``\1``", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"**\1**", text)
    return text


def _heading(out: list, title: str, level: int) -> None:
    char = _UNDERLINES[level]
    while out and out[-1] == "":
        out.pop()
    out.append("")
    out.append(title)
    out.append(char * len(title))


def _convert_changelog(md_path: Path) -> str:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    out: list = []
    in_intro = True

    for line in lines:
        if _LINK.match(line):
            continue

        m2 = _H2.match(line)
        if m2:
            in_intro = False
            _heading(out, f"{m2.group(1)} ({m2.group(2)})", 2)
            continue

        m3 = _H3.match(line)
        if m3:
            _heading(out, m3.group(1), 3)
            continue

        if in_intro:
            continue

        converted = _md_inline(line)
        if converted == "" and out and out[-1] == "":
            continue
        # RST nested lists require a blank line before the first sub-item.
        if re.match(r"^  +- ", converted) and out and out[-1] != "":
            out.append("")
        out.append(converted)

    header = ["Changelog", "=" * len("Changelog")]
    preamble = [
        "",
        "All notable changes to PBPrompt are documented here.",
        "The format is based on `Keep a Changelog"
        " <https://keepachangelog.com/en/1.1.0/>`_.",
    ]
    return "\n".join(header + preamble + out).rstrip() + "\n"


_DOCS_DIR = Path(__file__).parent
_CHANGELOG_MD = _DOCS_DIR.parent / "CHANGELOG.md"
_CHANGELOG_RST = _DOCS_DIR / "changelog.rst"

_CHANGELOG_RST.write_text(_convert_changelog(_CHANGELOG_MD), encoding="utf-8")
