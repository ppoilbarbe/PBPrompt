PBPrompt Documentation
======================

**PBPrompt** is a free, open-source desktop application for storing, organising,
and translating AI prompts.  It is built with PyQt5 and stores data in a
**SQLite database** (with YAML import/export for interoperability).

.. note::

   This project was written 100% by `Claude <https://claude.ai>`_, Anthropic's AI
   assistant, from a single detailed prompt — without any human writing code directly.

   The goal is to **evaluate Claude's capabilities**: its ability to produce clean,
   well-structured, and documented code from a specification, and its ability to
   diagnose and fix bugs when given only a symptom (an error message, unexpected
   behaviour, or a failed build) rather than a root cause.

   The prompt used to generate this project is available in ``claude_prompt.txt``.

.. toctree::
   :maxdepth: 2
   :caption: User guide

   installation
   usage
   development

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog
   licenses_overview

.. toctree::
   :maxdepth: 2
   :caption: API reference

   api/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
