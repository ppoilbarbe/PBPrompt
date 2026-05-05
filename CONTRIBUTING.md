# Contributing to PBPrompt

Thank you for your interest in contributing to PBPrompt!

## Ways to contribute

- **Bug reports** – open an issue with a clear description, steps to reproduce,
  and your OS / Python / PySide6 versions.
- **Feature requests** – open an issue describing the use case.
- **Pull requests** – see the workflow below.
- **Translations** – see *Adding a new language* below.

## Development setup

```bash
git clone https://github.com/pbsoft/pbprompt.git
cd pbprompt
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
make all
```

See [doc/development.rst](doc/development.rst) for full details including
the conda workflow.

## Pull request workflow

1. Fork the repository and create a branch from `main`.
2. Make your changes; add or update tests as appropriate.
3. Ensure the test suite passes:
   ```bash
   make test
   ```
4. Ensure the linter is happy:
   ```bash
   make lint
   ```
5. Open a pull request against `main` with a clear description of what
   changed and why.

## Code style

- **Python**: PEP 8, enforced by `ruff` (line length 88).  Run `make format`
  to auto-fix formatting.
- **Type hints**: all public functions and methods must be typed.
- **Docstrings**: Google-style, English only.
- **Qt files**: edit the `.ui` source files, never the generated `ui_*.py`.
  See the rules in [doc/development.rst](doc/development.rst).

## Adding a new language

1. Copy `locales/en/LC_MESSAGES/messages.po` to
   `locales/<lang>/LC_MESSAGES/messages.po`.
2. Translate all `msgstr` entries.
3. Add the language code to `LOCALE_LANGS` in the `Makefile`.
4. Run `make translations` to compile.
5. Open a pull request with the new `.po` file (the compiled `.mo` is
   excluded from version control).

## Commit messages

Use short imperative-mood subject lines, e.g.

```
Add Vietnamese translation
Fix setContentsMargins TypeError on PySide6
Bump version to 1.0.2
```

## License

By contributing you agree that your contributions will be licensed under the
same **MIT License** as the rest of the project (see `LICENSE`).
