Installation
============

Requirements
------------

* Python 3.11 or 3.12
* PySide6 ≥ 6.5
* ``gettext`` tools (``msgfmt``) for compiling translations


From source (recommended)
--------------------------

.. code-block:: bash

   git clone https://github.com/pbsoft/pbprompt.git
   cd pbprompt
   make all          # compile UI, resources and translations
   make run          # launch without installing

Using a **conda** environment (recommended on Linux with system Qt):

.. code-block:: bash

   conda create -n pbprompt python=3.12 pyside6 ruamel.yaml platformdirs requests
   conda activate pbprompt
   pip install deep-translator
   pip install -e . --no-deps   # --no-deps: do not reinstall conda-managed packages
   make all
   make run

Using a plain **venv**:

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   make all
   make run


Building a standalone executable
---------------------------------

PyInstaller is used to produce a single-file executable.  Use the ``make
bundle`` target, which compiles all required artefacts (UI files, Qt resources,
translation ``.mo`` files) before invoking PyInstaller:

.. code-block:: bash

   make bundle

The resulting executable is placed in ``dist/``.

.. note::

   **No cross-compilation.** PyInstaller produces an executable for the
   platform it runs on.  To build for Linux, Windows, and macOS you must run
   ``make bundle`` on each target platform (or rely on the CI pipeline, which
   builds all three in parallel).

.. warning::

   **macOS executables are not code-signed (as of 2026-04-12).**  No signing
   certificate is currently configured, so the binaries produced by the CI
   pipeline and attached to GitHub Releases are unsigned.  macOS Gatekeeper
   will block them by default; users must explicitly allow the executable in
   *System Settings → Privacy & Security* after the first launch attempt.
