Changelog
=========

All notable changes to PBPrompt are documented here.
This project follows `Semantic Versioning <https://semver.org/>`_.

1.0.1 (2024)
------------

Added
~~~~~

* **Duplicate row** – new toolbar button and ``Ctrl+D`` shortcut to duplicate
  the current row and insert it immediately below.
* **Current cell highlight** – the active cell is visually distinguished from
  other cells in the selected row by a coloured 2-px border.
* **argparse CLI** – ``--version``, ``--log-level``, and optional ``FILE``
  positional argument.  A file passed on the command line takes priority over
  the auto-loaded last file; errors show an informative dialog.
* **SVG icons** – custom 24×24 outline icons for all toolbar actions;
  icon resolution chain: desktop theme → QRC resource → filesystem → Qt
  standard.
* **Semver version management** – ``scripts/bump_version.py`` and Makefile
  targets ``bump-patch``, ``bump-minor``, ``bump-major``.
* **Five new UI languages** – Español (es), Italiano (it), Русский (ru),
  Tiếng Việt (vi), 中文(简体) (zh_CN).
* **Dynamic language discovery** – the Settings display-language combo is
  built at runtime by scanning compiled ``.mo`` files; no hard-coded list.
* **"System default" option** – both display-language and translation-language
  combos now offer *System default* (``""`` in config) as the first and
  default item.
* **Local language column header** – shows the actual language name and code
  (e.g. *Français (fr)*) from startup, not the generic label.
* **PyInstaller support** – ``get_locale_dir()`` in ``i18n.py`` resolves
  ``locales/`` correctly from both normal execution and PyInstaller bundles
  via ``sys._MEIPASS``.
* **Makefile** ``dist`` target – produces ``dist/pbprompt-x.y.z.tar.gz`` and
  ``dist/pbprompt-x.y.z.zip``.
* **Makefile** ``help`` target – lists all targets with descriptions in colour.
* **ReadTheDocs** – project documentation published to Read the Docs.

Fixed
~~~~~

* ``setContentsMargins`` called with a single argument (Qt6-only form) caused
  a ``TypeError`` at startup; fixed by using four separate margin properties
  in the ``.ui`` file.
* XML comments inside ``<layout>`` elements caused pyuic5 to crash; all
  comments removed from ``.ui`` files.
* Custom widget subclass ``PromptTableView`` was missing from the
  ``<customwidgets>`` declaration in ``main_window.ui``, causing an
  ``AttributeError`` at startup.
* ``bump_version.py`` failed to update ``pyproject.toml`` because ``^``
  requires ``re.MULTILINE``; flag added.
* Makefile ``dist`` used ``read -d ''`` (bash-only); replaced with POSIX
  ``read -r``.
* VERSION in Makefile was empty when ``__version__`` used double quotes;
  ``sed`` pattern updated to handle both quote styles.
* ``build-backend`` set to the legacy setuptools backend incompatible with
  setuptools ≥ 68; changed to ``"setuptools.build_meta"``.

1.0.0 (2024)
------------

Initial release.

* Five-column prompt table (AI, Group, Name, Local language, English).
* Multi-line inline editor for *Local language* and *English* cells.
* Per-column regex filtering (AND logic).
* Multi-key column sort with automatic sub-sort.
* YAML 1.2 persistence via ruamel.yaml.
* 12 translation services via deep-translator + Reverso.
* Recent-files submenu with auto-load on startup.
* Settings dialog (language, service, credentials, log level, max recent files).
* Gettext i18n: English and French UI.
* Platform-aware configuration directory (Linux, Windows, macOS).
* PyInstaller spec for standalone executables.
