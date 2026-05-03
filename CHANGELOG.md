# Changelog

All notable changes to PBPrompt are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [1.5.1] – 2026-05-03

### Added
- **German translation (`de`)**: complete UI translation; `LOCALE_LANGS` updated in
  Makefile to include `de`.

## [1.5.0] – 2026-04-20

### Added
- **Image viewer — zoom to cursor**: mouse wheel zoom now keeps the pixel under the
  cursor centred in the viewport (best approximation when scrollbar limits apply).
- **Image context menu — Copy image**: copies the full stored image to the system
  clipboard (`Ctrl+C`).
- **Image context menu — Save image to file…**: saves the image to a user-chosen file;
  the file-type filter and default extension are derived from the stored format (JPEG
  or PNG); raw bytes are written without recompression.
- Copy, Save and Clear image context-menu actions are now disabled when the cell
  contains no image.

### Fixed
- **Makefile `translations` target**: was declared `.PHONY` without file dependencies,
  causing all `.mo` files to be recompiled on every `make all` even when no `.po` had
  changed.  Now uses a pattern rule (`%.mo: %.po`) so only modified locales are rebuilt.

## [1.4.0] – 2026-04-18

### Added
- **Persistent column filters**: filter field values are saved to `AppConfig.column_filters`
  on close and restored on next launch (keys: `ai`, `group`, `name`, `local`, `english`).
- **CI: auto-deactivate old RTD versions**: `.github/workflows/ci.yml` now calls
  `scripts/rtd_cleanup.py` after each release to deactivate superseded ReadTheDocs versions.
- **F1 shortcut** for Help → About dialog.
- **Ctrl+R shortcut** for Tools → Refresh Thumbnails.
- **Filter field tooltips**: each column filter QLineEdit now shows a tooltip explaining
  that regular expressions are supported.
- **IMAGE header tooltip** enhanced with keyboard shortcuts hint
  (Enter: load from file · Ctrl+V: paste · Backspace: clear).

## [1.3.2] – 2026-04-13

### Changed
- README: clarify project goal.

### Fixed
- ReadTheDocs build: pin Sphinx version to fix versioning issues.

## [1.3.1] – 2026-04-13

### Added
- **CLAUDE.md**: operational instructions for Claude Code (commands, critical rules,
  git workflow, i18n, RST/Sphinx, maintenance of reference files).

### Fixed
- **ReadTheDocs build**: add `gettext` to `apt_packages` in `.readthedocs.yaml` so
  that `msgfmt` is available when `make translations` runs in the pre-build step.

## [1.3.0] – 2026-04-13

### Added
- **Multi-row image clear**: clearing an image now applies to all selected rows;
  falls back to the current row when nothing is selected.
- **Image clear confirmation**: a `QMessageBox.question` dialog (default: No)
  asks for confirmation before clearing, showing the number of affected rows.

### Changed
- Image-clear keyboard shortcut changed from `Del` to `Backspace` to eliminate
  the conflict with `Del` (delete row); context menu hint updated accordingly.

### Fixed
- CI release pipeline: `extract_changelog.py` was silently writing to
  `$GITHUB_OUTPUT` instead of stdout (the env var is always set on GitHub
  runners), so `--notes-file` received an empty stream. Script simplified to
  always print to stdout; CI step uses a temp file instead of process
  substitution.

## [1.2.0] – 2026-04-13

### Added
- **Persistent last-used directories**: the application now remembers the last
  directory used for YAML import (`last_import_dir`), YAML export
  (`last_export_dir`), and image loading (`last_image_dir`); the stored path is
  offered as the default in the file dialog on the next open.
- **Image column keyboard shortcuts**: `Return`/`Enter` opens the load-from-file
  dialog, `Ctrl+V` pastes from the clipboard, `Del` clears the image; shortcuts
  are also shown in the right-click context menu.
- **Settings dialog tooltips**: descriptive tooltips added to all settings fields
  (language selectors, translation service, API credentials, thumbnail dimensions).
- Four new tests for `last_import_dir` / `last_export_dir` / `last_image_dir`
  round-trip persistence in `AppConfig` (87 tests total).

### Fixed
- Image delegate: clearing the `HasDecoration` feature flag instead of assigning
  a null `QPixmap` prevents `QPainter::begin` errors on some platforms.
- Image preview in file dialog: `max(size − 8, 1)` guard prevents a zero-size
  crash in `QPixmap.scaled()` when the dialog is very small.
- CI release pipeline: `extract_changelog.py` was silently writing to
  `$GITHUB_OUTPUT` instead of stdout when called via process substitution,
  producing an empty release body. The script now always prints to stdout;
  the CI step uses a temp file instead of process substitution.

## [1.1.0] – 2026-04-12

### Added
- **Test suite**: comprehensive coverage for `pbprompt.config` (28 tests, 100 %)
  and `pbprompt.data` (41 tests, 100 %); 83 tests total, all green.
- `pytest-xvfb >= 3.0` added to dev extras — starts a private Xvfb virtual
  framebuffer automatically on Linux so PyQt5 tests run headless without
  `xvfb-run` or `QT_QPA_PLATFORM=offscreen`.

### Changed
- CI: GitLab CI configuration (`.gitlab-ci.yml`) removed; GitHub Actions is the
  sole CI pipeline.
- Documentation installation (conda): `pytest-xvfb` now installed via
  `conda create` (available as a conda package); `deep-translator` remains pip-only.
- Documentation development: *Running tests* section updated to explain the
  `pytest-xvfb` rationale.

### Fixed
- **Sphinx documentation** (`make clean all docs` now produces 0 warnings, 0 errors):
  - `doc/_static/` directory created to suppress the `html_static_path` warning.
  - `platform/windows.py`: unexpected indentation in module docstring corrected.
  - `translate/libretranslate.py`: docstring converted from NumPy style to Google
    style (`napoleon_numpy_docstring = False`).
  - `gui/models.py`: explicit `#:` docstrings added to the `collection_modified`
    and `cell_copied` PyQt signals (suppresses `*args` RST emphasis warning from
    autodoc).

## [1.0.6] – 2026-04-12

### Changed
- Organisation renamed from **PBSoft** to **PBMou** throughout all source files,
  licences, translations, and documentation.
- Copyright year corrected to 2026 in all project-owned files.
- CI: build jobs (`build-linux`, `build-windows`, `build-macos`) and the `docs`
  job now run on every push, not only on semver tags. ReadTheDocs trigger moved
  to tag-only. GitHub Release creation remains tag-only.
- CI: migrate all `actions/checkout` steps to **v5** (Node.js 24); add
  `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` workflow-level env var to cover
  remaining actions ahead of the June 2026 Node.js 20 deprecation deadline.
- macOS bundle identifier updated to `com.pbmou.pbprompt`.
- **About dialog**: label changed to *Authors* (plural); **Claude (Anthropic)**
  added alongside PBMou.
- `doc/_build/` added to `.gitignore`.

### Fixed
- **Thumbnail column**: when a thumbnail was narrower than the column, the image
  appeared twice — once left-aligned (drawn by `CE_ItemViewItem` from the
  `DecorationRole` pixmap) and once centred (drawn manually by the delegate).
  The ghost image on the left is now suppressed by clearing
  `opt.decorationPixmap` and the `HasDecoration` feature flag before calling
  `drawControl`.

## [1.0.5] – 2026-04-11

### Fixed
- Switch macOS CI runner from `macos-13` (Intel x86_64, being deprecated on the
  free tier) to `macos-14` (Apple Silicon arm64/M1), which is faster and more
  reliably available.  The macOS release binary is now `pbprompt-vX.Y.Z-macos-arm64`.
- Add `timeout-minutes: 30` to the `build-macos` job to fail fast instead of
  hanging indefinitely if the runner is slow.

## [1.0.4] – 2026-04-11

### Fixed
- `PromptCollection.__init__()` now accepts an optional `entries` parameter
  (`list[PromptEntry] | None`), restoring the API expected by the test suite.
- `test_save_and_load` updated to use `.sqlite` extension (consistent with the
  SQLite-first storage model).
- `test_load_empty_file` rewritten to create a valid empty PBPrompt database via
  `PromptCollection().save()` instead of an empty YAML file, which now correctly
  raises `ValueError`.  All 31 tests pass.

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
