Development
===========

Setting up the development environment
---------------------------------------

.. code-block:: bash

   git clone https://github.com/pbsoft/pbprompt.git
   cd pbprompt
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   pre-commit install
   make all

With **conda**:

.. code-block:: bash

   conda create -n pbprompt-dev python=3.12 pyside6 ruamel.yaml platformdirs requests pytest-xvfb
   conda activate pbprompt-dev
   pip install deep-translator
   pip install -e ".[dev]" --no-deps
   pre-commit install
   make all


Build system (Makefile)
------------------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Target
     - Description
   * - ``make all``
     - Compile UI files, resources and translations
   * - ``make ui``
     - ``pyside6-uic *.ui → ui_*.py``
   * - ``make resources``
     - ``pyside6-rcc resources.qrc → resources_rc.py``
   * - ``make translations``
     - ``msgfmt *.po → *.mo`` for all locales
   * - ``make run``
     - Launch without installing (``PYTHONPATH=src``)
   * - ``make lint``
     - ``ruff check`` + ``ruff format --check``
   * - ``make format``
     - ``ruff format`` + ``ruff check --fix``
   * - ``make test``
     - ``pytest tests/``
   * - ``make test-cov``
     - Pytest with HTML coverage report
   * - ``make docs``
     - Build Sphinx HTML documentation
   * - ``make bundle``
     - Build standalone executable with PyInstaller
   * - ``make dist``
     - Create ``dist/pbprompt-x.y.z.{tar.gz,zip}``
   * - ``make clean``
     - Remove all generated artefacts including ``dist/``
   * - ``make version``
     - Print current version
   * - ``make bump-patch``
     - Bump patch version (1.0.0 → 1.0.1)
   * - ``make bump-minor``
     - Bump minor version (1.0.1 → 1.1.0)
   * - ``make bump-major``
     - Bump major version (1.1.0 → 2.0.0)


Version management
------------------

PBPrompt uses `Semantic Versioning <https://semver.org/>`_.  The version is
stored in ``src/pbprompt/__init__.py`` and mirrored in ``pyproject.toml``.
Use the Makefile targets or the script directly:

.. code-block:: bash

   make bump-patch                          # 1.0.1 → 1.0.2
   make bump-minor                          # 1.0.2 → 1.1.0
   make bump-major                          # 1.1.0 → 2.0.0
   python scripts/bump_version.py patch     # same as make bump-patch


Project structure
-----------------

.. code-block:: text

   src/pbprompt/
   ├── __init__.py          package metadata, __version__
   ├── __main__.py          CLI entry point (argparse)
   ├── config.py            AppConfig dataclass + YAML I/O
   ├── data.py              PromptEntry, PromptCollection
   ├── i18n.py              gettext helpers
   ├── gui/
   │   ├── main_window.py   main window behaviour
   │   ├── models.py        Qt models and item delegates
   │   ├── icons.py         icon resolution chain
   │   ├── settings_dialog.py
   │   └── about_dialog.py
   ├── platform/            OS-specific paths and notifications
   └── translate/           translation service adapters


Qt Designer files
-----------------

The ``.ui`` XML files in ``src/pbprompt/gui/`` are the source of truth for
widget layouts.  **Never** edit the generated ``ui_*.py`` files directly;
changes would be overwritten by ``make ui``.

Rules for editing ``.ui`` files:

* Do **not** insert XML comments inside ``<layout>`` or ``<widget>`` elements
  — pyuic5 may crash on comment nodes.
* Use four separate margin properties instead of ``<contentsMargins>``::

    <property name="leftMargin"><number>6</number></property>
    <property name="topMargin"><number>6</number></property>
    <property name="rightMargin"><number>6</number></property>
    <property name="bottomMargin"><number>4</number></property>

* Declare any custom widget subclass in a ``<customwidgets>`` section with
  ``<header>`` set to the Python module path.
* Define all QActions (including shortcuts) in the ``.ui`` file.


Adding a translation service
-----------------------------

#. Create ``src/pbprompt/translate/<service>.py`` implementing
   ``BaseTranslator._do_translate()``.
#. Register the service key in ``config.TRANSLATION_SERVICES``.
#. Add an entry to ``get_translator()`` in ``src/pbprompt/translate/__init__.py``.
#. Add a display label in ``settings_dialog._SERVICE_LABELS``.


Running tests
-------------

.. code-block:: bash

   make test
   # or with coverage:
   make test-cov

The test suite uses **pytest-xvfb** (listed in ``[project.optional-dependencies]``
dev extras).  On Linux, PySide6 widgets require a running X display — even in
headless CI environments.  ``pytest-xvfb`` starts a private Xvfb virtual
framebuffer automatically before each test session and tears it down
afterwards, so neither ``xvfb-run`` nor ``QT_QPA_PLATFORM=offscreen`` is
needed.  On macOS and Windows the plugin is a no-op.

Install with the other dev dependencies:

.. code-block:: bash

   pip install -e ".[dev]"   # includes pytest-xvfb


Building documentation locally
--------------------------------

.. code-block:: bash

   pip install sphinx sphinx-rtd-theme
   make docs
   # HTML output: doc/_build/html/index.html
