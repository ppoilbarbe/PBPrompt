# ---------------------------------------------------------------------------
# PBPrompt – top-level Makefile
# ---------------------------------------------------------------------------
PYTHON     := python3
PYUIC5     := pyuic5
PYRCC5     := pyrcc5
MSGFMT     := msgfmt
MSGMERGE   := msgmerge
XGETTEXT   := xgettext

SRC_GUI    := src/pbprompt/gui
RESOURCES  := resources
LOCALES    := locales
LOCALE_LANGS := en fr es it ru vi zh_CN

VERSION    := $(shell sed -n "s/__version__ = [\"']\([^\"']*\)[\"']/\1/p" src/pbprompt/__init__.py)
DIST_NAME  := pbprompt-$(VERSION)
DIST_DIR   := dist
DIST_TMP   := $(DIST_DIR)/.tmp-$(DIST_NAME)

UI_FILES   := $(wildcard $(SRC_GUI)/*.ui)
PY_UI_FILES := $(UI_FILES:$(SRC_GUI)/%.ui=$(SRC_GUI)/ui_%.py)

.DEFAULT_GOAL := help

.PHONY: all ui resources translations run bundle clean lint test test-cov docs help version bump-patch bump-minor bump-major dist

all: ui resources translations  ## Build everything (UI, resources, translations)

# ---------------------------------------------------------------------------
# Run without installing
# ---------------------------------------------------------------------------
run:  ## Run the application without installing (uses src/ layout)
	PYTHONPATH=src $(PYTHON) -m pbprompt

# ---------------------------------------------------------------------------
# Compile Qt Designer .ui files → ui_*.py
# ---------------------------------------------------------------------------
ui: $(PY_UI_FILES)  ## Compile all .ui files with pyuic5

$(SRC_GUI)/ui_%.py: $(SRC_GUI)/%.ui
	$(PYUIC5) $< -o $@
	@echo "[ui] compiled $< → $@"

# ---------------------------------------------------------------------------
# Compile Qt resource file → resources_rc.py
# ---------------------------------------------------------------------------
resources: $(SRC_GUI)/resources_rc.py  ## Compile resources.qrc with pyrcc5

$(SRC_GUI)/resources_rc.py: $(RESOURCES)/resources.qrc $(wildcard $(RESOURCES)/icons/*)
	$(PYRCC5) $< -o $@
	@echo "[res] compiled $< → $@"

# ---------------------------------------------------------------------------
# Compile gettext translations (.po → .mo)
# ---------------------------------------------------------------------------
translations:  ## Compile all .po files to .mo
	@for lang in $(LOCALE_LANGS); do \
	    dir=$(LOCALES)/$$lang/LC_MESSAGES; \
	    echo "[i18n] compiling $$dir/messages.po"; \
	    $(MSGFMT) $$dir/messages.po -o $$dir/messages.mo; \
	done

# Update .pot template from source
pot:  ## Extract translatable strings from Python sources
	$(XGETTEXT) --language=Python --keyword=_ \
	    --output=$(LOCALES)/messages.pot \
	    --from-code=UTF-8 \
	    $(shell find src -name "*.py" | grep -v ui_ | grep -v resources_rc)
	@echo "[i18n] updated $(LOCALES)/messages.pot"

# Merge updated template into existing .po files
merge-po: pot  ## Merge new strings into .po files
	@for lang in $(LOCALE_LANGS); do \
	    dir=$(LOCALES)/$$lang/LC_MESSAGES; \
	    $(MSGMERGE) --update $$dir/messages.po $(LOCALES)/messages.pot; \
	done

# ---------------------------------------------------------------------------
# Linting / formatting
# ---------------------------------------------------------------------------
lint:  ## Run ruff linter + formatter check
	ruff check src tests
	ruff format --check src tests

format:  ## Auto-format with ruff
	ruff format src tests
	ruff check --fix src tests

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
test:  ## Run pytest
	$(PYTHON) -m pytest tests/

test-cov:  ## Run pytest with coverage
	$(PYTHON) -m pytest tests/ --cov=pbprompt --cov-report=html

# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------
docs:  ## Build Sphinx documentation
	$(MAKE) -C doc html

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
	    pyinstaller \
	        --onefile \
	        --windowed \
	        --name pbprompt \
	        --add-data "locales:locales" \
	        --add-data "resources:resources" \
	        src/pbprompt/__main__.py; \
	else \
	    echo "[bundle] using existing $(SPEC_FILE)"; \
	    pyinstaller $(SPEC_FILE); \
	fi
	@echo "[bundle] binary written to dist/"

# ---------------------------------------------------------------------------
# Version management (semver)
# ---------------------------------------------------------------------------
version:  ## Display the current version
	@grep -E '__version__' src/pbprompt/__init__.py | head -1

bump-patch:  ## Bump patch version  (1.0.0 → 1.0.1)
	$(PYTHON) scripts/bump_version.py patch

bump-minor:  ## Bump minor version  (1.0.1 → 1.1.0, resets patch)
	$(PYTHON) scripts/bump_version.py minor

bump-major:  ## Bump major version  (1.1.0 → 2.0.0, resets minor+patch)
	$(PYTHON) scripts/bump_version.py major

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
