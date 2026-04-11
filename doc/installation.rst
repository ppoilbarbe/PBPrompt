Installation
============

Requirements
------------

* Python 3.11 or 3.12
* PyQt5 ≥ 5.15
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

   conda create -n pbprompt python=3.12 pyqt pyqt5-sip ruamel.yaml platformdirs requests
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

PyInstaller is used to produce a single-file executable.  The compiled
translation files (``.mo``) and resources must exist before running
PyInstaller:

.. code-block:: bash

   make all                  # compile .mo, ui_*.py, resources_rc.py
   pyinstaller pbprompt.spec

The ``pbprompt.spec`` file already includes the ``locales/`` and
``resources/`` directories in ``datas``.  The resulting executable is placed
in ``dist/``.

Platform-specific helper scripts are provided in ``scripts/``:

* ``scripts/build_linux.sh``
* ``scripts/build_windows.bat``
* ``scripts/build_macos.sh``
