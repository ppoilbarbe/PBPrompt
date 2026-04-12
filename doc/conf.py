"""Sphinx configuration for PBPrompt documentation."""

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
