Usage
=====

Starting the application
-------------------------

.. code-block:: bash

   pbprompt                        # open the last used file (if any)
   pbprompt prompts.sqlite         # open a specific file
   pbprompt --log-level DEBUG      # verbose logging
   pbprompt --version              # print version and exit
   pbprompt --help                 # print help and exit

If ``FILE`` is given on the command line it takes priority over the
auto-loaded last file.  If the file cannot be read an error dialog shows the
path and the exact error message; the application then starts with an empty
list.


The prompt table
-----------------

Each row represents one prompt entry with five fields:

+----------------+--------------------------------------------------+
| Column         | Description                                      |
+================+==================================================+
| AI             | Name of the AI model (e.g. *ChatGPT*, *Claude*)  |
+----------------+--------------------------------------------------+
| Group          | Category grouping related prompts                |
+----------------+--------------------------------------------------+
| Name           | Short descriptive name for the prompt            |
+----------------+--------------------------------------------------+
| Local language | Prompt text in the configured local language     |
+----------------+--------------------------------------------------+
| English        | Prompt text in English                           |
+----------------+--------------------------------------------------+

The column header for *Local language* displays the actual language name and
code (e.g. **Français (fr)**) as configured in Settings.


Editing prompts
---------------

* **Single click** – select the row.
* **Double-click on AI / Group / Name** – edit the cell inline.
* **Double-click on Local language / English** – open a multi-line inline
  editor (``QPlainTextEdit``).  In this editor:

  * **Enter** validates the edit and closes the editor (same as Tab).
  * **Ctrl+Enter** or **Shift+Enter** inserts a real newline at the cursor.
  * **Tab** / **Shift+Tab** commit the edit and move to the next/previous cell.
  * **Escape** cancels the edit.
  * Clicking outside commits the edit.

  Line breaks stored in the data are shown as ``↵`` (U+21B5) in the table
  view.


Clipboard operations
---------------------

Use the keyboard shortcuts or the right-click context menu:

* **Ctrl+C** – copy the current cell value to the clipboard.
* **Ctrl+X** – cut (copy + clear) the current cell value.
* **Ctrl+V** – paste clipboard text into the current cell.
* **Right-click** → Copy / Cut / Paste.

A status bar message confirms the copied text (``Copied: …``).


Toolbar and keyboard shortcuts
-------------------------------

+-------------------------+---------------+----------------------------------------------+
| Action                  | Shortcut      | Description                                  |
+=========================+===============+==============================================+
| New file                | Ctrl+N        | Create an empty collection                   |
+-------------------------+---------------+----------------------------------------------+
| Open…                   | Ctrl+O        | Open a SQLite file                           |
+-------------------------+---------------+----------------------------------------------+
| Save                    | Ctrl+S        | Save the current file                        |
+-------------------------+---------------+----------------------------------------------+
| Save As…                | Ctrl+Shift+S  | Save to a new file                           |
+-------------------------+---------------+----------------------------------------------+
| Import YAML — Add…      | Ctrl+I        | Append entries from a YAML file              |
+-------------------------+---------------+----------------------------------------------+
| Import YAML — Replace…  | Ctrl+Shift+I  | Replace all entries from a YAML file         |
+-------------------------+---------------+----------------------------------------------+
| Export YAML…            | Ctrl+E        | Export all entries to a YAML file            |
+-------------------------+---------------+----------------------------------------------+
| Close                   | Ctrl+W        | Close the current file                       |
+-------------------------+---------------+----------------------------------------------+
| Quit                    | Ctrl+Q        | Quit the application                         |
+-------------------------+---------------+----------------------------------------------+
| Options…                | Ctrl+,        | Open the settings dialog                     |
+-------------------------+---------------+----------------------------------------------+
| New Prompt              | Ins           | Append a new empty row                       |
+-------------------------+---------------+----------------------------------------------+
| Duplicate               | Ctrl+D        | Duplicate the current row and insert below   |
+-------------------------+---------------+----------------------------------------------+
| Delete                  | Del           | Delete selected rows (with confirmation)     |
+-------------------------+---------------+----------------------------------------------+
| → English               | F6            | Translate selected rows to English           |
+-------------------------+---------------+----------------------------------------------+
| ← Local                 | F7            | Translate selected rows from English         |
+-------------------------+---------------+----------------------------------------------+

All action tooltips are also shown in the status bar when hovering over menu
items and toolbar buttons.


YAML import / export
--------------------

PBPrompt stores data in **SQLite** (``.sqlite``) but can exchange data with
YAML files via the **File › Import YAML** and **File › Export YAML…** menu items.

**Import YAML › Add entries…** (Ctrl+I)
  Appends all entries from the chosen YAML file to the current collection.

**Import YAML › Replace all…** (Ctrl+Shift+I)
  Clears the collection and replaces it with the contents of the chosen YAML
  file.  Unknown YAML keys are silently ignored; missing keys default to ``""``.

**Export YAML…** (Ctrl+E)
  Exports all entries to a YAML file.  All five columns are always written.
  The ``.yaml`` extension is appended automatically if omitted.


Filtering
---------

Each column has a filter field above the table.  Filters accept
**Python-compatible regular expressions** and are combined with AND logic:
a row is shown only if it matches *all* active filters.  Click **Clear** to
reset all filters.


Sorting
-------

Click any **AI**, **Group** or **Name** column header to sort.  A second click
reverses the direction.  Sub-sort criteria are applied automatically:

+--------------+-----------------------------+
| Primary key  | Sub-sort order              |
+==============+=============================+
| AI           | Group → Name                |
+--------------+-----------------------------+
| Group        | Name → AI                   |
+--------------+-----------------------------+
| Name         | Group → AI                  |
+--------------+-----------------------------+


Recent files
------------

**File › Recent Files** lists the most recently used SQLite files.  Clicking an
entry opens it (with unsaved-changes detection).  If the file no longer exists
a warning is displayed, the entry is removed from the list and an empty
collection is loaded.  Use **Clear list** to wipe the history.


Settings dialog
---------------

Open via **Tools › Options…** (Ctrl+,).

Language tab
~~~~~~~~~~~~

* **Display language** – the UI language.  *System default* follows the OS
  locale.  Available languages are discovered automatically from the compiled
  ``.mo`` files in ``locales/``:

  * English (en)
  * Français (fr)
  * Español (es)
  * Italiano (it)
  * Русский (ru)
  * Tiếng Việt (vi)
  * 中文(简体) (zh_CN)

* **Translation language** – source/target language for the *Local language*
  column.  *System default* follows the OS locale.

Translation service tab
~~~~~~~~~~~~~~~~~~~~~~~

+-------------------+---------------------------------+--------------------+
| Service           | Required credentials            | Notes              |
+===================+=================================+====================+
| Google Translate  | none                            | Unofficial API     |
+-------------------+---------------------------------+--------------------+
| MyMemory          | none                            | 10k chars/day free |
+-------------------+---------------------------------+--------------------+
| DeepL             | API key                         |                    |
+-------------------+---------------------------------+--------------------+
| Microsoft         | API key                         |                    |
+-------------------+---------------------------------+--------------------+
| Yandex            | API key                         |                    |
+-------------------+---------------------------------+--------------------+
| LibreTranslate    | URL + optional key              | Self-hostable      |
+-------------------+---------------------------------+--------------------+
| Baidu             | App ID + App secret             |                    |
+-------------------+---------------------------------+--------------------+
| Papago            | App ID + App secret             |                    |
+-------------------+---------------------------------+--------------------+
| QCRI              | API key                         | Arabic focus       |
+-------------------+---------------------------------+--------------------+
| PONS              | none                            | Dictionary only    |
+-------------------+---------------------------------+--------------------+
| Linguee           | none                            | Dictionary only    |
+-------------------+---------------------------------+--------------------+
| Reverso           | none                            | Unofficial API     |
+-------------------+---------------------------------+--------------------+

Configuration is stored in the platform-appropriate directory:

* Linux: ``~/.config/pbprompt/config.yaml``
* Windows: ``%APPDATA%\pbprompt\config.yaml``
* macOS: ``~/Library/Application Support/pbprompt/config.yaml``


Adding a new UI language
------------------------

#. Copy ``locales/en/LC_MESSAGES/messages.po`` to
   ``locales/<lang>/LC_MESSAGES/messages.po``.
#. Translate each ``msgstr`` entry.
#. Add the language code to ``LOCALE_LANGS`` in the ``Makefile``.
#. Run ``make translations`` to compile the ``.po`` file to ``.mo``.
#. The new language appears automatically in the Settings combo box on next
   launch (no code change required).


Known limitations
-----------------

* **Google Translate / Reverso** use unofficial endpoints and may be
  rate-limited or break without notice.
* **DeepL / Yandex / Microsoft** require a paid or free-tier API key.
* **LibreTranslate** requires a running instance; the default public endpoint
  may need an API key.
* The compiled files ``resources_rc.py``, ``ui_*.py`` and ``locales/**/*.mo``
  are not committed to the repository.  Run ``make all`` after cloning.
