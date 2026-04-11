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

+--------------------+-----------+------------------------------------------+
| Package            | License   | Notes                                    |
+====================+===========+==========================================+
| PyQt5              | GPL v3 /  | The GPL copy is used here.  A commercial |
|                    | Commercial| licence is available from Riverbank      |
|                    |           | Computing.                               |
+--------------------+-----------+------------------------------------------+
| ruamel.yaml        | MIT       |                                          |
+--------------------+-----------+------------------------------------------+
| deep-translator    | MIT       |                                          |
+--------------------+-----------+------------------------------------------+
| platformdirs       | MIT       |                                          |
+--------------------+-----------+------------------------------------------+
| requests           | Apache 2.0|                                          |
+--------------------+-----------+------------------------------------------+

Development / build dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+-----------+
| Package            | License   |
+====================+===========+
| pytest             | MIT       |
+--------------------+-----------+
| pytest-qt          | MIT       |
+--------------------+-----------+
| ruff               | MIT       |
+--------------------+-----------+
| pre-commit         | MIT       |
+--------------------+-----------+
| mypy               | MIT       |
+--------------------+-----------+
| Sphinx             | BSD 2-    |
|                    | Clause    |
+--------------------+-----------+
| sphinx-rtd-theme   | MIT       |
+--------------------+-----------+

Qt licensing note
-----------------

PBPrompt uses PyQt5, which is distributed under the GNU GPL v3.  As a
consequence, PBPrompt as a whole is also covered by the GPL v3 when
distributed as a binary that bundles Qt.  The source code of PBPrompt is
additionally made available under the MIT License for use in projects that
have their own Qt licence.

If you need to distribute PBPrompt under a non-GPL licence you must obtain a
commercial Qt licence from `Riverbank Computing
<https://riverbankcomputing.com/commercial/pyqt>`_ or migrate to PySide6
(LGPL).
