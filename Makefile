# ---------------------------------------------------------------------------
# PBPrompt – top-level Makefile
# ---------------------------------------------------------------------------
CONDA_ENV  := pbprompt
ifdef NOCONDA
CONDA_RUN  :=
else
CONDA_RUN  := conda run -n $(CONDA_ENV) --no-capture-output
endif

SRC_GUI    := src/pbprompt/gui
LOCALES    := locales
LOCALE_LANGS := en de fr es it ru vi zh_CN
MO_FILES     := $(foreach lang,$(LOCALE_LANGS),$(LOCALES)/$(lang)/LC_MESSAGES/messages.mo)

VERSION    := $(shell sed -n "s/__version__ = [\"']\([^\"']*\)[\"']/\1/p" src/pbprompt/__init__.py)
DIST_DIR   := dist

.DEFAULT_GOAL := help

.PHONY: all translations run dist clean lint format test test-cov docs help version bump-patch bump-minor bump-major srcdist venv pyvenv pot merge-po hooks

all: translations  ## Compile translations (.po → .mo)

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------
VENV_DIR   := pypbprompt

venv:  ## Create conda environment 'pbprompt' from environment.yml
	conda env create -f environment.yml
	conda run -n $(CONDA_ENV) pip install -e . --no-deps
	@echo ""
	@echo "[venv] environment '$(CONDA_ENV)' ready – activate with: conda activate $(CONDA_ENV)"

pyvenv:  ## Create Python virtual environment 'pypbprompt' with all deps via pip
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -e ".[dev]"
	@echo ""
	@echo "[pyvenv] environment '$(VENV_DIR)' ready – activate with: source $(VENV_DIR)/bin/activate"

# ---------------------------------------------------------------------------
# Run without installing
# ---------------------------------------------------------------------------
run:  ## Run the application without installing (uses src/ layout)
	PYTHONPATH=src $(CONDA_RUN) python -m pbprompt

# ---------------------------------------------------------------------------
# Compile gettext translations (.po → .mo)
# ---------------------------------------------------------------------------
translations: $(MO_FILES)  ## Compile all .po files to .mo

$(LOCALES)/%/LC_MESSAGES/messages.mo: $(LOCALES)/%/LC_MESSAGES/messages.po
	@echo "[i18n] compiling $<"
	$(CONDA_RUN) pybabel compile -f -i $< -o $@

# Update .pot template from source
pot:  ## Extract translatable strings from Python sources
	$(CONDA_RUN) pybabel extract -F babel.cfg -k _ \
	    --input-dirs=src \
	    -o $(LOCALES)/messages.pot
	@echo "[i18n] updated $(LOCALES)/messages.pot"

# Merge updated template into existing .po files
merge-po: pot  ## Merge new strings into .po files
	@for lang in $(LOCALE_LANGS); do \
	    $(CONDA_RUN) pybabel update -i $(LOCALES)/messages.pot \
	        -d $(LOCALES) -l $$lang \
	        -D messages --no-fuzzy-matching; \
	done
	$(CONDA_RUN) python tools/fix_po_files.py $(LOCALES)

# ---------------------------------------------------------------------------
# Linting / formatting
# ---------------------------------------------------------------------------
lint:  ## Run ruff linter + formatter check
	$(CONDA_RUN) ruff check src tests
	$(CONDA_RUN) ruff format --check src tests

format:  ## Auto-format with ruff
	$(CONDA_RUN) ruff format src tests
	$(CONDA_RUN) ruff check --fix src tests

hooks:  ## Run all pre-commit hooks on all files
	$(CONDA_RUN) pre-commit run --all-files

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
test:  ## Run pytest
	$(CONDA_RUN) python -m pytest tests/

test-cov:  ## Run pytest with coverage
	$(CONDA_RUN) python -m pytest tests/ --cov=pbprompt --cov-report=html

# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------
docs:  ## Build Sphinx documentation
	$(CONDA_RUN) sphinx-build -b html doc doc/_build/html

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean:  ## Remove generated artefacts (.mo, dist, caches)
	find $(LOCALES) -name "*.mo" -delete
	rm -rf doc/_build $(DIST_DIR)
	rm -rf .ruff_cache .pytest_cache htmlcov .coverage
	rm -rf build
	find . -name "*.spec" -not -path "./.git/*" -not -name "pbprompt.spec" -delete
	find . -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} +

# ---------------------------------------------------------------------------
# Distribution archives
# ---------------------------------------------------------------------------
srcdist: all  ## Build dist/pbprompt-x.y.z.tar.gz and dist/pbprompt-x.y.z.zip
	@GIT_VERSION=$$(bash tools/git_version.sh); \
	DIST_NAME=pbprompt-$$GIT_VERSION; \
	DIST_TMP=$(DIST_DIR)/.tmp-$$DIST_NAME; \
	mkdir -p $(DIST_DIR); \
	rm -rf $$DIST_TMP; \
	mkdir -p $$DIST_TMP/$$DIST_NAME; \
	find . \
	    ! -path './.git' ! -path './.git/*' \
	    ! -path './$(DIST_DIR)' ! -path './$(DIST_DIR)/*' \
	    ! -path '*/__pycache__' ! -path '*/__pycache__/*' \
	    ! -name '*.pyc' ! -name '*.pyo' \
	    ! -path '*.egg-info' ! -path '*.egg-info/*' \
	    ! -path './doc/_build' ! -path './doc/_build/*' \
	    ! -path './.ruff_cache' ! -path './.ruff_cache/*' \
	    ! -path './build' ! -path './build/*' \
	    ! -name '*.spec' \
	    -type f | sort | \
	  while IFS= read -r f; do \
	    dst="$$DIST_TMP/$$DIST_NAME/$${f#./}"; \
	    mkdir -p "$$(dirname "$$dst")"; \
	    cp "$$f" "$$dst"; \
	  done; \
	tar -czf $(DIST_DIR)/$$DIST_NAME.tar.gz -C $$DIST_TMP $$DIST_NAME; \
	(cd $$DIST_TMP && zip -qr ../$$DIST_NAME.zip $$DIST_NAME); \
	rm -rf $$DIST_TMP; \
	echo "[srcdist] $(DIST_DIR)/$$DIST_NAME.tar.gz"; \
	echo "[srcdist] $(DIST_DIR)/$$DIST_NAME.zip"

# ---------------------------------------------------------------------------
# PyInstaller standalone binary
# ---------------------------------------------------------------------------
SPEC_FILE  := pbprompt.spec

dist: all  ## Build a standalone binary with PyInstaller (named pbprompt-VERSION-os-arch)
	@GIT_VERSION=$$(bash tools/git_version.sh); \
	OS=$$(uname -s | tr '[:upper:]' '[:lower:]'); \
	ARCH=$$(uname -m); \
	EXENAME=pbprompt-$$GIT_VERSION-$$OS-$$ARCH; \
	if [ ! -f $(SPEC_FILE) ]; then \
	    echo "[dist] no $(SPEC_FILE) found – generating one"; \
	    $(CONDA_RUN) pyinstaller \
	        --onefile \
	        --windowed \
	        --name pbprompt \
	        --add-data "locales:locales" \
	        --add-data "resources:resources" \
	        src/pbprompt/__main__.py; \
	else \
	    echo "[dist] using existing $(SPEC_FILE)"; \
	    $(CONDA_RUN) pyinstaller $(SPEC_FILE); \
	fi; \
	EXT=""; [ -f $(DIST_DIR)/pbprompt.exe ] && EXT=".exe"; \
	mv $(DIST_DIR)/pbprompt$$EXT $(DIST_DIR)/$$EXENAME$$EXT; \
	echo "[dist] $(DIST_DIR)/$$EXENAME$$EXT"

# ---------------------------------------------------------------------------
# Version management (semver)
# ---------------------------------------------------------------------------
version:  ## Display the current version
	@grep -E '__version__' src/pbprompt/__init__.py | head -1

bump-patch:  ## Bump patch version  (1.0.0 → 1.0.1)
	$(CONDA_RUN) python tools/bump_version.py patch

bump-minor:  ## Bump minor version  (1.0.1 → 1.1.0, resets patch)
	$(CONDA_RUN) python tools/bump_version.py minor

bump-major:  ## Bump major version  (1.1.0 → 2.0.0, resets minor+patch)
	$(CONDA_RUN) python tools/bump_version.py major

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
help:  ## Show this help message
	@echo ""
	@echo "PBPrompt – available Makefile targets"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	    awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables:"
	@echo "  NOCONDA        Bypass conda wrapping; tools must be on PATH"
	@echo "                 e.g. make test NOCONDA=1  or  export NOCONDA=1"
	@echo ""
