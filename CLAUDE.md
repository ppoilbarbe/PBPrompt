# CLAUDE.md — PBPrompt

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mode

**Active mode: `full-en`**

| Layer | Language |
|---|---|
| Code (identifiers, comments, docstrings, debug messages) | English |
| Docs & prose (README, CHANGELOG, commit messages, reference files) | English |
| User-facing strings (UI labels, CLI messages, error messages) | English |

## Current state

- **Version**: 1.8.1
- **Storage**: SQLite (`.sqlite`, WAL). YAML = import/export only.
- **Columns**: `Column(IntEnum)` AI=0, GROUP=1, NAME=2, IMAGE=3, LOCAL=4, ENGLISH=5
- **Compiled locales**: en, de, fr, es, it, ru, vi, zh_CN

## Key commands

```
make all              # compile translations (.po → .mo)
make run              # run the application (PYTHONPATH=src)
make clean all        # full rebuild from sources
make test             # pytest (pytest-xvfb handles virtual display on Linux)
make test-cov         # pytest --cov --cov-report=html
make lint             # ruff check
make format           # ruff format + check --fix
make docs             # Sphinx (after make clean all)
make dist             # standalone PyInstaller executable (dist/pbprompt)
make srcdist          # archives dist/pbprompt-x.y.z.tar.gz and .zip
make translations     # compile .po → .mo
make bump-patch/minor/major  # bump semver version
```

## Mandatory rules — code

**UI definition files — `*_ui.py`:**
- `src/pbprompt/gui/main_window_ui.py`, `about_dialog_ui.py`, `settings_dialog_ui.py`
  are **source-controlled files** — edit them directly.
- There are no `.ui` (Qt Designer) files anymore, and no code generation step.
  The `make ui` and `make resources` targets no longer exist.
- All `QAction` instances are defined in the `*_ui.py` files, never in
  `main_window.py` or other behaviour files.

**Icons — `src/pbprompt/icons/`:**
- SVG files are loaded directly from the package via `get_icon_dir()` in
  `icons.py` (handles both normal execution and PyInstaller bundles).
- No more `resources_rc.py` or `resources.qrc`. To add an icon: drop a SVG in
  `src/pbprompt/icons/` and call `get_icon("name")`.
- `get_icon()` lookup order: FreeDesktop theme → file (`name`, `name_color`,
  `name_light`, `name_dark`) → Qt standard icon.
- PyInstaller: the directory is declared in `pbprompt.spec` under `pbprompt/icons/`.

**SQL — `"group"` is a reserved keyword:**
Always quote it in every SQL query: `"group"`.

**MRO bug — keyboard shortcuts:**
`MainWindow` inherits from both `QMainWindow` and `Ui_MainWindow`. Python MRO causes
`MainWindow.retranslate_ui()` to shadow `Ui_MainWindow.retranslate_ui()` → all
`setShortcut()` calls in the `*_ui.py` files are dead code.
→ All shortcuts must be defined in `MainWindow.retranslate_ui()` with the comment:
`# Keyboard shortcuts — set here because Ui_MainWindow.retranslate_ui is`
`# shadowed by this override (Python MRO) and therefore never called at runtime.`

**Proxy model — `Column(IntEnum)`:**
Explicitly cast to `int()` before any `model.index()` call. Some PySide6/Shiboken
builds silently return an invalid `QModelIndex` when passed an `IntEnum`.

## Mandatory rules — internationalisation

When a translated string is **added or changed**:
- Update **all** languages in `locales/*/LC_MESSAGES/messages.po`
- Never leave a `msgstr` empty or unchanged in an existing `.po` file
- Run `make translations` to recompile the `.mo` files

Language resolution: `lang = config.xxx_language or system_language()`.
Never compute the `locales/` path via `Path(__file__).parent...` outside of
`i18n.py`. Use `get_locale_dir()` from `i18n.py` (handles PyInstaller).

## Mandatory rules — RST documentation (Sphinx)

- Validate every modified `.rst`: `python3 -m docutils <file> /dev/null` (exit 0, no output).
- Use `.. list-table::` exclusively — never grid tables (`+----+----+`).
- Directive indentation: **3 spaces**, never tabs.
- After any `.rst` or docstring change: `make clean all docs` must complete
  **without any Sphinx WARNING or ERROR**. Running `make docs` alone is not enough.

## Git workflow

**Before every commit:**
```
pre-commit run --all-files
```
Verify all hooks pass (exit 0, no files modified). Never push if this command
fails or modifies files.

**Before every push — squash required:**
```
git log --oneline origin/main..HEAD   # count N commits
git reset --soft HEAD~N
git commit -m "..."
```
One push = one commit. The commit message summarises **all** included changes.

**Commit messages and tag names**: always in English.

**Before any tag/release:**
Update `CHANGELOG.md` with a `## [X.Y.Z] – YYYY-MM-DD` section (Added /
Changed / Fixed). The CI pipeline extracts release notes from this file.

## Installation (conda environment)

```
pip install deep-translator
pip install -e . --no-deps    # --no-deps required: do not reinstall conda packages
```

## Reference file maintenance — REQUIRED

At the end of every session that modifies the project, update these two files:

**`claude_prompt.txt`** — complete project specification:
- Add any new feature, technical constraint, or notable fix
- Keep it consistent with the actual source code

**`claude_summary.txt`** — current implementation state:
- Update version, architecture, modules, technical decisions
- This file allows resuming context across sessions without re-reading the code
- Update after every significant change

If these files diverge from the source code, **the source code prevails**.
