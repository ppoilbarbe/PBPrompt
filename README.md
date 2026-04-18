# PBPrompt

**A program to register and categorize AI prompts to keep tries.**

> **This project was written 100% by [Claude](https://claude.ai), Anthropic's AI assistant,**
> **from a single detailed prompt.**
> Every line of code, every configuration file, every icon, and this README were
> generated and maintained through conversations with Claude — without any human
> writing code directly.
>
> The goal is to **evaluate Claude's capabilities**: its ability to produce clean,
> well-structured, and documented code from a specification, and its ability to
> diagnose and fix bugs when given only a symptom (an error message, unexpected
> behaviour, or a failed build) rather than a root cause.
>
> Learn more at [claude.ai](https://claude.ai) or [anthropic.com](https://www.anthropic.com).

PBPrompt is a cross-platform PyQt5 desktop application for storing, searching,
and translating AI prompts.  Prompts are stored in a **SQLite database** (`.sqlite`)
and can be translated via Google Translate, DeepL, MyMemory, Yandex, LibreTranslate,
or Reverso.  YAML import/export is available for interoperability.

---

## Features

- Five-column prompt table: **AI**, **Group**, **Name**, **Local language**, **English**
- Per-column regex filters (cumulative AND logic)
- Multi-key sort on AI / Group / Name columns
- Multi-line editing of *Local* and *English* cells (QPlainTextEdit in-place editor):
  Enter **validates** the edit (same as Tab); Ctrl+Enter or Shift+Enter inserts a real
  newline; Tab / Shift+Tab commit and move to the next/previous cell;
  Escape cancels; clicking outside commits
- Automatic row height based on cell content (word-wrap aware)
- Real newlines displayed as ↵ (U+21B5) followed by a line break
- **Duplicate row** (toolbar button or Ctrl+D): copies the current row and inserts it immediately below
- **Current-cell highlight**: within a selected row, the active cell is visually distinct (coloured border)
- Right-click context menu: **Copy / Cut / Paste** (also Ctrl+C / Ctrl+X / Ctrl+V)
- One-click online translation of selected rows (→ English F6 / ← Local F7)
- Recent files sub-menu with auto-load of the last file on startup
- Optional startup file on the command line (overrides auto-load)
- **SQLite** primary storage format — `.sqlite` extension added automatically if omitted
- **YAML import/export**: add entries from YAML or replace all; export all entries to YAML
- Fully internationalised UI (7 languages included; easily extendable)
- Platform-appropriate configuration directory
- SVG icon set (scalable, theme-aware); falls back to desktop icon theme then Qt built-ins
- All action tooltips shown in the status bar with keyboard shortcuts

---

## Installation

### With conda (recommended)

Most dependencies are available on **conda-forge**; only `deep-translator`
requires pip.

```bash
# Clone
git clone <repo-url> PBPrompt && cd PBPrompt

# Create and activate the environment
conda create -n pbprompt python=3.11
conda activate pbprompt

# Install all conda-available dependencies
conda install -c conda-forge \
    pyqt "ruamel.yaml" platformdirs requests \
    pytest pytest-qt ruff pre-commit mypy \
    sphinx sphinx-rtd-theme

# Install the one package not on conda-forge
pip install deep-translator

# Install PBPrompt itself (editable)
pip install -e . --no-deps

# Compile translations
make translations          # or: ./scripts/compile_translations.sh

# Generate UI Python (requires pyuic5 / pyrcc5)
make ui resources          # or: ./scripts/build_qm.sh
```

> **Note for conda users**: `pyuic5` and `pyrcc5` are provided by the
> `pyqt` conda package.  Pre-generated `ui_*.py` files are also included
> in the repository so you can skip `make ui resources` if you haven't
> modified any `.ui` file.

### With venv / pip

```bash
# Clone
git clone <repo-url> PBPrompt && cd PBPrompt

# Create a virtual environment
python -m venv .venv && source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate                           # Windows

# Install with dev extras
pip install -e ".[dev]"

# Compile translations
make translations          # or: ./scripts/compile_translations.sh

# Generate UI Python (requires pyuic5 / pyrcc5)
make ui resources          # or: ./scripts/build_qm.sh
```

### Quick start (without compiling UI)

The repository ships pre-generated `ui_*.py` files so you can run the
application without `pyuic5` installed:

```bash
pip install -e .
make translations
pbprompt
```

---

## Running

```bash
pbprompt                        # open last-used file automatically
pbprompt path/to/prompts.sqlite # open a specific file at startup
python -m pbprompt              # same, without installing
make run                        # run from source tree (no install needed)
```

### Command-line options

```
usage: pbprompt [-h] [--version] [--log-level LEVEL] [FILE]
```

| Option | Description |
|---|---|
| `FILE` | SQLite file to open at startup. **Takes priority over the last-used file** (auto-load is skipped). If the file cannot be read, an error dialog shows the reason and an empty list is loaded. |
| `--version` | Print version number and exit. |
| `--log-level LEVEL` | Override the log level from the config file. Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `--help` / `-h` | Show full help and exit. |

---

## Keyboard shortcuts

| Action | Shortcut |
|---|---|
| New file | Ctrl+N |
| Open… | Ctrl+O |
| Save | Ctrl+S |
| Save As… | Ctrl+Shift+S |
| Import YAML — Add entries | Ctrl+I |
| Import YAML — Replace all | Ctrl+Shift+I |
| Export YAML… | Ctrl+E |
| Close | Ctrl+W |
| Quit | Ctrl+Q |
| Options… | Ctrl+, |
| New Prompt | Ins |
| Duplicate row | Ctrl+D |
| Delete selected | Del |
| → English (translate) | F6 |
| ← Local (translate) | F7 |
| Copy cell | Ctrl+C |
| Cut cell | Ctrl+X |
| Paste into cell | Ctrl+V |

---

## YAML import / export

PBPrompt stores data in **SQLite** (`.sqlite`) but can exchange data with YAML files.

### Import YAML

**File › Import YAML › Add entries…** (Ctrl+I)
: Appends all entries from the chosen YAML file to the current collection.

**File › Import YAML › Replace all…** (Ctrl+Shift+I)
: Clears the collection and replaces it with the contents of the chosen YAML file.

Unknown YAML keys are silently ignored; missing keys default to `""`.

### Export YAML

**File › Export YAML…** (Ctrl+E)
: Exports all entries to a YAML file.  All five columns are always written.
  The `.yaml` extension is appended automatically if omitted.

---

## Testing

```bash
pytest                     # run all tests
pytest -v tests/test_data.py   # single module
```

On headless systems (CI) set `QT_QPA_PLATFORM=offscreen`.

---

## Adding a language

1. Copy `locales/en/LC_MESSAGES/messages.po` to
   `locales/<lang>/LC_MESSAGES/messages.po`.
2. Translate every `msgstr` entry.
3. Compile: `make translations`.
4. Restart PBPrompt and select the new language in **Tools › Options…**.

---

## Version management

PBPrompt follows [Semantic Versioning](https://semver.org/).
The version string is kept in sync across `src/pbprompt/__init__.py` and
`pyproject.toml` by a single script.

```bash
make version        # display current version
make bump-patch     # 1.0.0 → 1.0.1  (bug fixes)
make bump-minor     # 1.0.1 → 1.1.0  (new features, resets patch)
make bump-major     # 1.1.0 → 2.0.0  (breaking changes, resets minor + patch)
```

The underlying script can also be called directly:

```bash
python scripts/bump_version.py {major|minor|patch}
```

It updates both files atomically and prints a confirmation line such as:

```
Version bumped (minor): 1.0.1 → 1.1.0
```

---

## Build standalone executables

### Linux

```bash
./scripts/build_linux.sh
# Output: dist/pbprompt
```

### Windows

```bat
scripts\build_windows.bat
REM Output: dist\pbprompt.exe
```

### macOS

```bash
./scripts/build_macos.sh
# Output: dist/pbprompt.app
```

> **Note**: All builds require `pip install pyinstaller` first.
> PyInstaller bundles the Python interpreter and all dependencies.
> macOS binaries should be code-signed for distribution.

---

## Project structure

```
PBPrompt/
├── src/pbprompt/          # Main package
│   ├── __main__.py        # Entry point
│   ├── config.py          # Settings management
│   ├── data.py            # Domain model + SQLite I/O + YAML import/export
│   ├── i18n.py            # Gettext helpers
│   ├── gui/               # PyQt5 UI
│   │   ├── *.ui           # Qt Designer sources
│   │   ├── ui_*.py        # Compiled UI (pyuic5) — excluded from ruff
│   │   ├── resources_rc.py# Compiled resources (pyrcc5) — excluded from ruff
│   │   ├── models.py      # Qt item models + delegate + table view
│   │   ├── main_window.py
│   │   ├── settings_dialog.py
│   │   └── about_dialog.py
│   ├── platform/          # OS-specific code
│   │   ├── linux.py
│   │   ├── windows.py
│   │   └── macos.py
│   └── translate/         # Translation back-ends
│       ├── base.py
│       ├── google.py
│       ├── deepl.py
│       ├── mymemory.py
│       ├── yandex.py
│       ├── reverso.py
│       └── libretranslate.py
├── locales/               # gettext .po / .mo files
├── resources/             # Icons + .qrc
├── tests/                 # pytest suite
├── doc/                   # Sphinx documentation
├── scripts/               # Build helpers
├── claude_original_prompt.txt  # The original prompt sent to Claude on day one — never modified
├── claude_prompt.txt           # Living specification: updated by Claude after each session
├── Makefile
└── pyproject.toml
```

---

## Extending the platform module

Each `pbprompt/platform/*.py` module exposes one function used by the app:

| Function | Purpose |
|---|---|
| `get_config_dir()` | Returns `Path` to the config directory |

To add a new platform, create `pbprompt/platform/myos.py` implementing
`get_config_dir()`, then update `pbprompt/platform/__init__.py`.

---

## Read the Docs — version retention policy

After each release the CI runs `scripts/rtd_cleanup.py` to deactivate outdated
versions in the Read the Docs dropdown.  The retention rules are (given the
current latest tag **X.Y.Z**):

| Scope | Rule |
|---|---|
| **Older major versions** (< X) | Keep the single latest release of each of the 3 most recent major versions |
| **Current major X, older minor versions** (< Y) | Keep the single latest patch of each of the 3 most recent minor versions |
| **Current major X, current minor Y, older patches** (< Z) | Keep the 3 most recent patches |

`latest` and `stable` are never touched.

To run the cleanup manually:

```bash
python scripts/rtd_cleanup.py --token YOUR_RTD_TOKEN [--dry-run]
```

The script requires a `READTHEDOCS_TOKEN` secret configured in the repository
(GitHub Settings → Secrets → Actions).

---

## Known limitations

- **Google Translate** uses an unofficial endpoint – may break without notice.
- **Reverso** uses an undocumented public REST endpoint.
- **DeepL** and **Yandex** require API keys configured in Options.
- `.mo` compiled translation files must be generated with `make translations`.
- `ui_*.py` and `resources_rc.py` should be regenerated with `make all`
  when `.ui` files or icons change.
- `deep-translator` is not available on conda-forge; install it with pip.
- When installing with pip in a conda environment, use
  `pip install -e . --no-deps` (not `pip install -e .`) to avoid
  reinstalling packages already managed by conda.

---

## License

MIT © 2026 PBMou

---

## About Claude

This project was written entirely by [Claude](https://claude.ai), Anthropic's AI
assistant, from a single detailed prompt — through an iterative, conversation-driven
development process.

No human wrote a single line of code.  The objective is to evaluate Claude on two
specific dimensions:

- **Code quality**: can Claude produce clean, well-structured, tested, and documented
  Python code from a written specification alone?
- **Symptom-driven debugging**: when a problem occurs, can Claude identify the root
  cause and apply the correct fix when given only the observable symptom — an error
  message, unexpected behaviour, or a failed CI step — without being told what is wrong?

Two prompt files are kept in the repository:

- [`claude_original_prompt.txt`](claude_original_prompt.txt) — the exact prompt
  sent to Claude on day one to generate the initial project.  This file is never
  modified by Claude; it is a read-only historical record.
- [`claude_prompt.txt`](claude_prompt.txt) — the living specification, updated by
  Claude after each session to reflect new features, constraints, and decisions.

- **Claude**: [claude.ai](https://claude.ai)
- **Anthropic**: [anthropic.com](https://www.anthropic.com)
- **Claude Code** (the CLI used): [claude.ai/code](https://claude.ai/code)
