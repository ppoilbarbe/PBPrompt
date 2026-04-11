# Changelog

All notable changes to PBPrompt are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.3] – 2026-04-11

### Fixed
- Apply all pending ruff format and lint fixes that were missing from the 1.0.2
  release: import ordering (`detect_image_format`, `generate_thumbnail`), line
  wrapping for long expressions, blank lines after local imports, and inline
  comment spacing.  `pre-commit run --all-files` now passes cleanly on every
  tracked file.
- Add explicit rule to the project spec: `pre-commit run --all-files` must
  return exit code 0 and must not modify any file before any commit or release.

## [1.0.2] – 2026-04-11

### Fixed
- Pre-commit hooks updated (`pre-commit-hooks` v6.0.0, `ruff` v0.15.10); all
  ruff lint and format errors corrected (E501 lines shortened, auto-formatted
  files committed).

## [1.0.1] – 2026-04-11

### Added
- **Automated multi-platform releases** – pushing a `vX.Y.Z` tag now triggers
  a full release pipeline on both GitHub Actions and GitLab CI: tests run,
  standalone executables are built for Linux (amd64), Windows (amd64), and
  macOS (x86\_64 / Rosetta), and a release is published automatically with the
  matching changelog section as description and all assets attached.
- `scripts/extract_changelog.py` – standalone helper that parses `CHANGELOG.md`
  and extracts the release notes for a given version.  Used by both CI
  pipelines; also writes a GitHub Actions `notes` output variable when
  `$GITHUB_OUTPUT` is set.

## [1.0.0] – 2026-04-11

### Added
- **Six-column prompt table** – AI, Group, Name, Image, Local language, English.
- **IMAGE column** – thumbnail display in the grid; double-click shows full image;
  right-click context menu: Load from file, Paste, Clear; drag & drop supported.
  Full image stored as SQLite BLOB; thumbnail auto-generated on import.
  YAML export encodes the full image as Base64; thumbnails are not exported.
  Thumbnail size (width × height) is configurable in Settings (default 64 × 64 px).
  *Refresh Thumbnails* action in the Tools menu regenerates all thumbnails.
- **YAML deduplication on import** – rows whose five text fields exactly match an
  existing entry are skipped; prevents duplicating a database by importing the same
  file twice.
- **Image file dialog with preview** – the Load Image dialog shows a live thumbnail
  of the selected file before confirming.
- **Multi-line inline editor** – `Enter` confirms; `Ctrl+Enter` / `Shift+Enter`
  inserts a real newline; `Tab` / `Shift+Tab` moves to the adjacent cell.
- **Per-column regex filtering** with AND logic across all text columns.
- **Multi-key column sort** with automatic sub-sort (e.g. AI → Group → Name).
- **SQLite persistence** (WAL mode) with automatic schema migration.
- **YAML import / export** – `Ctrl+I` (add), `Ctrl+Shift+I` (replace all),
  `Ctrl+E` (export).
- **12 translation services** via deep-translator + custom Reverso adapter.
- **Duplicate row** – toolbar button and `Ctrl+D` shortcut to duplicate the current
  row and insert it immediately below.
- **Current cell highlight** – the active cell is visually distinguished from other
  cells in the selected row by a coloured 2-px border.
- **argparse CLI** – `--version`, `--log-level`, and an optional `FILE` positional
  argument.  A file on the command line takes priority over the auto-loaded last
  file; read errors show an informative dialog.
- **SVG icons** – custom 24 × 24 outline icons for all toolbar actions with a
  four-level fallback chain (desktop theme → QRC → filesystem → Qt standard).
- **Semver version management** – `scripts/bump_version.py` and Makefile targets
  `bump-patch`, `bump-minor`, `bump-major`.
- **Seven UI languages** – English, Français (fr), Español (es), Italiano (it),
  Русский (ru), Tiếng Việt (vi), 中文(简体) (zh\_CN).
- **Dynamic language discovery** – the Settings display-language combo is built at
  runtime by scanning compiled `.mo` files; no hard-coded list required.
- **"System default" option** – both display-language and translation-language
  combos offer *System default* (`""` in config) as the first and default item.
- **Local language column header** – shows the actual language name and code
  (e.g. *Français (fr)*) from startup and after a language change.
- **PyInstaller support** – `get_locale_dir()` in `i18n.py` resolves `locales/`
  correctly from both normal execution and PyInstaller one-file bundles.
- **Makefile `dist` target** – produces `dist/pbprompt-x.y.z.tar.gz` and
  `dist/pbprompt-x.y.z.zip`.
- **Makefile `help` target** – lists all targets with descriptions in colour.
- **Sphinx documentation** published on Read the Docs.
- `LICENSES` file with full license texts for all dependencies.
- `CONTRIBUTING.md` contributor guide.

### Fixed
- `setContentsMargins` called with a single argument (Qt6-only form) caused a
  `TypeError` at startup; fixed by using four separate margin properties in the
  `.ui` file.
- XML comments inside `<layout>` elements caused pyuic5 to crash; all comments
  removed from `.ui` files.
- Custom widget subclass `PromptTableView` was missing from the
  `<customwidgets>` declaration in `main_window.ui`, causing an `AttributeError`
  at startup.
- `bump_version.py` failed to update `pyproject.toml` because `^` requires
  `re.MULTILINE`; flag added.
- Makefile `dist` used `read -d ''` (bash-only); replaced with POSIX `read -r`.
- `VERSION` in Makefile was empty when `__version__` used double quotes; `sed`
  pattern updated to handle both quote styles.
- `build-backend` set to the legacy setuptools backend incompatible with
  setuptools ≥ 68; changed to `"setuptools.build_meta"`.
