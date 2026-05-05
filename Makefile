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
RESOURCES  := resources
LOCALES    := locales
LOCALE_LANGS := en de fr es it ru vi zh_CN
MO_FILES     := $(foreach lang,$(LOCALE_LANGS),$(LOCALES)/$(lang)/LC_MESSAGES/messages.mo)

VERSION    := $(shell sed -n "s/__version__ = [\"']\([^\"']*\)[\"']/\1/p" src/pbprompt/__init__.py)
DIST_NAME  := pbprompt-$(VERSION)
DIST_DIR   := dist
DIST_TMP   := $(DIST_DIR)/.tmp-$(DIST_NAME)

UI_FILES   := $(wildcard $(SRC_GUI)/*.ui)
PY_UI_FILES := $(UI_FILES:$(SRC_GUI)/%.ui=$(SRC_GUI)/ui_%.py)

PNG_OUT    := pbprompt.png
SVG_SRC    := $(RESOURCES)/icons/app_color.svg

.DEFAULT_GOAL := help

.PHONY: all ui resources translations png run bundle clean lint format test test-cov docs help version bump-patch bump-minor bump-major dist venv pyvenv pot merge-po hooks

all: ui resources translations png  ## Build everything (UI, resources, translations, app icon)

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
# App icon PNG
# ---------------------------------------------------------------------------
png: $(PNG_OUT)  ## Generate pbprompt.png (128×128) from app_color.svg

$(PNG_OUT): $(SVG_SRC) scripts/make_png.py
	$(CONDA_RUN) python scripts/make_png.py

# ---------------------------------------------------------------------------
# Run without installing
# ---------------------------------------------------------------------------
run:  ## Run the application without installing (uses src/ layout)
	PYTHONPATH=src $(CONDA_RUN) python -m pbprompt

# ---------------------------------------------------------------------------
# Compile Qt Designer .ui files → ui_*.py
# ---------------------------------------------------------------------------
ui: $(PY_UI_FILES)  ## Compile all .ui files with pyside6-uic

$(SRC_GUI)/ui_%.py: $(SRC_GUI)/%.ui
	$(CONDA_RUN) pyside6-uic $< -o $@
	@echo "[ui] compiled $< → $@"

# ---------------------------------------------------------------------------
# Compile Qt resource file → resources_rc.py
# ---------------------------------------------------------------------------
resources: $(SRC_GUI)/resources_rc.py  ## Compile resources.qrc with pyside6-rcc

$(SRC_GUI)/resources_rc.py: $(RESOURCES)/resources.qrc $(wildcard $(RESOURCES)/icons/*)
	$(CONDA_RUN) pyside6-rcc $< -o $@
	@echo "[res] compiled $< → $@"

# ---------------------------------------------------------------------------
# Compile gettext translations (.po → .mo)
# ---------------------------------------------------------------------------
translations: $(MO_FILES)  ## Compile all .po files to .mo

$(LOCALES)/%/LC_MESSAGES/messages.mo: $(LOCALES)/%/LC_MESSAGES/messages.po
	@echo "[i18n] compiling $<"
	$(CONDA_RUN) pybabel compile -f -i $< -o $@

# Update .pot template from source
pot:  ## Extract translatable strings from Python sources
	$(CONDA_RUN) xgettext --language=Python --keyword=_ \
	    --output=$(LOCALES)/messages.pot \
	    --from-code=UTF-8 \
	    $(shell find src -name "*.py" | grep -v ui_ | grep -v resources_rc)
	@echo "[i18n] updated $(LOCALES)/messages.pot"

# Merge updated template into existing .po files
merge-po: pot  ## Merge new strings into .po files
	@for lang in $(LOCALE_LANGS); do \
	    dir=$(LOCALES)/$$lang/LC_MESSAGES; \
	    $(CONDA_RUN) msgmerge --update $$dir/messages.po $(LOCALES)/messages.pot; \
	done

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
clean:  ## Remove generated artefacts (UI, resources, .mo, dist, caches)
	rm -f $(PY_UI_FILES) $(SRC_GUI)/resources_rc.py
	find $(LOCALES) -name "*.mo" -delete
	rm -rf doc/_build $(DIST_DIR)
	rm -rf .ruff_cache .pytest_cache htmlcov .coverage
	rm -rf build
	find . -name "*.spec" -not -path "./.git/*" -delete
	find . -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} +

# ---------------------------------------------------------------------------
# Distribution archives
# ---------------------------------------------------------------------------
dist: all  ## Build dist/pbprompt-x.y.z.tar.gz and dist/pbprompt-x.y.z.zip
	@mkdir -p $(DIST_DIR)
	@rm -rf $(DIST_TMP)
	@mkdir -p $(DIST_TMP)/$(DIST_NAME)
	@find . \
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
	    dst="$(DIST_TMP)/$(DIST_NAME)/$${f#./}"; \
	    mkdir -p "$$(dirname "$$dst")"; \
	    cp "$$f" "$$dst"; \
	  done
	@tar -czf $(DIST_DIR)/$(DIST_NAME).tar.gz -C $(DIST_TMP) $(DIST_NAME)
	@cd $(DIST_TMP) && zip -qr ../$(DIST_NAME).zip $(DIST_NAME)
	@rm -rf $(DIST_TMP)
	@echo "[dist] $(DIST_DIR)/$(DIST_NAME).tar.gz"
	@echo "[dist] $(DIST_DIR)/$(DIST_NAME).zip"

# ---------------------------------------------------------------------------
# PyInstaller standalone binary
# ---------------------------------------------------------------------------
SPEC_FILE  := pbprompt.spec

bundle: all  ## Build a standalone binary with PyInstaller
	@if [ ! -f $(SPEC_FILE) ]; then \
	    echo "[bundle] no $(SPEC_FILE) found – generating one"; \
	    $(CONDA_RUN) pyinstaller \
	        --onefile \
	        --windowed \
	        --name pbprompt \
	        --add-data "locales:locales" \
	        --add-data "resources:resources" \
	        src/pbprompt/__main__.py; \
	else \
	    echo "[bundle] using existing $(SPEC_FILE)"; \
	    $(CONDA_RUN) pyinstaller $(SPEC_FILE); \
	fi
	@echo "[bundle] binary written to dist/"

# ---------------------------------------------------------------------------
# Version management (semver)
# ---------------------------------------------------------------------------
version:  ## Display the current version
	@grep -E '__version__' src/pbprompt/__init__.py | head -1

bump-patch:  ## Bump patch version  (1.0.0 → 1.0.1)
	$(CONDA_RUN) python scripts/bump_version.py patch

bump-minor:  ## Bump minor version  (1.0.1 → 1.1.0, resets patch)
	$(CONDA_RUN) python scripts/bump_version.py minor

bump-major:  ## Bump major version  (1.1.0 → 2.0.0, resets minor+patch)
	$(CONDA_RUN) python scripts/bump_version.py major

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
