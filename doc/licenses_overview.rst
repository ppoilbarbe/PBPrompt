Licenses
========

PBPrompt itself is distributed under the **MIT License** (see ``LICENSE`` at
the root of the repository).

Third-party dependencies
-------------------------

The table below lists the direct runtime and development dependencies of
PBPrompt together with their licenses.  Full license texts are collected in
the ``LICENSES`` file at the root of the repository.

Runtime dependencies
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Package
     - License
     - Notes
   * - PySide6
     - LGPL v3
     - Official Qt binding by The Qt Company.
   * - ruamel.yaml
     - MIT
     -
   * - deep-translator
     - MIT
     -
   * - platformdirs
     - MIT
     -
   * - requests
     - Apache 2.0
     -

Development / build dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Package
     - License
   * - pytest
     - MIT
   * - pytest-qt
     - MIT
   * - ruff
     - MIT
   * - pre-commit
     - MIT
   * - mypy
     - MIT
   * - Sphinx
     - BSD 2-Clause
   * - sphinx-rtd-theme
     - MIT

Qt licensing note
-----------------

PBPrompt uses PySide6, which is distributed under the GNU Lesser General
Public License v3 (LGPL v3).  Under the LGPL, PBPrompt can be distributed
under its own MIT License without any GPL obligations, provided PySide6 is
dynamically linked (the default installation mode).

The full LGPL v3 text is available at https://www.gnu.org/licenses/lgpl-3.0.html.
A commercial Qt licence is also available from `The Qt Company
<https://www.qt.io/licensing/>`_.
